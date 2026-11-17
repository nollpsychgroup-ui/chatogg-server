# THE QUIET CAR: Shot List (CG)

**DP** · Milestone 3 · Built on the locked `script/draft-02.md` and `FORMAT.md` (CG animation) · Read it with:
- **`camera/cut-timeline.md`**: all **65 shots** in order (63 plus sub-shots 8B and 12B, added after previs pass 1), **grouped by the treatment's 8 scenes**, with in/out times, position, lens, move and the cues each one holds (generated);
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
- **Nobody blocks the subject.** The line from each camera to its subject is tested against Walter's and Bea's bodies, Kai's until he vanishes, and Noor's position from the TA's `cg/data/blocking.json` at the shot's time.
- **Everything that must read is in the frame.** Each key shot lists its required panels, faces, sign, display and props, and the script projects them through the lens. That's how the old shot 7 and shot 26 framings were caught and fixed.

## Rules of the frame

1. **The Meter (Pos A) is the spine.** We cut back to it after every escalation to count the damage: shots 1, 4, 10, 16/18, 29, 42, 50, 57 and 63. It opens and closes the film on the same frame.
2. **Every cue is visible in the frame it plays in:** either the cued panel is in frame, or its light lands on a face. **Noor faces down the car**, so every panel in front of her lights her face: each Advance tick takes a step of light off her, and each relight gives one back. That's why the ticks and relights can play in her singles.
3. **The ceiling enters at the first lie.** Singles before cue 1 (shots 2, 3, 6) frame the ceiling out. From shot 7 on, every frame that can hold the ceiling does, until 8.10. The 75 mm close-ups are the one exception: there, her face is the meter.
4. **Lenses:** 32 · 40 · 50 · **75 (shots 54, 56 and 58 only, the confession)**. Virtual Super 35 sensor (24.89 × 10.41 mm, 2.39:1). There's no depth-of-field trickery: T2.8–T4-equivalent depth, so the panel row and the far end stay readable.
5. **Movement**, all while the car is awake: **shot 20** handheld (recorded operator motion, not procedural noise, per the treatment); **shot 42** the creep push, A → A2, 1.8 m over 21.5 s, tilted ~1° up so each panel going out stays inside the top of frame (changed after previs pass 1), landing just after 7.3 so the ticks after it play on a still frame; **shots 54 and 56** the confession push on the 75 (y 9.6 → 10.4), which **has landed by shot 58**, so the car falls asleep (8.10) on a still frame.
6. **Characters may move on twos, but the camera is always on ones**, like the lights.

## Virtual camera positions

The locations are in `cues.json` → `camera.positions`, in set coordinates (lighting-plan §1). Each shot also gives an **aim** point (a subject mark), so the TA can use a Track-To constraint.

| Pos | Where (x, y, z in m) | Default lens | Sees |
|---|---|---|---|
| **A, the Meter** | (0, −3.8, 1.65): unlit vestibule, standing eye height, level | 32 | the full row P12 → P1 (P12 inside the frame with margin), Kai and the doors in the near right foreground, Walter (left) and Bea (right) in the mid-ground, Noor at the far end under the sign and display |
| **A2** | (0, −2.0, 1.65), aim (0, 13, 2.0): where the creep push lands | 32 | the same axis, 1.8 m in, tilted ~1° up; P11 and P12 above frame (they're dark by then) |
| **B, Noor's end** | (0.55, 12.85, 1.0): side B corner beside Noor, low, looking down the car | 32 | the dark coming toward camera; Kai's seat and phone deep in frame |
| **C, Walter's side** | (−0.7, 10.9, 1.15): just in front of Walter, so his head never crosses frame (moved after previs pass 1) | 50 | Noor singles (aim NOOR) or Bea across the aisle (aim BEA) |
| **W, the call** | (0, 6.0, 1.0): low in the aisle by the doors, aim (0, 12.6, 1.8) | 32 | Noor framed between Walter (left) and Bea (right), with P1 and P2 above her: the two lies are countable in one frame, and we watch her the way Walter does (treatment, scene 2: wide, 25–32 mm) |
| **W7** | (0, 8.2, 0.9), aim (0, 12.6, 1.7) | 32 | lie 1 (shot 7) only: closer and low, so P1's fixture is large at the top of frame and visibly flickers (Director, previs-notes-01) |
| **T, the test** | (0.5, 5.0, 1.0): beside Kai's empty seat, aim (−0.4, 11.0, 1.9) | 32 | Noor standing by Walter, the wrist, and P2, P3 and P4 overhead, watched from the seat the car emptied |
| **C75** | (−0.25, 10.4, 1.2), aim at Noor's eyes | 75 | the confession close-ups only. The push travels from y 9.6 to 10.4 over shots 54–56 and holds there for 58: forehead to chin, so the panel row reads in her corneas |
| **D, Bea's side** | (0.7, 10.9, 1.15): just in front of Bea (moved after previs pass 1) | 40/50 | Noor singles from the other side, or Walter across the aisle |
| **E2, the two-shot** | (0, 7.4, 1.15), aim (0, 10.29, 1.25) | 32 | Walter and Bea in profile facing each other, Noor small between them under the sign (shots 8, 12, 33, 39, 55, 61). From Noor's end no 32/40 can hold both: they sit 2 m apart, 2.5 m away |
| **F, Kai's bay** | (−0.95, 4.875, 1.15) | 40/50 | Kai; the thumb over the red button |
| **G, the doors** | (−0.9, 6.5, 1.3), facing the doors | 32 | the doors and the platform through them |
| **G2** | (1.0, 8.4, 1.45) | 32 | shot 20, the handheld: Noor's panicked profile at the doors (from G we only saw her back) |
| **S** | (−0.9, 8.9, 1.5) | 50 | shot 24: Noor standing beside Walter (TA blocking 188–239 s), from in front |
| **B2** | (0.3, 12.85, 1.5) | 32 | shot 44: from beside Noor's head, looking down the car, clear of Walter and Bea |
| **R** | (−0.6, 3.4, 1.4) | 32 | shot 31: from beyond Kai's seat, Noor walking toward it |
| **K** | (1.25, 4.2, 0.75) | 40 | shot 32: low beside Kai's phone, the red end-call button with her thumb coming in from above |
| **E / E3** | (−1.0, 12.2, 1.4) / (−0.7, 6.6, 1.4) | 32 | shot 33 (Bea watching Noor walk back toward camera) / shot 61 (Walter's nod and Bea's closed eyes as Noor passes to the doors) |
| **DP_KAI** | (−0.25, 9.7, 1.6) | 50 | shot 25: Noor's POV from beside Walter, down to Kai's empty seat |
| **I** | per shot | 50 | inserts: the display, the newspaper, the phones, the lanyard |

## Key shots (notes for the TA and the animators)

| # | Shot | What matters |
|---|---|---|
| **1** | A · 32 · the opening Meter | All 12 panels lit and countable. Noor walks the full length away from us and sits facing us under the sign. Hold. The passing lights play in the glass only. *Board 01* |
| **2** | C · 50 · the lanyard | The ceiling is out (asleep). The 2-frame tick reads only as a blink in the badge laminate and her hair. *Board 02* |
| **7, 9, 11** | **W7 / W** · 32 low · the call | **The ceiling enters.** Shot 7 is from W7, so P1's own fixture is large at the top of frame and flickers on cue 1. Shots 9 and 11 are from W: P1 and P2 over Noor, countable, with Walter (left) and Bea (right) flanking her. **Keep Noor oblivious: the audience is ahead of her** (Director). *Board 03* |
| **8 / 8B** | D · 50 Walter / C · 50 Bea | Previs pass 1: the eye beat was unreadable as a two-shot, so it's split into two quick singles: Walter's eyes lift from his paper; Bea's eyes open |
| **12 / 12B** | B · 40 | Noor's POV: Walter, then Bea, staring at her. The first time the regulars look at her; their stares must read |
| **13** | D · 40 | Mouthed "Sorry" and the point over her shoulder: a performance single (it was unreadable at W 32) |
| **16–18** | A / F / A · the vanishing | We're in A from just before cue 3; a short F single gives Kai his nervous laugh; then **A holds from 153.5 s through the blackout and lights-up to 166 s, with no cut.** Kai is in the near right foreground; the seat is empty when the lights return. No dent in the cushion, no swinging strap. *Boards 04–06* |
| **20** | G · 32 · handheld | The only handheld. It steadies the moment we cut to Walter's paper |
| **22–23** | inserts · the newspaper | Two different hands, designed by the Character Designer. *Board 07* |
| **26** | **T** · 32 · "My name is S—" | Noor standing beside Walter under P3, from beside Kai's empty seat; **P2, P3 and P4 overhead, in frame**; the wrist clamp is the fastest motion in the film; hold through the recovery. Changed from E · 40 (approved): from E the three panels are above the frame. *Board 08* |
| **32** | F · 40 · the thumb | The red end-call button must read. It's lit by the screen and the steady P8. *Board 09* |
| **38** | D · 50 · Walter's wife | One unbroken 31-second shot. It lives on his eyes and his hands on the folded paper |
| **42** | A → A2 · 32 · the creep push | The camera rides in behind the dark edge as P12, P11 and P10 go. *Board 10* |
| **44** | B · 32 · the dark toward us | The panels and their reflections in the black windows go out together; Kai's seat goes dark (7.5) and his phone glows on. *Board 11* |
| **49** | C · 50 · Bea, "Say it." | Starts on the overlap ("I can't —" / "Say it."); 7.9 answers the pair; then **8.5 s of silence held on Bea** (no score event) until 7.10, when her own light dies to the edge. Approved by the Director |
| **50** | A2 · 32 · two left | Ten dark, two lit; Noor in the last pool; the display reads 2 MIN. *Board 12* |
| **53** | D · 50 · "He's asking." | Walter half-lit at the edge of the dark (**Director: keep him there**). **His lit-side eye must carry a readable catchlight (P2 or Noor's phone), and the lid line must hold.** The shadow side can sit at −3 stops. *Board 13* |
| **54, 56, 58** | **C75** · 75 · the confession | The first long lens of the film, from **C75 (−0.25, 10.4, 1.2)**, pushing in from y 9.6, near her line of sight down the car; her eyeline passes just camera-right of the lens. Each relight adds a step of front light to her face, so **the truth lights her face**, and **adds its catchlight to the reflected panel row in her corneas.** At 8.10 (shot 58), **the tip of the reflected row completes in her corneas**. P12 itself is sub-pixel at ~10 m, which the Director has accepted: **keep C75 as framed and don't push tighter.** The A♭ returning in the hum and shot 63's full Meter carry the rest. The meter is in her eyes (dp-notes-02; style guide §2.3 check (c)). The push has landed by 58, so 8.10 plays on a still frame. *Board 14* |
| **57** | A · 32 · the run | The relights run toward camera. Kai's empty seat (near right) relights at 8.6 with the phone still glowing. P10–P12 come after. *Board 15* |
| **62** | G · 32 · the platform | We stay inside. Cold-white lamp. The doors close; the PA plays; she slides away in the glass. *Board 16* |
| **63** | A · 32 · the innocent car | The opening frame again: the whole row lit, Noor's seat empty under the sign, Kai's seat empty in the foreground. Walter turns the page; Kai's phone dims; no light change; cut to black. *Board 17* |
