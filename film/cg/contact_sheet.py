"""Assemble the style frames into film/cg/stills/styleframes-sheet.png with captions (needs Pillow)."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import json

CG = os.path.dirname(os.path.abspath(__file__))
STILLS = os.path.join(CG, "stills")
BEATS = json.load(open(os.path.join(CG, "data", "styleframes.json")))["frames"]

W, PAD, CAP = 960, 14, 34
ims = [(n, b["caption"]) for n, b in BEATS.items() if os.path.exists(os.path.join(STILLS, n + ".png"))]
tiles = []
for n, cap in ims:
    im = Image.open(os.path.join(STILLS, n + ".png")).convert("RGB")
    im = im.resize((W, int(im.height * W / im.width)))
    tiles.append((n, cap, im))
H = sum(t[2].height + CAP for t in tiles) + PAD * (len(tiles) + 1)
sheet = Image.new("RGB", (W + 2 * PAD, H), (12, 12, 12))
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("DejaVuSans.ttf", 15)
except OSError:
    font = ImageFont.load_default()
y = PAD
for n, cap, im in tiles:
    sheet.paste(im, (PAD, y))
    d.text((PAD, y + im.height + 8), f"{n}  -  {cap}", fill=(205, 205, 200), font=font)
    y += im.height + CAP + PAD
out = os.path.join(STILLS, "styleframes-sheet.jpg")
sheet.save(out, quality=82)
print("wrote", out, sheet.size)
