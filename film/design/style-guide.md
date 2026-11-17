# THE QUIET CAR: Painterly Style Guide

**Character Designer** · Milestone 3 · v1 · **APPROVED by the Director** (`../notes/design-notes-01.md`) · build notes **agreed with the 3D/TA**
Companion to `../FORMAT.md`, `../camera/visual-approach.md`, `../notes/directors-treatment.md`.
Sheets: `sheets/` (incl. `seated.svg`), PNG previews in `png/`, expressions: `expressions/`, props: `props/`. Open `index.html` to see everything on one page.

---

## 0. The rule in one line

**The surfaces are painted. The light is real.**

Paint tells you *what a thing is*: its form, its material, its wear. Light tells you *what the car is doing*. We never paint light in. There are no painted highlights, baked shadows, painted rim lights or "mood" gradients in any texture, because the lights are the monster and every change in light has to be the car's (DP rule 1). If a texture had a highlight in it, the audience would see a light event the car didn't make.

Mood touchstones, for the whole crew: Edward Hopper's night interiors (flat fluorescent light, people alone together, big simple planes); Vilhelm Hammershøi's stillness and greys; gouache illustration where you can see the brush but never lose the form. The film should look like a **painting of a real place, lit by a real light**.

---

## 1. Form: how simplified

Three levels of simplification, by how close the camera gets and how much acting the thing does.

| Tier | What | Simplify to | Brush |
|---|---|---|---|
| **A: the set** | Walls, seats, floor, ceiling, windows, poles | Big flat planes, crisp construction. No screws, no rivets, few seams. The panel row stays geometrically exact: it's a meter the audience counts. | Large, broad strokes (stroke ~4–6 cm in world space), low contrast |
| **B: bodies and costume** | Coats, scrubs, hoodie, suit, bags, shoes | 3–5 big folds per garment, chosen for the pose. Clothes are shapes first, cloth second. No stitching, no small wrinkles. | Medium strokes (~1.5–3 cm), following the fold direction |
| **C: faces and hands** | Everything that acts | Simplified planes (forehead, cheek, jaw, nose wedge), but **full control in the acting zones** (section 2). Hands are simplified to four clear finger shapes and a big thumb, but knuckles bend properly: Walter's clamp and Noor's thumb over the red button are both close inserts. | Fine strokes (~3–6 mm), following form |

Proportions are **stylized-naturalistic**: about 6½ heads tall, heads slightly large and eyes slightly large for readability in a wide 2.39 frame, no cartoon squash. These are adults in a straight drama. Nothing is cute.

Each character has one **shape idea** that holds in silhouette, standing (`sheets/lineup.svg`) and, more importantly, **seated, as the down-the-carriage master sees them** (`sheets/seated.svg`). The Director's brief for the seated reads: Noor presenting and upright, Walter folded and still, Bea upright with her eyes shut, Kai slouched and loose.

- **Noor: the upright rectangle.** Squared blazer shoulders, vertical spine, everything aligned and pressed. She is holding a shape. Her arc is the rectangle softening: by the platform her shoulders have dropped and the blazer hangs open.
- **Kai: the slouched triangle.** Wide base (knees apart, sneakers), narrow top (hood, head down to the phone). All diagonals and ease.
- **Bea: the rounded bell.** Low centre of gravity, cardigan rounding the shoulders, both hands folded on the bag. Grounded, unmovable, safe.
- **Walter: the tall, leaning wedge, folded.** Standing: long coat, narrow at the shoulders, wider at the hem, a slight forward stoop. Seated: folded forward over the paper, coat over the knees, utterly still. Big hands (the clamp has to be believable).

---

## 2. Faces: the reason we chose this style

The film runs on small acting in a locked frame. A stylized face is only an advantage if it can still carry a 10% change. So:

### 2.1 Simplify the planes, never the acting zones

Simplify freely: skin texture, pores, wrinkles (keep only the 2–3 lines that describe age and character), ears, hairline detail, teeth (one shape, never individual teeth).

**Keep fully controllable and well-drawn** (these are the rig controls in `expressions/face-rig.md`):

1. **Upper lid line and lid height.** The single most important line in the film. It carries "eyes closed but awake" (Bea), "fine" vs. "not fine" (Noor) and every look Walter gives the badge.
2. **Lower lid and cheek raise.** Separates a real smile from a performed one. Noor's "fine" smile is mouth-only; her lower lid never lifts until the end.
3. **Brows: inner, mid, outer, per side.** Asymmetry allowed and encouraged.
4. **Mouth corners and lip press.** Noor holding her voice steady while crying is done with the lips pressed and the chin (5) working.
5. **Chin / mentalis.** The chin dimple and lift when someone is holding back tears.
6. **Nasolabial fold.** Drawn as a soft painted shape, never a line; it deepens with a real smile and with crying.
7. **Eye direction.** Eyes must read at 32 mm across the car. Irises are a clear mid-dark value against a pale sclera; see 2.3.

### 2.2 Range: small

Acting lives in the **5–25% range** of each control. The expression sheets show the *peaks*, and even those are capped at about 60% of what a cartoon face would do. If an expression reads from the back of a cinema without the face, it's too big. Hold, then shift.

### 2.3 Faces must survive top light

Every light in the car is overhead. A real fluorescent panel straight above will put eye sockets in shadow, and we are not allowed a fill light (no unmotivated light). So the faces are **designed for top light**:

- Shallow brow ridges and shallow eye sockets, so the eyes stay lit under the panels.
- Slightly paler sclera and slightly larger eyes than naturalistic.
- Catchlights are **never painted**. The eyes have a real glossy cornea, so the panel row reflects in them as a small row of soft rectangles. **When panels go out, the catchlights go out.** In the creeping dark you should be able to read the car's state in Noor's eyes. During the phone-lit stretch the catchlight becomes the phone's small blue-white square below the pupil.
- The **only** glossy surfaces on a character are the corneas, tear films (Noor in the confession), lips at a very low sheen, and plastic props (badge, phones). Skin is matte gouache.

### 2.4 Bea in the dark states (Director F2)

Bea's skin sits close in value to her navy scrubs. To keep her eyes-closed-but-awake acting alive under the brownout and at the edge of the creeping dark, we raise contrast **in the acting zones, not the skin**: brighter sclera `#F3F0E8`, a near-black lid line `#0E0907` about 40% heavier (v2: band ~0.42 of the lid radius), and a lighter lid albedo `#7C5642` (v2, up from `#6E4A38` after the TA's 7.10-edge test; a material value, not painted light). The oatmeal cardigan frames her face. The check strip is on `expressions/bea-expressions.svg`, and the TA's brownout style frame includes Bea as the real test.

### 2.5 Tears

A tear is a thin wet line that catches the panel above. It's built from the cornea/tear-film gloss, not painted. Noor's confession: wet lower lid, one track on the camera-side cheek, no streaming.

---

## 3. Brushwork

- **Strokes are locked to the surface** (object or UV space). **While the car is asleep they never boil, crawl or re-randomise from frame to frame.** A shimmering brush texture would read as a light event and break DP rule 1.
- **Awake-only boil is a test, not a default** (Director's treatment, art direction 4): look-dev may try a very faint boil that exists *only* while the car is awake, locked to the ±3% breathing. If it reads as the room breathing, it's in; if it reads as a style effect, it's out. It must be exactly zero while the car sleeps.
- **Timing:** people may be animated on twos for the painterly feel; **lights, the breathing and the camera stay on ones.** The car is smoother and more real than the people in it.
- **Stroke direction follows form**: across the cheek plane, down the length of a sleeve, along the moquette weave on the seats, lengthwise down the walls.
- **Stroke scale by tier** (section 1). Faces are the finest. That keeps the eye on the acting.
- **Where light meets shadow, the strokes show.** The terminator (the line where a form turns from light to shadow) breaks up into brush shapes a few strokes wide. This is the main "painterly" signature, and it's lighting-driven: when the panel above Noor dips, her terminator moves and the strokes go with it. Everything stays physically lit.
- **Paint quality:** matte gouache with some oil-like body in the darks. No impasto relief on characters (it would catch light like a real ridge). Allow a very subtle canvas/paper tooth on the set only.

---

## 4. Edges

- **Lit edges are firm; shadow edges are lost.** A form edge in light is crisp. As it turns into shadow it softens and finally merges with whatever is behind it. This is the Hopper/Hammershøi edge, and it's what makes near-darkness feel *painted* rather than *underexposed*.
- **Facial features are always firm** (lid line, brows, mouth line, iris edge) unless the face is in shadow, where they soften but **don't disappear before the shadow takes the cheek**. Features are the last thing to go.
- **No outlines.** No ink lines, no Freestyle, no toon contours.
- **No rim halos.** Silhouettes against the black windows are simply value against value. Any rim light must come from a real source (a panel behind, a phone).
- **The creeping dark (cue 7) is the exception the DP asked for:** each dark section has a **hard edge** travelling up the aisle. The paint doesn't soften the light boundary across the floor and seats. Light defines that edge, not the brush.

---

## 5. Paint in near-darkness, under one panel, and in true black

This film lives at the bottom of the exposure range. Rules for paint as light falls away:

| Light state | What the paint does |
|---|---|
| **Asleep, full row (~4300 K, slight green)** | Full palette, full stroke texture, flat and even. Faces read clearly. Unglamorous. |
| **Breathing (±2–3%)** | Nothing changes in the paint. Only the light moves. |
| **One panel dipping (cues 1, 2, 5, 6)** | The pool under the panel is the only full-detail area. Outside it, strokes **merge into larger, quieter shapes** and texture contrast drops, the way a painter would simplify a background in shadow. Faces in the dipped pool keep firm features (rule 4). |
| **Brownout (cue 3, ~2200 K, ~2.5 stops down)** | The whole frame goes close to monochrome warm and colour separation almost disappears. **In the brownout the car owns every colour: the red strap goes dark with everything else** (Director, `notes/cg-notes-03.md`). Under sodium light the red should physically die, and we never grade it back in. Shadows go to warm umber, never to noise. |
| **Single lit section / creeping dark (cue 7)** | Hard light edge on the floor (section 4). Inside the dark: real black, no texture showing. Inside the light: full detail. |
| **Phone light from below** | Small, cold, hard-ish source. Lights the underside of the chin, nose and brows. The strokes on the face follow the new terminator. Noor's MARK glow must read as cold blue-white against the warm skin. |
| **Blackout (cue 4)** | **Mathematically black: 0,0,0.** No paper texture, canvas tooth, grain, vignette or Kuwahara edge glow is allowed to lift it. Any texture overlay is **multiply-only** (black × anything = black). Nothing glows in the dark: no emissive paint, no glow in the eyes. |
| **Platform (cold white lamp, haze)** | One cold source, high and to one side. Noor is painted as big, simple lit and shadow shapes; she's far away through the doors, so tier B stroke scale applies to her face there. |

**No noise, ever.** The paint simplifies as it darkens; it doesn't get grainy. Darkness should look like a painter chose it.

---

## 6. Colour

### 6.1 The red rule

There is **one red** in the film, used on exactly two things:

- **Noor's lanyard strap**
- **The end-call button on Kai's phone screen**

Both use **THE RED `#C8102E`** (sRGB).

**Where the red must win** (measured as CIELAB chroma, emitters excluded): under **BASE** light and in the **creeping-dark** states, the strap is the highest-chroma object in frame. That covers the boarding tick (cue 0, shot 2), and the throw onto the floor, red on grey (shots 45–46). **In the brownout (cue 3) it doesn't have to win**: the car owns every colour there, and the strap goes dark with everything else. No grade, colour key or mask is ever used to rescue it, because every change in the frame has to be the car's light. Nothing else in the car may be red, pink, magenta, maroon, coral or rust: not lips, not cheeks, not a bag strap, not a newspaper masthead, not a shoelace, not a phone case, not a sticker, not an exit sign. Skin "warmth" is ochre and umber, not red. Lips are a desaturated mauve-brown. 

Noor's own phone UI has **no red**: her in-call screen uses a dark grey end-call button (see `props/props.md`).

### 6.2 Saturation budget

Everyone sinks into the car except the badge. Costume chroma is kept **below 25% saturation** (HSV), apart from the strap. The set is greyer than the people, and the people are greyer than you'd expect.

### 6.3 Master palette (sRGB hex; linear values for Blender are in `palette.json`)

**Set** (agreed with DP; the TA owns final values)

| Swatch | Hex | Use |
|---|---|---|
| Moquette teal | `#3F6866` | Seats. Muted, slightly worn at the edges of cushions |
| Moquette teal, shadow pattern | `#2F504F` | Small woven pattern on the seats |
| Laminate grey | `#A8ABA5` | Walls, end wall |
| Ceiling white | `#D9DBD3` | Ceiling between panels |
| Floor grey | `#4B4D4A` | Vinyl floor |
| Pole and trim | `#8E9394` | Brushed steel, low gloss |
| Sign vinyl | `#2C2E30` text on `#E4E4DC` | QUIET CAR sign |
| LED display | Amber is **not** allowed (orange = awake). Display is **cold white-green LED `#CFE8D8`** on black | Destination display |

**Characters** (full callouts in each sheet)

| Character | Key colours |
|---|---|
| Noor | Charcoal suit `#3A3B40`, pale grey-blue blouse `#C8CED4`, **THE RED strap `#C8102E`**, white badge `#EEEEE8`, black laptop bag `#25221F`, skin `#A9714F`, hair `#1E1A19` |
| Kai | Grey hoodie `#76787B`, black jeans `#2A2C30`, off-white sneakers `#D8D6CF`, white earbuds, skin `#D6B08C`, hair `#1A1817` |
| Bea | Navy scrubs `#22314F`, oatmeal cardigan `#B7AC95`, brown tote `#5A4A3B`, skin `#5E3C2C`, hair charcoal with grey `#4A4643` / `#9A9590` |
| Walter | Camel overcoat `#A8875A`, grey scarf `#77777A`, pale blue shirt `#B9C4CC`, brown-grey trousers `#4E4A45`, skin `#D9B79E` (desaturated, no flush), hair `#DCD8D0` |

### 6.4 Skin under each light

Skin is painted with **ochre/umber in the halftones and cool grey-green in the shadow** (fluorescent spill off the teal and grey surfaces). Never red in the shadow core. Under cue 3 all four skins collapse into a narrow warm band, so **value differences between the four characters must hold in black and white** (checked on the lineup sheet in greyscale).

---

## 7. Hair, cloth, props

- **Hair** is painted as 3–6 big locks/shapes with a few stroke breaks, never strands. A single loose lock on Noor (it comes loose during the handle-yanking) is the only hair that moves on its own.
- **Cloth** is matte. Folds are shapes (section 1). Noor's blazer is the only tailored garment: it should look pressed, almost too pressed.
- **Props that act** are built to tier C (full detail) because they get inserts: the lanyard and badge, Walter's newspaper and pen, both phones. See `props/props.md` and `props/props.svg`.

---

## 8. Build notes for the 3D/TA (to agree; the TA owns the implementation)

My proposal for how Blender can deliver this. **The TA has final say on method; these are the visual targets.** *Agreed with the TA:* posterising applies to albedo only, never to light; terminator breakup is a surface-locked stroke normal perturbation (no relief on characters); `palette.json` is read directly by look-dev; boil is off, and an awake-only test is optional. The section 8 checks come back with the style frames.

1. **Lighting:** physically based. Panels, the LED display, phone screens and the platform lamp are the only emitters. No fill lights, no light linking that cheats faces, no painted light in textures.
2. **Surface shading:** Principled BSDF, high roughness (0.7–0.9) on everything matte, specular low. Albedo from painted textures (hand-painted for finals; for previs a **procedural stroke texture** in object/UV space is fine). Gloss only on corneas, tear film, badge plastic, phone glass and steel trim.
3. **Painterly terminator:** break up the light/shadow transition with a **stroke-mask texture fixed to the surface** (e.g. a stretched Voronoi/noise in UV space, driving a small normal perturbation or a mix at the terminator). It must respond to the real light, and it must not change over time.
4. **Compositor:** an **anisotropic Kuwahara** pass for the painted look (Blender's compositor has a Kuwahara node), with a **smaller kernel on faces and hands** (TA: Object Index + ID Mask for previs, Cryptomatte at finals) so the acting zones stay crisp. Any canvas/paper texture goes on as **multiply only**, so the blackout stays at 0. No bloom/glare on the panels beyond a very small, stable amount; no vignette.
5. **No outlines** (Freestyle off). No noise in shadows (denoise, or EEVEE).
6. **Faces:** shape keys or bones for the controls in `expressions/face-rig.md`, with the values on the expression sheets as targets.
7. **Previs blocking figures** (Milestone 4): heights and seated heights are on the lineup sheet so the proxies are the right size for the DP's lenses and eye-lines.
8. **Checks I'd like on the first look-dev render:** (a) the blackout frame is all zeros; (b) the strap is the highest CIELAB-chroma object under BASE (shot 2) and on the floor in the creeping dark (shot 46), not under cue 3; (c) the catchlight row shows in the eyes at 40 mm and disappears panel by panel in cue 7; (d) nothing in the paint moves between two frames of an asleep shot.

---

## 9. Do / Don't

| Do | Don't |
|---|---|
| Paint form and material; let real light do the rest | Paint highlights, shadows or rim light into textures |
| Keep strokes locked to the surface | Animate or boil brush texture |
| Simplify everything except the acting zones | Simplify the lids, brows, mouth corners or chin |
| Lose edges in shadow, keep features firm | Add outlines or halos |
| Let the blackout be 0,0,0 | Lift blacks with paper texture or grain |
| Keep costumes greyed down | Use any red but THE RED, on anything but the strap and Kai's end-call button |
| Act in the 5–25% range | Push expressions to cartoon range |
