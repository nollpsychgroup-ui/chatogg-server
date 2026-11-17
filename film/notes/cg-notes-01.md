# Director's Notes: cg/ (set, rig, look-dev, style frames), Milestone 3

I reviewed `cg/README.md`, `stills/checks/REPORT.md`, the contact sheet, and sf01, sf03 and sf06 at full size.

**Verdict: the set, rig, cue driving and checks are APPROVED. The painterly look needs one revision before the M3 gate.**

## Approved

- **Conformed to the approved layout.** Noor sits under the sign at the far end, Walter and Bea are mid-car, and Kai is in the near-right foreground. Cues are read directly from `camera/cues.json`, with nothing copied. One source of truth for picture and score is exactly right.
- **Checks:** the blackout is 0.000000 after the comp, and the strap is the most saturated colour under cue 3. All 455 light keys land on whole frames, and the asleep frames are bit-identical. All PASS.
- **sf01, the Meter:** the row is countable, the window reflections are a lovely second meter, and the staging reads instantly.
- **sf03, the brownout:** the sodium sag reads as a failing system, not a "warm scene". Kai is lit cold by his phone in the foreground, which is a great accidental contrast.
- **sf04a/b:** true black, then an indifferent car with an empty seat. That's the film's best cut, in two frames.
- **Mannequin figures for now:** fine. Faces arrive with the M4 rig.
- **Brush boil:** parked. Surface-locked strokes are final. No test needed.

## Rulings on your flags

**Bea in the brownout: accept it as the image.** Don't raise BROWN, and don't add a shot. In the Meter, the brownout is about the *whole car* acting at once. Bea as shape and silhouette is right there, and her "don't" reach happens *before* the brownout (shot 15). Where Bea's face must read in the dark is **shot 49** ("Say it.", 50 mm, her light dying to an edge). That's a design follow-up for M4, with the Designer (F2 in `design-notes-01.md`): lift sclera and lid-line contrast, not skin value.

**Catchlight row PARTIAL: accepted for M3.** It's a hard requirement for M4 on the face rig, especially **shot 58**, where P12's catchlight must visibly return in Noor's eyes at 8.10 (`dp-notes-02.md`).

## Revision needed before the gate (R1 and R2)

**R1. The frames don't yet look painted.** At the moment the surfaces read as clean CG: smooth, plastic and evenly shaded. The light is beautifully *real*, but the other half of our rule, *the world is painted*, isn't visible yet, and that's what the human will judge the format decision on. Please do **one hero painterly pass on sf01 and sf03**, following style guide §3–§5:
- surface-locked stroke textures, with scale by tier (set strokes broad, at ~4–6 cm);
- a brush break-up at the light/shadow terminator, driven by the real light;
- lit edges firm, shadow edges lost, at a Hopper/Hammershøi level of simplification;
- the canvas/paper texture on the set as multiply-only.

Re-run the checks afterwards. The blackout must stay at 0 and the asleep frames must stay identical. The other frames can stay at proxy quality until M4.

**R2. sf06 (the 75 mm confession) exposure.** The end wall behind her is near white and flat, brighter than her face. That's P1 at 110% blowing the wall it's mounted against. **Expose for her face, and let the wall sit about a stop under it.** Take that from the wall's material value and the camera exposure, not from a fill light. This shot is the film's heart, and the face has to be the brightest, most detailed thing in it. Also lower the headroom slightly, so her eyes sit on the upper third.

When R1 and R2 are pushed, I'll approve and send M3 to the Producer.
