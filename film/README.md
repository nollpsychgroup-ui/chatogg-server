# Short Film Production Office

This folder is the shared workspace for a short film made by several Claude Code
sessions, each playing one crew role. Every session reads and writes here on the
branch `claude/film-production-multi-agent-c55jcr`.

## Crew

| Role | Owns | Session |
|------|------|---------|
| Producer (coordinator) | Schedule, milestones, check-ins with the human, `STATUS.md` | session_01W37kuJZHggutJjVDbzw8Cv |
| Screenwriter | `pitches/`, `script/` | see `CREW.md` |
| Director | Creative vision, `notes/`, approves script drafts | see `CREW.md` |

The human (the film's owner) approves at milestones. Nobody skips a milestone gate.

## Milestones

1. **Pitches**: Screenwriter writes 3 loglines with one-paragraph treatments in
   `pitches/PITCHES.md`; Director adds a ranked recommendation. Producer takes it to the human. **GATE: human picks one.**
2. **Script draft**: Screenwriter writes `script/draft-01.md` (target 5–10 pages,
   screenplay format in Markdown). Director gives notes in `notes/director-notes-01.md`;
   Screenwriter revises (`draft-02.md`, ...) until Director approves. **GATE: human approves the script.**
3. **Director's package**: Director writes `notes/directors-treatment.md` (tone, visual
   style, casting notes, scene-by-scene intent) and `notes/shot-list.md`. **GATE: human approves.**

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
