# THE QUIET CAR: Previs Review and Re-time Procedure (DP, Milestone 4)

The TA builds the animatic from **`camera/cues.json`**, the single timeline. This page says what I check on every previs pass, and how a timing change moves through camera, CG and music without anything drifting.

## What `cues.json` gives the TA for every shot

Each of the 63 shots in `shots[]` has:
- `in` / `out` (seconds) and `frames` (at 24 fps), plus its `scene` (1–8);
- `lens_mm`, on a Super 35 sensor cropped to 2.39:1 (`camera.sensor`);
- `camera_loc` and `aim` (set coordinates; aim with a Track-To constraint, no roll);
- `move`: `locked`, `push` (with `path.from` and `path.to`, constant speed across the shot), `handheld` (shot 20 only, with the `handheld` spec: a recorded operator clip layered on the base camera), or `still`;
- `cues`: the light cues that must play inside the shot.

`dialogue[]` holds the line windows (in, out, who, line), read at build time from the Screenwriter's `film/previs/voice/scratch-voice-lines.json` (anchored to these cues); the build checks that no Advance tick or relight lands on a line.

Inserts have their own cameras and prop marks (`NEWSPAPER`, `LANYARD_FLOOR`, `NOOR_PHONE_LAP`, `DISPLAY`, `KAI_PHONE`). `build_cues.py` refuses to write the file if any shot is missing a camera.

## My review of each previs pass

For every pass, I compare the render against the boards (`storyboards/index.html`) and the rules below, and send the TA notes by shot number.

1. **Framing:** everything in the shot's must-frame list (`MUST` in `build_cues.py`) is visible in the render, not just in the projection math. Characters may block things the math can't see.
2. **The Meter:** in shots 1, 4, 10, 16, 18, 29, 42, 50, 57 and 63, all lit panels are individually countable, and nothing else on the ceiling reads as a light.
3. **Cues land inside held shots:** no light change is visible across a cut. The blackout (shot 18) is exactly 0 for every pixel, with no cut inside it.
4. **Asleep means still:** before cue 1 and after 8.10 there is no light, brush or camera movement except what the shot list names (the window passing lights while asleep; the platform in the door glass; the page turn; Kai's phone dimming).
5. **Moves:** the pushes (42, 54, 56) run at constant speed and land on their marks; 58 is still; the handheld in 20 settles by the cut.
6. **Eyes and edges:** Walter's lit-side catchlight in 53; the reflected panel row completing in Noor's corneas at 8.10 (58, as accepted by the Director); the hard dark edge in 44, 49 and 50.
7. **The reds:** only the lanyard strap and Kai's end-call button are red; the strap reads under BASE and is the only red under BROWN and DIP.

## Re-timing to the scratch voice record

When the voice record changes the timing:

1. **The Composer and I agree the new times** for the cues and events (the cue IDs never change). The Advance stays steady (8 s or more, never accelerating, never on a line), and each tick follows its line.
2. **I edit the times in `build_cues.py`** (`cue(...)` calls, `ADV`, `REL`, `EVENTS` and the shot `in`/`out` in `S`) **and run it**, after the Screenwriter has re-placed the voice lines on the new cues. If any rule breaks, the script refuses to write `cues.json` and says why.
3. **I push and tell both of them in one message.** The Composer re-renders the temp score (about 40 s) and the TA rebuilds the scene; both read the same file.
4. I log the re-time in `STATUS.md`.

Nobody edits `cues.json` by hand.
