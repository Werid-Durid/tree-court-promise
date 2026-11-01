"""三渲二基线自检：测试立方体 + 球体，应用 Paper Anime Render Helper 的色阶/描边，渲染对照图。"""
import bpy
import math
import addon_utils
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'blender'
OUT.mkdir(exist_ok=True)

EXT = "bl_ext.user_default.Paperzhu_animehelper_extension"
if not hasattr(bpy.types.Scene, 'paper_render_helper'):
    try:
        addon_utils.enable(EXT, default_set=True, persistent=True)
    except Exception as exc:
        print('EXTENSION_ENABLE_ERROR', exc)
if not hasattr(bpy.types.Scene, 'paper_render_helper'):
    raise RuntimeError('Paper Anime Render Helper 未注册（paper_render_helper 缺失）')
print('EXTENSION_READY')

# 数据层清空默认场景（不使用 bpy.ops.object.select_all/delete，避免后台上下文 poll 失败）
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    for block in list(datablocks):
        if block.users == 0:
            datablocks.remove(block)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


# 相机（3/4 视角，能同时看到受光面与背光面/描边）
cam_data = bpy.data.cameras.new('TestCam')
cam_data.lens = 55
cam = bpy.data.objects.new('TestCam', cam_data)
scene.collection.objects.link(cam)
cam.location = (4.0, -4.4, 3.1)
look_at(cam, (0.8, 0.0, 0.95))
scene.camera = cam

# 主光（暖）+ 补光（冷）
sun_data = bpy.data.lights.new('TestSun', 'SUN')
sun_data.energy = 3.2
sun_data.color = (1.0, 0.94, 0.86)
sun = bpy.data.objects.new('TestSun', sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(12), math.radians(38))

fill_data = bpy.data.lights.new('TestFill', 'AREA')
fill_data.energy = 60.0
fill_data.color = (0.62, 0.76, 0.9)
fill_data.size = 4.0
fill = bpy.data.objects.new('TestFill', fill_data)
scene.collection.objects.link(fill)
fill.location = (-3.5, 2.0, 2.5)
look_at(fill, (0, 0, 1))

# 世界：中性灰
world = bpy.data.worlds.new('TestWorld')
if world.node_tree is None:
    world.use_nodes = True
nt = world.node_tree
bg = next((n for n in nt.nodes if n.type == 'BACKGROUND'), None)
if bg is None:
    bg = nt.nodes.new('ShaderNodeBackground')
    out = next((n for n in nt.nodes if n.type == 'OUTPUT_WORLD'), None) or nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(bg.outputs[0], out.inputs['Surface'])
bg.inputs['Color'].default_value = (0.55, 0.58, 0.62, 1)
bg.inputs['Strength'].default_value = 0.55
scene.world = world

# 暖肤色材质
mat = bpy.data.materials.new('TestSkin')
mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs['Base Color'].default_value = (0.86, 0.60, 0.42, 1)
bsdf.inputs['Roughness'].default_value = 0.5

# 测试立方体
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(0, 0, 0.95))
cube = bpy.context.object
cube.name = 'PaperNPRExtensionTestCube'
cube.data.materials.append(mat)

# 球体（辅助展示色阶边界）
mat2 = mat.copy()
mat2.name = 'TestSkin2'
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.78, location=(2.05, 0.25, 0.78))
sphere = bpy.context.object
sphere.name = 'PaperNPRExtensionTestSphere'
sphere.data.materials.append(mat2)
for p in sphere.data.polygons:
    p.use_smooth = True

scene.render.resolution_x = 960
scene.render.resolution_y = 960
scene.render.image_settings.file_format = 'PNG'

# 1) 默认 PBR 对照
scene.render.filepath = str(OUT / 'style_baseline_before.png')
bpy.ops.render.render(write_still=True)

# 2) 应用插件三渲二基线
for o in bpy.context.view_layer.objects:
    o.select_set(False)
cube.select_set(True)
sphere.select_set(True)
bpy.context.view_layer.objects.active = cube
settings = scene.paper_render_helper
settings.auto_switch_eevee = True
settings.color_look = 'AGX_HIGH'
settings.color_exposure = 0.0
settings.outline_thickness = 0.002
settings.toon_threshold = 0.45
settings.toon_softness = 0.08
settings.toon_shadow_strength = 0.35
settings.toon_light_influence = 0.8
settings.toon_min_brightness = 0.12

bpy.ops.paper_helper.apply_color()
bpy.ops.paper_helper.apply_toon_shadow()
bpy.ops.paper_helper.apply_outline()

# 3) 三渲二基线渲染
scene.render.filepath = str(OUT / 'style_baseline_render.png')
bpy.ops.render.render(write_still=True)

print('STYLE_BASELINE_RENDER_OK', str(OUT / 'style_baseline_render.png'))
