#!/usr/bin/env python3
"""THE QUIET CAR: motif sketch 01 (rev 2), the Carriage Chord, the Undertone,
the relight warmth and the release.

    python3 car_motif.py      # needs numpy; ffmpeg optional (for the .mp3)

Writes next to this script:
  car-motif-sketch-01.wav / .mp3   additive-synthesis render (mono)
  car-motif-sketch-01.mid          multitrack MIDI, microtuned by pitch bend
                                   (bend range +/-2 st, one channel per panel)
  phone-check.txt                  how much of the Undertone survives a phone speaker

System (see ../score-concept.md):
  * Mains hum 50 Hz (approx. G1 +35c) is the tonal centre.
  * 12 ceiling panels = 12 voices. Panels 1-11 sing partials 2-12 of the
    harmonic series on 50 Hz (Noor's panel = partial 2). The far panel is a
    deliberate impurity: partial 17, approx. A-flat, the car's note.
  * Lies bend partials, barely at first (10-20c), clearly only at Kai's brownout.
  * THE UNDERTONE (car motif): G -> A-flat -> F-sharp -> G, an octave below the
    hum, doubled at 100-200 Hz plus a bowed-metal grain so phones still hear it.
  * Relight warmth: cello harmonics double partials 4, 6, 7, 9 as they relight
    (G D F A, third withheld). Release: just 4:5:6 triad on partials 8/10/12
    on Walter's page turn, nearly subliminal. The hum stays to the cut.

Demo timeline (seconds), a demo of the system, not the cue:
   0-9.4  panels come on one by one (in the film the car is simply lit)
  11      Noor boards: 2-frame wobble on her panel (M3)
  15      lie 1: one partial bends ~10c, Undertone x1
  21      lie 2: two partials bend ~20c, Undertone x2
  28      Kai's lie: brownout, whole chord sags ~80c flat, full cluster
  35      BLACKOUT: digital zero, rails included
  38.5    the inhale (sound-design placeholder, pitched F#->G)
  40      lights up: hum back, in tune and indifferent
  45-61   panels go out toward Noor: A-flat panel first, then 12..4
  63-72   confession: panels relight outward from Noor (4..12, A-flat last);
          cello warmth on 4/6/7/9; vibrato freezes at 70 ("silence on the line")
  74-77   warmth thins as the train slows
  77      door chime (partials 18 then 12); 79-82 PA line (unscored)
  83-91   release triad on the page turn, gone by 91.5 (phone dims at 92)
  94      CUT TO BLACK: hum cut; rails continue to 96.3, then stop
"""
import math, os, shutil, struct, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR, DUR = 44100, 97.5
F0 = 50.0
PANELS = list(range(2, 13)) + [17]           # panel index 0 = above Noor
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)

BLACK_IN, BLACK_OUT = 35.0, 40.0
CUT = 94.0
far_first = [17] + list(range(12, 3, -1))     # sequential out (cue 7)
outward = list(range(4, 13)) + [17]           # relight outward from Noor (cue 8)
panel_out = {p: 45.0 + i * 1.6 for i, p in enumerate(far_first)}
panel_in = {p: 63.0 + i * 0.95 for i, p in enumerate(outward)}
LAST_RELIGHT = panel_in[17]
WARM = (4, 6, 7, 9)                           # cello-doubled partials, no 5 (the third)
FREEZE, WARM_OUT = 70.0, (74.0, 77.0)
REL = (83.0, 91.5)


def env(points):
    xs, ys = zip(*sorted(points, key=lambda q: q[0]))
    return np.interp(t, xs, ys)


def osc(freq, harmonics=((1, 1.0),)):
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return sum(a * np.sin(h * phase) for h, a in harmonics)


def gate(*spans):
    g = np.zeros(N)
    for a, b in spans:
        g[(t >= a) & (t < b)] = 1
    return g


# ---------- the carriage chord ----------------------------------------------
def detune(p):
    pts = [(0, 0), (DUR, 0)]
    if p == 2:                                   # boarding: 2 frames, ~8c
        pts += [(11.0, 0), (11.04, -8), (11.08, 0)]
    if p == 2:                                   # lie 1: ~10c, felt not heard
        pts += [(15.0, 0), (15.3, -11), (16.0, 3), (16.6, -9), (18.5, 0)]
    if p in (2, 3):                              # lie 2: ~20c
        pts += [(21.0, 0), (21.3, -20), (22.2, 5), (23.0, -18), (25.5, 0)]
    if p == 2:                                   # "I'm f-" stutter, small
        pts += [(41.5, 0), (41.6, -12), (41.75, 0), (41.85, -10), (42.0, 0)]
    pts += [(28.0, 0), (29.5, -70), (BLACK_IN, -90), (BLACK_OUT, 0)]   # brownout
    return pts


def amp(idx, p):
    on = 0.6 + idx * 0.8
    pts = [(0, 0), (on, 0), (on + 0.4, 1), (28.0, 1), (30.0, .45),
           (BLACK_IN - .001, .45), (BLACK_IN, 0), (BLACK_OUT - .001, 0), (BLACK_OUT, 1)]
    if p in panel_out:
        po, pi = panel_out[p], panel_in[p]
        pts += [(po, 1), (po + .03, 0), (pi, 0), (pi + .05, 1.12), (pi + .5, 1)]  # 110% overshoot
    if p >= 5:                                   # gentle thinning from the top at the end
        pts += [(84.0, 1), (90.0, .35)]
    pts += [(CUT - .001, pts[-1][1] if p < 5 else .35), (CUT, 0)]
    return pts


breathe = 1 + 0.03 * np.sin(2 * np.pi * t / 5.0) * gate((15.0, LAST_RELIGHT + .5))
hum = np.zeros(N)
for idx, p in enumerate(PANELS):
    f = F0 * p * 2 ** (env(detune(p)) / 1200) + 0.15 * np.sin(2 * np.pi * (.07 + .013 * idx) * t)
    hum += env(amp(idx, p)) * breathe * (0.11 / math.sqrt(p)) * osc(f, ((1, 1), (2, .18), (3, .06)))
fund = env([(0, 0), (.5, .05), (BLACK_IN - .001, .05), (BLACK_IN, 0), (BLACK_OUT - .001, 0),
            (BLACK_OUT, .05), (CUT - .001, .05), (CUT, 0)])
hum += fund * osc(np.full(N, F0), ((1, 1), (2, .5), (3, .35), (4, .2), (5, .12)))

# ---------- THE UNDERTONE ------------------------------------------------------
HALF = 2 ** (1 / 12)
METAL = (23.1, 31.7, 44.9, 61.3)                 # bowed-cymbal-ish inharmonic ratios


def undertone(start, length, level, width):
    path = [(0, 1.0), (start, 1.0), (start + length * .35, HALF),
            (start + length * .75, 1 / HALF), (start + length, 1.0), (DUR, 1.0)]
    ratio = env(path)
    a = env([(0, 0), (start, 0), (start + length * .3, level), (start + length * .8, level * .8),
             (start + length, 0), (DUR, 0)])
    voices = {1: [1.0], 2: [1.0, HALF], 3: [1.0, HALF, 1 / HALF]}[width]
    out = np.zeros(N)
    for v in voices:
        f = F0 / 2 * v * ratio
        out += osc(f, ((1, .6), (2, 1.0), (4, .7), (6, .35), (8, .3), (12, .22), (16, .15)))  # 25..400 Hz
        out += 0.28 * osc(f, tuple((m, 1 / (k + 1)) for k, m in enumerate(METAL)))  # grain
    noise = np.convolve(rng.standard_normal(N), np.ones(220) / 220, mode="same")
    return a * (out + 0.25 * noise * (a > 0))


und = (undertone(15.0, 3.5, .04, 1) + undertone(21.0, 4.5, .08, 2) +
       undertone(28.0, 7.0, .22, 3) + undertone(43.0, 1.6, .16, 3) +       # "S-": hungry swell
       undertone(45.0, 18.0, .14, 3))
dark = gate((BLACK_IN, BLACK_OUT))
hum *= 1 - dark
und *= 1 - dark

# inhale in the dark (SD placeholder, pitched F# -> G)
x = np.clip((t - 38.5) / 1.4, 0, 1)
inh = gate((38.5, 39.9)) * x ** 2
f = F0 * 2 ** ((x * 2 - 1) / 12)
breath = np.convolve(rng.standard_normal(N), np.ones(30) / 30, mode="same")
sfx = inh * (.25 * osc(f, ((1, 1), (2, .6), (3, .3))) + .5 * breath)

# ---------- relight warmth: cello harmonics, third withheld --------------------
warm = np.zeros(N)
vib_depth = env([(0, 1), (FREEZE, 1), (FREEZE + 1.0, 0), (DUR, 0)])          # vibrato freezes
for k, p in enumerate(WARM):
    on = panel_in[p]
    a = env([(0, 0), (on, 0), (on + 1.5, 1), (WARM_OUT[0], 1), (WARM_OUT[1], 0), (DUR, 0)])
    vib = 2 ** (8 * vib_depth * np.sin(2 * np.pi * (5.1 + .3 * k) * t + k) / 1200)
    warm += a * (.018 / math.sqrt(p / 4)) * osc(F0 * p * vib, ((1, 1), (2, .35), (3, .18), (4, .08)))

# ---------- release triad on the page turn (nearly subliminal) -----------------
rel = env([(0, 0), (REL[0], 0), (REL[0] + 4, 1), (REL[1] - 3, .8), (REL[1], 0), (DUR, 0)])
release = sum(rel * lv * osc(np.full(N, F0 * p), ((1, 1), (2, .1)))
              for p, lv in ((8, .016), (10, .013), (12, .011)))

# ---------- sound-design placeholders: rails, ticks, chime ----------------------
rumble = np.convolve(rng.standard_normal(N), np.ones(400) / 400, mode="same") * .6
rails_amp = env([(0, 0), (.3, .5), (BLACK_IN - .001, .5), (BLACK_IN, 0), (BLACK_OUT - .001, 0),
                 (BLACK_OUT, .5), (75, .5), (77, .15), (82, .15), (84, .5), (96.0, .5), (96.3, 0)])
clack = np.zeros(N)
for c in np.arange(.4, DUR, .83):
    for off in (0, .11):
        i = int((c + off) * SR)
        if i + 800 < N:
            clack[i:i + 800] += np.exp(-np.arange(800) / 90) * rng.standard_normal(800) * .35
sfx += rails_amp * (rumble + clack)
for tk in [11.0] + list(panel_out.values()) + list(panel_in.values()):
    i = int(tk * SR)
    sfx[i:i + 300] += np.exp(-np.arange(300) / 25) * rng.standard_normal(300) * .25
for start, p, lv in ((77.0, 18, .07), (77.45, 12, .08)):
    a = np.where(t >= start, np.exp(-(t - start) * 2.2), 0) * lv
    sfx += a * osc(np.full(N, F0 * p), ((1, 1), (2.76, .3), (5.4, .1)))

# ---------- mix & write ---------------------------------------------------------
mix = hum + und + warm + release + sfx
mix *= 1 - gate((BLACK_IN, 38.5))                       # true dead air
peak = np.max(np.abs(mix)) / .89
mix, und_n = mix / peak, und / peak

base = os.path.join(HERE, "car-motif-sketch-01")
with wave.open(base + ".wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
if shutil.which("ffmpeg"):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base + ".wav", "-b:a", "160k",
                    base + ".mp3"], check=False)


# ---------- phone-speaker check -------------------------------------------------
def band(sig, lo, hi):
    spec = np.fft.rfft(sig)
    fr = np.fft.rfftfreq(len(sig), 1 / SR)
    spec[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(spec, len(sig))


def db(x):
    return 20 * math.log10(max(1e-9, float(np.sqrt(np.mean(x ** 2)))))


lines = ["Phone-speaker check (phone band = 300 Hz - 6 kHz, roughly a phone/laptop speaker)",
         "Undertone level relative to the full mix in the same section, in dB:", ""]
for label, a, b in (("lie 2", 21.0, 25.5), ("brownout", 28.0, 35.0), ("creeping dark", 47.0, 60.0)):
    s = slice(int(a * SR), int(b * SR))
    full_rel = db(und_n[s]) - db(mix[s])
    ph_rel = db(band(und_n[s], 300, 6000)) - db(band(mix[s], 300, 6000))
    lines.append(f"  {label:14s} full range {full_rel:6.1f} dB   phone band {ph_rel:6.1f} dB")
lines += ["", "A phone-band figure within ~10 dB of full range means the motif still reads on a phone."]
open(os.path.join(HERE, "phone-check.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

# ---------- MIDI ---------------------------------------------------------------
TPQ = 480                                       # tempo 60 bpm: 1 beat = 1 s


def vlq(n):
    out = [n & 0x7F]
    while n > 127:
        n >>= 7; out.insert(0, (n & 0x7F) | 0x80)
    return bytes(out)


def track(events):
    events.sort(key=lambda e: e[0]); data = b""; last = 0
    for sec, msg in events:
        tk = int(round(sec * TPQ)); data += vlq(tk - last) + msg; last = tk
    data += b"\x00\xff\x2f\x00"
    return b"MTrk" + struct.pack(">I", len(data)) + data


def name(s):
    return b"\xff\x03" + vlq(len(s)) + s.encode()


def nb(freq):
    m = 69 + 12 * math.log2(freq / 440); n = int(round(m)); return n, (m - n) * 100


def bend(ch, cents):
    v = int(8192 + max(-200, min(200, cents)) / 200 * 8191)
    return bytes([0xE0 | ch, v & 0x7F, v >> 7])


def setup(ch, program, label, cents):
    return [(0, name(label)), (0, bytes([0xC0 | ch, program])), (0, bytes([0xB0 | ch, 101, 0])),
            (0, bytes([0xB0 | ch, 100, 0])), (0, bytes([0xB0 | ch, 6, 2])),
            (0, bytes([0xB0 | ch, 38, 0])), (0, bend(ch, cents))]


def notes(ch, n, segs):
    ev = []
    for on, off, vel in segs:
        if off > on:
            ev += [(on, bytes([0x90 | ch, n, vel])), (off, bytes([0x80 | ch, n, 0]))]
    return ev


CH = [c for c in range(16) if c != 9]           # 15 melodic channels
tracks = [track([(0, b"\xff\x51\x03" + (1_000_000).to_bytes(3, "big")),
                 (0, name("THE QUIET CAR - motif sketch 01 rev 2"))])]

for idx, p in enumerate(PANELS):                # channels 0-11: panels, GM 90 warm pad
    ch = CH[idx]; n, base_c = nb(F0 * p); on = .6 + idx * .8
    ev = setup(ch, 89, f"panel {idx + 1} (partial {p})", base_c)
    xs, ys = zip(*sorted(detune(p)))
    ev += [(float(s), bend(ch, base_c + float(np.interp(s, xs, ys)))) for s in np.arange(0, 42.5, .05)]
    segs = [(on, BLACK_IN, 70)]
    segs += ([(BLACK_OUT, panel_out[p], 70), (panel_in[p], CUT, 78)] if p in panel_out
             else [(BLACK_OUT, CUT, 70)])
    tracks.append(track(ev + notes(ch, n, segs)))

ch = CH[12]; ng = nb(F0)[0]                     # Undertone, GM 44 contrabass
ev = [(0, name("THE UNDERTONE (car motif)")), (0, bytes([0xC0 | ch, 43]))]
for s0, ln, vel in ((15, 3.5, 45), (21, 4.5, 65), (28, 7.0, 100), (43, 1.6, 95), (45, 18, 85)):
    for nn, a, b in ((ng, 0, .35), (ng + 1, .35, .75), (ng - 1, .75, 1.0)):
        ev += notes(ch, nn, [(s0 + a * ln, min(s0 + b * ln, BLACK_IN if s0 == 28 else 1e9), vel)])
tracks.append(track(ev))

ch = CH[13]                                     # cello warmth, GM 43 cello (one shared bend)
ev = setup(ch, 42, "relight warmth: cello harmonics 4/6/7/9 (approx. tuning)", nb(F0 * 4)[1])
for p in WARM:
    ev += notes(ch, nb(F0 * p)[0], [(panel_in[p], WARM_OUT[1], 50)])
tracks.append(track(ev))

ch = CH[14]                                     # release, GM 12 vibraphone (one shared bend)
ev = setup(ch, 11, "release triad 8/10/12 (approx. tuning)", nb(F0 * 8)[1])
for p, d in ((8, 0), (10, .6), (12, 1.2)):
    ev += notes(ch, nb(F0 * p)[0], [(REL[0] + d, REL[1], 40)])
tracks.append(track(ev))

with open(base + ".mid", "wb") as fh:
    fh.write(b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), TPQ) + b"".join(tracks))
print("wrote", base + ".{wav,mp3,mid}")
