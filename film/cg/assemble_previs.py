"""Assemble the previs animatic from the rendered frame plan (system python: numpy + Pillow + ffmpeg).

    python3 film/cg/assemble_previs.py [--from 0 --to 570] [--out film/previs/quiet-car-previs.mp4]

- 24 fps timeline on the cues.json clock; frames not in the render plan hold the last rendered frame
  of the same shot (never across a cut).
- Picture 960x402 (2.39:1), upscaled from the render; burn-in (timecode, shot, scene, lens, move) sits
  in a black bar BELOW the picture, so nothing is drawn on the image (the blackout stays 0).
- Audio: music/temp/temp-mix-48k.flac + previs/voice/scratch-voice.flac summed at unity gain (no
  normalisation, no loudness processing: the Composer's levels are absolute). Subtitles:
  previs/quiet-car.srt as a soft mov_text track.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

CG = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(CG)
FRAMES = os.path.join(CG, ".cache", "previs", "frames")
W, H, BAR = 960, 402, 44


def main():
    argv = sys.argv[1:]
    arg = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d
    D = json.load(open(os.path.join(FILM, "camera", "cues.json")))
    fps = D["fps"]
    t0, t1 = arg("--from", 0.0), arg("--to", float(D["duration_s"]))
    out = arg("--out", os.path.join(FILM, "previs", "quiet-car-previs.mp4"))
    crf = arg("--crf", 27)
    f0, f1 = int(round(t0 * fps)), int(round(t1 * fps))
    have = sorted(int(n[:5]) for n in os.listdir(FRAMES) if n.endswith(".png"))
    have_set = set(have)
    shots = D["shots"]
    font = ImageFont.truetype("DejaVuSansMono.ttf", 15)
    font_s = ImageFont.truetype("DejaVuSans.ttf", 12)

    def shot_of(f):
        for s in shots:
            if s["frames"][0] <= f < s["frames"][1]:
                return s
        return shots[-1]

    srt = os.path.join(FILM, "previs", "quiet-car.srt")
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H + BAR}", "-r", str(fps), "-i", "-",
           "-ss", str(t0), "-t", str(t1 - t0), "-i", os.path.join(FILM, "music", "temp", "temp-mix-48k.flac"),
           "-ss", str(t0), "-t", str(t1 - t0), "-i", os.path.join(FILM, "previs", "voice", "scratch-voice.flac")]
    if t0 == 0:
        cmd += ["-i", srt]
    cmd += ["-filter_complex", "[2:a]pan=stereo|c0=c0|c1=c0[v];[1:a][v]amix=inputs=2:normalize=0:duration=first[a]",
            "-map", "0:v", "-map", "[a]"]
    if t0 == 0:
        cmd += ["-map", "3:s", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng"]
    # keyframe at every cut and every hard cue so no residual from the previous picture leaks into the blackout
    keys = sorted({s["in"] for s in shots} | {c["t"] for c in D["cues"] if c.get("type") in ("blackout", "hard_dip")})
    keys = [k - t0 for k in keys if t0 <= k < t1]
    cmd += ["-force_key_frames", ",".join(f"{k:.4f}" for k in keys)]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-tune", "animation",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-t", str(t1 - t0), out]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cache_src, cache_img = None, None
    missing = 0
    for f in range(f0, f1):
        s = shot_of(f)
        src = None
        for g in range(f, s["frames"][0] - 1, -1):
            if g in have_set:
                src = g
                break
        if src is None:
            pic = np.zeros((H, W, 3), np.uint8)
            missing += 1
        else:
            if src != cache_src:
                im = Image.open(os.path.join(FRAMES, f"{src:05d}.png")).convert("RGB").resize((W, H), Image.LANCZOS)
                cache_src, cache_img = src, np.asarray(im)
            pic = cache_img
        bar = Image.new("RGB", (W, BAR), (0, 0, 0))
        d = ImageDraw.Draw(bar)
        secs = f / fps
        tc = f"{int(secs // 3600):02d}:{int(secs // 60) % 60:02d}:{int(secs) % 60:02d}:{f % fps:02d}"
        d.text((10, 6), f"TC {tc}   SHOT {s['shot']:>2}   SC {s['scene']}   {s['pos']} {s['lens_mm']}mm {s['move']}", fill=(200, 200, 190), font=font)
        d.text((10, 26), (s["beat"][:118] + ("" if src is not None else "   [NOT RENDERED]")), fill=(140, 140, 135), font=font_s)
        d.text((W - 150, 6), "PREVIS PASS 1", fill=(120, 120, 115), font=font)
        frame = np.vstack([pic, np.asarray(bar)])
        p.stdin.write(frame.tobytes())
    p.stdin.close()
    p.wait()
    print("wrote", out, f"{os.path.getsize(out) / 1e6:.1f} MB", "frames", f1 - f0, "missing", missing)


if __name__ == "__main__":
    main()
