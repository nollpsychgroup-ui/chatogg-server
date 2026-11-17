# Format Decision: CG Animation (decided by the human, 2026-11-17)

THE QUIET CAR is now a **computer-generated animated film**, not live action.

- **Style:** stylized characters with a **painterly** look (visible brushwork, simplified
  painted forms, oil or gouache textures), lit with **physically motivated light**.
  The light is the monster, so the fluorescent panels, true blacks and the sodium platform light
  must behave like real light even though the surfaces are painted.
- **Why it suits the film:** stylized faces avoid the uncanny valley in a film that runs on small
  performance (Walter's speech, Noor's confession). The locked-off camera, long takes and
  single set keep the animation budget contained.
- **Tool:** Blender, driven by Python scripts committed under `film/cg/`. The scripts are the
  source of truth; renders are low-res previews.
- **What the crew delivers:** a complete **previs animatic** with the set, lighting cues,
  cameras, timing, temp voices and score. Final character animation and final renders are
  done afterwards by human animators and/or AI video tools, guided by this package.

## What carries over / what changes

- **Script:** unchanged and still locked (`script/draft-02.md`).
- **The P1–P12 panel map and cues 0–8** become keyframed virtual lights in Blender. They're
  still the shared sync language between camera, CG and music.
- **Live-action tech is dropped:** DMX panels, board op, transducers, IR safety light,
  blackout set, wagon and test day. Lens choices, framing and the shot list remain, as virtual cameras.
- **Casting becomes voice casting:** all 6 voices are recorded first, and animation follows the record.
- **Music:** unchanged. A real-carriage impulse-response recording is still useful for sound.
- **Palette rule still holds:** no reds in the car except Noor's lanyard strap and Kai's end-call button.
