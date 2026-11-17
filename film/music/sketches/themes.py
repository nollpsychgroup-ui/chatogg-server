#!/usr/bin/env python3
"""THE QUIET CAR: theme sketches for the cue sheet (Milestone 3).

    python3 themes.py         # needs numpy; ffmpeg optional (for .mp3)

Three short, self-contained sketches of the film's themes, each as
.mp3 (render; .wav is git-ignored) and .mid (microtuned by pitch bend, +/-2 st):

  theme-1-undertone   THE UNDERTONE, the car's motif (cues 1M1-1M6):
                      x1, x2, x3 cluster, the hungry swell, then the inhale
                      reversed. Over a quiet carriage chord for reference.
  theme-2-relight     1M7 RELIGHT: P3->P12 relight at the script's uneven pace,
                      cello harmonics double partials 4/6/7/9 (G D F A, no third),
                      vibrato freezes on "silence on the line", thins as the train slows.
  theme-3-page-turn   1M8 PAGE TURN: dead-stable hum, nearly subliminal 4:5:6 triad
                      (partials 8/10/12, B = the withheld third), gone before the phone
                      dims; hum to the cut; rails over black, then stop.

Tuning: 50 Hz mains hum (approx. G1 +35c). Panel map P1..P11 = partials 2..12,
P12 = partial 17 (approx. A-flat). See ../score-concept.md and ../cue-sheet.md.
"""
import math, os, shutil, struct, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR, F0 = 44100, 50.0
PANEL_PARTIAL = {i + 1: p for i, p in enumerate(list(range(2, 13)) + [17])}   # P1..P12
HALF = 2 ** (1 / 12)
METAL = (23.1, 31.7, 44.9, 61.3)
rng = np.random.default_rng(11)


class Piece:
    def __init__(self, dur):
        self.dur, self.n = dur, int(SR * dur)
        self.t = np.arange(self.n) / SR
        self.mix = np.zeros(self.n)
        self.midi = []            # (label, program, freq, [(on, off, vel)], vibrato?)

    def env(self, pts):
        xs, ys = zip(*sorted(pts, key=lambda q: q[0]))
        return np.interp(self.t, xs, ys)

    def osc(self, f, harm=((1, 1.0),)):
        ph = 2 * np.pi * np.cumsum(np.broadcast_to(f, (self.n,))) / SR
        return sum(a * np.sin(h * ph) for h, a in harm)

    def panel(self, P, amp_pts, level=1.0, cents_pts=((0, 0),)):
        p = PANEL_PARTIAL[P]
        f = F0 * p * 2 ** (self.env(list(cents_pts) + [(self.dur, cents_pts[-1][1])]) / 1200)
        self.mix += self.env(amp_pts) * level * (0.11 / math.sqrt(p)) * self.osc(f, ((1, 1), (2, .18), (3, .06)))

    def fundamental(self, amp_pts):
        self.mix += self.env(amp_pts) * 0.05 * self.osc(F0, ((1, 1), (2, .5), (3, .35), (4, .2), (5, .12)))

    def undertone(self, start, length, level, width, reverse=False):
        a, b = (1 / HALF, 1.0) if reverse else (HALF, 1 / HALF)
        ratio = self.env([(0, 1), (start, a if reverse else 1), (start + length * .35, a),
                          (start + length * .75, b), (start + length, 1), (self.dur, 1)])
        amp = self.env([(0, 0), (start, 0), (start + length * .3, level),
                        (start + length * .8, level * .8), (start + length, 0), (self.dur, 0)])
        out = np.zeros(self.n)
        for v in {1: [1.0], 2: [1.0, HALF], 3: [1.0, HALF, 1 / HALF]}[width]:
            f = F0 / 2 * v * ratio
            out += self.osc(f, ((1, .6), (2, 1.0), (4, .7), (6, .35), (8, .3), (12, .22), (16, .15)))
            out += .28 * self.osc(f, tuple((m, 1 / (k + 1)) for k, m in enumerate(METAL)))
        noise = np.convolve(rng.standard_normal(self.n), np.ones(220) / 220, mode="same")
        self.mix += amp * (out + .25 * noise * (amp > 0))

    def cello(self, partial, on, off_pts, level, freeze_at=None):
        depth = self.env([(0, 1)] + ([(freeze_at, 1), (freeze_at + 1, 0)] if freeze_at else []) + [(self.dur, 0 if freeze_at else 1)])
        vib = 2 ** (8 * depth * np.sin(2 * np.pi * (5.1 + .07 * partial) * self.t + partial) / 1200)
        amp = self.env([(0, 0), (on, 0), (on + 1.5, 1)] + off_pts)
        self.mix += amp * level * self.osc(F0 * partial * vib, ((1, 1), (2, .35), (3, .18), (4, .08)))

    def tone(self, partial, amp_pts, level):
        self.mix += self.env(amp_pts) * level * self.osc(F0 * partial, ((1, 1), (2, .1)))

    def tick(self, at, level=.25):
        i = int(at * SR)
        self.mix[i:i + 300] += np.exp(-np.arange(300) / 25) * rng.standard_normal(300) * level

    def rails(self, amp_pts):
        rumble = np.convolve(rng.standard_normal(self.n), np.ones(400) / 400, mode="same") * .6
        clack = np.zeros(self.n)
        for c in np.arange(.4, self.dur, .83):
            for off in (0, .11):
                i = int((c + off) * SR)
                if i + 800 < self.n:
                    clack[i:i + 800] += np.exp(-np.arange(800) / 90) * rng.standard_normal(800) * .35
        self.mix += self.env(amp_pts) * (rumble + clack)

    def write(self, name):
        peak = np.max(np.abs(self.mix)) / .89
        base = os.path.join(HERE, name)
        with wave.open(base + ".wav", "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((self.mix / peak * 32767).astype("<i2").tobytes())
        if shutil.which("ffmpeg"):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base + ".wav", "-b:a", "160k",
                            base + ".mp3"], check=False)
        write_midi(base + ".mid", name, self.midi)
        print("wrote", base + ".{wav,mp3,mid}")


# ---------- MIDI ----------------------------------------------------------------
def vlq(n):
    out = [n & 0x7F]
    while n > 127:
        n >>= 7; out.insert(0, (n & 0x7F) | 0x80)
    return bytes(out)


def write_midi(path, title, voices):
    def track(ev):
        ev.sort(key=lambda e: e[0]); data = b""; last = 0
        for sec, msg in ev:
            tk = int(round(sec * 480)); data += vlq(tk - last) + msg; last = tk
        data += b"\x00\xff\x2f\x00"
        return b"MTrk" + struct.pack(">I", len(data)) + data

    def meta_name(s):
        return b"\xff\x03" + vlq(len(s)) + s.encode()

    chans = [c for c in range(16) if c != 9]
    tracks = [track([(0, b"\xff\x51\x03" + (1_000_000).to_bytes(3, "big")), (0, meta_name(title))])]
    for ch, (label, prog, freq, segs) in zip(chans, voices):
        m = 69 + 12 * math.log2(freq / 440); n = int(round(m)); cents = (m - n) * 100
        v = int(8192 + cents / 200 * 8191)
        ev = [(0, meta_name(label)), (0, bytes([0xC0 | ch, prog])), (0, bytes([0xB0 | ch, 101, 0])),
              (0, bytes([0xB0 | ch, 100, 0])), (0, bytes([0xB0 | ch, 6, 2])), (0, bytes([0xB0 | ch, 38, 0])),
              (0, bytes([0xE0 | ch, v & 0x7F, v >> 7]))]
        for on, off, vel in segs:
            ev += [(on, bytes([0x90 | ch, n, vel])), (off, bytes([0x80 | ch, n, 0]))]
        tracks.append(track(ev))
    with open(path, "wb") as fh:
        fh.write(b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), 480) + b"".join(tracks))


# ---------- theme 1: THE UNDERTONE ------------------------------------------------
def theme_undertone():
    D = 30.0
    pc = Piece(D)
    for P in range(1, 13):
        pc.panel(P, [(0, 0), (.5, .6), (D - 1, .6), (D, 0)], level=.5)
    pc.fundamental([(0, 0), (.5, .6), (D - 1, .6), (D, 0)])
    plan = [(1.0, 3.5, .05, 1, "x1 (lie 1)"), (6.0, 4.5, .09, 2, "x2 (lie 2)"),
            (12.0, 6.0, .20, 3, "x3 cluster (Kai)"), (19.5, 1.8, .16, 3, "hungry swell (S-)")]
    for s, ln, lv, w, _ in plan:
        pc.undertone(s, ln, lv, w)
    pc.undertone(24.5, 1.6, .12, 1, reverse=True)       # the inhale shape, rising
    g = F0 / 2 * 4                                      # MIDI an octave+ up so GM can sound it
    segs = {0: [], 1: [], -1: []}
    for s, ln, lv, w, _ in plan:
        vel = int(40 + lv * 300)
        segs[0].append((s, s + ln * .35, vel)); segs[1].append((s + ln * .35, s + ln * .75, vel))
        segs[-1].append((s + ln * .75, s + ln, vel))
    segs[-1].append((24.5, 24.5 + .56, 60)); segs[0].append((24.5 + .56, 26.1, 70))
    pc.midi = [("Undertone G", 43, g, segs[0]), ("Undertone A-flat", 43, g * HALF, segs[1]),
               ("Undertone F-sharp", 43, g / HALF, segs[-1])]
    pc.write("theme-1-undertone")


# ---------- theme 2: RELIGHT ------------------------------------------------------
def theme_relight():
    D = 38.0
    pc = Piece(D)
    # script pace (approx.): 8.0 P1 brighter, 8.1 P3, 8.2 P4, 8.3-8.9 P5-P11 quick, 8.10 P12 last
    relight = {3: 3.0, 4: 13.0, 5: 19.0, 6: 19.7, 7: 20.4, 8: 21.1, 9: 21.8, 10: 22.5, 11: 23.2, 12: 30.0}
    SILENCE, SLOW, DOORS = 27.0, 31.0, 36.0
    pc.panel(1, [(0, .9), (.8, .9), (1.0, 1.25), (1.6, 1.1), (D, 1.1)])     # 8.0: steadies, brighter
    pc.panel(2, [(0, 1), (D, 1)])
    for P, at in relight.items():
        pc.panel(P, [(0, 0), (at, 0), (at + .05, 1.12), (at + .5, 1), (D, 1)])
        pc.tick(at)
    pc.fundamental([(0, 1), (D, 1)])
    pc.undertone(-4.0, 22.0, .10, 3)                    # receding under the confession
    warm = {4: 3, 6: 5, 7: 6, 9: 8}                     # partial -> panel
    for p, P in warm.items():
        pc.cello(p, relight[P], [(SLOW, 1), (DOORS - .5, 0)], .018 / math.sqrt(p / 4), freeze_at=SILENCE)
    pc.rails([(0, .45), (SLOW, .45), (DOORS, .15), (D, .1)])
    pc.midi = [(f"P{P} partial {PANEL_PARTIAL[P]}", 89, F0 * PANEL_PARTIAL[P],
                [(relight.get(P, 0), D, 60)]) for P in range(1, 13)]
    pc.midi += [(f"cello harmonic {p} (with P{P})", 42, F0 * p, [(relight[P], DOORS - .5, 55)])
                for p, P in warm.items()]
    pc.write("theme-2-relight")


# ---------- theme 3: PAGE TURN ----------------------------------------------------
def theme_page_turn():
    D = 18.0
    TURN, GONE, PHONE, CUT, STOP = 1.0, 9.5, 10.5, 14.0, 16.3
    pc = Piece(D)
    for P in range(1, 13):
        late = [(TURN + 1, 1), (TURN + 7, .35)] if PANEL_PARTIAL[P] >= 5 else []
        pc.panel(P, [(0, 1), (TURN, 1)] + late + [(CUT - .001, .35 if late else 1), (CUT, 0)])
    pc.fundamental([(0, 1), (CUT - .001, 1), (CUT, 0)])
    rel = [(0, 0), (TURN, 0), (TURN + 4, 1), (GONE - 3, .8), (GONE, 0)]
    for p, lv in ((8, .016), (10, .013), (12, .011)):
        pc.tone(p, rel, lv)
    pc.rails([(0, .5), (STOP - .3, .5), (STOP, 0)])
    pc.midi = [(f"hum P{P}", 89, F0 * PANEL_PARTIAL[P], [(0, CUT, 55)]) for P in range(1, 13)]
    pc.midi += [(f"release partial {p}", 11, F0 * p, [(TURN + d, GONE, 40)])
                for p, d in ((8, 0), (10, .6), (12, 1.2))]
    pc.write("theme-3-page-turn")
    print(f"   page turn {TURN}s, triad gone {GONE}s, phone dims {PHONE}s, cut {CUT}s, rails stop {STOP}s")


if __name__ == "__main__":
    theme_undertone(); theme_relight(); theme_page_turn()
