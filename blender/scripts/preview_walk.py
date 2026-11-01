"""渲染新走路的关键帧姿势（接触/下沉/经过/抬起）。"""
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


cid = 'anaxa'
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/walking' / f'{cid}.blend'))
scene = bpy.context.scene
set_eevee(scene)
scene.render.resolution_x = 720
scene.render.resolution_y = 960
scene.render.image_settings.file_format = 'PNG'

for o in [o for o in scene.objects if o.type == 'LIGHT']:
    bpy.data.objects.remove(o, do_unlink=True)

sun_data = bpy.data.lights.new('WalkSun', 'SUN')
sun_data.energy = 3.4
sun_data.color = (1.0, 0.92, 0.82)
sun = bpy.data.objects.new('WalkSun', sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(56), math.radians(10), math.radians(40))

fill_data = bpy.data.lights.new('WalkFill', 'AREA')
fill_data.energy = 90.0
fill_data.color = (0.64, 0.78, 0.94)
fill_data.size = 4.0
fill = bpy.data.objects.new('WalkFill', fill_data)
scene.collection.objects.link(fill)
fill.location = (-2.4, 2.2, 2.2)
look_at(fill, (0, 1, 0.8))

cam_data = bpy.data.cameras.new('WalkCam')
cam_data.lens = 55
cam = bpy.data.objects.new('WalkCam', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

# 走路段从 t=6s 开始（第 145 帧），一个步幅 24 帧。
poses = {
    'contact': 145,
    'down': 148,
    'pass': 151,
    'up': 154,
}
views = {
    '3q': ((2.4, -3.4, 1.55), (0, 0.95, 0)),
    'side': ((4.2, 0.2, 1.45), (0, 0.95, 0)),
}
for view, (pos, target) in views.items():
    cam.location = pos
    look_at(cam, target)
    for name, frame in poses.items():
        scene.frame_set(frame)
        scene.render.filepath = str(PREVIEW / f'walk-{cid}-{view}-{name}.png')
        bpy.ops.render.render(write_still=True)
        print('RENDERED', view, name, frame, flush=True)

print('WALK_PREVIEW_OK')
