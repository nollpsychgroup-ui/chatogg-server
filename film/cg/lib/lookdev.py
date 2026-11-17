"""Painterly look-dev.

Two layers, both procedural so the scripts stay the source of truth:

1. Surface paint (shader): every surface material goes through the PaintSurface node group.
   Stretched, quantised noise breaks the albedo into flat brush dabs, with small value/hue
   jitter, a little roughness variation and a faint impasto bump. Light is NOT faked:
   Cycles computes it physically, so blacks, the fluorescent bounce and the sodium sag
   stay true.
2. Image paint (compositor): an anisotropic Kuwahara pass flattens the render into painted
   strokes that follow the image structure, then a canvas tooth is MULTIPLIED in (never added),
   so 0 stays 0 and the blackout stays a true black.

Values here are the TA's first pass; tune them to design/style-guide.md (Character Designer).
"""
import bpy

from .common import kelvin_rgb

# ----------------------------------------------------------------------------- palette
# Linear-ish RGB. Reds are reserved: only LANYARD and KAI_END_CALL may be red.
PALETTE = {
    "moquette":   (0.022, 0.058, 0.056),   # muted teal seats
    "seat_frame": (0.20, 0.21, 0.21),
    "laminate":   (0.33, 0.34, 0.33),      # grey laminate walls
    "ceiling":    (0.55, 0.56, 0.53),
    "floor":      (0.055, 0.062, 0.068),   # blue-grey vinyl
    "steel":      (0.62, 0.63, 0.64),
    "door":       (0.26, 0.27, 0.27),
    "end_wall":   (0.30, 0.31, 0.30),
    "sign_vinyl": (0.03, 0.05, 0.09),      # deep blue-black, white type
    "sign_type":  (0.80, 0.80, 0.78),
    "display_bezel": (0.005, 0.005, 0.005),
    # characters (blocking proxies, to be matched to design/)
    "noor_suit":  (0.040, 0.042, 0.046),   # charcoal
    "lanyard":    (0.50, 0.018, 0.022),    # THE red
    "badge":      (0.80, 0.80, 0.78),
    "walter_coat": (0.33, 0.20, 0.090),    # camel
    "bea_scrubs": (0.020, 0.035, 0.085),   # navy
    "bea_cardigan": (0.10, 0.10, 0.11),
    "kai_hoodie": (0.15, 0.155, 0.16),     # grey
    "trousers":   (0.03, 0.03, 0.035),
    "newspaper":  (0.60, 0.58, 0.52),
    "skin_a":     (0.42, 0.25, 0.17),
    "skin_b":     (0.62, 0.43, 0.33),
    "skin_c":     (0.24, 0.14, 0.09),
    "skin_d":     (0.55, 0.36, 0.26),
    "hair_dark":  (0.02, 0.016, 0.014),
    "hair_grey":  (0.35, 0.34, 0.33),
    "phone":      (0.01, 0.01, 0.012),
}

PAINT_DEFAULTS = dict(stroke_scale=9.0, stretch=5.0, variation=0.26, hue_jitter=0.015, bump=0.04, dab_steps=5)


def _paint_group():
    ng = bpy.data.node_groups.get("PaintSurface")
    if ng:
        return ng
    ng = bpy.data.node_groups.new("PaintSurface", "ShaderNodeTree")
    iface = ng.interface
    iface.new_socket("Base Color", in_out="INPUT", socket_type="NodeSocketColor")
    for nm, dv in (("Stroke Scale", 9.0), ("Stretch", 5.0), ("Variation", 0.16), ("Hue Jitter", 0.015),
                   ("Roughness", 0.7), ("Bump", 0.04), ("Metallic", 0.0), ("Seed", 0.0)):
        s = iface.new_socket(nm, in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = dv
    iface.new_socket("BSDF", in_out="OUTPUT", socket_type="NodeSocketShader")
    N = ng.nodes
    L = ng.links
    gi = N.new("NodeGroupInput")
    go = N.new("NodeGroupOutput")
    tc = N.new("ShaderNodeTexCoord")
    # anisotropic coords: strokes run long along local X (the car's length) and Z on vertical faces
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    comb = N.new("ShaderNodeCombineXYZ")
    divx = N.new("ShaderNodeMath"); divx.operation = "DIVIDE"
    L.new(sep.outputs["X"], divx.inputs[0]); L.new(gi.outputs["Stretch"], divx.inputs[1])
    L.new(divx.outputs[0], comb.inputs["X"])
    L.new(sep.outputs["Y"], comb.inputs["Y"])
    L.new(sep.outputs["Z"], comb.inputs["Z"])
    # stroke noise (with a little wobble so strokes are hand-made, not lines)
    n1 = N.new("ShaderNodeTexNoise"); n1.noise_dimensions = "4D"
    n1.inputs["Detail"].default_value = 1.5
    n1.inputs["Distortion"].default_value = 0.6
    n1.inputs["Roughness"].default_value = 0.45
    L.new(comb.outputs[0], n1.inputs["Vector"]); L.new(gi.outputs["Stroke Scale"], n1.inputs["Scale"])
    L.new(gi.outputs["Seed"], n1.inputs["W"])
    # quantise into flat dabs
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    steps = [(0.0, 0.0), (0.38, 0.25), (0.47, 0.5), (0.55, 0.75), (0.64, 1.0)]
    els[0].position, els[0].color = steps[0][0], (steps[0][1],) * 3 + (1,)
    els[1].position, els[1].color = steps[1][0], (steps[1][1],) * 3 + (1,)
    for pos, v in steps[2:]:
        e = els.new(pos); e.color = (v, v, v, 1)
    L.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    # value jitter: 1 + variation*(dab-0.5)*2
    sub = N.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = 0.5
    L.new(ramp.outputs["Color"], sub.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    L.new(sub.outputs[0], mul.inputs[0]); L.new(gi.outputs["Variation"], mul.inputs[1])
    val = N.new("ShaderNodeMath"); val.operation = "MULTIPLY_ADD"
    L.new(mul.outputs[0], val.inputs[0]); val.inputs[1].default_value = 2.0; val.inputs[2].default_value = 1.0
    # large, soft colour patches for hue drift (warm/cool, like a painter mixing on the surface)
    n2 = N.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 1.2; n2.inputs["Detail"].default_value = 0.0
    L.new(tc.outputs["Object"], n2.inputs["Vector"])
    hsub = N.new("ShaderNodeMath"); hsub.operation = "SUBTRACT"; hsub.inputs[1].default_value = 0.5
    L.new(n2.outputs["Fac"], hsub.inputs[0])
    hmul = N.new("ShaderNodeMath"); hmul.operation = "MULTIPLY_ADD"
    L.new(hsub.outputs[0], hmul.inputs[0]); L.new(gi.outputs["Hue Jitter"], hmul.inputs[1]); hmul.inputs[2].default_value = 0.5
    hsv = N.new("ShaderNodeHueSaturation")
    L.new(gi.outputs["Base Color"], hsv.inputs["Color"])
    L.new(hmul.outputs[0], hsv.inputs["Hue"])
    L.new(val.outputs[0], hsv.inputs["Value"])
    # roughness variation and impasto
    rmix = N.new("ShaderNodeMath"); rmix.operation = "MULTIPLY_ADD"
    L.new(sub.outputs[0], rmix.inputs[0]); rmix.inputs[1].default_value = 0.25
    L.new(gi.outputs["Roughness"], rmix.inputs[2])
    bump = N.new("ShaderNodeBump")
    L.new(gi.outputs["Bump"], bump.inputs["Strength"])
    L.new(n1.outputs["Fac"], bump.inputs["Height"])
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
    L.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])
    L.new(rmix.outputs[0], bsdf.inputs["Roughness"])
    L.new(gi.outputs["Metallic"], bsdf.inputs["Metallic"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    L.new(bsdf.outputs["BSDF"], go.inputs["BSDF"])
    return ng


def paint_material(name, color, **kw):
    """A painted surface. kw: stroke_scale, stretch, variation, hue_jitter, roughness, bump, metallic, seed."""
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    if isinstance(color, str):
        color = PALETTE[color]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    g = nt.nodes.new("ShaderNodeGroup"); g.node_tree = _paint_group()
    g.inputs["Base Color"].default_value = tuple(color) + (1.0,)
    p = dict(PAINT_DEFAULTS); p.update(kw)
    mapping = {"stroke_scale": "Stroke Scale", "stretch": "Stretch", "variation": "Variation",
               "hue_jitter": "Hue Jitter", "roughness": "Roughness", "bump": "Bump",
               "metallic": "Metallic", "seed": "Seed"}
    for k, sock in mapping.items():
        if k in p:
            g.inputs[sock].default_value = p[k]
    nt.links.new(g.outputs["BSDF"], out.inputs["Surface"])
    mat.diffuse_color = tuple(color) + (1.0,)
    return mat


def glass_material():
    """Carriage window glass. Clear glass over a black night: it shows the passing tunnel lights
    and mirrors the panel row (a second meter), and goes dead black in every cue."""
    mat = bpy.data.materials.get("glass_window")
    if mat:
        return mat
    mat = bpy.data.materials.new("glass_window")
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.9, 0.95, 0.93, 1)
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.52
    return mat


def emission_material(name, color=(1, 1, 1), strength=1.0):
    """Self-lit surface (panel diffusers, display, phone screens). Its Strength input is
    driven by the light rig so the visible diffuser always matches the light it represents."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.name = "EMIT"
    em.inputs["Color"].default_value = tuple(color) + (1,)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return mat


def text_emission_material(name, color, strength, bg=(0, 0, 0)):
    return emission_material(name, color, strength)


# ----------------------------------------------------------------------------- render + compositor

def setup_render(scene, res=(960, 402), samples=64):
    scene.render.engine = "CYCLES"
    c = scene.cycles
    c.device = "CPU"
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.03
    c.use_denoising = True
    try:
        c.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    c.max_bounces = 6
    c.diffuse_bounces = 4
    c.glossy_bounces = 3
    c.transmission_bounces = 4
    c.sample_clamp_indirect = 8.0
    c.caustics_reflective = False
    c.caustics_refractive = False
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = -0.4
    scene.view_settings.gamma = 1.0
    w = bpy.data.worlds.new("NightVoid")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    scene.world = w


def canvas_image(w=960, h=402, seed=7):
    """Canvas tooth: a multiplier around 1.0 (0.90-1.03) with a fine weave plus fibre noise."""
    import numpy as np
    img = bpy.data.images.get("canvas_tooth")
    if img and tuple(img.size) == (w, h):
        return img
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    weave = 0.5 + 0.25 * np.sin(x * 2 * np.pi / 3.1) * np.sin(y * 2 * np.pi / 3.3)
    fib = rng.random((h, w)).astype(np.float32)
    # soften fibre noise
    for _ in range(2):
        fib = (fib + np.roll(fib, 1, 0) + np.roll(fib, 1, 1) + np.roll(fib, -1, 0) + np.roll(fib, -1, 1)) / 5
    t = 0.55 * weave + 0.45 * (fib - fib.min()) / (np.ptp(fib) + 1e-6)
    mult = 0.90 + 0.13 * t
    rgba = np.dstack([mult, mult, mult, np.ones_like(mult)]).astype(np.float32)
    img = bpy.data.images.new("canvas_tooth", w, h, float_buffer=True, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    return img


def setup_compositor(scene, kuwahara_size=7, canvas_strength=1.0, enabled=True):
    """RenderLayers -> anisotropic Kuwahara -> x canvas tooth -> output."""
    ng = bpy.data.node_groups.new("PainterlyComp", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    N, L = ng.nodes, ng.links
    rl = N.new("CompositorNodeRLayers")
    out = N.new("NodeGroupOutput")
    if not enabled:
        L.new(rl.outputs["Image"], out.inputs[0])
        scene.compositing_node_group = ng
        return ng
    kw = N.new("CompositorNodeKuwahara")
    kw.inputs["Type"].default_value = "Anisotropic"
    kw.inputs["Size"].default_value = kuwahara_size
    kw.inputs["Uniformity"].default_value = 4
    kw.inputs["Sharpness"].default_value = 0.6
    kw.inputs["Eccentricity"].default_value = 1.1
    L.new(rl.outputs["Image"], kw.inputs["Image"])
    # canvas tooth, tiled over the frame
    cim = N.new("CompositorNodeImage"); cim.image = canvas_image(scene.render.resolution_x, scene.render.resolution_y)
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = canvas_strength
    L.new(kw.outputs[0], mix.inputs["A"])
    L.new(cim.outputs["Image"], mix.inputs["B"])
    L.new(mix.outputs["Result"], out.inputs[0])
    scene.compositing_node_group = ng
    return ng
