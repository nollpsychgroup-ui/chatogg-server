# THE QUIET CAR: Shot List (CG)

**DP** · Milestone 3 · Built on the locked `script/draft-02.md` and `FORMAT.md` (CG animation) · Read it with:
- **`camera/cut-timeline.md`**: all **63 shots** in order, **grouped by the treatment's 8 scenes**, with in/out times, position, lens, move and the cues each one holds (generated);
- **`camera/cues.json`**: the same cut as data, with camera locations and aim points for the TA's Blender cameras;
- `camera/lighting-plan.md` for the set plan, panels and cues, and `camera/storyboards/index.html` for the key frames.

---

## Why this is a cut and not coverage

In live action we'd shoot coverage and find the film in the edit. In animation, every second on screen is animated, so **the shot list is the cut.** There are 63 shots in about 9:25, with nothing animated that won't be used. The previs animatic is where we test it. If a beat doesn't work, we change a shot in `build_cues.py`, re-run it, and the TA, the Composer and the boards all pick up the change.

`build_cues.py` checks the Director's rules every time it runs, and refuses to write the file if any are broken:
- **Cut on behaviour, never on cues.** Every light cue sits at least 0.5 s inside a held shot.
- **No cut inside the blackout.**
- **The Advance ticks are steady:** 8.5 s apart, at least 8 s, never accelerating.
- **The 75 mm is used only in the confession.**
- **The camera moves only while the car is awake.**
- **Everything that must read is in the frame.** Each key shot lists its required panels, faces, sign, display and props, and the script projects them through the lens. That's how the old shot 7 and shot 26 framings were caught and fixed.

## Rules of the frame

1. **The Meter (Pos A) is the spine.** We cut back to it after every escalation to count the damage: shots 1, 4, 10, 16/18, 29, 42, 50, 57 and 63. It opens and closes the film on the same frame.
2. **Every cue is visible in the frame it plays in:** either the cued panel is in frame, or its light lands on a face. **Noor faces down the car**, so every panel in front of her lights her face: each Advance tick takes a step of light off her, and each relight gives one back. That's why the ticks and relights can play in her singles.
3. **The ceiling enters at the first lie.** Singles before cue 1 (shots 2, 3, 6) frame the ceiling out. From shot 7 on, every frame that can hold the ceiling does, until 8.10. The 75 mm close-ups are the one exception: there, her face is the meter.
4. **Lenses:** 32 · 40 · 50 · **75 (shots 54, 56 and 58 only, the confession)**. Virtual Super 35 sensor (24.89 × 10.41 mm, 2.39:1). There's no depth-of-field trickery: T2.8–T4-equivalent depth, so the panel row and the far end stay readable.
5. **Movement**, all while the car is awake: **shot 20** handheld (recorded operator motion, not procedural noise, per the treatment); **shot 42** the creep push, A → A2, 2.8 m over 21.5 s, landing just after 7.3 so the ticks after it play on a still frame; **shots 54 and 56** the confession push on the 75 (y 9.6 → 10.4), which **has landed by shot 58**, so the car falls asleep (8.10) on a still frame.
6. **Characters may move on twos, but the camera is always on ones**, like the lights.

## Virtual camera positions

The locations are in `cues.json` → `camera.positions`, in set coordinates (lighting-plan §1). Each shot also gives an **aim** point (a subject mark), so the TA can use a Track-To constraint.

| Pos | Where (x, y, z in m) | Default lens | Sees |
|---|---|---|---|
| **A, the Meter** | (0, −3.8, 1.65): unlit vestibule, standing eye height, level | 32 | the full row P12 → P1 (P12 inside the frame with margin), Kai and the doors in the near right foreground, Walter (left) and Bea (right) in the mid-ground, Noor at the far end under the sign and display |
| **A2** | (0, −1.0, 1.65): where the creep push lands | 32 | the same axis, 2.8 m in; P11 and P12 above frame (they're dark by then) |
| **B, Noor's end** | (0.55, 12.85, 1.0): side B corner beside Noor, low, looking down the car | 32 | the dark coming toward camera; Kai's seat and phone deep in frame |
| **C, Walter's side** | (−0.95, 9.6, 1.15) | 50 | Noor singles (aim NOOR) or Bea across the aisle (aim BEA) |
| **W, the call** | (0, 6.0, 1.0): low in the aisle by the doors, aim (0, 12.6, 1.8) | 32 | Noor framed between Walter (left) and Bea (right), with P1 and P2 above her: the two lies are countable in one frame, and we watch her the way Walter does (treatment, scene 2: wide, 25–32 mm) |
| **T, the test** | (0.5, 5.0, 1.0): beside Kai's empty seat, aim (−0.4, 11.0, 1.9) | 32 | Noor standing by Walter, the wrist, and P2, P3 and P4 overhead, watched from the seat the car emptied |
| **C75** | (−0.25, 10.4, 1.2), aim at Noor's eyes | 75 | the confession close-ups only. The push travels from y 9.6 to 10.4 over shots 54–56 and holds there for 58: forehead to chin, so the panel row reads in her corneas |
| **D, Bea's side** | (0.95, 9.6, 1.15) | 40/50 | Noor singles from the other side, or Walter across the aisle |
| **E** | (−1.0, 12.6, 1.15): side A corner by end wall A | 32/40 | Walter/Bea two-shots, deep staging down the car |
| **F, Kai's bay** | (−0.95, 4.875, 1.15) | 40/50 | Kai; the thumb over the red button |
| **G, the doors** | (−0.9, 6.5, 1.3), facing the doors | 32 | the doors and the platform through them |
| **I** | per shot | 50 | inserts: the display, the newspaper, the phones, the lanyard |

## Key shots (notes for the TA and the animators)

| # | Shot | What matters |
|---|---|---|
| **1** | A · 32 · the opening Meter | All 12 panels lit and countable. Noor walks the full length away from us and sits facing us under the sign. Hold. The passing lights play in the glass only. *Board 01* |
| **2** | C · 50 · the lanyard | The ceiling is out (asleep). The 2-frame tick reads only as a blink in the badge laminate and her hair. *Board 02* |
| **7, 9, 11, 13** | **W** · 32 low · the call | **The ceiling enters.** P1 is in the top of frame for lie 1; P1 and P2 are both in frame for lie 2, so it's countable, with Walter (left) and Bea (right) flanking her as they react. **Keep Noor oblivious in it: the audience is ahead of her** (Director). Changed from C · 40 after the TA's style frames (approved): no 40 mm from Walter's side can hold P1 and Noor in a 2.39 frame (geometry check in `build_cues.py`). *Board 03* |
| **16–18** | A / F / A · the vanishing | We're in A from just before cue 3; a short F single gives Kai his nervous laugh; then **A holds from 153.5 s through the blackout and lights-up to 166 s, with no cut.** Kai is in the near right foreground; the seat is empty when the lights return. No dent in the cushion, no swinging strap. *Boards 04–06* |
| **20** | G · 32 · handheld | The only handheld. It steadies the moment we cut to Walter's paper |
| **22–23** | inserts · the newspaper | Two different hands, designed by the Character Designer. *Board 07* |
| **26** | **T** · 32 · "My name is S—" | Noor standing beside Walter under P3, from beside Kai's empty seat; **P2, P3 and P4 overhead, in frame**; the wrist clamp is the fastest motion in the film; hold through the recovery. Changed from E · 40 (approved): from E the three panels are above the frame. *Board 08* |
| **32** | F · 40 · the thumb | The red end-call button must read. It's lit by the screen and the steady P8. *Board 09* |
| **38** | D · 50 · Walter's wife | One unbroken 31-second shot. It lives on his eyes and his hands on the folded paper |
| **42** | A → A2 · 32 · the creep push | The camera rides in behind the dark edge as P12, P11 and P10 go. *Board 10* |
| **44** | B · 32 · the dark toward us | The panels and their reflections in the black windows go out together; Kai's seat goes dark (7.5) and his phone glows on. *Board 11* |
| **49** | C · 50 · Bea, "Say it." | Hold on Bea through 7.10: her light dies to an edge |
| **50** | A2 · 32 · two left | Ten dark, two lit; Noor in the last pool; the display reads 2 MIN. *Board 12* |
| **53** | D · 50 · "He's asking." | Walter half-lit at the edge of the dark (**Director: keep him there**). **His lit-side eye must carry a readable catchlight (P2 or Noor's phone), and the lid line must hold.** The shadow side can sit at −3 stops. *Board 13* |
| **54, 56, 58** | **C75** · 75 · the confession | The first long lens of the film, from **C75 (−0.25, 10.4, 1.2)**, pushing in from y 9.6, near her line of sight down the car; her eyeline passes just camera-right of the lens. Each relight adds a step of front light to her face, so **the truth lights her face**, and **adds its catchlight to the reflected panel row in her corneas.** At 8.10 (shot 58), **P12's catchlight must visibly reappear in her eyes**, completing the row: the meter is in her eyes (dp-notes-02; style guide §2.3 check (c)). The push has landed by 58, so 8.10 plays on a still frame. *Board 14* |
| **57** | A · 32 · the run | The relights run toward camera. Kai's empty seat (near right) relights at 8.6 with the phone still glowing. P10–P12 come after. *Board 15* |
| **62** | G · 32 · the platform | We stay inside. Cold-white lamp. The doors close; the PA plays; she slides away in the glass. *Board 16* |
| **63** | A · 32 · the innocent car | The opening frame again: the whole row lit, Noor's seat empty under the sign, Kai's seat empty in the foreground. Walter turns the page; Kai's phone dims; no light change; cut to black. *Board 17* |
