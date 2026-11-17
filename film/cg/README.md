# film/cg: carriage set, painterly look-dev, light rig, previs

**Owner:** 3D / Technical Artist · Milestone 3 · Blender 5.3 (headless; scripts also run inside the `bpy` 5.3 wheel)

The Python scripts are the source of truth. Renders are low-res previews only (960×402, 2.39:1). No `.blend` files are committed; `build_scene.py` rebuilds the whole scene from data in under a second.

## Run it

```bash
pip install bpy==5.3.0 numpy pillow          # or use a Blender 5.3 binary: blender -b --python <script> -- <args>
python film/cg/build_scene.py --save film/cg/.cache/quiet_car.blend   # whole scene, cue-keyed, ready to scrub
python film/cg/render_styleframes.py                 # all style frames -> film/cg/stills/  (~40 s each, 4 CPU cores)
python film/cg/render_styleframes.py --only sf03 --raw   # one frame, without the painterly pass
python film/cg/contact_sheet.py                      # stills/styleframes-sheet.jpg
```

Headless Linux needs `libegl1 libgl1 libxkbcommon0 libsm6 libxi6` installed for `bpy`.

## Files

| File | What |
|---|---|
| `data/set_layout.json` | Set dimensions, door/window bays, seat rows, P1–P12 positions, character marks, provisional cameras |
| `data/cue-stack.json` | **Shared sync data**: lighting cues 0–8 (sub-cues 7.1–7.10 and 8.0–8.10) plus practical channels, with timecodes and per-panel envelopes. It is numbered 1:1 with `camera/` and `music/cue-sheet.md`. Edit values here, never in code |
| `data/styleframes.json` | Which cue, camera and poses each style frame uses |
| `build_scene.py` | Entry point: set → figures → light rig → cue keys → cameras → compositor |
| `lib/build_set.py` | The carriage: shell, windows, doors, 2+2 transverse seats, rails, baffled light trough, end walls, QUIET CAR sign, LED display, platform flat, passing-light rig |
| `lib/lookdev.py` | Palette, the `PaintSurface` shader group, glass, emitters, render settings, painterly compositor |
| `lib/light_rig.py` | P1–P12 named area lights, diffusers and drivers; practical channels |
| `lib/cue_driver.py` | Keyframes everything from `cue-stack.json` and adds a timeline marker per cue |
| `lib/figures.py` | Seated blocking mannequins in costume colour, with phones and props |
| `lib/cameras.py` | Virtual cameras (Super 35, 2.39:1, spherical, T4-ish depth of field) |
| `render_styleframes.py`, `contact_sheet.py` | Style frames |
| `stills/` | Small PNGs and the contact sheet |

## Layout (coordinates everyone can share)

Metres. **+X runs from Noor's end (x=0) to the far end wall (x=20)**, which carries the QUIET CAR sign and the destination display. +Y is the right-hand side looking down +X, and the platform is on −Y. The interior is 20 × 2.8 × 2.3 m.

- **Panels:** one centre row. P1 sits at x=2.6, above Noor, with a 1.45 m pitch to P12 at x=18.55 (far end). Baffles sit between panels and each light is spread-limited to 90°, which gives the DP's "no spill between sections" hard edge for cue 7.
- **Doors:** pairs at x=4.6 (A, Noor's door and the platform at Holloway) and x=14.6 (B, next to Kai).
- **Marks:** Noor is at x=2.6, aisle seat on −Y, facing +X toward the others. Walter is at x=8.9 (+Y) and Bea at x=8.9 (−Y), across the aisle from him, both facing Noor. Kai is at x=16.1 (+Y) by door B, facing Noor's end, so his phone sits in the dark section during cue 7.

## Painterly look-dev: light physical, surfaces painted

1. **Paint lives on the surfaces, not in the light.** Every material goes through `PaintSurface`. Stretched, distorted noise is quantised into flat brush dabs, which drive small value and hue shifts, roughness variation and a faint impasto bump. Strokes run along the car on long surfaces. Brush scale is set per material: broad on walls, fine on faces and hands.
2. **Light is computed physically** (Cycles path tracing, 6 bounces). The fluorescent bounce off the laminate, the sodium sag and the phone's underlight are real light transport, nothing is painted in, and the window glass mirrors the panel row as a second meter.
3. **Image paint:** an anisotropic Kuwahara filter (size 7) turns the render into strokes that follow form. Then a canvas tooth (0.90–1.03) is **multiplied** in. Because a multiply keeps 0 at 0, the blackout and the dead sections of cue 7 stay true black.
4. **Palette rules are enforced in `lookdev.PALETTE`:** the only red is `lanyard` (and later Kai's end-call button). The display LED and door indicators are cool green-white, so orange means only *the car is awake*. The platform lamp is cold white (5600 K).
5. **Colour temperature:** the virtual camera is white-balanced to 4000 K. Panels at 4300 K with a small green tint read as cool transit light, the 2200 K brownout reads as sodium orange, and the platform reads cold.

These are TA defaults. Brush scale, edge treatment and the costume and skin values will be matched to `design/style-guide.md` when it lands.

## Light rig and cue driver

- **P1–P12** are Blender area lights named exactly `P1`…`P12`. Each carries `["level"]` (1.0 = baseline, 0 = off, 1.1 = relight overshoot), `["rgb"]` (from Kelvin), `["breath"]` and `["partial"]` (its hum partial, from the cue sheet). Drivers feed **both** the light and its visible diffuser from these properties, so a panel can never look on while casting no light.
- **Breathing:** `energy = base × level × (1 + depth × awake × breath × sin(2πt / period))`, with depth and period taken from `cue-stack.json` (±3% over 5 s, provisional). `awake` is keyed by cues 1 and 8.10. Cue 8.0 turns off P1's breathing alone ("steadies").
- **Practical channels:** `CTRL_DISPLAY`, `CTRL_WINDOWS` (passing tunnel lights, visible only in the glass and never lighting faces, like the DP's flagged rig), `CTRL_PLATFORM`, `CTRL_PHONE_NOOR`, `CTRL_PHONE_KAI` and `CTRL_DOOR_LIGHT`.
- **The cue driver** reads every event's `keys` (`[t_offset_s, level, interp]`, where interp is `const`, `linear` or `smooth`, describing how the value *arrives* at that key). It keys them at `frame = 1 + tc × 24` and drops a named timeline marker on each cue. Timecodes are the Composer's ~9:05 estimates until the temp voice record fixes the edit. Change `tc` in one place and lights, markers and (in M4) music sync all move together.

## Style frames (`stills/`)

| Frame | Beat |
|---|---|
| `sf01_first_flicker` | Cue 1, P1 mid-flicker, over Walter's shoulder |
| `sf02a/b/c` | Kai: brownout → true black → lights up on the same locked wide, seat empty |
| `sf03_creeping_dark` | Cue 7.7, P6–P12 out, the dark walking up the aisle |
| `sf04a_final_relight` | Cue 8.10, P12 overshooting, the room whole again |
| `sf04b_confession_75` | Cue 8.3 on the 75 mm, relights spreading out from Noor |

## Built for Milestone 4 (previs animatic)

- The scene is already the full film length (`frame_end` from `duration_s`), with every cue keyed and marked.
- **Still to add:** blocking animation per character, door-leaf animation, display text per minute, cameras keyed per shot from `camera/shot-list.md`, Kai's vanish in the blackout, and a VSE edit with temp voices and the score stems laid against the markers. Animatic renders will use Cycles at around 16 spp (or Workbench) at 480p.

## Open items

1. **DP:** confirm or redline the layout and the provisional cameras against `shot-list.md` and `lighting-plan.md`. The display colour (cool green-white LED) also needs approval.
2. **Composer:** the cue `tc` values are copied from the cue sheet estimates. Once there's a cut, the file is the single place to update.
3. **Character Designer:** the figures are blocking proxies. Brush and palette values will be matched to the style guide.
4. The breathing depth and period are still provisional (±3% / 5 s).
