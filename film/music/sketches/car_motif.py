#!/usr/bin/env python3
"""THE QUIET CAR: motif sketch 01, "The Carriage Chord" and "The Undertone".

Produces two files next to this script:
  car-motif-sketch-01.mid  multitrack MIDI, one channel per ceiling panel,
                           microtuned with pitch bend (bend range +/-2 st)
  car-motif-sketch-01.wav  an additive-synthesis render so the idea can be
                           heard without a synth (also .mp3 if ffmpeg exists)

Concept (see ../score-concept.md):
  * The carriage's mains hum is 50 Hz (UK). Each lit ceiling panel "sings"
    one partial of the harmonic series on 50 Hz (partials 2..11). Fully lit
    car = the whole series, fused into what sounds like ordinary hum.
  * A lie detunes panels and wakes THE UNDERTONE, the car's voice, which sits
    below the hum and moves by a half step around G (G -> A-flat -> F-sharp -> G).
  * Panels going dark remove partials; relighting restores them.
  * The release ("Thank you for riding quietly") is a pure 4:5:6 triad on
    partials 8, 10, 12, the only sound in the film that can't be the train.

Timeline of the sketch (seconds). This is a demo of the system, not the cue:
   0-10  panels come on one by one (in the film they are simply already on)
  11     Noor boards: a tick and one subliminal wobble (Director note M3)
  15     lie 1 "just leaving the office": 1 panel bends, faint undertone
  21     lie 2 "the Henley account": 2 panels bend, louder undertone
  28     Kai's lie: brownout, every partial sags, undertone from the walls
  35     BLACKOUT: true digital silence, rails included
  38.5   the inhale (undertone reversed), cut
  40     lights up: chord back, steady and indifferent
  45-61  panels go out one by one toward Noor, top partials first
  63-73  confession: one partial relights per true sentence, bottom up
  76     door chime (tuned to the series)
  79-92  release triad as Walter turns the page; the hum thins to nothing
  92-96  rails alone, then stop
"""
import math, os, struct, shutil, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
DUR = 97.0
F0 = 50.0                      # mains hum = tonal centre (approx. G1 +35 cents)
PARTIALS = list(range(2, 12))  # one per ceiling panel, near panel = low partial
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def env(points, default=0.0):
    """Piecewise-linear curve from [(time, value), ...]."""
    if not points:
        return np.full(N, default)
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)


def osc(freq_curve, harmonics=((1, 1.0),)):
    phase = 2 * np.pi * np.cumsum(freq_curve) / SR
    return sum(a * np.sin(h * phase) for h, a in harmonics)


# ---------- events -----------------------------------------------------------
BLACK_IN, BLACK_OUT = 35.0, 40.0
ticks = [11.0]                                   # boarding tick
panel_out = {p: 45.0 + i * 2.0 for i, p in enumerate(reversed(PARTIALS[2:]))}  # 11..4 go dark
panel_in = {p: 63.0 + i * 1.25 for i, p in enumerate(PARTIALS[2:])}             # 4..11 relight
ticks += list(panel_out.values()) + list(panel_in.values())

# detune (cents) per partial: lies bend specific panels, Kai's lie sags them all
def detune_points(p):
    pts = [(0, 0)]
    if p == 7:   # subliminal wobble at boarding
        pts += [(11.0, 0), (11.15, -25), (11.5, 0)]
    if p == 7:   # lie 1
        pts += [(15.0, 0), (15.3, -45), (16.0, 10), (16.6, -35), (18.5, 0)]
    if p in (7, 9):  # lie 2
        pts += [(21.0, 0), (21.3, -55), (22.2, 15), (23.0, -50), (25.5, 0)]
    pts += [(28.0, 0), (29.5, -70), (35.0, -90), (40.0, 0)]  # brownout sag, snap back
    pts.sort()
    return pts

def amp_points(p, idx):
    on = 0.6 + idx * 0.95                      # build-up in the demo
    pts = [(0, 0), (on, 0), (on + 0.4, 1)]
    pts += [(28.0, 1), (30.0, 0.45), (BLACK_IN - 0.001, 0.45), (BLACK_IN, 0)]
    pts += [(BLACK_OUT - 0.001, 0), (BLACK_OUT, 1)]
    if p in panel_out:
        pts += [(panel_out[p], 1), (panel_out[p] + 0.03, 0)]
        pts += [(panel_in[p], 0), (panel_in[p] + 0.05, 1.1)]
    # release: the hum thins out from the top as the triad takes over
    fade_at = 80.0 + (11 - p) * -0.6 + 6
    pts += [(fade_at, 1), (fade_at + 4, 0)]
    pts.sort(key=lambda x: x[0])
    return pts

mix = np.zeros(N)

# the carriage chord
for idx, p in enumerate(PARTIALS):
    cents = env(detune_points(p))
    freq = F0 * p * 2 ** (cents / 1200)
    freq += 0.15 * np.sin(2 * np.pi * (0.07 + 0.013 * p) * t)   # ballast drift
    a = env(amp_points(p, idx)) * (0.11 / math.sqrt(p))
    mix += a * osc(freq, ((1, 1.0), (2, 0.18), (3, 0.06)))

# the fundamental hum (50 Hz) with buzz, also dies in the blackout
hum_amp = env([(0, 0), (0.5, 0.05), (BLACK_IN - 0.001, 0.05), (BLACK_IN, 0),
               (BLACK_OUT - 0.001, 0), (BLACK_OUT, 0.05), (86, 0.05), (91, 0)])
mix += hum_amp * osc(np.full(N, F0), ((1, 1), (2, .5), (3, .35), (4, .2), (5, .12)))

# THE UNDERTONE: the car's motif, G -> A-flat -> F-sharp -> G, an octave below hum.
# Each waking is louder and wider (Director note M2).
def undertone(start, length, level, width):
    """width 1 = single voice motif, 3 = full half-step cluster."""
    g = F0 / 2  # 25 Hz is felt more than heard; we double at 50 and 100 Hz
    half = 2 ** (1 / 12)
    path = [(start, 1.0), (start + length * .35, half), (start + length * .75, 1 / half),
            (start + length, 1.0)]
    ratio = env([(0, 1.0)] + path + [(DUR, 1.0)])
    a = env([(0, 0), (start, 0), (start + length * .3, level), (start + length * .8, level * .8),
             (start + length, 0), (DUR, 0)])
    out = np.zeros(N)
    voices = [1.0] if width == 1 else ([1.0, half, 1 / half] if width == 3 else [1.0, half])
    for v in voices:
        f = g * v * ratio
        out += osc(f, ((1, .6), (2, 1.0), (4, .5), (6, .2), (8, .08)))
    # breath: band-limited noise shaped by the same envelope
    noise = rng.standard_normal(N)
    out += 0.25 * np.convolve(noise, np.ones(220) / 220, mode="same") * (a > 0)
    return a * out

mix += undertone(11.0, 1.2, 0.015, 1)    # almost nothing at boarding
mix += undertone(15.0, 3.5, 0.06, 1)
mix += undertone(21.0, 4.5, 0.11, 2)
mix += undertone(28.0, 7.0, 0.22, 3)     # cut hard by the blackout below
mix += undertone(45.0, 18.0, 0.14, 3)    # patient rise under the creeping dark
mix *= np.where((t >= BLACK_IN) & (t < BLACK_OUT), 0.0, 1.0)

# the inhale in the dark: undertone motif reversed (rising), plus air
inh = (t >= 38.5) & (t < 39.9)
x = np.clip((t - 38.5) / 1.4, 0, 1)
f = F0 / 2 * 2 ** ((x * 2 - 1) / 12) * 2
breath = rng.standard_normal(N)
breath = np.convolve(breath, np.ones(30) / 30, mode="same")
mix += inh * (x ** 2) * (0.25 * osc(f, ((1, 1), (2, .6), (3, .3))) + 0.5 * breath)

# rails: rumble and clacks, silent in the blackout, gone at the end
rumble = np.convolve(rng.standard_normal(N), np.ones(400) / 400, mode="same") * 0.6
rail_amp = env([(0, 0.0), (0.3, 0.5), (BLACK_IN - 0.001, .5), (BLACK_IN, 0),
                (BLACK_OUT - 0.001, 0), (BLACK_OUT, .5), (74, .5), (76, .15),
                (79, .15), (81, .5), (95.0, .5), (95.3, 0)])
clack = np.zeros(N)
for c in np.arange(0.4, DUR, 0.83):
    for off in (0, 0.11):
        i = int((c + off) * SR)
        if i + 800 < N:
            clack[i:i + 800] += np.exp(-np.arange(800) / 90) * rng.standard_normal(800) * .35
mix += rail_amp * (rumble + clack)

# panel ticks (relay clicks, a sound-design element; here as placeholders)
for tk in ticks:
    i = int(tk * SR)
    mix[i:i + 300] += np.exp(-np.arange(300) / 25) * rng.standard_normal(300) * 0.25

# door chime, tuned to partials 9 and 6 (A+39c, D+37c): in tune with the car
def bell(start, freq, level):
    a = np.where(t >= start, np.exp(-(t - start) * 2.2), 0) * level
    return a * osc(np.full(N, freq), ((1, 1), (2.76, .3), (5.4, .1)))
mix += bell(76.0, F0 * 18, 0.07) + bell(76.45, F0 * 12, 0.08)

# THE RELEASE: pure 4:5:6 triad on partials 8, 10, 12, as Walter turns the page.
rel = env([(0, 0), (79.0, 0), (84.0, 1), (89.0, .9), (93.5, 0), (DUR, 0)])
for p, lv in ((8, .05), (10, .04), (12, .035)):
    vib = 1 + 0.0012 * np.sin(2 * np.pi * 4.6 * t)
    mix += rel * lv * osc(F0 * p * vib, ((1, 1), (2, .12), (4, .03)))

# ---------- write WAV ---------------------------------------------------------
mix /= max(1e-9, np.max(np.abs(mix))) / 0.89
mix *= np.where((t >= BLACK_IN) & (t < 38.5), 0.0, 1.0)  # true dead air
pcm = (mix * 32767).astype("<i2")
wav_path = os.path.join(HERE, "car-motif-sketch-01.wav")
with wave.open(wav_path, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

if shutil.which("ffmpeg"):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path, "-b:a", "160k",
                    wav_path[:-4] + ".mp3"], check=False)

# ---------- write MIDI (same system, microtuned by pitch bend) ----------------
TPQ, BPM = 480, 60          # 1 beat = 1 second, so ticks = seconds * 480

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

def name(s): return b"\xff\x03" + vlq(len(s)) + s.encode()

def note_and_bend(freq, extra_cents=0.0):
    m = 69 + 12 * math.log2(freq / 440)
    n = int(round(m)); cents = (m - n) * 100 + extra_cents
    return n, cents

def bend_msg(ch, cents):
    v = int(8192 + max(-200, min(200, cents)) / 200 * 8191)
    return bytes([0xE0 | ch, v & 0x7F, v >> 7])

tracks = [track([(0, b"\xff\x51\x03" + (1_000_000).to_bytes(3, "big")),
                 (0, name("THE QUIET CAR - motif sketch 01"))])]
channels = [c for c in range(16) if c != 9]

def add_voice(label, ch, freq, segments, detune=None, program=0):
    """segments: [(on, off, velocity)]; detune: [(time, cents)] (step-sampled)."""
    n, base = note_and_bend(freq)
    ev = [(0, name(label)), (0, bytes([0xC0 | ch, program])),
          (0, bytes([0xB0 | ch, 101, 0])), (0, bytes([0xB0 | ch, 100, 0])),
          (0, bytes([0xB0 | ch, 6, 2])), (0, bytes([0xB0 | ch, 38, 0])),   # bend range 2 st
          (0, bend_msg(ch, base))]
    if detune:
        xs, ys = zip(*detune)
        for s in np.arange(xs[0], xs[-1], 0.05):
            ev.append((float(s), bend_msg(ch, base + float(np.interp(s, xs, ys)))))
    for on, off, vel in segments:
        if off > on:
            ev += [(on, bytes([0x90 | ch, n, vel])), (off, bytes([0x80 | ch, n, 0]))]
    tracks.append(track(ev))

for idx, p in enumerate(PARTIALS):
    on = 0.6 + idx * 0.95
    end = 80.0 + (11 - p) * -0.6 + 10
    segs = [(on, BLACK_IN, 70), (BLACK_OUT, end, 70)]
    if p in panel_out:
        segs = [(on, BLACK_IN, 70), (BLACK_OUT, panel_out[p], 70), (panel_in[p], end, 78)]
    add_voice(f"panel {idx+1} (partial {p})", channels[idx], F0 * p, segs,
              detune=detune_points(p), program=89)       # GM 90 "Warm Pad"

# undertone motif on a low voice (GM 43 contrabass, program 43)
ut = channels[10]
ev = [(0, name("THE UNDERTONE (car motif)")), (0, bytes([0xC0 | ut, 43]))]
n_g = note_and_bend(F0)[0]          # G1
for start, length, vel in ((15, 3.5, 50), (21, 4.5, 70), (28, 7.0, 100), (45, 18, 85)):
    seq = [(n_g, 0, .35), (n_g + 1, .35, .75), (n_g - 1, .75, 1.0)]
    for nn, a, b in seq:
        ev += [(start + a * length, bytes([0x90 | ut, nn, vel])),
               (start + b * length, bytes([0x80 | ut, nn, 0]))]
ev += [(38.5, bytes([0x90 | ut, n_g - 1, 40])), (39.2, bytes([0x80 | ut, n_g - 1, 0])),
       (39.2, bytes([0x90 | ut, n_g, 60])), (39.9, bytes([0x80 | ut, n_g, 0]))]
tracks.append(track(ev))

# release triad (GM 12 vibraphone, bowed in the real score)
add_voice("release: partial 8", channels[11], F0 * 8, [(79, 93.5, 64)], program=11)
add_voice("release: partial 10", channels[12], F0 * 10, [(79.6, 93.5, 58)], program=11)
add_voice("release: partial 12", channels[13], F0 * 12, [(80.2, 93.5, 54)], program=11)

mid_path = os.path.join(HERE, "car-motif-sketch-01.mid")
with open(mid_path, "wb") as fh:
    fh.write(b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), TPQ) + b"".join(tracks))

print("wrote", wav_path, "and", mid_path)
