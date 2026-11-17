#!/usr/bin/env python3
"""Build film/camera/cues.json and film/camera/cut-timeline.md (DP, Milestone 3/4).

cues.json is the shared sync file for the previs. It holds:
  - the panel map (P1-P12 positions in set coordinates, plus the Composer's partials)
  - the light cues 0-8 with exact levels, colour temperature and keyframe shapes
  - world events (display, doors, platform lamp, phones, PA)
  - the virtual cameras (positions A-G and their lenses)
  - the animatic cut: every shot with in/out times, camera, lens, move and aim

The Composer's render_temp_score.py reads the same file ("cues", "events", "fps",
"duration_s"), so picture and score move together. The TA's Blender scripts read it to
keyframe the lights and cameras.

Set coordinates (metres, Blender convention, Z up): Y runs down the car from end wall B
(y = 0, far end) to end wall A (y = 13, Noor's end). Side A is -X, side B is +X. The floor
is z = 0 and the ceiling z = 2.3. The unlit vestibule runs from y = -4 to 0.

Times are seconds from the first frame at 24 fps. They are estimates for a ~9:25 cut,
built on the Composer's provisional timeline. When the voice record exists, re-time the
TIMES table below and re-run; every check is repeated.

Run: python3 build_cues.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24
LEN, HALF, CEIL, N = 13.0, 1.4, 2.3, 12
SP = LEN / N

def py(i):                       # panel centre on Y
    return round(LEN - (i - 0.5) * SP, 3)

PARTIAL = {1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 10: 11, 11: 12, 12: 17}
ALL = ["P%d" % i for i in range(1, 13)]

# ---- looks -------------------------------------------------------------------------
LOOKS = {
    "BASE":  {"level": 1.0, "kelvin": 4300, "green": 0.25, "note": "asleep: never altered by anything except a cue"},
    "BROWN": {"level": 0.18, "kelvin": 2200, "green": 0.0, "note": "about -2.5 stops; level and colour temperature move together like a failing tungsten load"},
    "DIP":   {"level": 0.05, "kelvin": 3200, "green": 0.0, "note": "cue 5 only: near-black with a hint of warmth"},
    "OVER":  {"level": 1.10, "kelvin": 4300, "green": 0.25, "note": "cue 8 relight overshoot, settling to BASE in 12 frames"},
    "OFF":   {"level": 0.0},
}
BREATH = {"depth": 0.03, "period_s": 5.0, "phase": "all panels in phase",
          "on_cue": "1", "off_cue": "8.10",
          "note": "a sine on each lit panel's level, layered on top of its keyframes. Depth and period are variables shared with the Composer's hum build, and may drop to 0.02 or slow down after the look-dev visibility check"}

# ---- light cues --------------------------------------------------------------------
# shape: list of (frame offset, level) applied to the cue's panels; "hold" means the
# level persists until a later cue changes it. Interpolation is CONSTANT (lights on ones)
# unless "ease" says otherwise.
C = []
def cue(id, t, type, panels, line, shape, **kw):
    C.append(dict(id=id, t=t, type=type, panels=panels, line=line, shape=shape, **kw))

cue("0", 40.0, "tick", ["P1"], "(Noor straightens her lanyard, the badge settling face-out)",
    [(0, 0.85), (2, 1.0)], note="subliminal; only Walter reacts")
cue("1", 80.0, "flicker", ["P1"], "Just leaving the office now.",
    [(0, 1.0), (0, 0.30), (3, 0.85), (5, 0.40), (8, 1.0)], breath="on", windows="off",
    note="first groan; from here the windows stay black until 8.10")
cue("2", 95.0, "flicker", ["P1", "P2"], "Long day. The Henley account. Again.",
    [(0, 0.10), (4, 0.60), (8, 0.10), (16, 0.10), (22, 1.0)], lag_frames={"P2": 2})
cue("3", 145.0, "brownout", ALL, "I'm at the library, Mum.",
    [(0, 1.0), (8, "BROWN")], ease="sag over 8 frames, level and colour together", hold=True)
cue("4", 155.0, "blackout", ALL, "No, that's — it's the library. They're doing work on the —",
    [(0, 0.0)], world_off=["DISPLAY", "WINDOWS", "DOOR", "PHONES_EXCEPT_NONE"],
    note="TRUE BLACK: world, emitters, display all 0; nothing in the render, comp or grade lifts it. Kai is removed in the dark (no animation)")
cue("4.up", 158.0, "lights_up", ALL, "(LIGHTS UP)", [(0, 1.0)], note="snap to BASE; display back; breathing resumes in phase; windows stay black")
cue("5", 225.0, "hard_dip", ["P3", "P2", "P4"], "My name is S—",
    [(0, 1.0), (2, "DIP")], main="P3", sympathy={"P2": 0.40, "P4": 0.40},
    recover={"t": 229.0, "frames": 72, "ease": "slow ease-in back to BASE"},
    note="Noor is standing in the aisle beside Walter, under P3; 'the panel above her' is P3")
cue("6", 295.0, "stutter", ["P1"], "I'm f—", [(0, 0.50), (2, 1.0), (4, 0.45), (8, 1.0)])

# The Advance: 10 ticks, steady 8.5 s apart, never accelerating, never on a line; each
# follows a line or a look, as if the car were answering it (Director, composer-notes-02).
ADV = [("7.1", 360.0, "P12", "(display 5 MIN; no word spoken)"),
       ("7.2", 368.5, "P11", "after NOOR: \"Nobody said anything.\""),
       ("7.3", 377.0, "P10", "after Walter's eyes reach her lanyard"),
       ("7.4", 385.5, "P9", "after BEA: \"It isn't only what you say.\""),
       ("7.5", 394.0, "P8", "after Noor looks down at herself (Kai's seat goes dark; his phone glows on)"),
       ("7.6", 402.5, "P7", "after the lanyard hits the floor (\"It isn't enough.\")"),
       ("7.7", 411.0, "P6", "(silence; Bea leans in)"),
       ("7.8", 419.5, "P5", "after BEA: \"Whatever it is, say it.\""),
       ("7.9", 428.0, "P4", "after the overlap: NOOR \"I can't —\" / BEA \"Say it.\" (the car's answer)"),
       ("7.10", 436.5, "P3", "(silence: rails and the rising groan only, no score event; held on Bea as her light dies to the edge; two panels left)")]
for id, t, p, line in ADV:
    cue(id, t, "panel_out", [p], line, [(0, 0.0)], note="snap off, relay tick on the same frame, no flicker")

cue("8.0", 462.0, "steady", ["P1"], "No. Listen. I'm not leaving the office.", [(0, 1.10)], hold=True,
    note="P1 steadies and burns brighter: held at 110% (its breathing stops) until 8.10")
REL = [("8.1", 470.0, "P3", "...They let me go. The whole floor."),
       ("8.2", 483.0, "P4", "...And then I come home."),
       ("8.3", 493.0, "P5", "I didn't tell you because —"),
       ("8.4", 494.1, "P6", "— you'd have been kind about it —"),
       ("8.5", 495.2, "P7", "— and I couldn't — (run)"),
       ("8.6", 496.3, "P8", "(run; Kai's empty seat relights, phone still glowing)"),
       ("8.7", 497.4, "P9", "(run)"),
       ("8.8", 498.5, "P10", "(run)"),
       ("8.9", 499.6, "P11", "(run)"),
       ("8.10", 508.0, "P12", "(Silence on the line.)")]
for id, t, p, line in REL:
    extra = {}
    if id == "8.10":
        extra = dict(also={"P1": "settle 1.10 -> 1.0 on the same frame"}, breath="off",
                     note="the far panel comes on last; every panel exactly BASE; the car is asleep")
    cue(id, t, "relight", [p], line, [(0, 1.10), (12, 1.0)], **extra)

# ---- world events (not car cues) --------------------------------------------------
EVENTS = [
    ("board_chime", 25.0, "door chime; Noor boards"),
    ("D0", 0.0, "DISPLAY: NEXT STOP: HOLLOWAY"),
    ("doors_open_board", 0.0, "doors open at the starting platform; PLATFORM lamp on (cold white) while the train idles"),
    ("lanyard", 40.0, "Noor straightens the lanyard (cue 0)"),
    ("doors_close", 48.0, "doors close; the starting platform and its lamp slide away (48-58); WINDOWS chase on (glass only, while asleep)"),
    ("D1", 50.0, "DISPLAY: NEXT STOP: HOLLOWAY — 11 MIN"),
    ("mark_call_1", 65.0, "PHONE (Noor): MARK"),
    ("lie_1", 80.0, "cue 1"),
    ("lie_2", 95.0, "cue 2"),
    ("love_you", 110.0, "'Love you' (true: nothing happens)"),
    ("mum_call", 133.0, "PHONE (Kai): MUM"),
    ("kai_lie", 145.0, "cue 3"),
    ("D2", 236.0, "DISPLAY: 8 MIN"),
    ("thumb_over_end_call", 264.0, "PHONE (Kai): end-call red button on screen"),
    ("D3", 357.0, "DISPLAY: 5 MIN"),
    ("D4", 438.0, "DISPLAY: 2 MIN"),
    ("marks_call", 440.0, "PHONE (Noor): MARK; her screen becomes a key light"),
    ("he_is_asking", 452.0, "WALTER: 'He's asking.'"),
    ("silence_on_line", 505.0, "silence on the line"),
    ("train_slows", 512.0, "DISPLAY: NOW ARRIVING: HOLLOWAY; the Holloway platform slides in, seen only in the door glass (512-520)"),
    ("arrival_chime", 520.0, "door chime"),
    ("doors_open", 521.0, "doors open; PLATFORM lamp on (cold white ~5000 K, slight green)"),
    ("doors_close_final", 535.0, "doors close"),
    ("pa_line", 538.0, "PA: 'Thank you for riding quietly.' (no light cue)"),
    ("pull_away", 540.0, "platform + lamp slide away in the door glass; WINDOWS stay black"),
    ("pull_away_end", 548.0, "platform gone; PLATFORM 0; the frame is dead still from here"),
    ("page_turn", 552.0, "Walter turns the page (no light change)"),
    ("phone_dims", 561.0, "Kai's phone screen fades to black over 2 s"),
    ("cut", 565.0, "CUT TO BLACK"),
    ("rails_stop", 568.0, "rails stop over black"),
]

# ---- dialogue windows (in, out, who, line) ------------------------------------------
# PROVISIONAL: seeded from the Composer's music/temp/dialogue-windows.json estimates.
# Replace with the Screenwriter's scratch-voice timings when they exist (see previs-review.md).
DIALOGUE = [
    (66.0, 72.0, 'NOOR', "Hi. Hi, yeah. I'm on the train."),
    (72.0, 77.0, 'MARK', '(murmur)'),
    (79.0, 81.5, 'NOOR', 'Just leaving the office now.'),
    (91.5, 95.0, 'NOOR', 'Long day. The Henley account. Again.'),
    (103.0, 105.0, 'KAI', 'Was that the brakes?'),
    (108.5, 111.0, 'NOOR', "No, don't wait up. Love you."),
    (122.0, 124.0, 'NOOR', '(mouths) Sorry.'),
    (135.0, 136.5, 'KAI', 'Yeah?'),
    (143.0, 145.3, 'KAI', "I'm at the library, Mum."),
    (148.5, 155.0, 'KAI', "No, that's — it's the library. They're doing work on the —"),
    (159.5, 164.0, 'MUM', 'Kai? ... Kai?'),
    (170.5, 172.5, 'NOOR', 'What — where did he —'),
    (175.0, 177.5, 'NOOR', 'Hey. Hey!'),
    (206.5, 208.5, 'NOOR', "That's insane."),
    (216.0, 218.0, 'NOOR', 'My name is Noor.'),
    (222.5, 225.2, 'NOOR', 'My name is S—'),
    (253.0, 255.0, 'MUM', 'Kai?'),
    (283.5, 285.5, 'BEA', 'You okay?'),
    (293.5, 295.2, 'NOOR', "I'm f—"),
    (297.0, 299.0, 'NOOR', "I'm not fine."),
    (301.0, 306.5, 'BEA', "Me neither. I haven't slept in two days."),
    (309.5, 311.5, 'NOOR', "You've seen this before."),
    (314.0, 316.0, 'WALTER', 'I ride it every night.'),
    (317.0, 318.0, 'NOOR', 'Why?'),
    (322.0, 342.0, 'WALTER', 'My wife was ill a long time. ... This is the only place nobody can say that to me.'),
    (363.0, 365.5, 'NOOR', 'Nobody said anything.'),
    (380.5, 384.0, 'BEA', "It isn't only what you say."),
    (416.0, 419.0, 'BEA', 'Whatever it is, say it.'),
    (426.0, 427.2, 'NOOR', "I can't —"),
    (426.9, 427.6, 'BEA', 'Say it.'),
    (452.0, 454.5, 'WALTER', "He's asking."),
    (457.0, 458.5, 'NOOR', 'Mark.'),
    (459.0, 461.5, 'MARK', '(murmur)'),
    (461.8, 465.0, 'NOOR', "No. Listen. I'm not leaving the office."),
    (465.5, 469.8, 'NOOR', "I haven't been to the office since September. They let me go. The whole floor."),
    (474.5, 482.5, 'NOOR', 'I get dressed and I get on the train and I go to the library — ... — and I sit there. All day. And then I come home.'),
    (486.0, 492.8, 'NOOR', "I didn't tell you because you'd have been kind about it, and I couldn't —"),
    (502.0, 504.0, 'NOOR', "I'm sorry."),
    (527.0, 533.0, 'MARK', '(murmur restarts)'),
    (538.0, 540.5, 'PA', 'Thank you for riding quietly.'),
]

# The Screenwriter's scratch-voice placement is the source for lines when it exists
# (film/previs/voice/scratch-voice-lines.json, generated from voice-sides.md + this cues.json).
VOICE = os.path.join(HERE, "..", "previs", "voice", "scratch-voice-lines.json")
DIALOGUE_SOURCE = "provisional (Composer's estimates)"
if os.path.exists(VOICE):
    with open(VOICE) as fh:
        _v = json.load(fh)
    DIALOGUE = [(float(l["start"]), float(l["end"]), l["voice"], l["id"] + (": " + l["note"] if l.get("note") else ""))
                for l in _v["lines"]]
    DIALOGUE_SOURCE = "previs/voice/scratch-voice-lines.json (Screenwriter)"

# ---- clock trims (previs-notes-02) -----------------------------------------------------
# Every time above is written on the ORIGINAL clock. These spans are cut out of it:
#   [0, 13)    shot 1's pre-entry hold, 25 s -> 12 s
#   [545, 550) the tail of shot 62: cut ~2 s after Noor clears the glass (the PA stays before the cut)
TRIMS = [(0.0, 13.0), (545.0, 5.0)]
CLOCK = "v2: trims " + ", ".join("[%g, %g)" % (a, a + l) for a, l in TRIMS)

def M(t):
    """Original clock -> current clock."""
    out = t
    for a, l in TRIMS:
        if t >= a + l:
            out -= l
        elif t > a:
            out -= (t - a)
    return round(out, 3)

# ---- virtual cameras -------------------------------------------------------------
HEAD = {"NOOR": (0.0, 12.75, 1.22), "NOOR_STAND": (-0.35, 10.0, 1.62), "WALTER": (-1.0, py(3), 1.22),
        "BEA": (1.0, py(3), 1.22), "KAI": (1.05, py(8), 1.22), "KAI_PHONE": (1.05, py(8), 0.48),
        "DOORS": (1.4, 6.5, 1.2), "DISPLAY": (0.0, 13.0, 1.82),
        "NOOR_EYES": (0.0, 12.75, 1.24), "NOOR_CHIN": (0.0, 12.75, 1.10), "NOOR_CROWN": (0.0, 12.75, 1.36),
        "SIGN": (0.0, 13.0, 2.07), "WRIST": (-0.6, 10.1, 1.0),
        "NEWSPAPER": (-0.78, 10.1, 1.32),        # held up by Walter toward Noor, who stands beside him (TA blocking 188-239 s) (shots 22-23)
        "LANYARD_FLOOR": (0.2, 12.1, 0.02),      # where it lands at 7.6 (it stays there to the end)
        "NOOR_PHONE_LAP": (0.0, 12.45, 0.62),
        "AIM_15": (0.8, 7.5, 1.1),
        "AIM_42": (0.0, 13.0, 2.0),
        "NOOR_UP": (0.0, 12.3, 1.62),            # standing up at her seat (arrival; TA blocking 515-519 s)
        "NOOR_AT_DOORS": (1.0, 7.25, 1.62),       # at the emergency release by the doors (shot 20; TA blocking)
        "HANDLE": (1.385, 7.75, 1.45),           # the emergency release (TA set)
        "NOOR_PLATFORM": (2.6, 6.85, 1.62),      # on the platform, framed in the right door leaf's window, clear of the seam (shot 62)
        "NOOR_AT_KAI": (0.75, 5.3, 0.95),        # leaning in over Kai's seat, thumb over the call (32; TA blocking)
        "AIM_32": (0.7, 4.875, 0.85),            # between the screen and her face
        "AIM_33": (0.8, 9.0, 1.4),               # her walk back up the car, Bea watching
        "AIM_DOWN_CAR": (0.3, 0.0, 1.0)}         # looking down the car from Noor's end       # the creep push: ~1 deg up from level       # shot 15: Bea's reach in the foreground, Kai deep    # MARK, in her lap (shot 51)

# Insert cameras: shot -> (loc, aim mark). All 50 mm.
INSERTS = {
    5:  ((0.0, 10.0, 1.50), "DISPLAY"),          # the display over Noor's head; the top of her head may sit in the bottom of frame
    19: ((0.55, 4.6, 1.25), "KAI_PHONE"),        # high, looking down at the phone on the cushion
    22: ((0.1, 10.6, 1.8), "NEWSPAPER"),        # over Noor's right shoulder (she stands beside Walter), clear of her body
    23: ((0.1, 10.6, 1.8), "NEWSPAPER"),
    28: ((0.0, 10.0, 1.50), "DISPLAY"),
    30: ((0.55, 4.6, 1.25), "KAI_PHONE"),
    41: ((0.0, 10.0, 1.50), "DISPLAY"),
    46: ((0.1, 11.2, 1.10), "LANYARD_FLOOR"),    # high, red on grey
    51: ((0.3, 12.6, 1.35), "NOOR_PHONE_LAP"),   # her POV, down at the phone in her lap
    59: ((0.0, 10.0, 1.50), "DISPLAY"),
}

# The one handheld shot: recorded operator motion layered on the base camera (treatment, scene 4).
HANDHELD = {20: {"base_loc": (0.8, 9.8, 1.55), "aim": "NOOR_AT_DOORS",
                 "source": "a recorded handheld operator clip (real body motion), not procedural noise",
                 "amplitude": "about 3-5 cm translation and 1-2 degrees rotation, following Noor's panic",
                 "settle": "steady by the cut to shot 21 (Walter's paper); the camera is on sticks again from there"}}
POS = {
    "A":  {"loc": (0.0, -3.8, 1.65), "aim": (0.0, 13.0, 1.65), "lens": 32,
           "note": "the Meter: in the unlit vestibule, standing eye height, level. Holds all 12 panels, Noor, the sign and the display"},
    "A2": {"loc": (0.0, -2.0, 1.65), "aim": (0.0, 13.0, 2.0), "lens": 32,
           "note": "where the creep push lands (1.8 m in from A, tilted ~1 deg up like the push)"},
    "B":  {"loc": (0.55, 12.85, 1.0), "aim": (0.3, 0.0, 1.0), "lens": 32,
           "note": "Noor's end, side B corner, low, looking down the car"},
    "C":  {"loc": (-0.7, 10.9, 1.15), "lens": 50, "note": "side A, just in front of Walter (so his head never crosses frame): Noor singles (aim NOOR) or Bea across the aisle (aim BEA)"},
    "W":  {"loc": (0.0, 6.0, 1.0), "aim": (0.0, 12.6, 1.8), "lens": 32,
           "note": "the call (scene 2): low in the aisle by the doors, Noor framed between Walter (left) and Bea (right) with P1 and P2 above her. We watch her the way Walter does"},
    "T":  {"loc": (0.5, 5.0, 1.0), "aim": (-0.4, 11.0, 1.9), "lens": 32,
           "note": "the test (scene 4): from beside Kai's empty seat, looking back up the car at Noor standing by Walter, with P2, P3 and P4 in frame"},
    "C75": {"loc": (-0.25, 10.4, 1.2), "aim": (0.0, 12.75, 1.24), "lens": 75,
            "note": "the confession: near Noor's line of sight down the car, so the panel row reflects in her corneas and reads at 75 mm (dp-notes-02). Her eyeline passes just camera-right of the lens, down the car"},
    "D":  {"loc": (0.7, 10.9, 1.15), "lens": 50, "note": "side B, just in front of Bea (so her head never crosses frame): Noor singles or Walter across the aisle"},
    "E":  {"loc": (-1.0, 12.2, 1.4), "aim": (0.0, py(3), 1.2), "lens": 40, "note": "side A corner at end A: Walter/Bea two-shots, deep staging"},
    "W7": {"loc": (0.0, 8.2, 0.9), "aim": (0.0, 12.6, 1.7), "lens": 32,
           "note": "lie 1 (shot 7): closer and low, so P1's fixture reads large enough to flicker visibly (from W it was a grazing sliver at the far end)"},
    "G2": {"loc": (0.8, 9.8, 1.55), "aim": (1.25, 7.2, 1.35), "lens": 32,
           "note": "the handle (shot 20): Noor at the emergency release, the release itself and the doors in one frame (previs-notes-02)"},
    "B2": {"loc": (0.3, 12.85, 1.5), "aim": (0.3, 0.0, 1.2), "lens": 32,
           "note": "Noor's end, side A corner: looking down the car clear of Bea (from B, Bea's body blocked the foreground)"},
    "K":  {"loc": (1.12, 4.62, 0.72), "aim": (0.96, 4.845, 0.505), "lens": 50,
           "note": "at Kai's seat, low beside the phone: the red end-call button with her thumb coming in from above (shot 32). Her face can't share a tight frame with a phone lying on the seat"},
    "DP_POV": {"loc": (0.3, 6.9, 1.55), "aim": (0.0, 10.29, 1.25), "lens": 32,
           "note": "Noor's POV from the doors, looking back up the car at Walter and Bea (shot 61)"},
    "S":  {"loc": (-0.9, 8.9, 1.62), "lens": 50,
           "note": "Noor standing beside Walter (TA blocking 188-239 s), seen from in front and slightly down the car (shot 24)"},
    "E3": {"loc": (-0.7, 6.6, 1.4), "aim": (0.0, 10.29, 1.25), "lens": 32,
           "note": "shot 61: from down the car on side A, Walter (left) and Bea (right) as Noor walks toward camera on side B to the doors"},
    "R":  {"loc": (-0.6, 3.4, 1.4), "aim": (0.3, 9.0, 1.3), "lens": 32,
           "note": "shot 31: from beyond Kai's seat, Noor walking down the car toward it"},
    "DP_KAI": {"loc": (-0.25, 9.7, 1.6), "aim": (1.05, 4.875, 0.48), "lens": 50,
           "note": "Noor's POV from beside Walter down to Kai's empty seat (shot 25)"},
    "E2": {"loc": (0.0, 7.4, 1.15), "aim": (0.0, 10.29, 1.25), "lens": 32,
           "note": "the Walter/Bea two-shot: from down the car, both in profile facing each other, Noor small between them under the sign. From Noor's end no 32/40 can hold both (they sit 2 m apart, 2.5 m away)"},
    "F":  {"loc": (-0.95, py(8), 1.15), "lens": 40, "note": "across the aisle from Kai"},
    "G":  {"loc": (-0.9, 6.5, 1.3), "aim": (2.6, 6.85, 1.5), "lens": 32, "note": "facing the doors"},
    "I":  {"note": "inserts: placement per shot"},
}
# Camera paths for the moving shots: (loc at shot in, loc at shot out). Constant speed, keyed on ones.
PATHS = {
    42: ((0.0, -3.8, 1.65), (0.0, -2.0, 1.65)),     # the creep push: A -> A2, 1.8 m; tilted ~1 deg up (AIM_42) so each panel going out stays inside the top of frame (previs pass 1)
    54: ((-0.25, 9.6, 1.2), (-0.25, 10.0, 1.2)),    # the confession push, part 1
    56: ((-0.25, 10.0, 1.2), (-0.25, 10.4, 1.2)),   # part 2: lands on C75 (the CU), and shot 58 holds it
}

SENSOR = {"width_mm": 24.89, "height_mm": 10.41, "format": "Super 35 cropped to 2.39:1"}

# ---- the cut ---------------------------------------------------------------------
# (n, in, out, pos, lens, aim, move, scene, beat, cues expected inside)
S = [
 (1, 0.0, 36.0, "A", 32, None, "locked", 1, "Carriage idling; Noor boards and walks the length of the car; sits under P1 facing us", []),
 (2, 36.0, 44.0, "C", 50, "NOOR", "locked", 1, "Noor straightens her lanyard (ceiling out of frame: asleep)", ["0"]),
 (3, 44.0, 47.5, "D", 50, "WALTER", "locked", 1, "Walter's eyes to the badge and back to his paper", []),
 (4, 47.5, 60.0, "A", 32, None, "locked", 1, "Doors close, train pulls away; 11 MIN", []),
 (5, 60.0, 63.0, "I", 50, "DISPLAY", "locked", 1, "Display: 11 MIN", []),
 (6, 63.0, 78.0, "D", 40, "NOOR", "locked", 2, "Phone buzzes, MARK; she glances up at the sign and answers low", []),
 (7, 78.0, 86.0, "W7", 32, None, "locked", 2, "'Just leaving the office now.' The ceiling enters: P1 in the top of frame", ["1"]),
 (8, 86.0, 88.5, "D", 50, "WALTER", "locked", 2, "Walter's eyes lift from his paper to Noor (single)", []),
 ("8B", 88.5, 91.0, "C", 50, "BEA", "locked", 2, "Bea's eyes open, on Noor (single)", []),
 (9, 91.0, 101.0, "W", 32, None, "locked", 2, "'The Henley account. Again.' P1 and P2 both in frame, Walter and Bea watching her", ["2"]),
 (10, 101.0, 108.0, "A", 32, None, "locked", 2, "The whole car reacts: paper lowers, Bea sits up, Kai: 'Was that the brakes?'", []),
 (11, 108.0, 116.0, "W", 32, None, "locked", 2, "'No, don't wait up. Love you.' Hangs up, sags, looks up", []),
 (12, 116.0, 118.0, "B", 40, "WALTER", "locked", 2, "Noor's POV: Walter staring at her", []),
 ("12B", 118.0, 120.0, "B", 40, "BEA", "locked", 2, "Noor's POV: Bea staring at her", []),
 (13, 120.0, 130.0, "D", 40, "NOOR", "locked", 2, "Mouths 'Sorry', points over her shoulder at the sign", []),
 (14, 130.0, 138.0, "F", 40, "KAI", "locked", 3, "Kai's phone: MUM. 'Yeah?'", []),
 (15, 138.0, 143.0, "B", 32, "AIM_15", "locked", 3, "Bea's hand shoots out, too far away", []),
 (16, 143.0, 147.0, "A", 32, None, "locked", 3, "'I'm at the library, Mum.' Brownout", ["3"]),
 (17, 147.0, 153.5, "F", 50, "KAI", "locked", 3, "Kai in the brownout: looks up, nervous laugh", []),
 (18, 153.5, 166.0, "A", 32, None, "locked", 3, "'They're doing work on the —' BLACKOUT. Inhale. Lights up: the seat is empty. 'Kai? ... Kai?'", ["4", "4.up"]),
 (19, 166.0, 170.0, "I", 50, "KAI_PHONE", "locked", 3, "Kai's phone face-up, call connected", []),
 (20, 170.0, 180.0, "G2", 32, None, "handheld", 4, "Noor at the doors, the emergency handle. 'Hey. Hey!' (recorded operator motion)", []),
 (21, 180.0, 186.0, "D", 50, "WALTER", "locked", 4, "Walter writes in the margin and holds it up", []),
 (22, 186.0, 190.0, "I", 50, None, "locked", 4, "DON'T LIE IN HERE.", []),
 (23, 190.0, 200.0, "I", 50, None, "locked", 4, "Bea writes underneath: IT'S AWAKE NOW. YOU WOKE IT.", []),
 (24, 200.0, 210.0, "S", 50, "NOOR_STAND", "locked", 4, "Noor reads it twice; eyes to Kai's seat. 'That's insane.'", []),
 (25, 210.0, 213.0, "DP_KAI", 50, None, "locked", 4, "Kai's empty seat, the phone", []),
 (26, 213.0, 234.0, "T", 32, None, "locked", 4, "Standing beside Walter under P3. 'My name is Noor.' Nothing. 'My name is S—' The wrist clamp. P3 near black, P2/P4 dip. Nobody breathes. Recovery", ["5"]),
 (27, 234.0, 236.0, "T", 50, "NOOR_STAND", "locked", 4, "He releases her. She's shaking", []),
 (28, 236.0, 239.0, "I", 50, "DISPLAY", "locked", 4, "Display: 8 MIN", []),
 (29, 239.0, 252.0, "A", 32, None, "locked", 5, "She sits back down slowly (the walk to P1). Long beat of rails", []),
 (30, 252.0, 256.0, "I", 50, "KAI_PHONE", "locked", 5, "Kai's phone, still lit: 'Kai?'", []),
 (31, 256.0, 262.0, "R", 32, None, "locked", 5, "She walks down the car to Kai's seat", []),
 (32, 262.0, 272.0, "K", 50, None, "locked", 5, "Her thumb over the red end-call button. She can't", []),
 (33, 272.0, 282.0, "E", 32, "AIM_33", "locked", 5, "She goes back to her seat; Bea watches the whole time", []),
 (34, 282.0, 290.0, "C", 50, "BEA", "locked", 5, "Bea: 'You okay?'", []),
 (35, 290.0, 300.0, "D", 50, "NOOR", "locked", 5, "'I'm f—' (stutter) ... 'I'm not fine.'", ["6"]),
 (36, 300.0, 309.0, "C", 50, "BEA", "locked", 5, "'Me neither. I haven't slept in two days.' Nothing happens", []),
 (37, 309.0, 313.0, "D", 50, "NOOR", "locked", 5, "'You've seen this before.'", []),
 (38, 313.0, 344.0, "D", 50, "WALTER", "locked", 5, "Walter: 'I ride it every night.' ... the wife speech, one unbroken shot", []),
 (39, 344.0, 349.0, "E2", 32, None, "locked", 5, "Bea looks at him with real tenderness", []),
 (40, 349.0, 355.0, "C", 50, "NOOR", "locked", 5, "Noor turns the badge over in her fingers", []),
 (41, 355.0, 358.5, "I", 50, "DISPLAY", "locked", 6, "Display: 5 MIN", []),
 (42, 358.5, 380.0, "A", 32, "AIM_42", "push A->A2", 6, "Tick: the far panel out. Bea stiffens. 'Nobody said anything.' Walter's eyes to the lanyard. The camera rides in behind the dark edge", ["7.1", "7.2", "7.3"]),
 (43, 380.0, 384.5, "C", 50, "BEA", "locked", 6, "Bea: 'It isn't only what you say.'", []),
 (44, 384.5, 398.0, "B2", 32, None, "locked", 6, "The dark comes toward camera; Kai's seat goes dark, his phone glows on in it", ["7.4", "7.5"]),
 (45, 398.0, 405.5, "C", 50, "NOOR", "locked", 6, "She looks down at herself; yanks the lanyard over her head and throws it (each tick takes a step of front light off her face)", ["7.6"]),
 (46, 405.5, 408.5, "I", 50, None, "locked", 6, "The lanyard on the floor: red on grey", []),
 (47, 408.5, 416.0, "C", 50, "NOOR", "locked", 6, "It isn't enough", ["7.7"]),
 (48, 416.0, 426.5, "D", 50, "NOOR", "locked", 6, "Bea (off): 'Whatever it is, say it.' Noor gathers herself", ["7.8"]),
 (49, 426.5, 440.0, "C", 50, "BEA", "locked", 6, "Noor (off): 'I can't —' / Bea over her: 'Say it.' The 7.9 tick answers the pair. Then 8.5 s of silence (rails, the rising groan, no score event) held on Bea, and on 7.10 her own light dies to the edge", ["7.9", "7.10"]),
 (50, 440.0, 445.0, "A2", 32, None, "locked", 6, "Two panels left; Noor in the last pool; display 2 MIN; her phone buzzes", []),
 (51, 445.0, 448.0, "I", 50, None, "locked", 6, "MARK, in her lap", []),
 (52, 448.0, 451.0, "C", 50, "NOOR", "locked", 6, "She looks across at Kai's phone glowing in the dark", []),
 (53, 451.0, 455.5, "D", 50, "WALTER", "locked", 6, "Walter, half-lit at the edge of the dark: 'He's asking.' His lit-side eye carries a readable catchlight (P2 or Noor's phone) and the lid line holds", []),
 (54, 455.5, 469.0, "C75", 75, None, "push", 7, "She answers. 'Mark.' ... 'I'm not leaving the office.' (P1 burns brighter)", ["8.0"]),
 (55, 469.0, 474.0, "E2", 32, None, "locked", 7, "Walter and Bea come back into the light", ["8.1"]),
 (56, 474.0, 486.0, "C75", 75, None, "push", 7, "'I go to the library —' the half-beat, her eyes to Kai's phone — '— and I come home.'", ["8.2"]),
 (57, 486.0, 501.0, "A", 32, None, "locked", 7, "'I didn't tell you because —' the relights run toward us; Kai's empty seat relights", ["8.3", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9"]),
 (58, 501.0, 512.0, "C75", 75, None, "still (the push has landed)", 7, "'I'm sorry.' Silence on the line. The far panel comes on: on the 8.10 frame the tip of the reflected panel row in her corneas completes (P12 itself is sub-pixel at ~10 m; accepted by the Director). Hold C75 as framed, no tighter. The car is asleep", ["8.10"]),
 (59, 512.0, 515.0, "I", 50, "DISPLAY", "locked", 8, "Display: NOW ARRIVING: HOLLOWAY", []),
 (60, 515.0, 519.0, "D", 40, "NOOR_UP", "locked", 8, "The train slows; she stands and looks back at them", []),
 (61, 519.0, 523.0, "E3", 32, None, "locked", 8, "Walter's smallest nod; Bea has closed her eyes", []),
 (62, 523.0, 550.0, "G", 32, "DOORS", "locked", 8, "Out under the cold-white lamp, phone to her ear. Doors close. PA. She slides away in the glass", []),
 (63, 550.0, 565.0, "A", 32, None, "locked", 8, "The opening frame again: Walter turns the page; Kai's phone dims. CUT TO BLACK", []),
]

# Points that must be inside the frame (checked by projection through each shot's lens).
def _P(i):
    return (0.0, py(i), 2.29)
MUST = {
    1: ["P%d" % i for i in range(1, 13)] + ["NOOR", "SIGN", "DISPLAY"],
    7: ["P1", "NOOR", "NOOR_CHIN"], 9: ["P1", "P2", "NOOR", "NOOR_CHIN", "WALTER", "BEA"],
    11: ["P1", "NOOR"], 13: ["NOOR", "NOOR_CHIN"],
    16: ["P%d" % i for i in range(1, 13)] + ["KAI"], 18: ["P%d" % i for i in range(1, 13)] + ["KAI", "KAI_PHONE"],
    26: ["P2", "P3", "P4", "NOOR_STAND", "WRIST", "WALTER"],
    8: ["WALTER"], "8B": ["BEA"], 12: ["WALTER"], "12B": ["BEA"], 39: ["WALTER", "BEA"], 55: ["WALTER", "BEA"], 61: ["WALTER", "BEA"], 22: ["NEWSPAPER"], 23: ["NEWSPAPER"], 51: ["NOOR_PHONE_LAP"],
    15: ["BEA", "KAI"], 20: ["NOOR_AT_DOORS", "HANDLE", "DOORS"], 62: ["NOOR_PLATFORM"], 24: ["NOOR_STAND"], 25: ["KAI_PHONE"],
    32: [], 33: ["BEA"], 44: ["KAI_PHONE"], 60: ["NOOR_UP"], 61: ["WALTER", "BEA"], 22: ["NEWSPAPER"], 23: ["NEWSPAPER"], 51: ["NOOR_PHONE_LAP"], 6: ["NOOR", "NOOR_CHIN"], 38: ["WALTER"], 53: ["WALTER"], 34: ["BEA"], 36: ["BEA"],
    50: ["P1", "P2", "NOOR", "DISPLAY"],
    54: ["NOOR_CHIN", "NOOR_CROWN"], 58: ["NOOR_CHIN", "NOOR_CROWN"],
    57: ["P%d" % i for i in range(1, 13)] + ["KAI_PHONE"],
    63: ["P%d" % i for i in range(1, 13)] + ["SIGN", "DISPLAY", "WALTER", "KAI_PHONE"],
}

def frame_xy(cam, aim, f, p):
    def sub(a, b): return [a[i] - b[i] for i in range(3)]
    def dot(a, b): return sum(a[i] * b[i] for i in range(3))
    def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    def norm(a):
        n = dot(a, a) ** 0.5
        return [v / n for v in a]
    fw = norm(sub(aim, cam)); r = norm(cross(fw, [0, 0, 1])); u = cross(r, fw)
    d = sub(p, cam); z = dot(d, fw)
    if z <= 0:
        return None
    return (f * dot(d, r) / z / (SENSOR["width_mm"] / 2), f * dot(d, u) / z / (SENSOR["height_mm"] / 2))

def apply_clock():
    """Move everything written on the original clock to the current clock (see TRIMS)."""
    global EVENTS, S, DIALOGUE, DIALOGUE_SOURCE
    for c in C:
        c["t"] = M(c["t"])
        if "recover" in c:
            c["recover"]["t"] = M(c["recover"]["t"])
    EVENTS = [(i, M(t), w) for i, t, w in EVENTS]
    S = [(r[0], M(r[1]), M(r[2])) + tuple(r[3:]) for r in S]
    S = [r for r in S if r[2] > r[1]]
    # The Screenwriter's voice placement is anchored to these cues. If it is still on the original
    # clock (NOOR-02 ends 0.25 s before the ORIGINAL cue 1 at 80.0), map it; once they rebuild, it isn't.
    lie1 = [d for d in DIALOGUE if str(d[3]).startswith("NOOR-02")]
    if lie1 and abs(lie1[0][1] - 79.75) < 0.05:
        DIALOGUE = [(M(a), M(b), w, l) for a, b, w, l in DIALOGUE]
        DIALOGUE_SOURCE += " (mapped from the original clock)"

def blocking_on_current_clock(segs):
    """The TA's blocking is on the original clock while Noor boards at 25.0 s; map it if so."""
    if segs and abs(segs[0]["t"][0] - 25.0) < 0.01:
        return [dict(g, t=[M(g["t"][0]), M(g["t"][1])]) for g in segs]
    return segs

def build():
    apply_clock()
    times = {c["id"]: c["t"] for c in C}
    ev = {e[0]: e[1] for e in EVENTS}
    awake = (times["1"], times["8.10"])
    problems = []
    # continuity of the cut
    for a, b in zip(S, S[1:]):
        if abs(a[2] - b[1]) > 1e-6:
            problems.append("gap/overlap between shots %s and %s" % (a[0], b[0]))
    if S[-1][2] != ev["cut"]:
        problems.append("last shot doesn't end on the cut")
    # every cue inside its declared shot, and no cut within 0.5 s of a cue
    where = {}
    for s in S:
        for cid in s[9]:
            where[cid] = s[0]
            if not (s[1] + 0.5 <= times[cid] <= s[2] - 0.5):
                problems.append("cue %s not safely inside shot %s" % (cid, s[0]))
    for c in C:
        if c["id"] not in where:
            problems.append("cue %s is not assigned to a shot" % c["id"])
        for s in S:
            for edge in (s[1], s[2]):
                if 0 < edge < ev["cut"] and abs(edge - c["t"]) < 0.5:
                    problems.append("cut at %.1f within 0.5 s of cue %s" % (edge, c["id"]))
    # no cut inside the blackout
    for s in S:
        if times["4"] < s[1] < times["4.up"]:
            problems.append("cut inside the blackout")
    # Advance: steady, >= 8 s, never accelerating
    outs = [c["t"] for c in C if c["type"] == "panel_out"]
    gaps = [round(b - a, 3) for a, b in zip(outs, outs[1:])]
    if min(gaps) < 8.0 or len(set(gaps)) != 1:
        problems.append("Advance ticks must be steady and >= 8 s apart: %s" % gaps)
    # Advance ticks and relights never land inside a line (they follow lines; Director)
    for c in C:
        if c["type"] in ("panel_out", "relight"):
            for a_, b_, who, line in DIALOGUE:
                if a_ - 0.2 < c["t"] < b_ + 0.2:
                    problems.append("cue %s at %.1f lands on a line (%s: %s)" % (c["id"], c["t"], who, line[:30]))
    # the 75 mm only in the confession, camera moves only while awake
    for s in S:
        if s[4] == 75 and s[7] != 7:
            problems.append("75 mm outside the confession (shot %s)" % s[0])
        if s[6] not in ("locked", "still (the push has landed)") and not (awake[0] <= s[1] and s[2] <= awake[1]):
            problems.append("camera moves while the car is asleep (shot %s)" % s[0])
    for s_ in S:
        n, pos, lens, aim = s_[0], s_[3], s_[4], s_[5]
        cam = POS.get(pos, {})
        if n not in MUST or "loc" not in cam:
            continue
        aim_pt = HEAD[aim] if aim else cam["aim"]
        for lab in MUST[n]:
            pt = _P(int(lab[1:])) if lab[0] == "P" and lab[1:].isdigit() else HEAD[lab]
            q = frame_xy(cam["loc"], aim_pt, lens, pt)
            if not q or abs(q[0]) > 0.95 or abs(q[1]) > 0.95:
                problems.append("shot %s: %s falls outside the frame (%s)" % (n, lab, q and "%.2f, %.2f" % q))
    # In the panel-row shots, every panel a cue changes must be in frame AT THE CUE'S TIME
    # (moving shots are evaluated along their path).
    cue_by_id = {c["id"]: c for c in C}
    for s_ in S:
        n, a_, b_, pos, lens, aim = s_[0], s_[1], s_[2], s_[3], s_[4], s_[5]
        if pos not in ("A", "A2", "W", "W7", "T"):
            continue
        cam = POS[pos]; aim_pt = HEAD[aim] if aim else cam["aim"]
        for cid in s_[9]:
            c = cue_by_id[cid]
            if c["type"] in ("brownout", "blackout", "lights_up"):
                continue
            loc = cam["loc"]
            if n in PATHS:
                u = (c["t"] - a_) / (b_ - a_)
                f0, f1 = PATHS[n]
                loc = tuple(f0[i] + (f1[i] - f0[i]) * u for i in range(3))
            for pnl in [c.get("main")] + c["panels"] if c.get("main") else c["panels"]:
                q = frame_xy(loc, aim_pt, lens, _P(int(pnl[1:])))
                if not q or abs(q[0]) > 0.95 or abs(q[1]) > 0.95:
                    problems.append("shot %s: cue %s's panel %s is out of frame at %.1f s (%s)" % (n, cid, pnl, c["t"], q and "%.2f, %.2f" % q))
    # Occlusion: no seated cast member (Walter, Bea; Kai until cue 4) may stand between the camera and the
    # shot's subject. Bodies are vertical capsules (radius 0.28 m, floor to head) at their seats.
    BODIES = {"WALTER": (-1.0, py(3), 1.35), "BEA": (1.0, py(3), 1.35), "KAI": (1.05, py(8), 1.35)}
    BLK = os.path.join(HERE, "..", "cg", "data", "blocking.json")
    noor_segs = blocking_on_current_clock(json.load(open(BLK))["NOOR"]) if os.path.exists(BLK) else []
    def noor_at(t):
        for g in noor_segs:
            if g["t"][0] <= t < g["t"][1]:
                if g["kind"] == "seat":
                    return (0.0, 12.75, 1.35)
                if g["kind"] == "stand":
                    return (g["at"][0], g["at"][1], 1.75) if not g.get("platform") else None
                u = (t - g["t"][0]) / (g["t"][1] - g["t"][0])
                return (g["from"][0] + (g["to"][0] - g["from"][0]) * u, g["from"][1] + (g["to"][1] - g["from"][1]) * u, 1.75)
        return None
    for s_ in S:
        n, a_, pos, aim = s_[0], s_[1], s_[3], s_[5]
        cam = POS.get(pos, {})
        loc = INSERTS[n][0] if n in INSERTS else cam.get("loc")
        aim_key = INSERTS[n][1] if n in INSERTS else aim
        aim_pt = HEAD[aim_key] if aim_key else cam.get("aim")
        if not loc or not aim_pt:
            continue
        mid = (s_[1] + s_[2]) / 2.0
        bodies = dict(BODIES)
        nb = noor_at(mid)
        NOOR_SUBJECT = {"A", "A2", "W", "W7", "T", "G2", "C75", "R", "B2"}   # positions framed on Noor
        if nb and pos not in NOOR_SUBJECT and not (aim_key and aim_key.startswith("NOOR")) \
                and ((loc[0] - nb[0]) ** 2 + (loc[1] - nb[1]) ** 2) ** 0.5 > 0.45:   # not a POV from her own head
            bodies["NOOR"] = nb
        for who, (bx, by, bh) in bodies.items():
            if aim_key and aim_key.startswith(who):
                continue
            if who == "KAI" and a_ >= 155.0:
                continue
            for k in range(1, 20):
                u = k / 20.0
                px, py_, pz = (loc[i] + (aim_pt[i] - loc[i]) * u for i in range(3))
                if pz <= bh and ((px - bx) ** 2 + (py_ - by) ** 2) ** 0.5 < 0.28:
                    problems.append("shot %s: %s blocks the line to the subject" % (n, who)); break
    if problems:
        raise SystemExit("CHECKS FAILED:\n  " + "\n  ".join(problems))

    shots = []
    for n, a, b, pos, lens, aim, move, scene, beat, cues_in in S:
        cam = dict(POS.get(pos, {}))
        if n in INSERTS:
            cam["loc"], aim = INSERTS[n]
        aim_pt = HEAD[aim] if aim else cam.get("aim")
        if not cam.get("loc") or not aim_pt:
            raise SystemExit("shot %s has no camera location or aim" % n)
        path = PATHS.get(n)
        shots.append({"shot": n, "in": a, "out": b, "frames": [round(a * FPS), round(b * FPS)],
                      "path": {"from": path[0], "to": path[1]} if path else None,
                      "scene": scene, "pos": pos, "lens_mm": lens, "move": move,
                      "camera_loc": cam.get("loc"), "aim": aim_pt, "aim_subject": aim,
                      "handheld": HANDHELD.get(n), "cues": cues_in, "beat": beat})
    doc = {
        "_note": "Shared sync file for THE QUIET CAR previs. Written by camera/build_cues.py (DP); do not edit by hand. Times are seconds from the first frame; re-time in build_cues.py when the voice record exists.",
        "fps": FPS, "duration_s": M(570.0), "clock": CLOCK,
        "set": {"units": "m", "axes": "Blender: Z up; Y down the car from end wall B (0) to end wall A (13, Noor); side A = -X, side B = +X",
                "length": LEN, "half_width": HALF, "ceiling": CEIL, "vestibule_y": [-4.0, 0.0],
                "doors": {"side": "B", "y": [round(py(7) - 0.55, 3), round(py(6) + 0.55, 3)]},
                "seats": {"NOOR": "transverse seat against end wall A, under P1, facing down the car",
                          "WALTER": "side A bench under P3", "BEA": "side B bench under P3",
                          "KAI": "side B bench under P8, by the doors"},
                "marks": {k: v for k, v in HEAD.items()}},
        "panels": [{"id": "P%d" % i, "y": py(i), "size_m": [0.64, 0.6], "partial": PARTIAL[i],
                    "dmx_legacy": [4 * (i - 1) + 1, 4 * i]} for i in range(1, 13)],
        "looks": LOOKS, "breath": BREATH,
        "lights_on_ones": True,
        "cues": [{k: v for k, v in c.items()} for c in C],
        "events": [{"id": e[0], "t": e[1], "what": e[2]} for e in EVENTS],
        "dialogue_note": "source: " + DIALOGUE_SOURCE + ". build_cues.py checks that no Advance tick or relight lands on a line",
        "dialogue": [{"in": a_, "out": b_, "who": w_, "line": l_} for a_, b_, w_, l_ in DIALOGUE],
        "camera": {"sensor": SENSOR, "positions": POS},
        "shots": shots,
    }
    with open(os.path.join(HERE, "cues.json"), "w") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)

    def tc(x):
        return "%d:%04.1f" % (int(x // 60), x % 60)
    L = ["# THE QUIET CAR: Animatic Cut Timeline", "",
         "**Generated by `camera/build_cues.py` from the same data as `camera/cues.json`. Don't edit by hand.** "
         "Times are estimates for a ~9:25 cut, to be re-timed to the voice record. "
         "Positions and cue numbers: `camera/lighting-plan.md`. Boards: `camera/storyboards/index.html`.", "",
         "Checks passed on build: the cut is continuous; every cue sits at least 0.5 s inside a held shot "
         "(cut on behaviour, never on cues); no cut inside the blackout; the Advance ticks are steady at "
         "%.1f s (rule: 8 s or more, never accelerating); the 75 mm is used only in the confession; and the "
         "camera moves only while the car is awake; no Advance tick or relight lands on a line of dialogue; and in the key shots every panel, face and prop that must read is inside the frame (projected through the lens)." % gaps[0], "",
         ]
    SCENES = {1: "Boarding (11:00)", 2: "The call: Noor's lies (11:00 → ~10:00)", 3: "Kai (~10:00 → ~9:00)",
              4: "The note and the test (~9:00 → 8:00)", 5: "The truth exchange (8:00 → 5:00)",
              6: "The creeping dark (5:00 → 2:00)", 7: "The confession (2:00 → arrival)", 8: "Holloway (arrival → end)"}
    for sc in range(1, 9):
        ss = [s for s in shots if s["scene"] == sc]
        L += ["", "## Scene %d: %s · %s–%s · %d shots" % (sc, SCENES[sc], tc(ss[0]["in"]), tc(ss[-1]["out"]), len(ss)), "",
              "| # | In | Out | Pos | Lens | Move | Cues | Beat |", "|---|---|---|---|---|---|---|---|"]
        for s in ss:
            L.append("| %s | %s | %s | %s | %d | %s | %s | %s |" % (s["shot"], tc(s["in"]), tc(s["out"]), s["pos"],
                     s["lens_mm"], s["move"], ", ".join(s["cues"]) or "—", s["beat"].replace("|", "/")))
    L += ["", "**Cut to black at %s; rails stop at %s; the title and credits are silent.**" % (tc(ev["cut"]), tc(ev["rails_stop"])), ""]
    with open(os.path.join(HERE, "cut-timeline.md"), "w") as fh:
        fh.write("\n".join(L))
    print("OK: %d cues, %d shots, Advance gap %.1f s, cut at %s" % (len(C), len(shots), gaps[0], tc(ev["cut"])))


# ---- export for the TA's cue driver (film/cg/lib/cue_driver.py schema and axes) ------
def to_ta(pt):
    """DP set coords -> TA axes: +X from Noor's end (0) toward the far end, +Y = side A
    (right-hand side looking down +X), Z up."""
    if pt is None:
        return None
    # The TA adopted the DP axes (Y from wall B = 0 to wall A = 13, side A = -X), so this is now identity.
    return [round(v, 3) for v in pt]

def export_cg(shots):
    F = 1.0 / FPS
    def keys(shape, lag=0):
        out = []
        for fr, lv in shape:
            lv = LOOKS[lv]["level"] if isinstance(lv, str) else lv
            out.append([round((fr + lag) * F, 4), lv, "const"])
        return out
    kind = {"tick": "lie", "flicker": "lie", "brownout": "lie", "blackout": "lie", "lights_up": "return",
            "hard_dip": "lie", "stutter": "lie", "panel_out": "advance", "steady": "truth", "relight": "truth"}
    cues = []
    for c in C:
        ev = []
        if c["type"] == "brownout":
            ev.append({"target": "ALL", "keys": [[0.0, 1.0, "smooth"], [round(8 * F, 4), 0.18, "smooth"]],
                       "kelvin": 2200, "kelvin_fade_s": round(8 * F, 4)})
        elif c["type"] == "blackout":
            ev += [{"target": t, "keys": [[0.0, 0.0, "const"]]} for t in
                   ("ALL", "DISPLAY", "WINDOWS", "PHONE_KAI", "PHONE_NOOR", "DOOR_LIGHT")]
        elif c["type"] == "lights_up":
            ev += [{"target": "ALL", "keys": [[0.0, 1.0, "const"]], "kelvin": 4300},
                   {"target": "DISPLAY", "keys": [[0.0, 1.0, "const"]]},
                   {"target": "PHONE_KAI", "keys": [[0.0, 1.0, "const"]]}]
        elif c["type"] == "hard_dip":
            r = c["recover"]; t0 = r["t"] - c["t"]; t1 = t0 + r["frames"] * F
            ev.append({"target": c["main"], "keys": [[0.0, 1.0, "const"], [round(2 * F, 4), 0.05, "const"],
                                                      [round(t0, 4), 0.05, "smooth"], [round(t1, 4), 1.0, "smooth"]]})
            for p_, lv in c["sympathy"].items():
                ev.append({"target": p_, "keys": [[0.0, 1.0, "const"], [round(2 * F, 4), lv, "const"],
                                                   [round(t0, 4), lv, "smooth"], [round(t1, 4), 1.0, "smooth"]]})
        elif c["type"] == "steady":
            ev.append({"target": "P1", "breath": 0, "keys": [[0.0, 1.1, "const"]]})
        elif c["type"] == "relight":
            ev.append({"target": c["panels"][0], "keys": [[0.0, 1.1, "const"], [round(12 * F, 4), 1.0, "smooth"]]})
            if c["id"] == "8.10":
                ev.append({"target": "P1", "keys": [[0.0, 1.0, "const"]]})
        else:
            lag = c.get("lag_frames", {})
            for p_ in c["panels"]:
                ev.append({"target": p_, "keys": keys(c["shape"], lag.get(p_, 0))})
            if c["id"] == "1":
                ev.append({"target": "WINDOWS", "keys": [[0.0, 0.0, "const"]]})
        item = {"id": c["id"], "tc": c["t"], "label": c["type"], "line": c["line"], "kind": kind[c["type"]], "events": ev}
        if c.get("breath") == "on":
            item["awake"] = 1
        if c.get("breath") == "off":
            item["awake"] = 0
        if c.get("note"):
            item["_note"] = c["note"]
        cues.append(item)
    ev_t = {e[0]: e[1] for e in EVENTS}
    def prac(id, t, label, events):
        cues.append({"id": id, "tc": t, "label": label, "line": "", "kind": "practical", "events": events})
    prac("DOORS_CLOSE", ev_t["doors_close"], "doors close, pull away: platform falls behind, passing lights in the glass",
         [{"target": "PLATFORM", "keys": [[0.0, 1.0, "linear"], [6.0, 0.0, "linear"]]},
          {"target": "WINDOWS", "keys": [[2.0, 0.0, "linear"], [6.0, 1.0, "linear"]]}])
    prac("PHONE_NOOR_ON", ev_t["mark_call_1"], "MARK calls", [{"target": "PHONE_NOOR", "keys": [[0.0, 1.0, "const"]]}])
    prac("PHONE_NOOR_OFF", ev_t["love_you"] + 2.0, "she hangs up", [{"target": "PHONE_NOOR", "keys": [[0.0, 1.0, "linear"], [1.0, 0.0, "linear"]]}])
    prac("PHONE_NOOR_MARK", ev_t["marks_call"], "MARK calls again: her screen becomes a key", [{"target": "PHONE_NOOR", "keys": [[0.0, 1.0, "const"]]}])
    prac("ARRIVAL", ev_t["doors_open"], "doors open: platform lamp, door light",
         [{"target": "PLATFORM", "keys": [[0.0, 1.0, "const"]]}, {"target": "DOOR_LIGHT", "keys": [[0.0, 1.0, "const"]]}])
    prac("DOORS_CLOSE_FINAL", ev_t["doors_close_final"], "doors close", [{"target": "DOOR_LIGHT", "keys": [[0.0, 0.0, "const"]]}])
    prac("PULL_AWAY", ev_t["pull_away"], "the platform slides away in the door glass; WINDOWS stay OFF (Director)",
         [{"target": "PLATFORM", "keys": [[0.0, 1.0, "linear"], [8.0, 0.0, "linear"]]}])
    prac("PHONE_KAI_DIMS", ev_t["phone_dims"], "Kai's phone fades to black", [{"target": "PHONE_KAI", "keys": [[0.0, 1.0, "linear"], [2.0, 0.0, "linear"]]}])
    cues.sort(key=lambda c: c["tc"])
    doc = {
        "_doc": ["GENERATED by camera/build_cues.py (DP) from the approved lighting plan, in the schema of film/cg/lib/cue_driver.py. Do not edit by hand: ask the DP to change build_cues.py and re-run.",
                 "Same cue ids and times as camera/cues.json (which the Composer's temp score reads), so lights and music cannot drift.",
                 "Camera locations in 'shots' use the shared DP axes (Z up; Y from end wall B = 0 to end wall A = 13; side A = -X), the same as camera/cues.json."],
        "fps": FPS, "duration_s": 570.0,
        "baseline": {"kelvin": 4300, "green_tint": 0.06, "level": 1.0},
        "sodium": {"kelvin": 2200, "green_tint": 0.0},
        "platform": {"kelvin": 5000, "_note": "cold white, mercury-vapour look; orange is reserved for the car being awake"},
        "breathing": {"depth": BREATH["depth"], "period_s": BREATH["period_s"], "_note": "provisional until look-dev check L3"},
        "initial": {"ALL": {"level": 1.0, "breath": 1}, "DISPLAY": {"level": 1.0}, "WINDOWS": {"level": 0.0},
                    "PLATFORM": {"level": 1.0}, "PHONE_NOOR": {"level": 0.0}, "PHONE_KAI": {"level": 1.0},
                    "DOOR_LIGHT": {"level": 0.0}, "awake": 0},
        "cues": cues,
        "shots": [{"shot": s["shot"], "in": s["in"], "out": s["out"], "lens_mm": s["lens_mm"], "move": s["move"],
                   "loc": to_ta(s["camera_loc"]), "look_at": to_ta(s["aim"]), "pos": s["pos"]} for s in shots],
    }
    with open(os.path.join(HERE, "cue-stack.cg.json"), "w") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)

if __name__ == "__main__":
    build()
