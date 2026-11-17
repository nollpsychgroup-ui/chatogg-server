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
TIER = {
    "set":     dict(stroke_scale=20.0, stretch=4.0, variation=0.22, roughness=0.82, bump=0.05),
    "costume": dict(stroke_scale=45.0, stretch=3.0, variation=0.18, roughness=0.85, bump=0.02),
    "face":    dict(stroke_scale=180.0, stretch=2.0, variation=0.08, roughness=0.6, bump=0.004, hue_jitter=0.02),
}
PASS_FACE, PASS_CHAR = 1, 2   # object pass_index for the compositor masks


def _paint_group():
    ng = bpy.data.node_groups.get("PaintSurface")
    if ng:
        return ng
    ng = bpy.data.node_groups.new("PaintSurface", "ShaderNodeTree")
    iface = ng.interface
    iface.new_socket("Base Color", in_out="INPUT", socket_type="NodeSocketColor")
    ax = iface.new_socket("Axis Scale", in_out="INPUT", socket_type="NodeSocketVector")
    ax.default_value = (1.0, 0.25, 1.0)
    for nm, dv in (("Stroke Scale", 20.0), ("Stretch", 4.0), ("Variation", 0.2), ("Hue Jitter", 0.012),
                   ("Roughness", 0.8), ("Bump", 0.03), ("Metallic", 0.0), ("Seed", 0.0)):
        s = iface.new_socket(nm, in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = dv
    iface.new_socket("BSDF", in_out="OUTPUT", socket_type="NodeSocketShader")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    tc = N.new("ShaderNodeTexCoord")
    # stroke space: object coordinates (locked to the surface), long along the stroke axis
    comb = N.new("ShaderNodeVectorMath"); comb.operation = "MULTIPLY"
    L.new(tc.outputs["Object"], comb.inputs[0]); L.new(gi.outputs["Axis Scale"], comb.inputs[1])
    n1 = N.new("ShaderNodeTexNoise"); n1.noise_dimensions = "4D"
    n1.inputs["Detail"].default_value = 1.5
    n1.inputs["Distortion"].default_value = 0.7
    n1.inputs["Roughness"].default_value = 0.45
    L.new(comb.outputs[0], n1.inputs["Vector"]); L.new(gi.outputs["Stroke Scale"], n1.inputs["Scale"])
    L.new(gi.outputs["Seed"], n1.inputs["W"])
    # quantise into flat dabs (paint is posterised; light never is)
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    steps = [(0.0, 0.0), (0.38, 0.25), (0.47, 0.5), (0.55, 0.75), (0.64, 1.0)]
    for i, (pos, v) in enumerate(steps):
        e = els[i] if i < 2 else els.new(pos)
        e.position, e.color = pos, (v, v, v, 1)
    L.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    sub = N.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = 0.5
    L.new(ramp.outputs["Color"], sub.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    L.new(sub.outputs[0], mul.inputs[0]); L.new(gi.outputs["Variation"], mul.inputs[1])
    val = N.new("ShaderNodeMath"); val.operation = "MULTIPLY_ADD"
    L.new(mul.outputs[0], val.inputs[0]); val.inputs[1].default_value = 2.0; val.inputs[2].default_value = 1.0
    n2 = N.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 1.2; n2.inputs["Detail"].default_value = 0.0
    L.new(tc.outputs["Object"], n2.inputs["Vector"])
    hsub = N.new("ShaderNodeMath"); hsub.operation = "SUBTRACT"; hsub.inputs[1].default_value = 0.5
    L.new(n2.outputs["Fac"], hsub.inputs[0])
    hmul = N.new("ShaderNodeMath"); hmul.operation = "MULTIPLY_ADD"
    L.new(hsub.outputs[0], hmul.inputs[0]); L.new(gi.outputs["Hue Jitter"], hmul.inputs[1]); hmul.inputs[2].default_value = 0.5
    hsv = N.new("ShaderNodeHueSaturation")
    L.new(gi.outputs["Base Color"], hsv.inputs["Color"]); L.new(hmul.outputs[0], hsv.inputs["Hue"]); L.new(val.outputs[0], hsv.inputs["Value"])
    rmix = N.new("ShaderNodeMath"); rmix.operation = "MULTIPLY_ADD"
    L.new(sub.outputs[0], rmix.inputs[0]); rmix.inputs[1].default_value = 0.15
    L.new(gi.outputs["Roughness"], rmix.inputs[2])
    # terminator breakup: stroke-shaped normal perturbation, fixed to the surface
    bump = N.new("ShaderNodeBump")
    L.new(gi.outputs["Bump"], bump.inputs["Strength"]); L.new(ramp.outputs["Color"], bump.inputs["Height"])
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    L.new(hsv.outputs["Color"], bsdf.inputs["Base Color"]); L.new(rmix.outputs[0], bsdf.inputs["Roughness"])
    L.new(gi.outputs["Metallic"], bsdf.inputs["Metallic"]); L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    L.new(bsdf.outputs["BSDF"], go.inputs["BSDF"])
    return ng


def paint(name, color, tier="set", axis="y", **kw):
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
    p = dict(TIER[tier]); p.update(kw)
    names = {"stroke_scale": "Stroke Scale", "stretch": "Stretch", "variation": "Variation", "hue_jitter": "Hue Jitter",
             "roughness": "Roughness", "bump": "Bump", "metallic": "Metallic", "seed": "Seed"}
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


def canvas_image(w, h, seed=7):
    """Canvas tooth multiplier, 0.90-1.03 (multiply only)."""
    import numpy as np
    img = bpy.data.images.get("canvas_tooth")
    if img and tuple(img.size) == (w, h):
        return img
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    weave = 0.5 + 0.25 * np.sin(x * 2 * np.pi / 3.1) * np.sin(y * 2 * np.pi / 3.3)
    fib = rng.random((h, w)).astype(np.float32)
    for _ in range(2):
        fib = (fib + np.roll(fib, 1, 0) + np.roll(fib, 1, 1) + np.roll(fib, -1, 0) + np.roll(fib, -1, 1)) / 5
    t = 0.55 * weave + 0.45 * (fib - fib.min()) / (np.ptp(fib) + 1e-6)
    mult = 0.92 + 0.10 * t
    rgba = np.dstack([mult, mult, mult, np.ones_like(mult)]).astype(np.float32)
    img = bpy.data.images.new("canvas_tooth", w, h, float_buffer=True, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    return img


def setup_compositor(scene, k_set=7, k_face=3, enabled=True):
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
    L.new(inv.outputs[0], mul.inputs["Factor"])
    L.new(mix.outputs[2], mul.inputs[6]); L.new(cim.outputs["Image"], mul.inputs[7])
    L.new(mul.outputs[2], out.inputs[0])
    return ng
