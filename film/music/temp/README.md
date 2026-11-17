# Temp score for the previs animatic

- `temp-score.mp3`: music only (1M0 hum bed + 1M1–1M8), ~9:30, 24 kHz mono. A rough temp, not a final.
- `temp-mix.mp3`: the same music plus temp sound-design placeholders (rails, relay ticks, door chimes, the inhale in the blackout), at the same gain. Use this one to cut the animatic.
- `temp-sync-report.txt`: every cue and event time the render used.
- `render_temp_score.py`: renders both from the cue timeline: `python3 render_temp_score.py [cues.json]` (numpy, ffmpeg; ~40 s).

**Sync source:** the renderer reads `film/camera/cues.json` (DP, shared with 3D/TA; now live). It also takes the panel partials, the breathing depth/period/on/off and cue 5's main/sympathy panels from there. `cues-provisional.json` is the fallback the DP's file was built from, and is now superseded: cue ids match DP cues 0–8 and sub-cues 7.x/8.x, panels are P1 (above Noor) to P12 (far end), and times are seconds from the first frame. If picture timing changes, re-time the cue file and re-run. The score follows automatically.

Rules the render enforces: the blackout is digital zero (only the SD inhale in its last 1.5 s, in the temp mix), the Advance ticks are checked against the ≥ 8 s rule, the hum holds to the cut, the release clears 1 s before Kai's phone dims, and the credits are silent.
