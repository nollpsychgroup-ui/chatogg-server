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
       ("7.9", 428.0, "P4", "after NOOR: \"I can't —\""),
       ("7.10", 436.5, "P3", "after BEA: \"Say it.\" (two panels left; Walter and Bea go into the edge)")]
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
    ("lanyard", 40.0, "Noor straightens the lanyard (cue 0)"),
    ("doors_close", 48.0, "doors close; WINDOWS chase on (glass only, while asleep)"),
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
    ("train_slows", 512.0, "DISPLAY: NOW ARRIVING: HOLLOWAY"),
    ("arrival_chime", 520.0, "door chime"),
    ("doors_open", 521.0, "doors open; PLATFORM lamp on (cold white ~5000 K, slight green)"),
    ("doors_close_final", 535.0, "doors close"),
    ("pa_line", 538.0, "PA: 'Thank you for riding quietly.' (no light cue)"),
    ("pull_away", 540.0, "platform + lamp slide away in the door glass; WINDOWS stay black"),
    ("page_turn", 552.0, "Walter turns the page (no light change)"),
    ("phone_dims", 561.0, "Kai's phone screen fades to black over 2 s"),
    ("cut", 565.0, "CUT TO BLACK"),
    ("rails_stop", 568.0, "rails stop over black"),
]

# ---- virtual cameras -------------------------------------------------------------
HEAD = {"NOOR": (0.0, 12.75, 1.22), "NOOR_STAND": (-0.35, 10.0, 1.62), "WALTER": (-1.0, py(3), 1.22),
        "BEA": (1.0, py(3), 1.22), "KAI": (1.05, py(8), 1.22), "KAI_PHONE": (1.05, py(8), 0.48),
        "DOORS": (1.4, 6.5, 1.2), "DISPLAY": (0.0, 13.0, 1.82)}
POS = {
    "A":  {"loc": (0.0, -3.5, 1.65), "aim": (0.0, 13.0, 1.65), "lens": 32,
           "note": "the Meter: in the unlit vestibule, standing eye height, level. Holds all 12 panels, Noor, the sign and the display"},
    "A2": {"loc": (0.0, -1.0, 1.65), "aim": (0.0, 13.0, 1.65), "lens": 32,
           "note": "where the creep push lands (2.5 m in from A)"},
    "B":  {"loc": (0.55, 12.85, 1.0), "aim": (0.3, 0.0, 1.0), "lens": 32,
           "note": "Noor's end, side B corner, low, looking down the car"},
    "C":  {"loc": (-0.95, 9.6, 1.15), "lens": 50, "note": "side A beside Walter: Noor singles (aim NOOR) or Bea across the aisle (aim BEA)"},
    "C75": {"loc": (-0.4, 9.4, 1.2), "lens": 75,
            "note": "the confession: near Noor's line of sight down the car, so the panel row reflects in her corneas and reads at 75 mm (dp-notes-02). Her eyeline passes just camera-right of the lens, down the car"},
    "D":  {"loc": (0.95, 9.6, 1.15), "lens": 50, "note": "side B beside Bea: Noor singles or Walter across the aisle"},
    "E":  {"loc": (-1.0, 12.6, 1.15), "aim": (0.0, py(3), 1.2), "lens": 40, "note": "side A corner at end A: Walter/Bea two-shots, deep staging"},
    "F":  {"loc": (-0.95, py(8), 1.15), "lens": 40, "note": "across the aisle from Kai"},
    "G":  {"loc": (-0.9, 6.5, 1.3), "aim": HEAD["DOORS"], "lens": 32, "note": "facing the doors"},
    "I":  {"note": "inserts: placement per shot"},
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
 (7, 78.0, 86.0, "C", 40, "NOOR", "locked", 2, "'Just leaving the office now.' The ceiling enters: P1 in the top of frame", ["1"]),
 (8, 86.0, 91.0, "E", 40, None, "locked", 2, "Walter's eyes lift; Bea's eyes open", []),
 (9, 91.0, 101.0, "C", 40, "NOOR", "locked", 2, "'The Henley account. Again.' P1 and P2 both in frame", ["2"]),
 (10, 101.0, 108.0, "A", 32, None, "locked", 2, "The whole car reacts: paper lowers, Bea sits up, Kai: 'Was that the brakes?'", []),
 (11, 108.0, 116.0, "C", 40, "NOOR", "locked", 2, "'No, don't wait up. Love you.' Hangs up, sags, looks up", []),
 (12, 116.0, 120.0, "B", 40, "BEA", "locked", 2, "Walter and Bea staring at her", []),
 (13, 120.0, 130.0, "D", 40, "NOOR", "locked", 2, "Mouths 'Sorry', points over her shoulder at the sign", []),
 (14, 130.0, 138.0, "F", 40, "KAI", "locked", 3, "Kai's phone: MUM. 'Yeah?'", []),
 (15, 138.0, 143.0, "E", 32, "KAI", "locked", 3, "Bea's hand shoots out, too far away", []),
 (16, 143.0, 147.0, "A", 32, None, "locked", 3, "'I'm at the library, Mum.' Brownout", ["3"]),
 (17, 147.0, 153.5, "F", 50, "KAI", "locked", 3, "Kai in the brownout: looks up, nervous laugh", []),
 (18, 153.5, 166.0, "A", 32, None, "locked", 3, "'They're doing work on the —' BLACKOUT. Inhale. Lights up: the seat is empty. 'Kai? ... Kai?'", ["4", "4.up"]),
 (19, 166.0, 170.0, "I", 50, "KAI_PHONE", "locked", 3, "Kai's phone face-up, call connected", []),
 (20, 170.0, 180.0, "G", 32, "DOORS", "handheld", 4, "Noor at the doors, the emergency handle. 'Hey. Hey!' (recorded operator motion)", []),
 (21, 180.0, 186.0, "D", 50, "WALTER", "locked", 4, "Walter writes in the margin and holds it up", []),
 (22, 186.0, 190.0, "I", 50, None, "locked", 4, "DON'T LIE IN HERE.", []),
 (23, 190.0, 200.0, "I", 50, None, "locked", 4, "Bea writes underneath: IT'S AWAKE NOW. YOU WOKE IT.", []),
 (24, 200.0, 210.0, "C", 50, "NOOR_STAND", "locked", 4, "Noor reads it twice; eyes to Kai's seat. 'That's insane.'", []),
 (25, 210.0, 213.0, "B", 50, "KAI_PHONE", "locked", 4, "Kai's empty seat, the phone", []),
 (26, 213.0, 234.0, "E", 40, "NOOR_STAND", "locked", 4, "Standing beside Walter under P3. 'My name is Noor.' Nothing. 'My name is S—' The wrist clamp. P3 near black, P2/P4 dip. Nobody breathes. Recovery", ["5"]),
 (27, 234.0, 236.0, "D", 50, "NOOR_STAND", "locked", 4, "He releases her. She's shaking", []),
 (28, 236.0, 239.0, "I", 50, "DISPLAY", "locked", 4, "Display: 8 MIN", []),
 (29, 239.0, 252.0, "A", 32, None, "locked", 5, "She sits back down slowly (the walk to P1). Long beat of rails", []),
 (30, 252.0, 256.0, "I", 50, "KAI_PHONE", "locked", 5, "Kai's phone, still lit: 'Kai?'", []),
 (31, 256.0, 262.0, "B", 32, "KAI_PHONE", "locked", 5, "She walks down the car to Kai's seat", []),
 (32, 262.0, 272.0, "F", 40, "KAI_PHONE", "locked", 5, "Her thumb over the red end-call button. She can't", []),
 (33, 272.0, 282.0, "E", 40, None, "locked", 5, "She goes back to her seat; Bea watches the whole time", []),
 (34, 282.0, 290.0, "C", 50, "BEA", "locked", 5, "Bea: 'You okay?'", []),
 (35, 290.0, 300.0, "D", 50, "NOOR", "locked", 5, "'I'm f—' (stutter) ... 'I'm not fine.'", ["6"]),
 (36, 300.0, 309.0, "C", 50, "BEA", "locked", 5, "'Me neither. I haven't slept in two days.' Nothing happens", []),
 (37, 309.0, 313.0, "D", 50, "NOOR", "locked", 5, "'You've seen this before.'", []),
 (38, 313.0, 344.0, "D", 50, "WALTER", "locked", 5, "Walter: 'I ride it every night.' ... the wife speech, one unbroken shot", []),
 (39, 344.0, 349.0, "E", 40, None, "locked", 5, "Bea looks at him with real tenderness", []),
 (40, 349.0, 355.0, "C", 50, "NOOR", "locked", 5, "Noor turns the badge over in her fingers", []),
 (41, 355.0, 358.5, "I", 50, "DISPLAY", "locked", 6, "Display: 5 MIN", []),
 (42, 358.5, 380.0, "A", 32, None, "push A->A2", 6, "Tick: the far panel out. Bea stiffens. 'Nobody said anything.' Walter's eyes to the lanyard. The camera rides in behind the dark edge", ["7.1", "7.2", "7.3"]),
 (43, 380.0, 384.5, "C", 50, "BEA", "locked", 6, "Bea: 'It isn't only what you say.'", []),
 (44, 384.5, 398.0, "B", 32, None, "locked", 6, "The dark comes toward camera; Kai's seat goes dark, his phone glows on in it", ["7.4", "7.5"]),
 (45, 398.0, 405.5, "C", 50, "NOOR", "locked", 6, "She looks down at herself; yanks the lanyard over her head and throws it (each tick takes a step of front light off her face)", ["7.6"]),
 (46, 405.5, 408.5, "I", 50, None, "locked", 6, "The lanyard on the floor: red on grey", []),
 (47, 408.5, 416.0, "C", 50, "NOOR", "locked", 6, "It isn't enough", ["7.7"]),
 (48, 416.0, 432.0, "D", 50, "NOOR", "locked", 6, "Bea (off): 'Whatever it is, say it.' Noor: 'I can't —'", ["7.8", "7.9"]),
 (49, 432.0, 440.0, "C", 50, "BEA", "locked", 6, "'Say it.' On the last tick Bea's light dies to an edge", ["7.10"]),
 (50, 440.0, 445.0, "A2", 32, None, "locked", 6, "Two panels left; Noor in the last pool; display 2 MIN; her phone buzzes", []),
 (51, 445.0, 448.0, "I", 50, None, "locked", 6, "MARK, in her lap", []),
 (52, 448.0, 451.0, "C", 50, "NOOR", "locked", 6, "She looks across at Kai's phone glowing in the dark", []),
 (53, 451.0, 455.5, "D", 50, "WALTER", "locked", 6, "Walter, half-lit at the edge of the dark: 'He's asking.' His lit-side eye carries a readable catchlight (P2 or Noor's phone) and the lid line holds", []),
 (54, 455.5, 469.0, "C75", 75, "NOOR", "push", 7, "She answers. 'Mark.' ... 'I'm not leaving the office.' (P1 burns brighter)", ["8.0"]),
 (55, 469.0, 474.0, "E", 40, None, "locked", 7, "Walter and Bea come back into the light", ["8.1"]),
 (56, 474.0, 486.0, "C75", 75, "NOOR", "push", 7, "'I go to the library —' the half-beat, her eyes to Kai's phone — '— and I come home.'", ["8.2"]),
 (57, 486.0, 501.0, "A", 32, None, "locked", 7, "'I didn't tell you because —' the relights run toward us; Kai's empty seat relights", ["8.3", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9"]),
 (58, 501.0, 512.0, "C75", 75, "NOOR", "still (the push has landed)", 7, "'I'm sorry.' Silence on the line. The far panel comes on: P12's catchlight reappears in her eyes on the 8.10 frame, completing the reflected row. The car is asleep", ["8.10"]),
 (59, 512.0, 515.0, "I", 50, "DISPLAY", "locked", 8, "Display: NOW ARRIVING: HOLLOWAY", []),
 (60, 515.0, 519.0, "D", 40, "NOOR", "locked", 8, "The train slows; she stands and looks back at them", []),
 (61, 519.0, 523.0, "E", 40, None, "locked", 8, "Walter's smallest nod; Bea has closed her eyes", []),
 (62, 523.0, 550.0, "G", 32, "DOORS", "locked", 8, "Out under the cold-white lamp, phone to her ear. Doors close. PA. She slides away in the glass", []),
 (63, 550.0, 565.0, "A", 32, None, "locked", 8, "The opening frame again: Walter turns the page; Kai's phone dims. CUT TO BLACK", []),
]

def build():
    times = {c["id"]: c["t"] for c in C}
    ev = {e[0]: e[1] for e in EVENTS}
    awake = (times["1"], times["8.10"])
    problems = []
    # continuity of the cut
    for a, b in zip(S, S[1:]):
        if abs(a[2] - b[1]) > 1e-6:
            problems.append("gap/overlap between shots %d and %d" % (a[0], b[0]))
    if S[-1][2] != ev["cut"]:
        problems.append("last shot doesn't end on the cut")
    # every cue inside its declared shot, and no cut within 0.5 s of a cue
    where = {}
    for s in S:
        for cid in s[9]:
            where[cid] = s[0]
            if not (s[1] + 0.5 <= times[cid] <= s[2] - 0.5):
                problems.append("cue %s not safely inside shot %d" % (cid, s[0]))
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
    # the 75 mm only in the confession, camera moves only while awake
    for s in S:
        if s[4] == 75 and s[7] != 7:
            problems.append("75 mm outside the confession (shot %d)" % s[0])
        if s[6] not in ("locked", "still (the push has landed)") and not (awake[0] <= s[1] and s[2] <= awake[1]):
            problems.append("camera moves while the car is asleep (shot %d)" % s[0])
    if problems:
        raise SystemExit("CHECKS FAILED:\n  " + "\n  ".join(problems))

    shots = []
    for n, a, b, pos, lens, aim, move, scene, beat, cues_in in S:
        cam = dict(POS.get(pos, {}))
        aim_pt = HEAD[aim] if aim else cam.get("aim")
        shots.append({"shot": n, "in": a, "out": b, "frames": [round(a * FPS), round(b * FPS)],
                      "scene": scene, "pos": pos, "lens_mm": lens, "move": move,
                      "camera_loc": cam.get("loc"), "aim": aim_pt, "aim_subject": aim,
                      "cues": cues_in, "beat": beat})
    doc = {
        "_note": "Shared sync file for THE QUIET CAR previs. Written by camera/build_cues.py (DP); do not edit by hand. Times are seconds from the first frame; re-time in build_cues.py when the voice record exists.",
        "fps": FPS, "duration_s": 570.0,
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
        "camera": {"sensor": SENSOR, "positions": POS},
        "shots": shots,
    }
    with open(os.path.join(HERE, "cues.json"), "w") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
    export_cg(shots)

    def tc(x):
        return "%d:%04.1f" % (int(x // 60), x % 60)
    L = ["# THE QUIET CAR: Animatic Cut Timeline", "",
         "**Generated by `camera/build_cues.py` from the same data as `camera/cues.json`. Don't edit by hand.** "
         "Times are estimates for a ~9:25 cut, to be re-timed to the voice record. "
         "Positions and cue numbers: `camera/lighting-plan.md`. Boards: `camera/storyboards/index.html`.", "",
         "Checks passed on build: the cut is continuous; every cue sits at least 0.5 s inside a held shot "
         "(cut on behaviour, never on cues); no cut inside the blackout; the Advance ticks are steady at "
         "%.1f s (rule: 8 s or more, never accelerating); the 75 mm is used only in the confession; and the "
         "camera moves only while the car is awake." % gaps[0], "",
         ]
    SCENES = {1: "Boarding (11:00)", 2: "The call: Noor's lies (11:00 → ~10:00)", 3: "Kai (~10:00 → ~9:00)",
              4: "The note and the test (~9:00 → 8:00)", 5: "The truth exchange (8:00 → 5:00)",
              6: "The creeping dark (5:00 → 2:00)", 7: "The confession (2:00 → arrival)", 8: "Holloway (arrival → end)"}
    for sc in range(1, 9):
        ss = [s for s in shots if s["scene"] == sc]
        L += ["", "## Scene %d: %s · %s–%s · %d shots" % (sc, SCENES[sc], tc(ss[0]["in"]), tc(ss[-1]["out"]), len(ss)), "",
              "| # | In | Out | Pos | Lens | Move | Cues | Beat |", "|---|---|---|---|---|---|---|---|"]
        for s in ss:
            L.append("| %d | %s | %s | %s | %d | %s | %s | %s |" % (s["shot"], tc(s["in"]), tc(s["out"]), s["pos"],
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
    x, y, z = pt
    return [round(LEN - y, 3), round(-x, 3), z]

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
                 "Camera locations in 'shots' are converted to the TA axes (+X from Noor's end, +Y = side A, Z up) for the DP's 13 m set; see camera/lighting-plan.md section 1."],
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
