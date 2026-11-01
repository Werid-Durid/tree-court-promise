"""渲染新教室预览：玩家视角 / 广角 / 窗边。"""
import bpy
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / 'pics' / 'previews'
PREVIEW.mkdir(parents=True, exist_ok=True)


def set_eevee(scene):
    for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            scene.render.engine = engine
            return
        except Exception:
            continue


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/build/cinematic-classroom/story_classroom.blend'))
scene = bpy.context.scene
set_eevee(scene)
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.image_settings.file_format = 'PNG'

# 清掉可能存在的旧灯
for o in [o for o in scene.objects if o.type == 'LIGHT']:
    bpy.data.objects.remove(o, do_unlink=True)

# 暖色黄昏主光（从左侧窗）+ 中性补光 + 环境
sun_data = bpy.data.lights.new('CineSun', 'SUN')
sun_data.energy = 4.0
sun_data.color = (1.0, 0.82, 0.58)
sun_data.angle = math.radians(3)
sun = bpy.data.objects.new('CineSun', sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(58), 0.0, math.radians(100))

fill_data = bpy.data.lights.new('CineFill', 'AREA')
fill_data.energy = 220.0
fill_data.color = (0.72, 0.84, 0.98)
fill_data.size = 8.0
fill = bpy.data.objects.new('CineFill', fill_data)
scene.collection.objects.link(fill)
fill.location = (5.5, 3.0, 4.5)
look_at(fill, (0, 1.2, -1))

world = bpy.data.worlds.new('CineWorld')
if world.node_tree is None:
    world.use_nodes = True
nt = world.node_tree
bg = next((n for n in nt.nodes if n.type == 'BACKGROUND'), None)
if bg is None:
    bg = nt.nodes.new('ShaderNodeBackground')
    out = next((n for n in nt.nodes if n.type == 'OUTPUT_WORLD'), None) or nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(bg.outputs[0], out.inputs['Surface'])
bg.inputs['Color'].default_value = (0.62, 0.72, 0.86, 1)
bg.inputs['Strength'].default_value = 0.55
scene.world = world

cam_data = bpy.data.cameras.new('CineCam')
cam_data.lens = 24
cam = bpy.data.objects.new('CineCam', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

views = {
    'cine-classroom-player.png': ((1.8, 1.65, 2.4), (0.0, 2.0, -6.2), 24),
    'cine-classroom-wide.png': ((6.2, 2.8, 5.6), (-0.5, 1.5, -2.2), 20),
    'cine-classroom-window.png': ((3.6, 1.9, 1.2), (-7.6, 2.4, 0.0), 26),
}
for name, (pos, target, lens) in views.items():
    cam.location = pos
    cam_data.lens = lens
    look_at(cam, target)
    scene.render.filepath = str(PREVIEW / name)
    bpy.ops.render.render(write_still=True)
    print('RENDERED', name, flush=True)

print('CINEMATIC_PREVIEW_OK')
