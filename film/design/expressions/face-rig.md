# Face rig controls: THE QUIET CAR

**Character Designer** · v1 · used by the expression sheets (`*-expressions.svg`) and intended as the shape-key / bone list for the TA's face rigs.

The four faces share **one control set**. Every expression on the sheets is just a set of values for these controls, printed under each drawing as "RIG VALUES". The drawings are generated from those numbers (`tools/face.py`), so sheet and rig can't drift apart.

## Controls

| Control | Range | What it does | Why the film needs it |
|---|---|---|---|
| `lid_up` (L/R) | 0 closed → 1 wide | Upper lid height | The most important control. Bea's closed-but-awake eyes, Walter's heavy neutral, Noor's lids "stopping holding" |
| `lid_low` (L/R) | 0 → 1 | Lower lid / cheek raise | Separates a real smile (Walter's end of speech) from a performed one (Noor's "fine"). Also held tears |
| `tension` | 0 → 1 | Lid squeeze while closed, outer-corner crease | **Awake vs. asleep** for Bea |
| `brow_in` (L/R) | -1 knit → +1 up | Inner brow | Grief/worry (up), urgency (down) |
| `brow_out` (L/R) | -1 → +1 | Outer brow | With inner-up + outer-down = the grief brow |
| `smile` (L/R) | -1 → +1 | Mouth corners | Kai's lopsided half-smile, Noor's mouth-only smile |
| `press` | 0 → 1 | Lip press / thinning | Noor holding her voice steady while crying |
| `jaw` | 0 → 1 | Mouth open | Dialogue, "I'm f—" |
| `chin` | 0 → 1 | Mentalis: chin lift and pucker | Holding back tears (Noor), suppressed emotion (Walter's speech) |
| `naso` | 0 → 1 | Nasolabial fold depth | Age (Walter's neutral is 0.6) and real smiles |
| `gaze_x`, `gaze_y` | -1 → 1 | Eye direction (camera-left / up = -1) | The film's looks: Walter to the badge, Noor to Kai's phone, Kai to the ceiling |
| `tear` | 0/1 | Wet tear line + wet lower lid (gloss, not paint) | Confession only |
| `catch` | 0–3 | Panel catchlights drawn in the eye | **Not a rig control in Blender**: the real cornea reflects the real panels. Shown on the sheets as a reminder |

## Neutrals (each character's zero)

| | lid_up | naso | lid_low | Note |
|---|---|---|---|---|
| Noor | 0.82 | 0.20 | 0 | Alert, pleasant, "on" |
| Kai | 0.70 | 0.10 | 0 | Tired, easy |
| Bea | 0.70 | 0.35 | 0.10 | Tired lids, kind |
| Walter | 0.62 | 0.60 | 0 | Heavy-lidded, misses nothing |

## Acting range

Most of the film plays at **5–25% of each control**. The sheet values are peaks. Two rules for animators:

1. **Noor's lower lid stays at 0** in every "fine" smile until the confession. If it lifts, the smile becomes real and the tell is gone.
2. **Walter's lids only open fully once**, on the clamp. Save it.

## Asymmetry

Allowed and encouraged on brows and mouth corners (`_L` / `_R`). Kai is the most asymmetric (lopsided smile). Walter is the most symmetric (stillness).

## In 3D

`../rig/heads.py` implements these controls as custom properties on a head root, with drivers to lids, eyes, brows and lips. See `../rig/README.md`. In 3D, `_L` is the character's left; the 2D sheets draw `_L` on camera-left.
