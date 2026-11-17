# Director's Notes: cg/ look-dev v2 (R1/R2)

I reviewed sf01, sf03, sf06 and sf08 at full size, plus the check report.

**Verdict: big step forward, with one more targeted pass on the paint before the M3 gate.**

## What's now right

- **The checks still all pass after the paint:** blackout 0, the strap, keys on ones, and bit-identical asleep frames. The paint lives in albedo and normals only, and the light is untouched. That's exactly the rule.
- **R2, sf06 exposure: approved.** The face is now the brightest thing in frame (0.53 vs 0.38) with no fill, and her eyes sit on the upper third.
- **Noor sculpted to her sheet, with the catchlight row in her eyes:** good. E1 stays PARTIAL until M4, as already ruled.
- **sf01 reads as painted** for the first time. The seats, floor and ceiling now carry visible brushwork at the Meter distance.
- **Taste call on the far, dark paint: keep it as it is.** Darks should merge into big quiet shapes (style guide §5). Don't raise the painted-board strength.

## R3: make the dabs read as brushstrokes, not camouflage

At close range (sf06, and the costumes everywhere) the dabs read as **cellular patches (Voronoi/camouflage)**, and the figures read as **faceted low-poly**. That pulls toward "video-game texture" rather than "painting", which is the opposite of what the human asked for. It's worst on the **end wall behind Noor in sf06**: large, high-contrast blotches compete with her face in the film's most important shot. Three fixes:

1. **Elongate and orient the dabs.** Strokes should be roughly **3:1 to 5:1 in aspect**, aligned to a direction field that follows the form (style guide §3): along the sleeve, down the blazer front, lengthwise on the walls, across the cheek planes. Vary length and width a little. Real brush marks are directional; cells aren't.
2. **Calm the large flat planes.** On big surfaces (walls, ceiling, seat backs), reduce the value spread between adjacent dabs. The 4 steps should be **close in value** (subtle), with stronger separation only near the terminator and on form changes. The end wall in sf06 should read as a quiet painted field behind her, not a pattern.
3. **Smooth the figure geometry.** Lose the visible faceting on bodies and costume (subdivide or shade smooth). Simplification should come from **painted planes and fold shapes**, not from polygon edges. Keep the hard planes the Designer specified (blazer shoulders, the jaw/cheek wedge), but as designed shapes, not tessellation.

Re-render **sf01, sf06 and sf08** at least, re-run the checks, and update the contact sheet. Once R3 lands, I'll approve and send M3 to the Producer.
