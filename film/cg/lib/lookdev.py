"""Painterly look-dev: painted surfaces, physically real light.

Rules (Director / design/style-guide.md section 8 / camera/lighting-plan.md section 2):
- Only real emitters light the scene; no light is painted into any texture.
- Strokes are locked to object space and never move (no boil): asleep frames are identical.
- Albedo is broken into flat brush dabs (posterised paint, never posterised light).
- The terminator breaks up via a small stroke-shaped normal perturbation fixed to the surface.
- Compositor: anisotropic Kuwahara, a smaller kernel on faces and hands (Object Index mask),
  and a canvas tooth on the set only, MULTIPLIED, so true black stays exactly 0.
Colours come from design/palette.json (Character Designer).
"""
import bpy

from .common import pal

# stroke size tiers (world space): set ~4-6 cm, costume ~1.5-3 cm, faces/hands ~3-6 mm
TIER = {   # R3: elongated dabs (stretch 3-5:1), close values on planes, separation from the light at form turns
    "set":     dict(stroke_scale=20.0, stretch=4.5, variation=0.07, roughness=0.85, tilt=0.12, bristle=0.10, hue_jitter=0.015),
    "costume": dict(stroke_scale=40.0, stretch=4.0, variation=0.07, roughness=0.88, tilt=0.20, bristle=0.08, hue_jitter=0.015),
    "face":    dict(stroke_scale=160.0, stretch=3.0, variation=0.03, roughness=0.62, tilt=0.07, bristle=0.02, hue_jitter=0.01),
}
PASS_FACE, PASS_CHAR = 1, 2   # object pass_index for the compositor masks


def _paint_group():
    """PaintSurface v2: brush dabs locked to the surface.

    - Coordinates: object space x Axis Scale (strokes elongate along the stroke axis), warped by a
      low-frequency noise so stroke edges wobble like a loaded brush.
    - Two overlapping Voronoi layers = individual dabs; each dab gets one random value (quantised to
      4 painted steps), a small hue shift and its OWN NORMAL TILT. The tilt is what breaks the real
      terminator into brush shapes: near the light/shadow turn each dab flips lit/unlit on its own,
      in flat light it gives colour variation within a plane. Light itself is never quantised.
    - Bristle streaks along the stroke add brush texture inside each dab.
    Nothing depends on time, so asleep frames stay bit-identical (no boil).
    """
    ng = bpy.data.node_groups.get("PaintSurface")
    if ng:
        return ng
    ng = bpy.data.node_groups.new("PaintSurface", "ShaderNodeTree")
    iface = ng.interface
    iface.new_socket("Base Color", in_out="INPUT", socket_type="NodeSocketColor")
    sh = iface.new_socket("Shadow Color", in_out="INPUT", socket_type="NodeSocketColor")
    sh.default_value = (0.5, 0.5, 0.5, 1)
    ax = iface.new_socket("Axis Scale", in_out="INPUT", socket_type="NodeSocketVector")
    ax.default_value = (1.0, 0.25, 1.0)
    for nm, dv in (("Stroke Scale", 20.0), ("Stretch", 4.0), ("Variation", 0.2), ("Hue Jitter", 0.012),
                   ("Roughness", 0.85), ("Bump", 0.03), ("Metallic", 0.0), ("Seed", 0.0), ("Tilt", 0.25),
                   ("Bristle", 0.05), ("Shadow Mix", 0.0)):
        sk = iface.new_socket(nm, in_out="INPUT", socket_type="NodeSocketFloat")
        sk.default_value = dv
    iface.new_socket("BSDF", in_out="OUTPUT", socket_type="NodeSocketShader")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")

    def math(op, a, b=None, c=None):
        m = N.new("ShaderNodeMath"); m.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                L.new(v, m.inputs[i])
        return m.outputs[0]

    def vmath(op, a, b=None, scale=None):
        m = N.new("ShaderNodeVectorMath"); m.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, tuple):
                m.inputs[i].default_value = v
            else:
                L.new(v, m.inputs[i])
        if scale is not None:
            if isinstance(scale, (int, float)):
                m.inputs["Scale"].default_value = scale
            else:
                L.new(scale, m.inputs["Scale"])
        return m.outputs["Vector"] if op != "LENGTH" else m.outputs["Value"]

    tc = N.new("ShaderNodeTexCoord")
    p = vmath("MULTIPLY", tc.outputs["Object"], gi.outputs["Axis Scale"])
    # wobble: low-frequency warp, amplitude ~0.35 dab
    wn = N.new("ShaderNodeTexNoise"); wn.noise_dimensions = "3D"
    wn.inputs["Detail"].default_value = 1.0
    L.new(p, wn.inputs["Vector"])
    L.new(math("MULTIPLY", gi.outputs["Stroke Scale"], 0.35), wn.inputs["Scale"])
    wv = vmath("SUBTRACT", wn.outputs["Color"], (0.5, 0.5, 0.5))
    amp = math("DIVIDE", 1.1, gi.outputs["Stroke Scale"])
    pw = vmath("ADD", p, vmath("SCALE", wv, None, amp))

    def dabs(offset):
        v = N.new("ShaderNodeTexVoronoi"); v.voronoi_dimensions = "4D"; v.feature = "F1"
        v.inputs["Randomness"].default_value = 1.0
        L.new(vmath("ADD", pw, offset), v.inputs["Vector"])
        L.new(gi.outputs["Stroke Scale"], v.inputs["Scale"])
        L.new(gi.outputs["Seed"], v.inputs["W"])
        return v
    d1, d2 = dabs((0, 0, 0)), dabs((0.37, 0.61, 0.23))
    # which layer is on top: a mid-frequency mask
    mk = N.new("ShaderNodeTexNoise"); mk.inputs["Detail"].default_value = 0.0
    L.new(pw, mk.inputs["Vector"]); L.new(math("MULTIPLY", gi.outputs["Stroke Scale"], 0.8), mk.inputs["Scale"])
    top = math("GREATER_THAN", mk.outputs["Fac"], 0.5)
    mixc = N.new("ShaderNodeMix"); mixc.data_type = "RGBA"
    L.new(top, mixc.inputs["Factor"]); L.new(d1.outputs["Color"], mixc.inputs[6]); L.new(d2.outputs["Color"], mixc.inputs[7])
    rnd = mixc.outputs[2]                       # per-dab random RGB
    sep = N.new("ShaderNodeSeparateColor"); L.new(rnd, sep.inputs[0])
    # value: 4 painted steps
    q = math("DIVIDE", math("FLOOR", math("MULTIPLY", sep.outputs["Red"], 4.0)), 3.0)
    val = math("MULTIPLY_ADD", math("SUBTRACT", q, 0.5), math("MULTIPLY", gi.outputs["Variation"], 2.0), 1.0)
    # bristle streaks inside the dab, running along the stroke
    br = N.new("ShaderNodeTexWave"); br.wave_type = "BANDS"; br.bands_direction = "X"
    br.inputs["Distortion"].default_value = 6.0; br.inputs["Detail"].default_value = 2.0
    L.new(vmath("MULTIPLY", tc.outputs["Object"], gi.outputs["Axis Scale"]), br.inputs["Vector"])
    L.new(math("MULTIPLY", gi.outputs["Stroke Scale"], 3.0), br.inputs["Scale"])
    val = math("MULTIPLY", val, math("MULTIPLY_ADD", math("SUBTRACT", br.outputs["Fac"], 0.5), gi.outputs["Bristle"], 1.0))
    hue = math("MULTIPLY_ADD", math("SUBTRACT", sep.outputs["Green"], 0.5), gi.outputs["Hue Jitter"], 0.5)
    # cool/warm halftone dabs: some dabs lean toward the Shadow Color (a design value, not painted light)
    cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"
    L.new(math("MULTIPLY", math("GREATER_THAN", sep.outputs["Blue"], 0.7), gi.outputs["Shadow Mix"]), cm.inputs["Factor"])
    L.new(gi.outputs["Base Color"], cm.inputs[6]); L.new(gi.outputs["Shadow Color"], cm.inputs[7])
    hsv = N.new("ShaderNodeHueSaturation")
    L.new(cm.outputs[2], hsv.inputs["Color"]); L.new(hue, hsv.inputs["Hue"]); L.new(val, hsv.inputs["Value"])
    # per-dab normal tilt (terminator break-up), surface-locked
    tilt = vmath("SCALE", vmath("SUBTRACT", rnd, (0.5, 0.5, 0.5)), None, math("MULTIPLY", gi.outputs["Tilt"], 2.0))
    geo = N.new("ShaderNodeNewGeometry")
    nrm = vmath("NORMALIZE", vmath("ADD", geo.outputs["Normal"], tilt))
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    L.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    L.new(math("MULTIPLY_ADD", math("SUBTRACT", sep.outputs["Blue"], 0.5), 0.12, gi.outputs["Roughness"]), bsdf.inputs["Roughness"])
    L.new(gi.outputs["Metallic"], bsdf.inputs["Metallic"])
    L.new(nrm, bsdf.inputs["Normal"])
    L.new(bsdf.outputs["BSDF"], go.inputs["BSDF"])
    return ng


def paint(name, color, tier="set", axis="y", shadow=None, **kw):
    """Painted matte surface. color: palette key ('set/moquette') or linear RGB tuple.
    axis: the direction strokes run along ('y' = down the car, 'x' = across, 'z' = vertical)."""
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    rgb = pal(color) if isinstance(color, str) else tuple(color)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    g = nt.nodes.new("ShaderNodeGroup"); g.node_tree = _paint_group()
    g.inputs["Base Color"].default_value = rgb + (1.0,)
    if shadow is not None:
        srgb = pal(shadow) if isinstance(shadow, str) else tuple(shadow)
        g.inputs["Shadow Color"].default_value = srgb + (1.0,)
        kw.setdefault("shadow_mix", 0.6)
    p = dict(TIER[tier]); p.update(kw)
    names = {"stroke_scale": "Stroke Scale", "stretch": "Stretch", "variation": "Variation", "hue_jitter": "Hue Jitter",
             "roughness": "Roughness", "bump": "Bump", "metallic": "Metallic", "seed": "Seed", "tilt": "Tilt",
             "bristle": "Bristle", "shadow_mix": "Shadow Mix"}
    for k, sock in names.items():
        if k in p:
            g.inputs[sock].default_value = p[k]
    st = p.get("stretch", 4.0)
    g.inputs["Axis Scale"].default_value = tuple(1.0 / st if a == axis else 1.0 for a in "xyz")
    nt.links.new(g.outputs["BSDF"], out.inputs["Surface"])
    mat.diffuse_color = rgb + (1.0,)
    return mat


def gloss(name, color, roughness=0.05, coat=0.0, metallic=0.0):
    """The only glossy things: corneas, badge plastic, phone glass, steel trim."""
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    rgb = pal(color) if isinstance(color, str) else tuple(color)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgb + (1,)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Coat Weight"].default_value = coat
    return mat


def glass():
    mat = bpy.data.materials.get("glass_window")
    if mat:
        return mat
    mat = bpy.data.materials.new("glass_window")
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.92, 0.96, 0.94, 1)
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.52
    return mat


def emission(name, color, strength=1.0):
    """Self-lit surface. Its EMIT Strength is driven by the light rig."""
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    rgb = pal(color) if isinstance(color, str) else tuple(color)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission"); em.name = "EMIT"
    em.inputs["Color"].default_value = rgb + (1,)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return mat


# ----------------------------------------------------------------------------- render + compositor

def setup_render(scene, res=(1280, 536), samples=64):
    scene.render.engine = "CYCLES"
    c = scene.cycles
    c.device = "CPU"
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.02
    c.use_denoising = True
    c.seed = 0
    c.use_animated_seed = False      # L1: identical noise pattern every frame, no shimmer
    c.max_bounces = 6
    c.diffuse_bounces = 4
    c.glossy_bounces = 3
    c.transmission_bounces = 4
    c.sample_clamp_indirect = 6.0
    c.caustics_reflective = False
    c.caustics_refractive = False
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.use_freestyle = False
    scene.render.dither_intensity = 0.0   # L2: no output dither, so black stays exactly 0
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = -0.3
    w = bpy.data.worlds.new("NightVoid")   # world black (0): no ambient, no HDRI, no fill
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    scene.world = w
    bpy.context.view_layer.use_pass_object_index = True


def canvas_image(w, h, seed=7, strength=1.0):
    """Painted-board texture: a field of overlapping, oriented brush strokes with bristle streaks
    over a fine canvas weave, as a MULTIPLIER (~0.84-1.06). Static (same every frame of a shot, so
    asleep frames stay identical) and multiply-only (0 stays 0). Stroke size scales with the frame
    (~2.5% of width long), so brushwork reads at every distance, including the Meter."""
    import numpy as np
    img = bpy.data.images.get("canvas_tooth")
    if img and tuple(img.size) == (w, h):
        return img
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    weave = 0.5 + 0.25 * np.sin(x * 2 * np.pi / 3.1) * np.sin(y * 2 * np.pi / 3.3)
    acc = np.ones((h, w), np.float32)
    # flow field: strokes mostly follow a slow, smooth direction field (a painter's hand)
    def smooth_noise(scale):
        g = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
        yi, xi = y / scale, x / scale
        y0, x0 = yi.astype(int), xi.astype(int)
        fy, fx = yi - y0, xi - x0
        return (g[y0, x0] * (1 - fx) * (1 - fy) + g[y0, x0 + 1] * fx * (1 - fy) + g[y0 + 1, x0] * (1 - fx) * fy + g[y0 + 1, x0 + 1] * fx * fy)
    flow = (smooth_noise(max(8, w // 6)) - 0.5) * np.pi * 1.2
    L = max(10, int(w * 0.025))
    Wd = max(4, int(L * 0.32))
    S = L + 4
    yy, xx = np.mgrid[-S // 2:S // 2, -S // 2:S // 2].astype(np.float32)
    stamps = []
    for ang in np.linspace(-np.pi / 2, np.pi / 2, 24, endpoint=False):
        c, s_ = np.cos(ang), np.sin(ang)
        u = xx * c + yy * s_
        v = -xx * s_ + yy * c
        hw = (Wd / 2) * np.sqrt(np.clip(1 - (2 * u / L) ** 2, 0, 1)) + 1e-3   # tapered, rounded ends
        body = np.clip((hw - np.abs(v)) / 1.5, 0, 1)                            # ~1.5 px soft edge
        bristle = 0.7 + 0.3 * np.sin(v * 2.2) * (0.6 + 0.4 * np.sin(u * 0.35))  # streaks along the stroke
        stamps.append((ang, body * 0.85, bristle))
    n = int(w * h / (L * Wd) * 4.0)
    cys = rng.integers(0, h, n); cxs = rng.integers(0, w, n)
    vals = rng.normal(0.0, 0.045, n).astype(np.float32)
    for cy, cx, dv in zip(cys, cxs, vals):
        ang = flow[cy, cx] + rng.normal(0, 0.25)
        ang = (ang + np.pi / 2) % np.pi - np.pi / 2
        k = int((ang + np.pi / 2) / np.pi * 24) % 24
        _, m, br = stamps[k]
        y0, x0 = cy - S // 2, cx - S // 2
        ys, xs = max(0, y0), max(0, x0)
        ye, xe = min(h, y0 + S), min(w, x0 + S)
        mm = m[ys - y0:ye - y0, xs - x0:xe - x0]
        bb = br[ys - y0:ye - y0, xs - x0:xe - x0]
        tgt = 1.0 + dv * bb
        acc[ys:ye, xs:xe] = acc[ys:ye, xs:xe] * (1 - mm) + tgt * mm
    mult = (acc - 1.0) * strength + 1.0
    mult *= 0.97 + 0.04 * weave
    mult = np.clip(mult, 0.80, 1.08)
    rgba = np.dstack([mult, mult, mult, np.ones_like(mult)]).astype(np.float32)
    img = bpy.data.images.new("canvas_tooth", w, h, float_buffer=True, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    return img


def setup_compositor(scene, k_set=4, k_face=2, enabled=True):
    """RenderLayers -> Kuwahara (big on the set, small on faces/hands) -> canvas tooth x (set only)."""
    ng = bpy.data.node_groups.new("PainterlyComp", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    N, L = ng.nodes, ng.links
    rl = N.new("CompositorNodeRLayers")
    rl.scene = scene
    out = N.new("NodeGroupOutput")
    scene.compositing_node_group = ng
    if not enabled:
        L.new(rl.outputs["Image"], out.inputs[0])
        return ng

    def kuwa(size):
        k = N.new("CompositorNodeKuwahara")
        k.inputs["Type"].default_value = "Anisotropic"
        k.inputs["Size"].default_value = size
        k.inputs["Uniformity"].default_value = 4
        k.inputs["Sharpness"].default_value = 0.7
        k.inputs["Eccentricity"].default_value = 1.1
        L.new(rl.outputs["Image"], k.inputs["Image"])
        return k

    big, small = kuwa(k_set), kuwa(k_face)
    idx = rl.outputs.get("Object Index") or rl.outputs.get("IndexOB")

    def idmask(i):
        m = N.new("CompositorNodeIDMask")
        m.inputs["Index"].default_value = i
        m.inputs["Anti-Alias"].default_value = True
        L.new(idx, m.inputs["ID value"])
        return m

    face = idmask(PASS_FACE)
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
    L.new(face.outputs["Alpha"], mix.inputs["Factor"])
    L.new(big.outputs[0], mix.inputs[6]); L.new(small.outputs[0], mix.inputs[7])
    # canvas tooth on the set only: factor = 1 - (face or character)
    charm = idmask(PASS_CHAR)
    anyc = N.new("ShaderNodeMath"); anyc.operation = "MAXIMUM"
    L.new(face.outputs["Alpha"], anyc.inputs[0]); L.new(charm.outputs["Alpha"], anyc.inputs[1])
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    L.new(anyc.outputs[0], inv.inputs[1])
    cim = N.new("CompositorNodeImage"); cim.image = canvas_image(scene.render.resolution_x, scene.render.resolution_y)
    mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
    # darks merge into bigger, quieter shapes: a larger kernel blended in where luminance is low
    # (set only; lit features stay crisp; 0 stays 0 because Kuwahara of black is black)
    dark = kuwa(k_set * 2 + 1)
    bw = N.new("CompositorNodeRGBToBW"); L.new(rl.outputs["Image"], bw.inputs[0])
    dm = N.new("ShaderNodeMath"); dm.operation = "MULTIPLY_ADD"; dm.use_clamp = True
    L.new(bw.outputs[0], dm.inputs[0]); dm.inputs[1].default_value = -1.0 / 0.12; dm.inputs[2].default_value = 0.16 / 0.12
    dmask = N.new("ShaderNodeMath"); dmask.operation = "MULTIPLY"
    L.new(dm.outputs[0], dmask.inputs[0]); L.new(inv.outputs[0], dmask.inputs[1])
    dmix = N.new("ShaderNodeMix"); dmix.data_type = "RGBA"
    L.new(dmask.outputs[0], dmix.inputs["Factor"])
    L.new(mix.outputs[2], dmix.inputs[6]); L.new(dark.outputs[0], dmix.inputs[7])
    L.new(inv.outputs[0], mul.inputs["Factor"])
    L.new(dmix.outputs[2], mul.inputs[6]); L.new(cim.outputs["Image"], mul.inputs[7])
    L.new(mul.outputs[2], out.inputs[0])
    return ng
