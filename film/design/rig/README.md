# Previs face rigs (`heads.py`)

**Character Designer** · for the TA's blocking figures (Milestone 4). Replaces the mannequin heads, eyes and nose in `cg/lib/figures.py`. The TA integrates it there; this folder owns the heads.

## What you get

`build_head("NOOR" | "KAI" | "BEA" | "WALTER")` builds one head under a root empty (`<NAME>_HEADRIG`), at real-world size (head 0.23 m tall, matching the TA's ellipsoid). It has:

- **Every control from `../expressions/face-rig.md` as a custom property on the root**, wired by drivers to the parts: lid pivots, eye (gaze) pivots and shape keys on the brows and lips. **Animators key only the root.**
- **Corneas are smooth spherical caps** (stylised flatter than real: radius 0.9 r, so the reflections are bigger) over an iris and pupil that lie on the eyeball. The real panel emitters reflect as a **row of diminishing rectangles**. Test at the C75 framing (75 mm at 0.9 m, 1:1 crop of a 1920 frame, upscaled ×2): `renders/catchlight_12_lit_x2.png` vs `catchlight_2_lit_x2.png`. About 5 panels are individually countable; beyond ~P6 the images are under 1 px (physics: a panel 10 m away reflects at ~0.3 mm), so they merge into the row's tip.
- **Shallow sockets:** the eyes protrude ~3 mm, so they catch top light (style guide 2.3).
- **Director F2 built in for Bea:** brighter sclera, a near-black lid band and lighter lid albedo. Test: `renders/bea_dark_brownout.png`, where her closed lids still read as shapes under the brownout.
- Materials default to flat albedo from `../palette.json`. Pass the TA's `PaintSurface` materials through `mats={...}` to override (keys: skin, lid, lid_ink, hair, brow, lips, sclera, iris, pupil, cornea, mouth, teeth, tear).
- `pass_index`: 1 for face parts (small Kuwahara kernel) and 2 for hair, matching the TA's ID-mask convention.

## Use

```python
import sys; sys.path.insert(0, "film/design/rig")
from heads import build_head, place, set_expression
root = build_head("NOOR", collection="CHAR_NOOR", mats={"skin": skin_mat, "hair": hair_mat})
place(root, head_c, f)                                        # head centre and facing vector (same as figures.py)
set_expression(root, {"smile": 0.45, "lid_low": 0.0}, frame=240, from_neutral=True)
```

- Local frame: +Y out of the face, +Z up. **`_L` = the character's left (−X).** The 2D sheets were drawn with `_L` on camera-left, so mirror Kai's lopsided values when copying them across (`test_render.py` shows how).
- Un-suffixed names (`lid_up`, `smile`, `brow_in`...) set both sides.
- `from_neutral=True` resets every control to that character's neutral first, the same way the sheets read.

## Known limits (previs, not final)

`naso` is a control with no geometry yet. The mouth interior only shows when `jaw > 0` (there's no hole in the skin), and the lips are thin ribbons. Hair is simple caps. The final heads are for the modellers. This rig fixes **proportions, eye placement and size, lid behaviour, and the control set**.

## Test renders

`python3 film/design/rig/test_render.py [--quick]` (bpy 5.3) writes `renders/`: lineup, a 3/4 view per character, each character's sheet expressions in 3D, Bea's dark-state check and the catchlight check. Only real area lights are used (a panel row) with a black world, so nothing is faked.
