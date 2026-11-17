# THE QUIET CAR: Lighting Plan (CG)

**DP** · Milestone 3 · Built on the locked `script/draft-02.md`, the approved `camera/visual-approach.md` and **`FORMAT.md` (CG animation, Blender)** · Cue numbers **0–8** match the visual-approach table and the Composer's `music/cue-sheet.md`, one to one.

**The machine-readable version of this plan is `camera/cues.json`**, written by `camera/build_cues.py`. The TA's Blender scripts keyframe the lights and cameras from it, and the Composer's `render_temp_score.py` reads it for sync. If this document and `cues.json` ever disagree, **`cues.json` wins**, and I fix the document.

The TA's Blender build (`film/cg/`) reads `cues.json` directly, in these axes.

---

## 1. Set geography

All camera positions, panels and character marks refer to this plan (boards: `storyboards/index.html`, frame 00). Set coordinates in `cues.json` use the Blender convention: Z is up, **Y runs down the car from end wall B (y = 0) to end wall A (y = 13, Noor)**, side A is −X and side B is +X.

```
 END WALL A                                                             END WALL B
 sign + display                                                         gangway, then the
 above Noor                                                             unlit vestibule (Pos A)
 ┌────────────────────────────────────────────────────────────────────────┐
 │NOOR  ······WALTER······················································│
 │(faces              a i s l e                                           │  ◄── Pos A
 │down) ······BEA·················[DOORS]···KAI···························│
 └────────────────────────────────────────────────────────────────────────┘
  P1    P2    P3    P4    P5    P6    P7    P8    P9    P10   P11   P12
  (· = longitudinal bench, side A above the aisle, side B below; doors on side B)
```

- **12 ceiling panels, P1–P12**, evenly spaced along the centreline about 1.08 m apart, over a 13 m seating section. **P1 is above Noor** at end wall A; **P12 is the far end**, by end wall B.
- **End wall A** holds the **QUIET CAR** sign and the destination display, directly above Noor's head. Every frame looking down the car toward her contains the sign (the rule), the display (the clock), Noor and the whole panel row. Noor glances up and back at the sign, and her "my bad" point is over her own shoulder.
- **Noor** sits in a single transverse seat against end wall A, under P1, **facing down the car** toward everyone else.
- **Walter** sits on the side A bench under P3, with **Bea** facing him across the aisle on side B, also under P3.
- **Doors:** sliding doors on side B, centred between P6 and P7. **Kai** sits on the side B bench under P8, by the doors. His phone stays on that seat for the rest of the film.
- **Seating:** commuter-style longitudinal benches along both walls (teal moquette), so the aisle and the panel row run clear for the whole length.
- **End vestibule (build it as real geometry):** an unlit 4 m section beyond end wall B's gangway (y −4 to 0), with no ceiling panel. **Pos A, the Meter, sits in it**, 3.8 m back from the last seat bay, at standing eye height (1.65 m), on a 32 mm. I checked the geometry: this is the only position that holds all 12 panels plus Noor under the sign in a 2.39 frame. Its walls frame the shot honestly, so we don't need to hide or cheat any geometry.
- **Display:** white (or pale green) dot-matrix, **not amber.** Orange belongs only to the car waking.
- **Noor's blocking decides which panel is "above her":** she's in her seat under P1 for cues 0, 1, 2 and 6 and all of cues 7 and 8. After Kai vanishes she runs to the doors, then drifts back up the aisle and **stands beside Walter under P3, holding the grab rail, for the test (cue 5)**, close enough for him to catch her wrist. Then she "sits back down slowly," which is the walk back to P1.

### What goes dark when (the meter, in plan)

| State | Lit panels | Who's in the light |
|---|---|---|
| Asleep / baseline | P1–P12 | everyone |
| After 7.5 | P1–P7 | Kai's seat goes dark; his phone glows on in the dark |
| After 7.6 | P1–P6 | the doors are dark |
| After 7.10 | **P1–P2 only** | Noor. Walter and Bea, under P3, are just inside the dark edge, lit only by the hard spill from P2 |
| End of cue 8 | P1–P12 | everyone, exactly as at the start |

**Still open for the Director:** at the last tick (7.10), **Walter and Bea go into the dark.** The car isn't hunting them, but they're inside its body: two faces cut by the shadow edge from P2, rim-lit on Noor's side. Walter's "He's asking" comes from a half-lit face. If you'd rather keep them lit, we move their bay to P2. That costs us the image, but it simplifies the blocking.

---

## 2. The virtual light rig (Blender)

The rule from the treatment: **the world is painted; the light is real.** Every light below is a physically placed, keyframed light, and nothing is painted in.

### Ceiling panels
- **12 rectangular area lights**, 0.64 × 0.6 m, at the ceiling (z = 2.29), facing down, one per panel. Each sits inside an **emissive diffuser mesh** that the camera sees (the panel itself) and is driven by the same level, so the visible panel and the light it casts can never disagree.
- **Colour:** a blackbody colour temperature per panel (BASE 4300 K with a slight green shift; BROWN 2200 K). Level and colour move together.
- **A hard edge for the dark (cue 7):** the area lights use a narrow **spread** (about 100°), and each diffuser has a short physical baffle box, so **each panel lights only its own section.** Spill into a dark neighbour stays below −4 stops. The painterly shader must not soften that edge across the floor and seats (style guide).
- **Keyframes on ones, constant interpolation**, except the eases named in the cue list (the cue 3 sag, the cue 5 recovery, the cue 8 overshoot settle). Characters may animate on twos, but **the lights, the breathing and the camera are always on ones.**
- **The breathing (`BREATH`):** a driver on a controller empty adds `1 + depth × sin(2πt/period)` to every **currently lit** panel, all in phase. `depth` = 0.03 and `period` = 5 s are properties shared by name with the Composer's hum build. It's on from cue 1 to 8.10. P1 stops breathing at 8.0, when it "steadies."

### Other lights
| ID | What | Rule |
|---|---|---|
| WINDOWS | emissive strips on a frame outside the side windows: passing tunnel lights | **Asleep only** (from the doors closing until cue 1, and never after). They show only in the glass and window frames, never on faces: use light linking so they illuminate nothing inside the car |
| DISPLAY | emissive texture, white dot-matrix | goes to 0 in the blackout |
| DOOR | small emissive door-open indicator | arrival only |
| PHONES | emissive screens: Noor's (MARK) and Kai's (MUM, the end-call screen with its red button) | Real light sources. Kai's phone is the only light left in the dark section after 7.5. Noor's MARK screen becomes a key on her face from 440 s |
| PLATFORM | one cold-white light in a street-lamp housing, about 5000 K, slight green (mercury-vapour look), plus light ground fog | from the doors opening; it slides away with the platform during the pull-away, visible only in the door glass |
| WORLD | **black (0).** No ambient, no HDRI, no fill | — |

**No fill lights.** If a face needs help, raise BASE for the whole car, never for one person. If the TA needs eye catchlights, they come from the actual panels (treatment, art direction rule 7).

### True black
In the blackout (cue 4), **every emitter is 0**: panels, diffusers, display, windows, door indicator and world. The painterly treatment must add nothing either: no paper texture, canvas grain, brush lift, glow, bloom or vignette that could lift black. **The check: every pixel of frames 155.0–158.0 s in the final comp is exactly 0.**

---

## 3. Looks

| Look | Level | Colour | Notes |
|---|---|---|---|
| **BASE** (asleep) | 1.0 | 4300 K, slight green | Flat and even, with slight under-eye shadow. **Never altered by anything except a cue.** The TA sets the absolute wattage in look-dev; everything else is relative to it |
| **BROWN** | 0.18 (about −2.5 stops) | 2200 K | Level and colour temperature move together, like a failing tungsten load |
| **DIP** | 0.05 | 3200 K | Cue 5 only: near-black with a hint of warmth |
| **OVER** | 1.10, settling to 1.0 in 12 frames | 4300 K | Cue 8 relights. P1 holds at 1.10 from 8.0 to 8.10 |
| **OFF** | 0 | — | Cue 4; cue 7 panels |

---

## 4. Cue list

Times are from `cues.json` (estimates for a ~9:25 cut, to be re-timed to the voice record). Durations are in frames at 24 fps. "Snap" means a constant keyframe on the frame.

### Opening (asleep)

| Cue | t (s) | On | What happens | Sound partner |
|---|---|---|---|---|
| — | 0 | top | BASE. Display: NEXT STOP: HOLLOWAY. Doors open onto the starting platform: PLATFORM lamp on (cold white). Windows off | idle rumble; the hum is room tone |
| — | 48 | doors close | The starting platform and its lamp slide away (48–58 s). WINDOWS on (glass only). Display: 11 MIN at 50 s | rails start |
| **0** | 40 | Noor straightens her lanyard | **P1 to 0.85 for 2 frames, then back to 1.0** | partial 2 wobbles; near-inaudible relay click |

### First lies (the car wakes)

| Cue | t | On | What happens | Sound partner |
|---|---|---|---|---|
| **1** | 80 | "Just leaving the office **now**." | **P1 flicker:** 0.30 → 0.85 → 0.40 → 1.0, at frames 0/3/5/8. **BREATH on. WINDOWS off**, and they stay black until the end | first groan (faint); Undertone ×1 |
| **2** | 95 | "The Henley account. **Again.**" | **P1 + P2:** 0.10 → 0.60 → 0.10, held, → 1.0, at frames 0/4/8–16/22. P2 lags 2 frames | groan louder and closer; Undertone ×2 |

### Kai

| Cue | t | On | What happens | Sound partner |
|---|---|---|---|---|
| **3** | 145 | "I'm at the library, **Mum**." | **Every panel sags to BROWN over 8 frames and holds** | groan from the walls; the chord goes flat; Undertone cluster |
| **4** | 155 | "They're doing work on the —" (cut on "the") | **TRUE BLACK** (§2). Kai is removed in the dark; there is no animation of him leaving | digital zero; the inhale arrives in the dark |
| **4.up** | 158 | after the inhale | **Snap to BASE.** Display back. BREATH resumes in phase. WINDOWS stay off | hum back instantly, in tune; rails; "Kai? ... Kai?" |

### Noor tests it

| Cue | t | On | What happens | Sound partner |
|---|---|---|---|---|
| — | | "That's insane." / "My name is Noor." | **Nothing** | rails and hum only |
| **5** | 225 | "My name is **S—**", as Walter's hand lands | Noor stands under P3. **P3 slams to DIP in 2 frames; P2 and P4 dip to 0.40 in sympathy.** They hold while he grips, then recover at 229 s over 72 frames with a slow ease-in | the Undertone's "hungry" swell, settling with the recovery |

### The breath (8 → 5 MIN)

| Cue | t | On | What happens | Sound partner |
|---|---|---|---|---|
| — | 264 | her thumb over Kai's call | Kai's screen with the **red end-call button** | rails alone |
| **6** | 295 | "I'm **f—**" | **P1 stutter:** 0.50 → 1.0 → 0.45 → 1.0, at frames 0/2/4/8 | one partial bends and snaps back on "I'm not fine" |
| — | | Bea's two days, Walter's wife | **Nothing.** The steadiest light in the film | the hum is steady |

### The Advance (5 → 2 MIN)

**Ten ticks, steady 8.5 s apart, never accelerating, and never on a line. Each one follows a line or a look, as if the car were answering it** (Director, `notes/composer-notes-02.md`). Each tick snaps one panel to 0, with a relay tick on the same frame and no flicker. BREATH continues on the panels still lit. **Noor faces down the car, so every tick also takes one step of front light off her face.** That's how the ticks read in her singles.

| Cue | t | Follows | Panel out | Lit after |
|---|---|---|---|---|
| **7.1** | 360.0 | (display 5 MIN; no word spoken) | **P12** | P1–P11 |
| **7.2** | 368.5 | NOOR: "Nobody said anything." | P11 | P1–P10 |
| **7.3** | 377.0 | Walter's eyes reach her lanyard | P10 | P1–P9 |
| **7.4** | 385.5 | BEA: "It isn't only what you say." | P9 | P1–P8 |
| **7.5** | 394.0 | Noor looks down at herself | **P8: Kai's seat goes dark, and his phone glows on in the dark** | P1–P7 |
| **7.6** | 402.5 | the lanyard hits the floor | P7 (the doors) | P1–P6 |
| **7.7** | 411.0 | (silence; Bea leans in) | P6 | P1–P5 |
| **7.8** | 419.5 | BEA: "Whatever it is, say it." | P5 | P1–P4 |
| **7.9** | 428.0 | NOOR: "I can't —" | P4 | P1–P3 |
| **7.10** | 436.5 | BEA: "*Say it.*" | **P3: Walter and Bea go into the edge** | **P1–P2** |

At 438 s the display reads 2 MIN. At 440 s Noor's phone rings (MARK), and from here her screen is a key on her face.

### The confession (2 MIN → arrival)

**Each 8.x snaps one panel on at OVER (1.10), settling to 1.0 in 12 frames, with a relay click.** The relights start at Noor's panel and spread outward, and **the far panel comes on last**.

| Cue | t | On | What happens |
|---|---|---|---|
| **8.0** | 462.0 | "No. Listen. **I'm not leaving the office.**" | **P1 steadies and burns brighter:** to 1.10 and held; its breathing stops |
| **8.1** | 470.0 | "...They let me go. **The whole floor.**" | P3 relights: Walter and Bea are back in the light |
| **8.2** | 483.0 | "...And then I come **home**." (after the library half-beat) | P4 |
| **8.3–8.9** | 493.0–499.6 | "I didn't tell you because you'd have been kind about it, and I couldn't —": *click, click*, panel after panel, about 1.1 s apart | P5 → P11 (Kai's empty seat relights at 8.6) |
| — | 502–505 | "I'm sorry." Silence on the line | **Nothing.** The far panel waits |
| **8.10** | 508.0 | the end of the silence | **P12 relights. P1 settles to 1.0 on the same frame. BREATH off.** Every panel is exactly BASE, as in the first frame of the film |

### Arrival and ending

| t | What happens |
|---|---|
| 512 | Display: NOW ARRIVING: HOLLOWAY. The Holloway platform slides in, seen only in the door glass (512–520) |
| 520–521 | Door chime; doors open; DOOR indicator on; **PLATFORM on** (cold white) |
| — | **No car cue.** The car stays at BASE: no parting cue |
| 535–538 | Doors close; PA: "Thank you for riding quietly." |
| 540–548 | The platform and its lamp slide away, seen only in the door glass. **WINDOWS stay off**, so from 548 s the frame holds no light movement |
| 552 | Walter turns the page: **no light change** |
| 561 | Kai's phone fades to black over 2 s |
| 565 | Cut to black. Rails stop at 568 |

---

## 5. Lighting the people

- **Noor** is lit by P1 from above, and by the whole lit car **in front of her**, since she faces down its length. That front light is the film's barometer: every tick in cue 7 takes a step of it away, and every relight in cue 8 gives one back. **The truth lights her face.** Her phone (MARK) is the other key in the final stretch. It's set so that by 7.10 the phone side of her face reads as the stronger light.
- **Walter and Bea** are under P3. After 7.10 they're lit only by the P2 spill from Noor's side: **a hard edge on the near cheek, the rest in the dark.** It must hold some detail at about −3 stops.
- **Kai** is under P8, plus his own phone glow on his thumb and chin.
- **Eyes:** catchlights come from the actual panels, so they go out with them.

---

## 6. Look-dev checks (these replace the live-action test day)

| # | Check | Pass condition |
|---|---|---|
| L1 | **No false light events:** render noise, denoiser shimmer, temporal flicker in the painterly pass | a static asleep shot rendered across 10 s shows **no** frame-to-frame change in the light. Fixed seeds; enough samples, or EEVEE |
| L2 | **True black** | every pixel of the blackout frames is exactly 0 after comp and grade (§2) |
| L3 | **Breathing visibility:** ±3% / 5 s, viewed on a monitor **and projected large** | nobody can point to it. If anyone can, drop to ±2% or slow it, and update `breath` in `cues.json` (the Composer's hum follows) |
| L4 | **Brush stillness:** any animated brushwork | dead still while the car is asleep. Also test the Director's option: a faint boil only while the car is awake, locked to BREATH |
| L5 | **Hard edge:** the cue 7 dark | the edge falls within about 15 cm of the panel join on the floor, seats and walls; the paint doesn't soften it |
| L6 | **Brownout colour** | 2200 K vs 2400 K: it reads as a power sag, not as "warm scene". **2400 K is the most we move** (Director); no camera white-balance chase |
| L7 | **The two reds** | the lanyard strap and Kai's end-call button read as red; nothing else in the car is red. Restated by the Designer and Director: **under BASE the strap is the most chromatic object; under BROWN and DIP it's the only red by hue separation.** It need not out-chroma the sodium-lit surfaces, which is honest physics: the car takes the colour out of everything. The strap widens to 25 mm, and strap and badge stay crisp out of the merge into the darks |
| L8 | **Lights on ones** | every light key lands on a whole frame, with no sub-frame or smoothed keys except the named eases |
| L9 | **Meter count** | in Pos A, all 12 panels are individually countable at 1080p |

## 7. What was dropped with the format change

The DMX patch, the board operator, bass transducers, IR safety light, the blackout-tight stage, the platform wagon and the camera/lighting test day are all gone (`FORMAT.md`). The cue design, the panel map and the numbering are unchanged; they became keyframes. The old DMX channel for each panel is kept in `cues.json` (`dmx_legacy`) in case a live-action version is ever shot.
