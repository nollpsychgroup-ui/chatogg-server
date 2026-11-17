"""Cue-crop sheet for the DP: frame before / cue frame / frame after / +0.5 s (eased cues), for chosen cues.

    python3 film/cg/cue_crops.py [--cues 0,1,2,3,7.1] [--out film/cg/stills/previs/cue_crops.jpg]

System python + PIL. Reads the previs frames in .cache/previs/frames. A frame that was not
rendered (frame plan) is shown as the held frame the animatic plays, labelled "held from N".
"""
import json, os, sys
from PIL import Image, ImageDraw

CG = os.path.dirname(os.path.abspath(__file__))
FILM = os.path.dirname(CG)
FRAMES = os.path.join(CG, ".cache", "previs", "frames")


def main():
    argv = sys.argv[1:]
    arg = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
    want = arg("--cues", "0,1,2,3,7.1").split(",")
    out = arg("--out", os.path.join(CG, "stills", "previs", "cue_crops.jpg"))
    D = json.load(open(os.path.join(FILM, "camera", "cues.json")))
    fps = D["fps"]
    have = sorted(int(n[:-4]) for n in os.listdir(FRAMES) if n.endswith(".png"))
    cues = {c["id"]: c for c in D["cues"]}

    def shot_at(f):
        for s in D["shots"]:
            if round(s["in"] * fps) <= f < round(s["out"] * fps):
                return s
        return D["shots"][-1]

    def held(f):
        s0 = round(shot_at(f)["in"] * fps)
        cand = [h for h in have if s0 <= h <= f]
        return cand[-1] if cand else None

    w, h = Image.open(os.path.join(FRAMES, f"{have[0]:05d}.png")).size
    lab = 34
    sheet = Image.new("RGB", (4 * w, len(want) * (h + lab)), (12, 12, 12))
    dr = ImageDraw.Draw(sheet)
    for r, cid in enumerate(want):
        c = cues[cid]
        fc = round(c["t"] * fps)
        for k, f in enumerate((fc - 1, fc, fc + 1, fc + fps // 2)):
            src = held(f)
            x, y = k * w, r * (h + lab)
            if src is not None:
                sheet.paste(Image.open(os.path.join(FRAMES, f"{src:05d}.png")).convert("RGB"), (x, y + lab))
            s = shot_at(f)
            tag = ["before", "CUE", "after", "+0.5s"][k]
            note = "" if src == f else f" (held from {src})"
            dr.text((x + 6, y + 4), f"cue {cid} {tag}  f{f}  t={f / fps:.3f}s  shot {s['shot']}{note}", fill=(230, 230, 230))
            dr.text((x + 6, y + 18), f"panels {','.join(c['panels'][:4])}{'...' if len(c['panels']) > 4 else ''}  {c.get('type', '')}", fill=(150, 150, 150))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out, quality=85)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main()
