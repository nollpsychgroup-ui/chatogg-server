# Scratch voice track (previs)

**Owner:** Screenwriter. **Status:** TEMP. TTS carries timing only and will be replaced by the voice record.

| File | What |
|---|---|
| `scratch-voice.flac` | 48 kHz mono, 9:30 (570 s), the same length and zero point as `camera/cues.json`. Drop it at frame 0. |
| `scratch-voice-lines.json` | Every placed clip: line ID (from `script/voice-sides.md`), voice, level, start and end in seconds. For the Composer's ducking windows and the animators' lip-sync blocking. |
| `../quiet-car.srt` | Subtitles: intelligible dialogue only. Phone beds (Mark, Mum's first bed) are deliberately **not** subtitled because they must never be intelligible. Phone and PA lines are in italics. |
| `build_scratch_voice.py` | Regenerates all three. **Re-run it whenever the DP re-times `cues.json`.** Every line is anchored to a cue or event time, not hard-coded to the cut. |

**Voices:** CMU Flite (system libflite, offline), pitch and tempo shifted per character with ffmpeg:

- **Noor:** slt.
- **Bea:** slt, lower and slower.
- **Mum:** slt, higher.
- **Kai:** kal16, higher and quicker.
- **Walter:** awb, lower and slower.
- **Mark:** rms.
- **PA:** kal, the machine diphone voice, through a speaker band-pass with a slap echo.

Every clip is loudness-normalised first, then given its **level** from the voice sides:

| Level | Treatment |
|---|---|
| FULL | 0 dB |
| LOW | −6 dB |
| WHISPER | −13 dB, high-passed |
| FAINT | −19 dB |
| PHONE | 350–3200 Hz band-pass, compressed, −14 dB |
| MURMUR | 520 Hz low-pass, −21 dB, unintelligible by design |

**Built-in checks** (the build fails if any is broken):

- Nothing sounds inside the blackout (cue 4 → 4.up is digital zero).
- Nothing runs past the cut.
- The three lies that set off cues 1–3 end within 1 s before their cue.
- No Advance tick or relight lands inside a line.
- There is no clipping.

**Cut-offs** are as the voice sides specify:

- **"My name is S—":** a synthetic 150 ms /s/, ending exactly on cue 5.
- **"I'm f—":** a 110 ms /f/, ending on cue 6.
- **Kai's line:** runs on past the cut and is hard-cut to zero on the cue 4 frame.
- **"I couldn't —":** fades out and ends 0.3 s before cue 8.3, so the relight run answers it.

TTS can't do breaths, efforts, crying or the mouthed "Sorry". Those are left as silence, and the animators should work from the voice sides for them.
