# THE QUIET CAR: Lighting Plan

**DP** · Milestone 3 · Built on the locked `script/draft-02.md` and the approved `camera/visual-approach.md` · Cue numbers **0–8** match the visual-approach table and the Composer's `music/score-concept.md` §7, one to one.

This document is the board operator's bible: it is the cue list the board operator runs on set. The Composer's cue sheet and the sound team's stems use the same cue numbers.

---

## 1. Set geography

All camera positions, panels and actor marks refer to this plan. (Storyboards: `storyboards/index.html`, frame 00.)

```
 END WALL A (fixed)                                                    END WALL B
 sign + display                                                        (wild: out
 above Noor                                                             for Pos A)
 ┌────────────────────────────────────────────────────────────────────────┐
 │NOOR  ······WALTER······················································│
 │(faces              a i s l e                                           │  ◄── Pos A
 │down) ······BEA·················[DOORS]···KAI···························│
 └────────────────────────────────────────────────────────────────────────┘
  P1    P2    P3    P4    P5    P6    P7    P8    P9    P10   P11   P12
  (· = longitudinal bench, side A above the aisle, side B below; doors on side B)
```

- **12 ceiling panels, P1–P12**, evenly spaced along the centreline (about 1.1 m apart, so the set is about 13 m). **P1 is above Noor** at end wall A. **P12 is the far end**, by end wall B.
- **End wall A** is fixed. It holds the **QUIET CAR** sign and the **LED destination display**, directly above Noor's head. The result is that every frame looking down the car toward her contains the sign (the rule), the display (the clock), Noor, and the whole panel row. Noor glances up and back at the sign, and her "my bad" point at it is over her own shoulder.
- **Noor** sits in a single transverse seat against end wall A, under P1, **facing down the length of the car** toward everyone else. She is literally "facing the others."
- **Walter** sits on the side A bench under P3, with **Bea** facing him across the aisle on side B under P3. That puts them midway between Noor and the doors.
- **Doors:** a pair of sliding doors on side B, centred between P6 and P7. **Kai** sits on the side B bench under P8, right by the doors. His phone stays on that seat for the rest of the film.
- **Seating:** commuter-style longitudinal benches along both walls (teal moquette), so the aisle and the panel row run clear the full length of the car. That's what 2.39:1 wants.
- **End vestibule (new requirement):** an unlit 4 m section beyond P12 (vestibule walls, no ceiling panel, gangway door at the end) for **Pos A, the Meter**. The camera sits in it 3.5 m back from the last seat bay at 1.65 m. That's the only place a 2.39 frame can hold all 12 panels plus Noor under the sign (see `shot-list.md`). It's dark, so it just frames the meter. Studio build: it adds 4 m of stage length, so the stage needs to be at least 20 m long. Borrowed carriage: use its own end vestibule if it's deep enough, or shoot through into the next carriage with its lights off.
- **Display colour:** the LED destination display is **white (or green) dot-matrix, not amber.** Orange belongs only to the car waking.
- **Wild walls:** end wall B (the vestibule's gangway end, out for Pos A), plus two side A window sections (P4–P5 and P8–P9) for the door shots and Kai's exit.
- **Noor's blocking (it decides which panel is "above her"):** she's in her seat under P1 for cues 0, 1, 2 and 6, and for the whole of cues 7 and 8. After Kai vanishes she runs to the doors (P6–P7), then drifts back up the aisle toward Walter and **stands under P4, holding the grab rail, for the test (cue 5)**. He's close enough to catch her wrist. Then she "sits back down slowly," which is the walk back to P1.
- **Kai's exit route in the blackout:** from the P8 bench, through the side B wall flap beside the doors (a hinged section, black on the inside, latched). IR guide marks on the floor. Rehearsed until it takes under 3 seconds.

### What goes dark when (the meter, in plan)

| State | Lit panels | Who's in the light |
|---|---|---|
| Asleep / baseline | P1–P12 | everyone |
| After cue 7.5 | P1–P7 | Kai's seat and phone go dark (his phone glows in the dark from here on) |
| After cue 7.7 | P1–P5 | the doors are dark |
| After cue 7.10 | **P1–P2 only** | Noor. Walter and Bea, under P3, are now just inside the dark edge, lit only by hard spill from P2 |
| End of cue 8 | P1–P12 | everyone, exactly as at the start |

**Decision for the Director:** at the last tick (7.10), **Walter and Bea go into the dark.** The car isn't hunting them, but they're inside its body: two faces cut by the shadow edge from P2, rim-lit on the side toward Noor. Walter's "He's asking" comes from a half-lit face at the edge of the dark. If you'd rather keep them fully lit, we move their bay to P2. That costs us the image, but the blocking is simpler.

---

## 2. The rig

### Ceiling panels
- **12 × RGBW (or RGB plus tunable-white) LED fixtures**, built into the set's diffuser housings (or the borrowed carriage's own housings). Each panel is one fixture.
- **Must have:** a PWM refresh rate of 20 kHz or more (or constant-current dimming); a smooth 16-bit dim curve down to 0% with no step at the bottom; a colour temperature range from **≤2200 K to ≥4300 K**, with green-shift control; and a snap response under one frame (no fixture-side smoothing). Camera-test every unit (§6).
- **A snoot or egg-crate on each diffuser**, plus black wrap at the panel joins, so each panel lights only its own section. **Spill between neighbouring panels must stay below −4 stops**, so the dark keeps a hard edge.

### Other lights
| ID | Unit | Purpose |
|---|---|---|
| F1–F6 | small bounce or soft units hidden above the luggage racks (side A and B, P1–P2, P3, P8) | fill only where the panels need help on faces. **Each one is ganged in the console to its parent panel** and is never cued on its own. If its panel dies, its fill dies. |
| WIN | LED pixel strip chase on a frame outside the side windows, flagged to hit **the glass and window frames only** | passing tunnel lights while the car is **asleep** (opening only). Off whenever the car is awake. |
| DOOR | small practical above the doors (door-open indicator) | door chime moments |
| DISP | power relay for the LED destination display (its content runs from its own controller, cued by the props/display op) | killed in the blackout |
| PLAT | single cold-white hard source in a street-lamp housing (mercury-vapour look: about 5000 K, slight green), on the platform flat | the ending. Rides the rolling wagon |
| IR1–IR4 | 850 nm (or 940 nm) IR LED floor markers along Kai's exit route plus one at the door flap | safety in the blackout. **Not on DMX.** Hard-wired and always on during the blackout setups. Tested to record nothing (§6) |
| PH1–PH3 | phone prop screens (Noor's MARK, Kai's MUM, Kai's end-call screen) | run from the props op's remote app, called like light cues |

### Control
- **Console:** a programmable lighting desk running cue stacks (for example ETC Eos or grandMA3 onPC) or **QLab driving DMX via Art-Net/sACN**. QLab is preferred because the same QLab workspace fires the groan, relay ticks and Undertone playback (seat transducers plus a reference monitor), so **every light cue fires its sound partner from one GO**.
- **Timecode:** the console generates LTC to the camera and the sound recorder, so on-set sync is captured and the editor and Composer get cue timestamps for free.
- **Board operator** on set every shooting day, calling cues on the actors' lines (not on timed fades), with the DP calling the GO points in rehearsal.
- **Effect engine: BREATH.** A sine on every **currently lit** panel's intensity, **depth ±3%, period 5 s, all panels in phase**. It's an effect layered on top of each panel's level, not baked into cues, so a panel coming back on joins the breath already in phase. `BREATH_DEPTH` and `BREATH_PERIOD` are console variables that match the Composer's hum build exactly. They may drop to ±2% or slow down after the test day (Director's condition).

### DMX patch (universe 1)

Each panel uses **4 channels: Intensity · CCT · Green/Magenta · (spare)**.

| Panel | Address | Composer's partial |
|---|---|---|
| P1 (above Noor) | 1–4 | 2 |
| P2 | 5–8 | 3 |
| P3 (Walter/Bea) | 9–12 | 4 |
| P4 | 13–16 | 5 |
| P5 | 17–20 | 6 |
| P6 | 21–24 | 7 |
| P7 (doors) | 25–28 | 8 |
| P8 (Kai) | 29–32 | 9 |
| P9 | 33–36 | 10 |
| P10 | 37–40 | 11 |
| P11 | 41–44 | 12 |
| P12 (far end) | 45–48 | **17 (A♭)** |
| WIN (intensity, speed) | 49–50 | — |
| DOOR | 51 | — |
| DISP relay | 52 | — |
| PLAT (intensity, CCT) | 53–54 | — |
| F1–F6 | 55–60 (followers: F1–F2 → P1, F3 → P2, F4–F5 → P3, F6 → P8) | — |

---

## 3. Looks (presets)

| Preset | Panels | CCT | Notes |
|---|---|---|---|
| **BASE** (asleep) | 100% | 4300 K, +¼ green | Faces exposed at about 1 stop under key at T2.8 / ISO 800 / 1/48. Flat and even, with slight under-eye shadow. **Never altered by anything except a cue.** |
| **BROWN** | 18% (≈ −2.5 stops) | 2200 K, no green | The sag curve: intensity and CCT move together, the way a failing tungsten load would |
| **BLACK** | 0% everything (P, F, WIN, DOOR, DISP relay off; PLAT off) | — | Must measure as true black at the lens (§6) |
| **DIP** | 5% | 3200 K | Cue 5 only: near-black with a hint of warmth, like the panel nearly dying |
| **OVER** | 110%, settling to 100% in 12 frames | 4300 K | Cue 8 relights. **100% in BASE must leave 10% headroom on the fixture**: BASE is set at 90% of fixture output, so "110%" is really full output |

---

## 4. Cue list

**Car cues are numbered 0–8** (the Composer maps these one to one). **World cues** (display D, windows/world W, phones PH) are prefixed so they never collide with the car's numbering. Timings are in frames at 24 fps unless marked. "Snap" means 0 frames. BREATH is on from cue 1 to cue 8.10.

### Opening (asleep)

| Cue | GO on | What happens | Timing | Sound partner (Composer / SD) |
|---|---|---|---|---|
| PRESET | top of take | BASE. DISP shows **NEXT STOP: HOLLOWAY**. WIN off (train idling at the platform). PLAT off (the platform beyond the doors is a dark flat, lit only by spill from the car) | — | idle rumble, fused hum = room tone |
| W1 | doors close | WIN chase on (slow, building with speed). Grips start the rocking | chase ramps over 4 s | rails start |
| D1 | train pulls away | DISP: **NEXT STOP: HOLLOWAY — 11 MIN** | snap | — |
| **0** | Noor straightens her lanyard, the badge settling face-out | **P1 −15% for 2 frames, then back to BASE** | snap down, hold 2 fr, snap up | partial 2 wobbles, near-inaudible relay click |

### First lies (car wakes)

| Cue | GO on | What happens | Timing | Sound partner |
|---|---|---|---|---|
| **1** | NOOR: "Just leaving the office **now**." | **P1 flicker:** 100 → 30 → 85 → 40 → 100 (irregular). **BREATH on** (all panels). **WIN off**, so the windows go dead black and stay black until 8.10. Grips: rocking holds through the cue, then resumes | 12 fr total, steps at 0/3/5/8/12 | first groan (faint); partial 2 bends ≈10¢; Undertone ×1 |
| **2** | NOOR: "The Henley account. **Again.**" | **P1 + P2 flicker deeper and longer:** 100 → 10 → 60 → 10, hold 10% for 8 fr → 100. P2 lags P1 by 2 fr | about 30 fr | groan louder and closer; two partials bend ≈20¢; Undertone ×2 |

### Kai

| Cue | GO on | What happens | Timing | Sound partner |
|---|---|---|---|---|
| PH1 | Kai's phone buzzes | Kai's screen: **MUM** | — | — |
| **3** | KAI: "I'm at the library, **Mum**." | **All panels P1–P12 sag to BROWN and HOLD.** Rocking stops dead | 8 fr sag (a sag, not a snap) | groan from the walls; whole chord flat ~70–90¢; Undertone cluster |
| **4.1** | KAI: "They're doing work on the —" (cut on "the") | **BLACK.** Snap everything to 0, including DISP. IR safety is on (hard-wired). **Shoot at least 5 s.** Kai exits on his rehearsed route | snap | **digital zero on the same frame**: hum, rails and score. The wet inhale (SD) arrives about 2 s in |
| **4.2** | DP's call after the inhale (on set, ≥5 s after 4.1) | **Snap to BASE.** DISP back (11 MIN). BREATH resumes in phase. WIN stays off | snap | hum back instantly, in tune and indifferent; rails resume; Mum's "Kai? … Kai?" |

### Noor tests it

| Cue | GO on | What happens | Timing | Sound partner |
|---|---|---|---|---|
| — | "That's insane." / "My name is Noor." | **Nothing.** Board op's hands off the desk | — | rails and hum only |
| **5** | NOOR: "My name is **S—**" (on the sibilant, as Walter's hand lands) | Noor is **standing in the aisle under P4**, beside Walter (see §1 blocking), so "the panel above her" is P4. **P4 slams to DIP (5%). P3 and P5 dip to 40% in sympathy.** Hold while Walter grips. **Recovery GO** is called by the board op on Walter's release (about 3–4 s): P3–P5 climb back to BASE | slam 2 fr; recovery 72 fr (3 s), slow ease-in | Undertone "hungry" swell, settling with the recovery; partials 5 (P4), and 4 and 6 (P3, P5) |
| D2 | after Walter releases her | DISP: **8 MIN** | snap | — |

### The breath (8 → 5 min)

| Cue | GO on | What happens | Timing | Sound partner |
|---|---|---|---|---|
| PH2 | Noor's thumb hovers over Kai's call | Kai's screen showing the **red end-call button**, at the brightness agreed in the camera test | — | rails alone (Director's ruling) |
| **6** | NOOR: "I'm **f—**" | **P1 stutter:** 100 → 50 → 100 → 45 → 100 | 8 fr | one partial bends and snaps back on "I'm not fine" |
| — | Bea's "two days", Walter's wife | **Nothing.** The steadiest light in the film | — | hum steady; no score |

### The creeping dark (5 → 2 min)

**Every 7.x cue snaps one panel to 0, with a relay tick on the same frame.** There's no flicker. Ganged fills die with their panel. BREATH continues on the panels still lit. The intervals **shorten** as the cue progresses: the car is hurrying.

| Cue | GO on | Panel out | Lit after |
|---|---|---|---|
| D3 | (start of sequence) | DISP: **5 MIN** | P1–P12 |
| **7.1** | "A soft tick from the far end" (≈3 s after D3) | **P12** | P1–P11 |
| **7.2** | NOOR: "Nobody said anything." (on the end of the line) | P11 | P1–P10 |
| **7.3** | as Walter's eyes reach her lanyard | P10 | P1–P9 |
| **7.4** | BEA: "It isn't only what you say." | P9 | P1–P8 |
| **7.5** | Noor looks down at herself | **P8: Kai's seat goes dark; his phone glows on in the dark** | P1–P7 |
| **7.6** | as she reaches for the lanyard | P7 (the doors) | P1–P6 |
| **7.7** | the lanyard hits the floor ("It isn't enough.") | P6 | P1–P5 |
| **7.8** | NOOR: "I can't —" | P5 | P1–P4 |
| **7.9** | BEA: "*Say it.*" | P4 | P1–P3 |
| **7.10** | "Only two lit panels remain" (half a beat after 7.9: the fastest gap) | **P3: Walter and Bea go into the edge** | **P1–P2** |
| D4 | after 7.10 | DISP: **2 MIN** | — |
| PH3 | Noor's phone buzzes | Noor's screen: **MARK**. From here the screen is a key light on her face (§5) | — |

Sound partner for 7.x: one relay tick per panel; each tick removes that panel's partial (the A♭ panel first, then highest to lowest); the Undertone rises underneath.

### The confession (2 min → arrival)

**Every 8.x cue snaps one panel on to OVER (110%), settling to BASE in 12 frames, with a relay click.** The relights start at Noor's panel and spread outward, and **the far panel comes on last** (Director's ruling).

| Cue | GO on | What happens | Lit after |
|---|---|---|---|
| **8.0** | NOOR: "No. Listen. **I'm not leaving the office.**" | **P1 steadies and burns brighter:** to 110% and **held there** (not settled) until 8.10. The one panel in the film that stays above BASE | P1–P2 |
| **8.1** | "...They let me go. **The whole floor.**" | P3 relights (Walter and Bea back in the light) | P1–P3 |
| **8.2** | "...And then I come **home**." (after the library half-beat) | P4 | P1–P4 |
| **8.3** | "I didn't tell you **because** —" | P5 | P1–P5 |
| **8.4** | "— you'd have been **kind** about it —" | P6 | P1–P6 |
| **8.5–8.9** | "— and I couldn't —" and the crying beat that follows, as one quick run (*click, click*, panel after panel) | P7, P8, P9, P10, P11, spaced 8–12 frames apart (Kai's seat relights at 8.6: the empty seat in full light, his phone still glowing) | P1–P11 |
| — | "I'm sorry." / silence on the line | **Nothing.** The far panel waits | P1–P11 |
| **8.10** | the end of the silence on the line (DP/Director call on the day, about 3–4 s) | **P12 relights. P1 settles from 110% to BASE on the same frame. BREATH OFF.** All panels at exactly the BASE level and colour from the first frame of the film | **P1–P12, asleep** |

Sound partner for 8.x: that panel's partial returns with a ~+1 dB swell; cello harmonics double partials 4/6/7/9 on the light, not the words; the A♭ comes back last.

### Arrival and ending

| Cue | GO on | What happens | Sound partner |
|---|---|---|---|
| D5 | the train slows | DISP: **NOW ARRIVING: HOLLOWAY** | cello cue thins out |
| W2 | the train stops / door chime | DOOR practical on. Doors open. **PLAT on** (cold white). Rocking stops | door chime (tuned) |
| — | Noor on the platform | **No car cue.** The car stays at BASE (no parting cue) | hum carries it |
| W3 | door chime, doors close | DOOR practical off | chime; PA "Thank you for riding quietly" |
| W4 | train pulls away | **PLAT and wagon pulled back** (grips). PLAT is panned and dimmed with the wagon, so its light **lives only in the door glass**. Rocking resumes gently. **WIN stays off**: the windows stay black, and the final frame holds no light movement except the two below | rails |
| — | Walter turns the page | **No light change** | release triad (nearly subliminal) |
| PH4 | after the page turn | Kai's phone screen **dims to black** (props op, about a 2 s fade) | the triad is gone before it |
| — | hold | BASE, dead stable, to the cut | hum held to the cut, then rails over black, then nothing |

**Flag for the Director (W4):** I've kept the platform lamp's pass during the pull-away inside the door glass. That's world motion, not a car cue. After the doors close the windows stay black, so the final frame has only the page turn and the phone dimming, as you asked.

---

## 5. Lighting the people

- **Noor:** under P1, with F1 and F2 adding just enough under-chin and eye light that the 75 mm close-up isn't all eye sockets. Her **phone screen (PH3, MARK)** is the other key in the final stretch. Screen brightness is set in the test (about 1 stop under the P1 level on her face at BASE), so by 7.10, with P2 behind her, the phone side reads as the stronger light.
- **Walter and Bea:** under P3, with F4 and F5 for their eyes. After 7.10 they're lit only by P2 spill coming from Noor's side: **a hard edge on the near cheek, the rest in the dark**. We measure that edge in the test, and it must hold detail at about −3 stops.
- **Kai:** under P8, lit by the panel and F6, plus his own phone glow on his thumb and chin.
- **Ground rule:** nothing hits a face that isn't ganged to a panel or a phone. If a frame needs more light, we raise BASE for the whole car, never one person.

---

## 6. Test day (before the shoot)

| # | Test | Pass condition |
|---|---|---|
| T1 | **PWM / flicker:** every panel at 5%, 18%, 50%, 90% and 110%, shot at 24 fps / 180° and at 172.8° and 360° | no roll, beat or banding at any level |
| T2 | **Shadow floor:** BROWN, the cue 7 edge and Walter and Bea at the edge | skin detail holds at −3 stops; noise acceptable at ISO 800 and 3200 |
| T3 | **True black:** BLACK preset, stray-light hunt (exit signs, monitors, camera tally lights, IR) | the scope reads 0 IRE across the frame; no lifted corner |
| T4 | **IR leakage:** IR1–IR4 on in BLACK, through the actual camera, lens, ND and filter stack | **nothing recorded**, at the actual ND stops we plan to shoot. If anything shows, change to 940 nm or add a hot-mirror/IR-cut filter and retest |
| T5 | **Breathing:** BREATH at ±3%/5 s, viewed on the monitor **and projected large** | no one in the room can point to it. If anyone can, drop to ±2% or lengthen the period, and tell the Composer the new values |
| T6 | **Brownout colour:** BROWN at 2200 K vs 2400 K, grade-checked | reads as "power sag", not as "warm scene" |
| T7 | **Phone screens:** MARK, MUM, and the end-call red button in the 40 mm insert | the red reads as red; the screens don't clip at T2.8 |
| T8 | **Spill:** cue 7 at 7.5 and 7.10 | the dark edge falls within ±15 cm of the panel join; no glow under the next panel |
| T9 | **Snap latency:** cue 4.1 and 8.x filmed alongside a slate LED fired by the same GO | panels change within 1 frame of the GO |
| T10 | **Full cue-stack run** with sound partners through QLab, Composer present | every pair lands on the same frame |
