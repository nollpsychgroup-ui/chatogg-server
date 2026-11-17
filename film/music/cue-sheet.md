# THE QUIET CAR: Music Cue Sheet

**Composer** · Milestone 3 · against the **locked** `script/draft-02.md` · implements `music/score-concept.md` (v2, approved, plus `notes/composer-notes-01.md`) · scene numbers **1–8** from `notes/directors-treatment.md`, lighting cue numbers **0–8** and panels **P1–P12** as agreed with the DP (`camera/visual-approach.md`; sub-cues 7.x/8.x as the DP proposed for `lighting-plan.md`)

> **How to read this.** The score is mostly a *system*, not a set of pieces: the panel hum (cue **1M0**) runs the whole film and changes state on the DP's lighting cues. The other cues are layers that sit on that bed. **In/out points are script lines and lighting cue numbers**, which are the real sync. Timecodes are **estimates** for a ~9:05 cut, to be replaced from the DP's shooting cue stack and the edit.
>
> **Cue naming:** `1Mx` (reel 1, music cue x). "DP n" = lighting cue n. "SD" = sound design.

---

## Constants

| | |
|---|---|
| Tonal centre | Mains hum **50 Hz** ≈ G1 +35¢. Score tuned to A4 ≈ 449 Hz |
| Panel map | **P1** (above Noor) = partial 2 · P2 = 3 · P3 = 4 · P4 = 5 · P5 = 6 · P6 = 7 · P7 = 8 · P8 = 9 · P9 = 10 · P10 = 11 · P11 = 12 · **P12** (far end) = partial **17 ≈ A♭** (deliberately off-series) |
| Fundamental | 50 Hz stem, separate from P1–P12 |
| Breathing | `BREATH_DEPTH` ±3%, `BREATH_PERIOD` 5 s, locked to the panels from DP 1 until DP 8.10. **Values are provisional until the test day** (Director may set ±2% or slower) |
| Undertone pitches | G0 / A♭0 / F♯0 (25 Hz region) + doubling to 400 Hz + bowed-metal grain. The phone-band layer must carry the motif alone (`sketches/phone-check.txt`) |
| Silence | DP 4 blackout = **digital zero** on every stem: music, hum, rails, room tone |

---

## Cue list

| Cue | Scene | Title | In | Out | Est. TC | DP cue / panels |
|---|---|---|---|---|---|---|
| **1M0** | 1–8 | Carriage Chord (bed) | first frame | CUT TO BLACK | 0:00 – 9:05 | all; P1–P12 + fundamental |
| **1M1** | 2 | First Waking | "Just leaving the office now." | end of groan | 1:20 – 1:27 | DP 1 · P1 |
| **1M2** | 2 | Second Waking | "The Henley account. Again." | end of groan | 1:35 – 1:44 | DP 2 · P1, P2 |
| **1M3** | 3 | Brownout | "I'm at the library, Mum." | **hard out on DP 4** | 2:25 – 2:35 | DP 3 · all |
| — | 3 | *(Blackout: no music)* | DP 4 | lights up | 2:35 – 2:38 | DP 4 |
| **1M4** | 4 | Hungry | "My name is S—" | panel back to white | 3:45 – 3:53 | DP 5 · P1 (+P2, P3 in sympathy) |
| **1M5** | 5 | Stutter | "I'm f—" | "I'm not fine." | 4:55 – 4:57 | DP 6 · P1 |
| **1M6** | 6 → 7 | The Advance | first far-end *tick* (DP 7.1) | receded by DP 8.10 | 6:00 – 8:08 | DP 7.1–7.10 · P12 → P3 |
| **1M7** | 7 → 8 | Relight | DP 8.1 (P3 relights) | thinned out by the door chime | 7:22 – 8:20 | DP 8.1–8.10 · P3 → P12 |
| **1M8** | 8 | Page Turn | Walter turns the page | before Kai's phone dims | 8:52 – 9:01 | no light change |

**By scene** (treatment): 1 Boarding: bed only, cue 0 tick · 2 The call: 1M1, 1M2 · 3 Kai: 1M3, blackout silence · 4 The note and the test: 1M4 · 5 Truth exchange: 1M5 only, otherwise unscored · 6 Creeping dark: 1M6 · 7 Confession: 1M6 receding, 1M7 · 8 Holloway: 1M7 tail out before the doors, PA unscored, 1M8, silent credits.

Approximate on-screen music (cues 1M1–1M8, excluding the bed): **about 3 minutes, almost all of it below conscious notice.**

---

## 1M0: Carriage Chord (bed)

- **Purpose:** the car itself. Until DP 1 it's just fluorescent hum: no score. Every later cue is a change to it.
- **Instrumentation:** 12 near-sine panel tones (partials per the map) with light ballast buzz, plus the 50 Hz fundamental. Recorded through a small speaker in a real carriage, or convolved with an IR of one. Optional glass/bowed vibraphone at very low level on P7–P11.
- **Stems:** **13**: `1M0_P01` … `1M0_P12` and `1M0_FUND`, one per DMX channel, delivered to SD for the mix. Mixed at room-tone level.
- **States:**

| From | State | Detail |
|---|---|---|
| 0:00 | Asleep | All 12 lit, fused, in tune, no breathing |
| DP 0 (Noor's lanyard, ~0:40) | Tick | P1 partial wobbles ~8¢ for **2 frames** with the light. Nothing else |
| DP 1 | Awake | **Breathing starts** (±3% / 5 s) |
| DP 3 | Brownout | Whole chord sags **70–90¢ flat** with the warm dim and drops ~6 dB. **The first clearly audible out-of-tune moment** |
| DP 4 | Blackout | **All stems to digital zero on the frame**, held for the blackout (~3 s on screen) |
| Lights up | Indifferent | All 12 back **instantly, in tune**, still breathing. No fade |
| DP 7.1–7.10 | Advance | Each relay tick removes one panel's stem on the frame: P12 (A♭) first, then P11 → P3. P1–P2 stay lit |
| DP 8.0 | Truth | P1 **steadies**: its breathing stops and it swells ~+1 dB ("burning brighter") |
| DP 8.1–8.10 | Relight | Each panel's stem returns on its click with a ~+1 dB, 0.5 s overshoot matching the 110% light overshoot. Order P3 → P12, so the A♭ panel returns last |
| DP 8.10 | Asleep again | **Breathing stops.** Dead stable to the end (no parting light cue) |
| Page turn → CUT | Thinning | Partials 5+ (P4–P11, P12) ease down ~9 dB under 1M8. **P1–P3 and the fundamental hold full until the cut** ("The lights hum.") |
| CUT TO BLACK | Out | Hum cut on the frame. Rails (SD) carry over black, then stop. **Title and credits silent** |

- **SD interaction:** SD owns the ticks and clicks, which are dry, on the lighting frame. The bed never "hits" a tick: a partial simply starts or stops under it.

## 1M1: First Waking

- **In:** "Just leaving the office now." on DP 1 · **Out:** as the groan fades.
- **Purpose:** the car hears her. It should be felt, not noticed.
- **Music:** P1 partial bends ≈ **10¢** flat in three irregular pulses with the flicker. **Undertone ×1**: G → A♭ → F♯ → G over ~3.5 s, very quiet.
- **Instrumentation:** contrabass (scordatura, sul pont., slow bow) + sub-sine, with bowed-cymbal grain.
- **SD:** the faint groan ("could be the brakes") is SD. The Undertone sits *inside* it, as its pitch.

## 1M2: Second Waking

- **In:** "The Henley account. Again." on DP 2 · **Out:** groan fades, before Kai's "Was that the brakes?"
- **Music:** P1 and P2 bend ≈ **20¢**. **Undertone ×2** (G and A♭ rubbing), louder and longer (~4.5 s).
- **SD:** the groan is "louder, longer and closer." The Undertone grows with it. **Dialogue:** Kai's line is in the clear.
- **"No, don't wait up. Love you."** is true: **nothing happens**, no bend and no Undertone (treatment, scene 2: "the first silent proof of the rule").

## 1M3: Brownout

- **In:** "I'm at the library, Mum." on DP 3 · **Out:** **hard cut on the DP 4 frame**, mid-phrase. No tail.
- **Purpose:** the whole car acts at once. It's the first time the audience *hears* the hum go wrong.
- **Music:** 1M0 sags 70–90¢ flat. **Undertone ×3 cluster** (F♯–G–A♭), full level, ~7 s, still rising when it's cut.
- **Instrumentation:** contrabass + sub, bowed bass drum, bowed cymbal, pitch-locked resampled coupling groan.
- **SD:** the groan "from the walls." **The seat transducers carry the Undertone + groan** at full level on non-dialogue takes. Kai's nervous line ("No, that's — it's the library…") sits over it: the cluster's phone-band layer ducks ~4 dB under dialogue.

## Blackout (DP 4): no cue

- **Digital zero** on every stem for the length of the blackout, rails included.
- **The inhale** is SD. Pitch reference from music: **F♯ → G rising** (the motif reversed, `sketches/theme-1-undertone` at 24.5 s). It's the only sound in the dark.
- **Lights up:** 1M0 returns instantly and in tune. Rails return. "Kai? … Kai?" from the phone is dialogue/SD.

## 1M4: Hungry

- **In:** "My name is S—" on DP 5 · **Out:** as "the panel climbs back up to white."
- **Purpose:** the car hears *intent*. The swell is cut off by Walter's grip, not by the lie finishing.
- **Music:** P1 bends ~20¢ (P2/P3 ~10¢ in sympathy). **Undertone ×3 "hungry" swell** rises fast out of the floor (~1.5 s), then *settles* slowly back into the rails over ~6 s while Walter holds on. Its longest decay in the film.
- **SD:** groan swell "up out of the floor" (SD), transducers. "Nobody breathes": no new sound events during the settle.

## (Rails beat and Kai's phone, 8 MIN): no cue

- From the 8 MIN display to Bea's "You okay?": **rails alone** (Director's ruling). 1M0 continues at room tone, breathing, with nothing changing. Includes Noor's thumb over the red button and Mum's faint "Kai?".

## 1M5: Stutter

- **In:** "I'm f—" on DP 6 · **Out:** "I'm not fine." (panel steadies).
- **Music:** P1 bends ~12¢ twice with the two hiccups, then snaps back in tune on "I'm not fine." **No Undertone.** The lie never finished.
- **SD:** no groan, or barely one.

## (Truth exchange, 8 → 5 MIN): no cue

- Bea's "I haven't slept in two days," Walter's wife, the lanyard: **no music events.** 1M0 steady and breathing. Truth does nothing.

## 1M6: The Advance

- **In:** the first *tick* from the far end (DP 7.1, display at 5 MIN) · **Out:** recedes through the relights, gone by DP 8.10.
- **Purpose:** an advance, not a reaction. The chord is taken apart from the top, so the car sounds duller and heavier as the dark approaches.
- **Music:**
  - 1M0 loses one partial per tick: **7.1 = P12 (A♭)**, then 7.2 = P11 … 7.10 = P3. P1–P2 remain.
  - **Undertone ×3** enters on 7.1 at low level and rises slowly and patiently with each tick, peaking at "He's asking."
  - **Lines in the clear:** "It isn't only what you say," "Whatever it is, say it," "Say it." The Undertone's phone-band layer ducks ~4 dB under each line.
- **Instrumentation:** contrabass, sub, bowed metal. No new colours.
- **SD:** a relay tick per panel (SD) and the groan rising underneath (SD), with the transducers. **The script names 5 ticks; the DP has 10 panels to clear** (7.1–7.10). Some ticks will fall between lines, and that's fine for the music: each tick is one partial.
- **Recedes:** from DP 8.1 the Undertone falls ~2 dB per relight and is gone with the last click ("THE GROAN recedes into the rails").

## 1M7: Relight

- **In:** DP 8.1, P3 relighting on "…They let me go. The whole floor." · **Out:** fully thinned before the doors open (door chime).
- **Purpose:** the film's one moment of warmth. It comes in *with the light*, never on the words, and never before Noor's first true sentence ("I'm not leaving the office" gets only 8.0, P1 steadying).
- **Music:** each relit partial returns in 1M0. On four of them, a **cello natural harmonic doubles the panel's pitch** with a slow, narrow vibrato:

| DP | Panel | Partial | Cello | Line |
|---|---|---|---|---|
| 8.1 | P3 | 4 | **G** (vc 1) | "…The whole floor." |
| 8.2 | P4 | 5 | **(no cello: B, the third, withheld)** | "…And then I come home." |
| 8.3 | P5 | 6 | **D** (vc 2) | "I didn't tell you…" (first of the *click, click* run) |
| 8.4 | P6 | 7 | **F** (vc 1, harmonic slightly flat, the "blue" 7th) | run |
| 8.5 | P7 | 8 | — | run |
| 8.6 | P8 | 9 | **A** (vc 2) | run |
| 8.7–8.9 | P9–P11 | 10–12 | — | run |
| 8.10 | P12 | A♭ | — | after "Silence on the line." Last panel, the car's note, back in its place |

  - **The "library" half-beat** (8.1 → 8.2): the cellos hold still. Nothing enters on it.
  - **"I'm sorry." / silence on the line:** the vibrato **freezes into straight tone** over ~1 s. Warmth stops breathing, like the car.
  - **The train slows → door chime:** the cellos thin out (~5 s) and are gone before the doors open.
- **Instrumentation:** 2 cellos, natural harmonics, sul tasto, very soft. A breath of glass doubling the G only.
- **Level:** *under* Noor's dialogue, never beside it. The sonority is G–D–F–A, neither major nor minor. **It does not resolve.**
- **SD:** relay clicks (SD), groan receding (SD). Mark's murmur and its silence are dialogue: no music reacts to them.

## (Arrival to the PA line): no cue

- Door chime ×2 (SD, **tuned by music**: partials 18 then 12, A then D above the hum). Noor's exit, the platform and the murmur restarting: **1M0 only**, dead stable. **"Thank you for riding quietly." is unscored.** PA voice ideally pitched near D (partial 12).

## 1M8: Page Turn

- **In:** Walter turns the page · **Out:** gone before Kai's phone screen dims (~1 s clear of it).
- **Purpose:** Walter's release. The B withheld at the confession arrives for him, not for Noor's marriage.
- **Music:** pure **4:5:6 triad, partials 8, 10, 12** (G–B–D, just intonation, three to three-and-a-half octaves above the hum). Slow attack (~4 s), no vibrato, staggered entries (G, then B +0.6 s, then D +1.2 s). Peaks well below the hum, then fades.
- **Instrumentation:** bowed vibraphone (G, D) and glass (B).
- **Level:** **nearly subliminal**, softer than you'd think. It should feel like the hum briefly lit up from inside. In `sketches/theme-3-page-turn` it sits ~20 dB under the hum.
- **1M0 under it:** partials 5+ ease down. P1–P3 and the fundamental hold to the cut.
- **SD:** the page turn itself, the train pulling away and rails are SD. There's no light change.

---

## Stems and deliverables

| Stem | Content | Notes |
|---|---|---|
| `1M0_P01`–`1M0_P12`, `1M0_FUND` | carriage chord | to SD; conform mechanically to the DMX cue stack (one stem per channel) |
| `UNDERTONE_FULL` | 1M1–1M6 full range | to the mix |
| `UNDERTONE_PHONE` | doubling + metal grain only | lets the mixer set the small-speaker balance independently |
| `UNDERTONE_TRANSDUCER` | sub-only print of 1M1–1M6 | for the seat transducers on set (live only while the car is awake; digital zero in the blackout; level per production sound's bleed sign-off) |
| `1M7_CELLO` | 2 cellos + glass | |
| `1M8_RELEASE` | vibraphone + glass | |
| Pitch map for SD | groan, inhale, door chime, PA | G / A♭ / F♯ around 50 Hz; inhale F♯→G; chime A, D |

**On-set playback:** 1M0 states and the Undertone fire from the DP's console/QLab cue stack (master clock) alongside the groan, so actors play to real sound. Music is re-laid clean in post.

## Ensemble and recording (flagged to the Producer)

- **Players:** 1 contrabass (scordatura), 2 cellos, 1 percussion (bowed vibraphone, bowed cymbal, bowed bass drum, glass). One session, roughly half a day.
- **Carriage session:** record the hum stems re-amped through a small speaker in a real carriage, or capture an IR there, plus field recordings of brakes and couplings for the Undertone.
- **No orchestra, no click track.** All sync is to picture and DMX cues.

## Open items

1. **Timecode:** replace the estimates once the DP's `lighting-plan.md` and the shooting cue stack exist. The cue numbering already matches 1:1.
2. **Breathing values** after the test day (`BREATH_DEPTH`, `BREATH_PERIOD`).
3. **Test-day listening:** play the sketches on the real system and on a phone, especially 1M2 (deniable?) and 1M8 (subliminal?).
4. **Panel count:** 12 is provisional until the set is measured. If it changes, panels P2…P(n−1) take consecutive partials and the far panel stays A♭.

## Sketches (`music/sketches/`)

| File | What |
|---|---|
| `theme-0-carriage-chord.mp3` / `.mid` | 1M0: the panel hum's states, from asleep to tick, lie, brownout sag, blackout zero, lights up, advance and relight |
| `theme-1-undertone.mp3` / `.mid` | THE UNDERTONE: ×1, ×2, ×3, the hungry swell, the inhale shape (1M1–1M6) |
| `theme-2-relight.mp3` / `.mid` | 1M7: P3 → P12 at the script's pace, cellos on 4/6/7/9, vibrato freeze, thinning |
| `theme-3-page-turn.mp3` / `.mid` | 1M8: dead-stable hum, the subliminal triad, hum to the cut, rails, stop |
| `car-motif-sketch-01.mp3` / `.mid` | the whole system in ~97 s (concept demo) |
| `themes.py`, `car_motif.py` | generators (`python3 themes.py`). Python plus numpy, ffmpeg for the MP3s |
| `phone-check.txt` | Undertone survival on a phone-band speaker |

Listen on headphones or a system with a sub: the Undertone sits low. The MIDI files are microtuned with pitch bend (±2 semitones) on one channel per voice.
