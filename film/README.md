# Short Film Production Office

> **Format:** stylized, painterly CG animation. Read `FORMAT.md` first.

This folder is the shared workspace for a short film made by several Claude Code
sessions, each playing one crew role. Every session reads and writes here on the
branch `claude/film-production-multi-agent-c55jcr`.

## Crew

| Role | Owns | Session |
|------|------|---------|
| Producer (coordinator) | Schedule, milestones, check-ins with the human, `STATUS.md` | session_01W37kuJZHggutJjVDbzw8Cv |
| Screenwriter | `pitches/`, `script/` | see `CREW.md` |
| Director | Creative vision, `notes/`, approves script drafts, camera and music work | see `CREW.md` |
| Cinematographer (DP) | `camera/`: visual approach, lighting plan, shot list, storyboards | see `CREW.md` |
| Composer | `music/`: score concept, cue sheet, themes, MIDI/audio sketches | see `CREW.md` |
| 3D / Technical Artist | `cg/`: Blender set, painterly shading, scripted light rig, cameras, previs renders | see `CREW.md` |
| Character Designer | `design/`: painterly style guide, character sheets, expressions, costume and colour | see `CREW.md` |

The human (the film's owner) approves at milestones. Nobody skips a milestone gate.

## Milestones

1. **Pitches**: Screenwriter writes 3 loglines with one-paragraph treatments in
   `pitches/PITCHES.md`; Director adds a ranked recommendation. Producer takes it to the human. **GATE: human picks one.**
2. **Script draft**: Screenwriter writes `script/draft-01.md` (target 5–10 pages,
   screenplay format in Markdown). Director gives notes in `notes/director-notes-01.md`;
   Screenwriter revises (`draft-02.md`, ...) until Director approves. **GATE: human approves the script.**
   *Prep in parallel:* while the script is in draft, the DP writes `camera/visual-approach.md`
   and the Composer writes `music/score-concept.md`, both reviewed by the Director. Base them on
   the latest draft and expect changes. Don't build detailed shot lists or cues until the script is locked.
3. **Director's package** (after the script is locked):
   - Director: `notes/directors-treatment.md` (tone, casting, scene-by-scene intent).
   - DP: `camera/shot-list.md`, `camera/lighting-plan.md`, `camera/storyboards/` (SVG or HTML frames).
   - Composer: `music/cue-sheet.md` (each cue's in/out point, purpose, instrumentation, and how it
     interacts with sound design) and sketches of the main themes in `music/sketches/`.
   - DP and Composer coordinate directly where picture and sound meet (lighting cues and stingers).
   - Character Designer: `design/style-guide.md` and sheets for Noor, Kai, Bea and Walter.
   - Technical Artist: `cg/` with the carriage set, painterly look-dev, P1–P12 light rig
     and style frames for the key beats.
   - Director approves all of it. **GATE: human approves.**
4. **Previs animatic:** the TA assembles a full-length Blender previs (blocking figures, every
   lighting cue, DP cameras) cut to temp voices and score. **GATE: human approves.**

## Working rules

- **Sync before and after working:** `git pull --rebase origin claude/film-production-multi-agent-c55jcr`
  before editing; commit and push when done. Only edit files you own (plus append-only
  entries in `STATUS.md`). If a push is rejected, pull --rebase and push again.
- **Talk with `send_message`** (claude-code-remote tool) to the session IDs in `CREW.md`.
  Keep messages short: say what changed and which file to read. The file is the source of truth.
- **Hand-offs:** when you finish a step, message the next role *and* the Producer.
- **Waiting:** when you are waiting on someone, end your turn. A message from them will wake you.
  Don't poll or sleep.
- **Gates:** only the Producer talks to the human. At a gate, message the Producer and wait.
