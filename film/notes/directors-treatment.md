# THE QUIET CAR: Director's Treatment

**Director** · based on the locked script, `script/draft-02.md` · **revised for the CG-animation format** (`FORMAT.md`) · companion to `camera/visual-approach.md`, `music/score-concept.md`, `design/` and `cg/`

---

## The film in one sentence

A woman who has been performing "fine" for weeks gets on a train carriage that can't be lied to, and the only way off alive is to stop performing.

## What it's about

It isn't a monster movie. It's a film about **the small, daily lies that keep us company**: "just leaving the office," "at the library, Mum," "I'm fine." The car is horrifying because its rule is *fair*: it never punishes the truth, however ugly. Noor isn't saved by cleverness or escape. She's saved by giving up the thing she was protecting. The ending is not a victory, just exposure, and the film's last question (*what will Mark say?*) is one we leave with her on the platform.

---

## Tone

- **Quiet, adult, real-time dread.** It's closer to a stage two-hander than to a creature feature. The scares are few, earned and physical: light, silence, a breath in the dark.
- **Played absolutely straight.** Nobody on screen knows they are in a horror film. Walter and Bea are commuters who know a rule, not mystics. No one explains the car, and no one ever will.
- **Fair-play rules.** Every light change means something. The audience should be able to "play along," predicting each cue from what was just said. That participation is the engine of the dread.
- **Restraint as the default.** When in doubt, hold the frame, kill the sound and wait.
- **Animated, not cartoon.** The animation format must never pull the film toward whimsy. This is an adult film that happens to be painted.

---

## Art direction: painted world, real light

The core principle in one line: **the world is painted; the light is real.**

The car is the only thing in the film that is *physically true*, so it's the one element rendered with complete physical honesty. Everything it shines on is a painting.

1. **Surfaces are painted.** Seats, walls, clothes and faces use simplified painted forms and visible brushwork in an oil/gouache texture. Shapes are simplified: fewer folds, flattened planes, a designed silhouette for each character.
2. **The light is never painted in.** No light or shadow is baked into any texture. All shading comes from the virtual lights (the P1–P12 panels, phones, windows, the platform lamp), physically placed and keyframed. When a panel dies, its light really leaves every surface it touched. This is what lets the brushwork and the horror coexist.
3. **True black is still true black.** In the blackout there's no paper texture, canvas grain, brush lift or vignette: **0 in the render and in the grade.** If the painterly treatment lifts the blacks anywhere, the blackout dies. The same goes for the hard-edged dark creeping up the aisle in scene 6.
4. **Asleep = still paint.** If look-dev uses any animated brushwork ("boil"), it must be **completely still while the car is asleep**, or it breaks rule 1 (no change without a lie). I'd like look-dev to *test* the reverse as an option: a very faint boil that exists only while the car is awake, locked to the ±3% breathing. If it reads as the room breathing, it's in. If it reads as a style effect, it's out.
5. **Light moves on ones; people may move on twos.** If the character animation is stepped (on twos) for the painterly feel, **every light cue, the breathing and the camera stay on ones.** The car is smoother and more real than the people in it, which is a small, unconscious hint at what it is.
6. **The palette rules carry over unchanged:** cool fluorescent white (~4300 K, slightly green) for asleep, sodium orange only when the car is awake, a cold white platform, and no reds except Noor's lanyard strap and Kai's end-call button.
7. **Faces are simplified, with eyes kept specific.** The stylisation should simplify the head, not the eyes. Walter's eyes, Bea's open-and-shut eyes and Noor's look at Kai's phone carry whole beats. The eyes need enough detail and catchlights from the *actual* panels to read in a wide 2.39 frame.

## The visual and sonic contract (summary)

The full detail is in the DP, Composer, Design and CG documents. The rules everyone works to:

1. **The panels are the monster.** The lights *are* the car's face and the hum *is* its voice. One panel equals one keyframed Blender light equals one partial of the 50 Hz hum. Cues 0–8 and P1–P12 are the shared language.
2. **Asleep = dead stable.** There is no mood flicker, no camera movement, no music and no brush boil.
3. **Awake = breathing.** There's a ±2–3% light swell, a matched hum swell, and the Undertone beneath it. The camera may move only now.
4. **The truth does nothing.** No cue, no music, no camera reaction.
5. **The blackout is absolute:** 0 in render and grade, digital zero in sound, held.
6. **Orange means awake.** It never appears outside a waking. The platform is cold white.
7. **One red object:** Noor's lanyard strap, rhymed with Kai's red end-call button.

---

## Voice casting

The voices are recorded **first**, and the animation follows the record. The voice performance *is* the performance.

**Who we want:** stage-trained actors who can play subtext quietly, close to the mic. This is a quiet car, so most of the film is murmured. Cast for **voices that carry thought at low volume**, not for big character voices.

**NOOR (40s).** She's in every minute. We need a voice whose "fine" is *excellent*: warm, competent, practised and likeable. The key skill is the confession: **she has to cry while her voice stays level.** Audition with the confession, not the opening.

**WALTER (70s).** Three lines, plus breath. The voice needs gravity and kindness with a lived-in grain. "He's asking." has to carry the whole film's compassion in two words. He's not "spooky old man," just someone who has done his grieving.

**BEA (50s).** A nurse's voice: the low, steady register you'd use with a patient. She's tired, direct, and has authority without volume. "Say it." has to be urgent while still being a whisper.

**KAI (19).** Two minutes of screen time, so he must be **instantly likeable**: cocky, tired, clearly somebody's son. His "I'm at the library, Mum" should be so ordinary that its punishment feels unjust.

**MARK and MUM (phone only).** These will be degraded in the mix. Cast for **warmth of tone**: we should hear love in the murmur even when we can't hear a word.

### Recording plan

- **Ensemble sessions, not solo lines.** Record Noor, Bea and Walter together in one room, at the volume people speak at in a quiet car, so the overlaps, silences and breaths are real. Record Kai's scene with Noor and Bea present.
- **Mark live opposite the confession.** Record Mark on a real phone line to Noor's booth, so her confession is said to someone actually listening. Mark's silence is real silence, and her reaction to it is real.
- **Record breaths and non-verbals as performance:** Noor's held breath after "S—", the "Nobody breathes" beat, Bea's sigh, and Walter's breathing behind his paper.
- **Play the cues in the room.** Feed the temp groan and blackout from the Composer's sketches into the actors' headphones at the cue points, so they react to the car, not to a description of it.
- **Shoot reference video** of every session with several cameras, faces and hands. Animators will use it for timing and micro-expressions, not for literal rotoscoping.
- **Keep the record in real time.** Read the film top to bottom, with the display clock's real-time pacing, at least once per session. Animation timing then follows the voice track, not the reverse.

---

## Performance notes for animators

The film runs on **small performance in long, locked shots.** That's the hardest thing in animation to do well, and the most important thing to get right here.

**General**
- **Stillness is acting.** Long holds are the default, but a "held" character is never frozen: keep a breath cycle, eye drift and weight shift going. We should always feel the person is alive and thinking. The *car* is the only thing allowed to be perfectly still, when it's asleep.
- **Under-animate.** There are no broad takes, no reaction "hits" timed to light cues, and no squash-and-stretch exaggeration. If you're unsure whether a gesture is too big, it is.
- **Characters do not react to cues they don't notice.** In scene 2, Noor is oblivious: she must not flinch, glance or pause at the flickers. Walter and Bea react only with their eyes. The gap between what we see and what Noor sees is the scene.
- **Breath is a performance channel.** Breathing is visible in every shot: it's the audience's measure of fear. In "Nobody breathes," everyone actually stops, and the first breath afterwards is a release.
- **Eyes lead, heads follow, bodies follow last.** Most beats in this film are eye moves.

**Per character**
- **NOOR: performing "fine."** Good posture, smoothing her skirt, putting the badge face-out: a body that's *presenting*. Over the film the performance drains out of her posture until, in the confession, she's slumped, open and still. Her tears should come with an unmanaged face over a level voice (follow the record).
- **WALTER: economy.** He barely moves. The paper lowers, the eyes lift. **The wrist clamp is the exception:** fast, with no anticipation and much stronger than his body suggests. It should be the single quickest motion in the film, as startling to the audience as to Noor. Then he goes slow again and releases gently.
- **BEA: a nurse's attention.** Eyes closed but listening: tiny reactions under the lids, a hand tightening on her bag. When she opens her eyes, she *assesses*. Her reach toward Kai ("don't") is real effort, and it falls short.
- **KAI: loose and alive.** Thumb scrolling, one earbud, slouching and fidgeting: the most kinetic body in the car, so the empty seat afterwards is the most still. His nervous laugh before the blackout is the first time he's scared. Give it to us.

**Kai's vanishing:** in the blackout the frame is literally black, so there's no animation. Lights up, and the seat is empty, in the same locked camera. No transition and no lingering trace except the phone. Don't add a dent in the cushion or a swinging strap. Absence only.

---

## Scene-by-scene intent

The clock on the destination display is the film's spine. Times are on-screen minutes to Holloway.

### 1. Boarding (11:00, about 1 min)
**Intent: teach the room, plant the rule, and make Noor someone we like.**
The opening master runs the length of the car, the full panel row lit: we're counting the meter before we know it's one. Walter and Bea are still, Kai is glowing. Noor arrives as a pleasant, harried professional. The lanyard straighten and the subliminal tick (cue 0) play with no reaction except Walter's eyes. Most viewers won't see it. It's there for the second viewing, and for fairness.
*Performance:* Noor is relieved to sit down. Nothing in her is "hiding" yet that we can read.

### 2. The call: Noor's lies (11:00 → ~10:00)
**Intent: the audience learns the rule before Noor does.**
Lie 1 makes one panel flicker and a faint groan. Lie 2 brings two panels and a louder groan. Walter's paper lowers and Bea's eyes open. The tension comes from the gap between what *we* notice and what *Noor* notices: she is busy performing for Mark and doesn't see the car performing back. "Love you" is true, and nothing happens. Let it land: it's the first silent proof of the rule.
*Performance:* the lies are casual, practised and almost affectionate. She lies the way people do to protect someone.
*Camera:* wide, observational, 25–32 mm. We watch her the way Walter does.

### 3. Kai (~10:00 → ~9:00)
**Intent: the first scare, and the film's promise that the rule is lethal.**
Kai's loud "I'm at the library, Mum" sets off the brownout. Every panel goes orange, the groan comes from the walls, and the hum audibly goes out of tune for the first time. His nervous doubling-down leads to the **blackout**. Hold the true black for longer than is comfortable. The inhale sounds in the dark. Lights up, and the seat is empty in the same locked wide, with no cut. The phone says "Kai? ... Kai?" The rails resume, indifferent.
*Directing note:* the horror is the indifference afterwards. The car doesn't celebrate. The train just carries on.

### 4. The note and the test (~9:00 → 8:00)
**Intent: put the rule into words once, then make the danger total.**
This is the film's only handheld passage, Noor at the emergency handle. In CG, use a virtual handheld with **real recorded camera-operator motion**, not procedural noise, and the frame steadies the moment Walter holds up the paper. "DON'T LIE IN HERE" is followed by Bea's "IT'S AWAKE NOW. YOU WOKE IT." in two distinct, legible hands: two different prop handwritings designed by the Character Designer. Noor looks at Kai's seat, and guilt arrives. Her truth test ("My name is Noor") gets nothing. Then "My name is S—", Walter's wrist clamp, and the hard dip. Nobody breathes.

### 5. The truth exchange (8:00 → 5:00)
**Intent: the film breathes. People finally speak honestly, and it's a relief we didn't expect.**
Here are the long rails and the stillness. Noor crosses to Kai's phone and can't end the call; that's a 40 mm insert of her thumb over the red button. Bea's "You okay?" brings the reflex "I'm f—", the stutter, and then "I'm not fine." Bea admits two sleepless days, and Walter tells his wife's story. This is the only warm passage in the film, and it's warm *because* nothing happens in the lights. The lens moves in to 40–50 mm as people move closer to each other.
*Directing note:* resist the urge to cut tension in here. The audience should almost relax, which makes the first tick of scene 6 devastating.
*Animation note:* Walter's wife speech is the film's longest held close shot of a character who isn't Noor. It lives on his eyes and his hands on the folded paper.

### 6. The creeping dark (5:00 → 2:00)
**Intent: the rule widens. A lie you are wearing counts too.**
The far panel goes out with no word spoken, then the next, and the next. It's a hard-edged dark walking up the aisle *toward camera* on the 32 mm master, and the hum loses its high partials as it comes. The ticks are steady and patient, never accelerating, and each one follows a line, as if answering it. Bea, reading Noor like a patient: "It isn't only what you say." Walter's eyes go to the badge, as they did at boarding, and the plant pays off. Noor throws the lanyard on the floor, and it isn't enough. "Say it." Two panels left. The MARK call arrives. Noor looks at Kai's glowing phone, and Walter says "He's asking."
*Camera:* the only slow creep push, at the pace of the dark.

### 7. The confession (2:00 → arrival)
**Intent: the climax is a phone call. Truth, sentence by sentence, rebuilds the room.**
This is the 75 mm, used for the first and only time: the closest we ever get to Noor. Her panel steadies and burns brighter, then panels relight outward from her, one per true sentence, as the hum's chord is rebuilt and the cello harmonics enter beneath it, warm but missing their third. The library line catches mid-sentence as her eyes go to Kai's phone. "I'm sorry." Silence on the line, and the last panel relights at the far end. The room is exactly as it was at the start, and the car is asleep. The push lands and stops at the last relight.
*Performance:* Noor cries but her voice stays level, because she has finally stopped managing anything. Mark's silence must be played by her face: she doesn't know what's coming either. This is the shot the animation budget should be spent on.

### 8. Holloway (arrival → end, about 1 min)
**Intent: release without resolution.**
She steps off onto a cold white platform under a single plain lamp, phone to her ear, listening. **We stay inside.** The doors close. "Thank you for riding quietly" plays unscored. Walter turns the page, and the nearly subliminal release triad blooms, its missing third finally arriving, for him. Kai's phone screen dims, and the triad is gone before it goes dark. The lights hum. Cut to black. The rails run, then stop. The title and credits play in silence.
*Directing note:* the car must look **completely innocent** in the last shot. There's no parting cue. That innocence is the final scare.

---

## Runtime and pacing

The target is **8:30–9:30**. The display clock gives a real-time feel, but we're allowed to cheat compression in scene 5 and expansion in the blackout. Rule for the edit and the animatic: **cut on behaviour, never on cues.** Light and sound changes always play inside a held shot. The voice record sets the timing, and the animatic is cut to it.

## What would make this film fail (and how we guard against it)

| Risk | Guard |
|---|---|
| The rule reads as random | Strict cue vocabulary, the countable panel meter, the truth test in scene 4, and no unmotivated light or brush changes |
| Painterly style fights the horror | Painted surfaces, physically real light; no baked lighting; true black in render and grade; still paint while asleep |
| Animation drifts toward cartoon | Stage-calibre voice cast recorded first; under-animate; reference video; no reaction "hits" on cues |
| Long locked takes feel dead in CG | Breath, eye drift and weight shift always alive in characters; only the sleeping car is perfectly still |
| It's too similar to *A Quiet Place* | The rule is about honesty, not noise. Never stage a "don't make a sound" beat |
| A sentimental ending | Mark's answer withheld, no score under the PA, a nearly subliminal triad, and an innocent car |
| Kai's death feels cheap | Cast his voice for warmth, keep his phone alive as a presence, and give Noor guilt for him |
