#!/usr/bin/env python3
"""THE QUIET CAR: rough temp score for the previs animatic (Milestone 4).

    python3 render_temp_score.py [cues.json]

Reads the shared cue timeline (default: ../../camera/cues.json if it exists, else
./cues-provisional.json) and renders the whole film's score system against it, the
same way music/cue-sheet.md describes it (1M0 bed + 1M1-1M8). Outputs next to this script:

  temp-score.mp3       music only (hum bed, Undertone, cello warmth, release)
  temp-mix.mp3         music + temp sound-design placeholders (rails, relay ticks,
                       door chimes, the inhale), for cutting the animatic
  temp-sfx.mp3         the temp sound-design stem alone (temp-score + temp-sfx = temp-mix)
  *-48k.flac           48 kHz stereo lossless versions of all three, for the TA to mux
  temp-sync-report.txt every cue/event time actually used, so picture can check sync

Dialogue windows (kept clear: Undertone/cellos -4 dB, rails -3 dB) come from the 'dialogue'
array in camera/cues.json (DP's build_cues.py; it also refuses any tick inside a line).
  (.wav versions are written too but git-ignored)

Sample rate is 24 kHz mono: a rough temp, not a final. The cue file format is
documented in cues-provisional.json; times are seconds from the first frame.
"""
import json, math, os, shutil, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.normpath(os.path.join(HERE, "..", "..", "camera", "cues.json"))
SR, F0 = 24000, 50.0
PARTIAL = {f"P{i + 1}": p for i, p in enumerate(list(range(2, 13)) + [17])}
HALF = 2 ** (1 / 12)
METAL = (23.1, 31.7, 44.9, 61.3)
BREATH_DEPTH, BREATH_PERIOD = 0.03, 5.0
WARM = {"P3": 4, "P5": 6, "P6": 7, "P8": 9}        # cello-doubled panels (B / P4 withheld)
rng = np.random.default_rng(3)

# ---------- load cues --------------------------------------------------------------
path = sys.argv[1] if len(sys.argv) > 1 else (SHARED if os.path.exists(SHARED) else
                                              os.path.join(HERE, "cues-provisional.json"))
doc = json.load(open(path))
cues = sorted(doc["cues"], key=lambda c: c["t"])
EV = {e["id"]: float(e["t"]) for e in doc.get("events", [])}
by_type = lambda ty: [c for c in cues if c["type"] == ty]
first = lambda ty: by_type(ty)[0]["t"]

T_BLACK, T_UP = first("blackout"), first("lights_up")
T_BROWN, T_DIP, T_STUT, T_TICK = first("brownout"), first("hard_dip"), first("stutter"), first("tick")
flick = by_type("flicker")
outs = by_type("panel_out")
rels = by_type("relight")
T_STEADY = first("steady")
# shared values from the DP's file when present (single source of truth)
if "panels" in doc:
    PARTIAL = {pn["id"]: pn["partial"] for pn in doc["panels"]}
BR = doc.get("breath", {})
BREATH_DEPTH = BR.get("depth", BREATH_DEPTH)
BREATH_PERIOD = BR.get("period_s", BREATH_PERIOD)
cue_t = {c["id"]: c["t"] for c in cues}
T_BREATH_ON = cue_t.get(BR.get("on_cue", "1"), flick[0]["t"])
T_BREATH_OFF = cue_t.get(BR.get("off_cue", ""), None)
DIP = by_type("hard_dip")[0]
DIP_MAIN = DIP.get("main", DIP["panels"][0])
DIP_SYMP = list(DIP.get("sympathy", {}) or [q for q in DIP["panels"] if q != DIP_MAIN])
DIP_REC = DIP.get("recover", {})
T_DIP_REC = DIP_REC.get("t", T_DIP + 2)
T_DIP_END = T_DIP_REC + DIP_REC.get("frames", 96) / float(doc.get("fps", 24))
T_LAST_REL = rels[-1]["t"]
CUT = EV["cut"]
DUR = float(doc.get("duration_s", CUT + 5))
N = int(SR * DUR)
t = (np.arange(N) / SR).astype(np.float32)


def env(points):
    xs, ys = zip(*sorted(points, key=lambda q: q[0]))
    return np.interp(t, xs, ys).astype(np.float32)


def osc(freq, harm=((1, 1.0),)):
    ph = (2 * np.pi * np.cumsum(np.broadcast_to(np.float64(1) * freq, (N,))) / SR)
    return sum(a * np.sin(h * ph) for h, a in harm).astype(np.float32)


def gate(a, b):
    return ((t >= a) & (t < b)).astype(np.float32)


dark = gate(T_BLACK, T_UP)

# ---------- 1M0: carriage chord ------------------------------------------------------
score = np.zeros(N, np.float32)
breath_on = gate(T_BREATH_ON, T_BREATH_OFF if T_BREATH_OFF is not None else T_LAST_REL + .5)
breathe = 1 + BREATH_DEPTH * np.sin(2 * np.pi * t / BREATH_PERIOD) * breath_on
out_at = {c["panels"][0]: c["t"] for c in outs}
in_at = {c["panels"][0]: c["t"] for c in rels}
T_PAGE = EV["page_turn"]

for P, p in PARTIAL.items():
    cents = [(0, 0), (DUR, 0)]
    if P == "P1":
        cents += [(T_TICK, 0), (T_TICK + .04, -8), (T_TICK + .08, 0)]
        cents += [(T_STUT, 0), (T_STUT + .1, -12), (T_STUT + .25, 0), (T_STUT + .35, -10), (T_STUT + .5, 0)]
    for k, fc in enumerate(flick):                       # lie 1 ~10c, lie 2 ~20c
        if P in fc["panels"]:
            d = -11 if k == 0 else -20
            s0 = fc["t"]
            cents += [(s0, 0), (s0 + .3, d), (s0 + 1, 3), (s0 + 1.6, d * .85), (s0 + 3.5 + k, 0)]
    if P == DIP_MAIN or P in DIP_SYMP:                   # cue 5 "S-": main panel + sympathy
        d = -20 if P == DIP_MAIN else -10
        cents += [(T_DIP, 0), (T_DIP + .2, d), (T_DIP_REC, d * .8), (T_DIP_END, 0)]
    cents += [(T_BROWN, 0), (T_BROWN + 1.5, -70), (T_BLACK, -90), (T_UP, 0)]
    amp = [(0, 1), (T_BROWN, 1), (T_BROWN + 2, .5), (T_BLACK - .001, .5), (T_BLACK, 0),
           (T_UP - .001, 0), (T_UP, 1)]
    if P in out_at:
        amp += [(out_at[P], 1), (out_at[P] + .03, 0)]
        if P in in_at:
            amp += [(in_at[P], 0), (in_at[P] + .05, 1.12), (in_at[P] + .5, 1)]
    if P == DIP_MAIN or P in DIP_SYMP:                   # hum dips with its light
        lo = .3 if P == DIP_MAIN else .75
        amp += [(T_DIP, 1), (T_DIP + .08, lo), (T_DIP_REC, lo), (T_DIP_END, 1)]
    if P == "P1":                                        # 8.0: held brighter until 8.10
        amp += [(T_STEADY, 1), (T_STEADY + .3, 1.12), (T_LAST_REL, 1.12), (T_LAST_REL + .5, 1)]
    if p >= 5:                                           # thin from the top under 1M8
        amp += [(T_PAGE, 1), (T_PAGE + 6, .35), (CUT - .001, .35)]
    else:
        amp += [(CUT - .001, 1)]
    amp += [(CUT, 0)]
    b = breathe if P != "P1" else breathe * (1 - gate(T_STEADY, DUR)) + gate(T_STEADY, DUR)
    f = F0 * p * 2 ** (env(cents) / 1200)
    score += env(amp) * b * (0.11 / math.sqrt(p)) * osc(f, ((1, 1), (2, .18), (3, .06)))
score += env([(0, .05), (T_BLACK - .001, .05), (T_BLACK, 0), (T_UP - .001, 0), (T_UP, .05),
              (CUT - .001, .05), (CUT, 0)]) * osc(F0, ((1, 1), (2, .5), (3, .35), (4, .2), (5, .12)))


# ---------- 1M1-1M6: THE UNDERTONE ---------------------------------------------------
def undertone(start, length, level, width, attack=.3, cut=None):
    """One breath of the car's motif, synthesised only inside its own window."""
    i0, i1 = max(0, int(start * SR)), min(N, int((start + length) * SR) + 1)
    out = np.zeros(N, np.float32)
    if i1 <= i0:
        return out
    tt = t[i0:i1]
    x = (tt - start) / length
    ratio = np.interp(x, [0, .35, .75, 1], [1, HALF, 1 / HALF, 1])
    a = np.interp(x, [0, attack, .8, 1], [0, level, level * .8, 0]).astype(np.float32)
    if cut is not None:
        a *= (tt < cut)
    seg = np.zeros(i1 - i0, np.float32)
    for v in {1: [1.0], 2: [1.0, HALF], 3: [1.0, HALF, 1 / HALF]}[width]:
        ph = 2 * np.pi * np.cumsum(F0 / 2 * v * ratio) / SR
        for h, g in ((1, .6), (2, 1.0), (4, .7), (6, .35), (8, .3), (12, .22), (16, .15)):
            seg += g * np.sin(h * ph)
        for k, m in enumerate(METAL):
            seg += .28 / (k + 1) * np.sin(m * ph)
    out[i0:i1] = a * seg
    return out


und = np.zeros(N, np.float32)
und += undertone(flick[0]["t"], 3.5, .04, 1)                         # 1M1
und += undertone(flick[1]["t"], 4.5, .08, 2)                         # 1M2
und += undertone(T_BROWN, (T_BLACK - T_BROWN) + 3, .22, 3, cut=T_BLACK)   # 1M3, hard out
und += undertone(T_DIP, T_DIP_END - T_DIP, .16, 3, attack=.2)        # 1M4 hungry, settles with the light
# 1M6: one breath of the car per tick, rising; then falling per relight, gone by the last
steps = [(c["t"], .05 + .012 * k) for k, c in enumerate(outs)]
peak_t, peak_lv = EV.get("he_is_asking", outs[-1]["t"] + 8), .05 + .012 * len(outs)
steps.append((peak_t - 8, peak_lv))
for k, c in enumerate(rels[:-1]):
    steps.append((c["t"], max(.01, peak_lv * (1 - (k + 1) / len(rels)))))
for (s0, lv), nxt in zip(steps, steps[1:] + [(T_LAST_REL, 0)]):
    ln = max(3.0, min(9.0, nxt[0] - s0 + 1.0))
    und += undertone(s0, ln, lv, 3, attack=.4)
und *= (t < T_LAST_REL + .5)
und *= 1 - dark

# ---------- 1M7: relight warmth (cellos, third withheld) -------------------------------
T_SIL, T_SLOW, T_ARR = EV["silence_on_line"], EV["train_slows"], EV["arrival_chime"]
depth = env([(0, 1), (T_SIL, 1), (T_SIL + 1, 0), (DUR, 0)])
warm = np.zeros(N, np.float32)
for P, p in WARM.items():
    on = in_at[P]
    a = env([(0, 0), (on, 0), (on + 1.5, 1), (T_SLOW, 1), (T_ARR - .5, 0), (DUR, 0)])
    vib = 2 ** (8 * depth * np.sin(2 * np.pi * (5.1 + .07 * p) * t + p) / 1200)
    warm += a * (.018 / math.sqrt(p / 4)) * osc(F0 * p * vib, ((1, 1), (2, .35), (3, .18), (4, .08)))

# ---------- 1M8: page turn ---------------------------------------------------------------
T_PHONE = EV["phone_dims"]
gone = T_PHONE - 1.0
rel = env([(0, 0), (T_PAGE, 0), (T_PAGE + 4, 1), (gone - 3, .8), (gone, 0), (DUR, 0)])
release = np.zeros(N, np.float32)
for p, lv, d in ((8, .016, 0), (10, .013, .6), (12, .011, 1.2)):
    release += rel * gate(T_PAGE + d, DUR) * lv * osc(F0 * p, ((1, 1), (2, .1)))

# ---------- dialogue windows: keep them clear --------------------------------------------
DLG_SRC = "camera/cues.json" if doc.get("dialogue") else "NONE (no 'dialogue' in the cue file: no ducking)"
DLG = doc.get("dialogue") or []
duck_pts = [(0, 0.0)]
for w in DLG:
    duck_pts += [(w["in"] - .15, 0.0), (w["in"], 1.0), (w["out"], 1.0), (w["out"] + .25, 0.0)]
duck_pts.append((DUR, 0.0))
in_dlg = np.clip(env(duck_pts), 0, 1)                  # 1 inside a line, 0 outside
DUCK_MUSIC = 1 - in_dlg * (1 - 10 ** (-4 / 20))         # Undertone + cellos -4 dB under lines
DUCK_RAILS = 1 - in_dlg * (1 - 10 ** (-3 / 20))         # rails -3 dB under lines
und *= DUCK_MUSIC
warm *= DUCK_MUSIC

score = score * (1 - dark) + und + warm + release

# ---------- temp sound design placeholders -----------------------------------------------
sfx = np.zeros(N, np.float32)
T_OPEN, T_CLOSE2, T_STOP = EV["doors_open"], EV["doors_close_final"], EV["rails_stop"]
rails_amp = env([(0, .25), (EV["doors_close"], .25), (EV["doors_close"] + 3, .5),
                 (T_BLACK - .001, .5), (T_BLACK, 0), (T_UP - .001, 0), (T_UP, .5),
                 (T_SLOW, .5), (T_OPEN, .0), (T_CLOSE2 + 1, 0), (T_CLOSE2 + 4, .5),
                 (T_STOP - .3, .5), (T_STOP, 0)])
rumble = np.convolve(rng.standard_normal(N).astype(np.float32), np.ones(220, np.float32) / 220, mode="same") * .6
clack = np.zeros(N, np.float32)
for c in np.arange(.4, DUR, .83):
    for off in (0, .11):
        i = int((c + off) * SR)
        if i + 440 < N:
            clack[i:i + 440] += np.exp(-np.arange(440) / 50) * rng.standard_normal(440) * .35
sfx += rails_amp * DUCK_RAILS * (rumble + clack)
for c in cues:
    if c["type"] in ("tick", "panel_out", "relight"):
        i = int(c["t"] * SR)
        sfx[i:i + 160] += np.exp(-np.arange(160) / 14) * rng.standard_normal(160) * (.08 if c["type"] == "tick" else .25)
for k in ("board_chime", "doors_close", "arrival_chime", "doors_close_final"):
    if k in EV:
        for d, p, lv in ((0, 18, .07), (.45, 12, .08)):
            s0 = EV[k] + d
            sfx += np.where(t >= s0, np.exp(-np.clip(t - s0, 0, 60) * 2.2), 0).astype(np.float32) * lv * osc(F0 * p, ((1, 1), (2.76, .3), (5.4, .1)))
x = np.clip((t - (T_UP - 1.5)) / 1.4, 0, 1)                  # the inhale, last 1.5 s of dark
inh = gate(T_UP - 1.5, T_UP - .1) * x ** 2
breath = np.convolve(rng.standard_normal(N).astype(np.float32), np.ones(16, np.float32) / 16, mode="same")
sfx += inh * (.25 * osc(F0 * 2 ** ((x * 2 - 1) / 12), ((1, 1), (2, .6), (3, .3))) + .5 * breath)
sfx *= 1 - gate(T_BLACK, T_UP - 1.5)                          # digital zero in the dark


# ---------- write ------------------------------------------------------------------------
def write(sig, name, peak):
    base = os.path.join(HERE, name)
    with wave.open(base + ".wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.clip(sig / peak * 32767, -32767, 32767).astype("<i2").tobytes())
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base + ".wav", "-b:a", "96k",
                        base + ".mp3"], check=False)


mix = score + sfx
peak = float(np.max(np.abs(mix))) / .89
write(mix, "temp-mix", peak)
write(score, "temp-score", peak)            # same gain as the mix, so levels compare
write(sfx, "temp-sfx", peak)                # stems sum to the mix: temp-score + temp-sfx

# 48 kHz stereo FLAC for the TA to mux (dual mono, lossless). WAV on request: same ffmpeg line.
if shutil.which("ffmpeg"):
    for name in ("temp-mix", "temp-score", "temp-sfx"):
        src = os.path.join(HERE, name + ".wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", "48000", "-ac", "2",
                        "-sample_fmt", "s16", os.path.join(HERE, name + "-48k.flac")], check=False)

fmt = lambda s: f"{int(s // 60)}:{s % 60:05.2f}"
lines = [f"Temp score sync report. Cue source: {os.path.relpath(path, HERE)}",
         f"Duration {fmt(DUR)} · cut {fmt(CUT)} · fps {doc.get('fps', 24)}", "",
         "LIGHT CUES (DP 0-8)"]
lines += [f"  {fmt(c['t'])}  {c['id']:>5}  {c['type']:<10} {','.join(c['panels']) if len(c['panels']) < 12 else 'all':<10} {c.get('line', '')}"
          for c in cues]
lines += ["", "EVENTS"] + [f"  {fmt(v)}  {k}" for k, v in sorted(EV.items(), key=lambda kv: kv[1])]
lines += ["", "MUSIC CUES (cue-sheet.md)",
          f"  1M1 First Waking   {fmt(flick[0]['t'])}", f"  1M2 Second Waking  {fmt(flick[1]['t'])}",
          f"  1M3 Brownout       {fmt(T_BROWN)} - hard out {fmt(T_BLACK)}",
          f"  blackout (zero)    {fmt(T_BLACK)} - {fmt(T_UP)}",
          f"  1M4 Hungry         {fmt(T_DIP)}", f"  1M5 Stutter        {fmt(T_STUT)}",
          f"  1M6 The Advance    {fmt(outs[0]['t'])} - {fmt(T_LAST_REL)}",
          f"  1M7 Relight        {fmt(rels[0]['t'])} - {fmt(T_ARR)}",
          f"  1M8 Page Turn      {fmt(T_PAGE)} - {fmt(gone)} (phone dims {fmt(T_PHONE)})",
          f"  hum to the cut     {fmt(CUT)}"]
gaps = [b["t"] - a["t"] for a, b in zip(outs, outs[1:])]
lines += ["", f"Cue 5 main {DIP_MAIN} (partial {PARTIAL[DIP_MAIN]}), sympathy {DIP_SYMP}, recovered {fmt(T_DIP_END)}",
          f"Breath depth {BREATH_DEPTH}, period {BREATH_PERIOD} s, on {fmt(T_BREATH_ON)}, off {fmt(T_BREATH_OFF or T_LAST_REL)}"]
on_line = [c["id"] for c in outs + rels + by_type("tick")
           if any(w["in"] <= c["t"] <= w["out"] for w in DLG)]
lines += ["", f"Dialogue windows: {len(DLG)} from {DLG_SRC} (Undertone/cellos -4 dB, rails -3 dB inside)",
          "  Advance/relight ticks landing inside a line: " + (", ".join(on_line) if on_line else "none (OK)")]
lines += ["", f"Advance tick spacing: min {min(gaps):.1f} s, max {max(gaps):.1f} s "
          f"({'OK' if min(gaps) >= 8 else 'BELOW the 8 s rule'})"]
open(os.path.join(HERE, "temp-sync-report.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines[-12:]))
