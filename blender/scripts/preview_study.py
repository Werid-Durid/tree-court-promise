"""生成自习室与那刻夏写字动画的预览图，供用户核对画面。"""
import bpy
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'pics/previews'
OUT.mkdir(parents=True, exist_ok=True)


def set_eevee(scene):
    for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            scene.render.engine = engine
            return engine
        except Exception:
            continue
    return scene.render.engine


def aim(cam, target):
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def add_warm_lights():
    sun_data = bpy.data.lights.new('PreviewSun', 'SUN')
    sun_data.energy = 3.2
    sun_data.color = (1.0, 0.78, 0.52)
    sun = bpy.data.objects.new('PreviewSun', sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (-4, -3, 5)
    sun.rotation_euler = (0.9, 0.2, 0.0)
    fill_data = bpy.data.lights.new('PreviewFill', 'AREA')
    fill_data.energy = 60.0
    fill_data.color = (0.62, 0.78, 0.88)
    fill = bpy.data.objects.new('PreviewFill', fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = (3, 2, 2.5)
    aim(fill, (0, 0, 1))


# ---------- 1. 房间预览（壁纸机位） ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/build/study-room/study_room.blend'))
scene = bpy.context.scene
set_eevee(scene)
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.image_settings.file_format = 'PNG'
cam_data = bpy.data.cameras.new('WallpaperCam')
cam_data.lens = 50
cam = bpy.data.objects.new('WallpaperCam', cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (0.55, 2.6, 1.6)
aim(cam, (0, -0.1, 1.0))
scene.camera = cam
add_warm_lights()
scene.render.filepath = str(OUT / 'room-wallpaper.png')
bpy.ops.render.render(write_still=True)

# 俯视布局参考
cam2 = bpy.data.objects.new('TopCam', bpy.data.cameras.new('TopCam'))
bpy.context.collection.objects.link(cam2)
cam2.location = (0, 0.1, 6.5)
cam2.rotation_euler = (0, 0, 0)
cam2.data.type = 'ORTHO'
cam2.data.ortho_scale = 9
scene.camera = cam2
scene.render.filepath = str(OUT / 'room-top.png')
bpy.ops.render.render(write_still=True)

# ---------- 2. 那刻夏写字动画预览 ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/study/anaxa.blend'))
scene = bpy.context.scene
set_eevee(scene)
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.image_settings.file_format = 'PNG'
# 正面 3/4 半身，看清坐姿与运笔手部。
for frame, name in ((1, 'anaxa-write-start.png'), (145, 'anaxa-write-mid.png'), (289, 'anaxa-write-end.png')):
    scene.frame_set(frame)
    cam_data = bpy.data.cameras.new('CharCam')
    cam_data.lens = 60
    cam = bpy.data.objects.new('CharCam', cam_data)
    bpy.context.collection.objects.link(cam)
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    cam.location = (0.9, -2.2, 1.15)
    aim(cam, (0, 0.15, 0.75))
    scene.camera = cam
    add_warm_lights()
    scene.render.filepath = str(OUT / name)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
    for light in [o for o in bpy.context.scene.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(light)

print('PREVIEW_READY')
