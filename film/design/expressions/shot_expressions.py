"""Per-shot expression track for the M4 previs (Character Designer).

Writes shot_expressions.json: a library of named expressions (face-rig values, rig convention:
_L = the character's LEFT) plus, per character, a list of [time_s, name, shot] keys across the film.
The TA applies it with heads.apply_track(root, keys, library, fps).

Times are absolute seconds on the film clock (camera/cues.json). Off-screen characters stay keyed
so continuity holds when a cut lands on them. Acting range is small (face-rig.md): these are targets
the animator eases into, not poses to hit.

    python3 film/design/expressions/shot_expressions.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

LIB = {
    # ---------------- NOOR: the performance, the crack, the end of the performance
    "noor/pleasant":        dict(smile=0.15, lid_up=0.82, brow_in=0.05),            # boarding: harried, likeable
    "noor/relieved":        dict(smile=0.12, lid_up=0.7, brow_in=0.1, naso=0.25),     # sits down
    "noor/fine_performed":  dict(smile=0.45, lid_low=0.0, lid_up=0.85, brow_in=0.1, naso=0.25),  # sheet
    "noor/fine_listening":  dict(smile=0.25, lid_up=0.8, brow_in=0.12, gaze_y=0.2),
    "noor/love_you":        dict(smile=0.3, lid_low=0.15, lid_up=0.75, brow_in=0.15),  # true: a hint of real smile
    "noor/sag":             dict(smile=0.0, lid_up=0.55, brow_in=0.15, gaze_y=0.5),
    "noor/sorry_mouthed":   dict(smile=0.25, jaw=0.1, brow_in=0.35, lid_up=0.85),
    "noor/unsettled":       dict(smile=-0.05, brow_in=0.2, lid_up=0.85, gaze_x=0.4),
    "noor/shock":           dict(lid_up=1.0, brow_in=0.5, brow_out=0.3, jaw=0.25),
    "noor/panic_shout":     dict(lid_up=1.05, brow_in=0.55, brow_out=0.2, jaw=0.45),
    "noor/reading":         dict(lid_up=0.7, brow_in=0.35, gaze_y=0.4, press=0.1),
    "noor/insane_barely":   dict(lid_up=0.9, brow_in=0.4, press=0.2, jaw=0.06, gaze_x=0.5),
    "noor/test":            dict(lid_up=0.8, brow_in=0.25, press=0.2, gaze_y=-0.5),
    "noor/clamped_fear":    dict(lid_up=1.05, brow_in=0.6, brow_out=0.2, jaw=0.15),
    "noor/shaking":         dict(lid_up=0.7, brow_in=0.5, press=0.4, chin=0.3),
    "noor/cant_end_call":   dict(lid_up=0.6, brow_in=0.5, smile=-0.15, press=0.3, gaze_y=0.6),
    "noor/caught_f":        dict(smile=0.12, jaw=0.22, lid_up=0.98, brow_in=0.3, brow_out=0.15, gaze_y=-0.7, gaze_x=-0.2),  # sheet
    "noor/not_fine":        dict(smile=-0.18, press=0.3, lid_up=0.6, brow_in=0.45, brow_out=-0.1, chin=0.3, gaze_y=0.35, gaze_x=-0.3),  # sheet
    "noor/listening":       dict(lid_up=0.72, brow_in=0.25, smile=-0.05),
    "noor/badge_turn":      dict(lid_up=0.45, brow_in=0.2, gaze_y=0.8, smile=-0.05),
    "noor/realising":       dict(lid_up=0.8, brow_in=0.4, brow_out=-0.1, jaw=0.05, gaze_y=0.6),
    "noor/cant":            dict(lid_up=0.7, brow_in=0.6, press=0.5, chin=0.4, smile=-0.15),
    "noor/phone_buzz":      dict(lid_up=0.85, brow_in=0.5, press=0.3, gaze_y=0.7),
    "noor/to_kais_phone":   dict(lid_up=0.8, brow_in=0.55, press=0.25, gaze_x=0.6),
    "noor/confession":      dict(smile=-0.1, press=0.45, jaw=0.08, lid_up=0.55, lid_low=0.35, brow_in=0.55, brow_out=-0.05,
                                 chin=0.6, naso=0.45, tear=1),  # sheet
    "noor/library_catch":   dict(lid_up=0.85, brow_in=0.6, press=0.35, chin=0.5, gaze_x=0.6, tear=1),
    "noor/sorry_small":     dict(smile=-0.15, press=0.3, lid_up=0.5, lid_low=0.3, brow_in=0.55, chin=0.5, tear=1),
    "noor/waiting":         dict(lid_up=0.72, brow_in=0.35, jaw=0.04, chin=0.2, tear=1),
    "noor/look_back":       dict(lid_up=0.75, brow_in=0.3, smile=0.05, lid_low=0.1),
    "noor/platform_neutral": dict(smile=-0.02, jaw=0.04, lid_up=0.75, brow_in=0.15, gaze_x=0.6, gaze_y=0.1),  # sheet; Director: neutral
    # ---------------- WALTER: economy
    "walter/watching":      dict(lid_up=0.55, smile=-0.08, naso=0.6, gaze_y=0.5),      # sheet (paper)
    "walter/to_badge":      dict(lid_up=0.6, smile=-0.08, naso=0.6, gaze_x=0.4, gaze_y=0.3),
    "walter/eyes_lift":     dict(lid_up=0.68, naso=0.6, gaze_x=0.4),
    "walter/stare":         dict(lid_up=0.72, brow_in=-0.05, smile=-0.1, naso=0.6),
    "walter/writing":       dict(lid_up=0.45, naso=0.6, gaze_y=0.8),
    "walter/clamp":         dict(lid_up=0.95, brow_in=-0.4, brow_out=0.1, press=0.6, naso=0.75, gaze_x=0.4),  # sheet
    "walter/release":       dict(lid_up=0.6, brow_in=0.2, naso=0.6),
    "walter/speech":        dict(lid_up=0.4, brow_in=0.28, smile=0.02, chin=0.15, jaw=0.06, naso=0.6, gaze_y=0.7),  # sheet
    "walter/speech_end":    dict(lid_up=0.62, lid_low=0.25, brow_in=0.15, smile=0.18, naso=0.7, gaze_x=0.4),     # sheet
    "walter/to_lanyard":    dict(lid_up=0.65, naso=0.6, gaze_x=0.4, gaze_y=0.5),
    "walter/asking":        dict(lid_up=0.68, brow_in=0.22, smile=0.08, lid_low=0.12, naso=0.65, gaze_x=0.55, jaw=0.05),  # sheet
    "walter/nod":           dict(lid_up=0.55, smile=0.1, lid_low=0.15, naso=0.65),
    "walter/page_turn":     dict(lid_up=0.5, smile=0.06, naso=0.6, gaze_y=0.7),
    # ---------------- BEA: a nurse's attention
    "bea/closed_awake":     dict(lid_up=0.0, tension=0.7, brow_in=-0.15, press=0.25, smile=-0.05),  # sheet
    "bea/assess":           dict(lid_up=0.8, brow_in=-0.05, gaze_x=-0.5),
    "bea/sits_up":          dict(lid_up=0.88, brow_in=0.1, gaze_x=-0.5),
    "bea/reach_dont":       dict(lid_up=0.95, brow_in=0.35, jaw=0.15, gaze_x=0.4),
    "bea/frozen":           dict(lid_up=0.9, brow_in=0.4, press=0.35),
    "bea/writing":          dict(lid_up=0.5, press=0.2, gaze_y=0.8),
    "bea/watching_noor":    dict(lid_up=0.72, brow_in=0.1, gaze_x=-0.4),
    "bea/you_okay":         dict(lid_up=0.72, lid_low=0.18, brow_in=0.25, smile=0.1, jaw=0.06, gaze_x=-0.45),  # sheet
    "bea/me_neither":       dict(lid_up=0.6, lid_low=0.1, brow_in=0.15, smile=0.08),
    "bea/tenderness":       dict(lid_up=0.6, lid_low=0.25, brow_in=0.25, smile=0.15, gaze_x=0.4),
    "bea/stiffens":         dict(lid_up=0.95, brow_in=0.2, press=0.3, gaze_y=-0.3),
    "bea/not_only":         dict(lid_up=0.66, brow_in=0.05, brow_out=-0.05, press=0.15, smile=-0.06, gaze_x=-0.4, gaze_y=0.45),  # sheet
    "bea/say_it":           dict(lid_up=0.88, brow_in=-0.32, brow_out=0.05, jaw=0.14, chin=0.2, naso=0.5, gaze_x=-0.5),  # sheet
    "bea/closed_rest":      dict(lid_up=0.0, tension=0.25, smile=0.06),
    # ---------------- KAI: loose and alive (sheet values mirrored into the rig's _L/_R)
    "kai/scrolling":        dict(lid_up=0.55, smile_L=0.28, smile_R=0.02, gaze_y=0.8, gaze_x=-0.1),  # sheet
    "kai/curious":          dict(lid_up=0.75, brow_in=0.1, gaze_x=0.4),
    "kai/brakes":           dict(lid_up=0.95, brow_in=0.35, brow_out=0.3, jaw=0.18, gaze_y=-0.6, gaze_x=0.3),  # sheet
    "kai/eyeroll":          dict(lid_up=0.75, gaze_y=-0.9, gaze_x=-0.3, brow_in=0.15, brow_out=0.25, smile_R=-0.12, smile_L=0.08),  # sheet
    "kai/library_lie":      dict(lid_up=0.62, smile_L=0.2, smile_R=0.05, gaze_y=0.3, jaw=0.08),
    "kai/nervous_laugh":    dict(lid_up=1.0, brow_in=0.5, brow_out=-0.05, smile=0.32, jaw=0.2, naso=0.3, gaze_y=-0.8),  # sheet
}

# per character: (time_s, expression). One line per beat, in shot order (shot numbers from camera/cues.json).
TRACK = {
    "NOOR": [
        (25.0, "noor/pleasant", 1), (33.0, "noor/relieved", 1), (36.0, "noor/fine_performed", 2), (40.0, "noor/relieved", 2),
        (63.0, "noor/sorry_mouthed", 6), (66.0, "noor/fine_performed", 6), (78.0, "noor/fine_performed", 7),
        (86.0, "noor/fine_listening", 8), (91.0, "noor/fine_performed", 9), (101.0, "noor/fine_listening", 10),
        (108.0, "noor/love_you", 11), (112.0, "noor/sag", 11), (114.5, "noor/unsettled", 11), (120.0, "noor/sorry_mouthed", 13),
        (125.0, "noor/unsettled", 13), (135.0, "noor/unsettled", 14), (143.0, "noor/unsettled", 16), (147.0, "noor/shock", 17),
        (166.0, "noor/shock", 18), (170.0, "noor/panic_shout", 20), (180.0, "noor/shock", 21), (186.0, "noor/reading", 22),
        (204.0, "noor/insane_barely", 24), (213.0, "noor/test", 26), (222.0, "noor/clamped_fear", 26), (234.0, "noor/shaking", 27),
        (239.0, "noor/shaking", 29), (262.0, "noor/cant_end_call", 32), (272.0, "noor/shaking", 33), (282.0, "noor/listening", 34),
        (290.0, "noor/caught_f", 35), (294.0, "noor/not_fine", 35), (300.0, "noor/listening", 36), (309.0, "noor/unsettled", 37),
        (313.0, "noor/listening", 38), (349.0, "noor/badge_turn", 40), (358.5, "noor/unsettled", 42), (380.0, "noor/listening", 43),
        (398.0, "noor/realising", 45), (408.5, "noor/cant", 47), (416.0, "noor/cant", 48), (440.0, "noor/phone_buzz", 50),
        (448.0, "noor/to_kais_phone", 52), (455.5, "noor/not_fine", 54), (460.0, "noor/confession", 54),
        (476.0, "noor/library_catch", 56), (480.0, "noor/confession", 56), (501.0, "noor/sorry_small", 58),
        (505.0, "noor/waiting", 58), (515.0, "noor/look_back", 60), (523.0, "noor/platform_neutral", 62),
    ],
    "WALTER": [
        (0.0, "walter/watching", 1), (44.0, "walter/to_badge", 3), (46.0, "walter/watching", 3), (86.0, "walter/eyes_lift", 8),
        (101.0, "walter/stare", 10), (116.0, "walter/stare", 12), (180.0, "walter/writing", 21), (184.0, "walter/stare", 21),
        (213.0, "walter/stare", 26), (222.0, "walter/clamp", 26), (234.0, "walter/release", 27), (239.0, "walter/watching", 29),
        (300.0, "walter/eyes_lift", 36), (313.0, "walter/speech", 38), (338.0, "walter/speech_end", 38), (349.0, "walter/watching", 40),
        (366.0, "walter/to_lanyard", 42), (384.5, "walter/stare", 44), (451.0, "walter/asking", 53), (469.0, "walter/stare", 55),
        (515.0, "walter/stare", 60), (520.0, "walter/nod", 61), (523.0, "walter/watching", 62), (556.0, "walter/page_turn", 63),
    ],
    "BEA": [
        (0.0, "bea/closed_awake", 1), (86.0, "bea/assess", 8), (101.0, "bea/sits_up", 10), (116.0, "bea/sits_up", 12),
        (138.0, "bea/reach_dont", 15), (143.0, "bea/frozen", 16), (190.0, "bea/writing", 23), (196.0, "bea/watching_noor", 23),
        (222.0, "bea/frozen", 26), (234.0, "bea/watching_noor", 27), (272.0, "bea/watching_noor", 33), (282.0, "bea/you_okay", 34),
        (300.0, "bea/me_neither", 36), (339.0, "bea/tenderness", 39), (360.0, "bea/stiffens", 42), (380.0, "bea/not_only", 43),
        (416.0, "bea/say_it", 48), (432.0, "bea/say_it", 49), (469.0, "bea/watching_noor", 55), (515.0, "bea/watching_noor", 60),
        (519.0, "bea/closed_rest", 61),
    ],
    "KAI": [
        (0.0, "kai/scrolling", 1), (101.0, "kai/brakes", 10), (106.0, "kai/scrolling", 10), (130.0, "kai/eyeroll", 14),
        (134.0, "kai/library_lie", 14), (143.0, "kai/library_lie", 16), (147.0, "kai/nervous_laugh", 17),
    ],
}

NOTES = {
    "kai": "Kai is removed at cue 4 (blackout); no keys after 153.5 s.",
    "bea/closed_awake": "Director F2: under BROWN/DIP use tension >= 0.35 (TA default) so the lid line holds.",
    "noor/platform_neutral": "Director's note: Noor is neutral on the platform, not hopeful and not afraid.",
    "noor/love_you": "'Love you' is TRUE: the only early smile where her lower lid lifts a touch.",
    "gaze": "gaze_x + = the character's right, gaze_y + = down. Gaze values are intent (down to the paper, toward Noor); in staging, aim the eyes at the real subject and let gaze override.",
    "walter/clamp": "The only time his lids open fully. Fastest move in the film: no anticipation, 2-3 frames in.",
}


def main():
    for ch, keys in TRACK.items():
        for t, name, shot in keys:
            assert name in LIB, name
    out = {"_note": __doc__.strip().splitlines()[0], "fps": 24, "library": LIB,
           "tracks": {ch: [[t, n, s] for t, n, s in keys] for ch, keys in TRACK.items()}, "notes": NOTES}
    with open(os.path.join(HERE, "shot_expressions.json"), "w") as f:
        json.dump(out, f, indent=1)
    # readable table
    rows = ["# Shot expressions (M4 previs)", "",
            "Generated by `shot_expressions.py`; data in `shot_expressions.json`. Expression names point into the library "
            "(face-rig values; rig convention `_L` = character's left). Ease ~6–8 frames into each change "
            "(the clamp: 2–3 frames). Acting stays in the 5–25% range; these are targets.", "",
            "| t (s) | shot | NOOR | WALTER | BEA | KAI |", "|---|---|---|---|---|---|"]
    events = sorted({(t, s) for keys in TRACK.values() for t, _, s in keys})
    for t, s in events:
        cells = []
        for ch in ("NOOR", "WALTER", "BEA", "KAI"):
            hit = [n.split("/")[1] for tt, n, ss in TRACK[ch] if tt == t]
            cells.append(", ".join(hit))
        rows.append(f"| {t:.1f} | {s} | " + " | ".join(cells) + " |")
    rows += ["", "## Notes", ""] + [f"- **{k}**: {v}" for k, v in NOTES.items()]
    with open(os.path.join(HERE, "shot-expressions.md"), "w") as f:
        f.write("\n".join(rows) + "\n")
    print("wrote shot_expressions.json and shot-expressions.md")


if __name__ == "__main__":
    main()
