"""验证物理姿态烘焙：动画 -> 物理缓存 -> nla.bake(visual_keying) -> 检查头发 F-Curve。"""
import bpy
import json
from pathlib import Path
from mathutils import Quaternion

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/physics/anaxa.blend'))
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
pb = arm.pose.bones

for f, ang in [(1, 0.0), (12, 0.6), (24, 0.0), (36, -0.6), (48, 0.0)]:
    scene.frame_set(f)
    pb['上半身'].rotation_mode = 'QUATERNION'
    pb['上半身'].rotation_quaternion = Quaternion((0, 0, 1), ang)
    pb['上半身'].keyframe_insert('rotation_quaternion')

scene.frame_start = 1
scene.frame_end = 48
if scene.rigidbody_world:
    scene.rigidbody_world.enabled = True
bpy.ops.ptcache.bake_all(bake=True)
print('CACHE_BAKED', True, flush=True)

bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.nla.bake(frame_start=1, frame_end=48, step=1, only_selected=True,
                 visual_keying=True, clear_constraints=False, use_current_action=False,
                 bake_types={'POSE'})
action = arm.animation_data.action
print('ACTION', action.name, flush=True)


def all_fcurves(act):
    out = []
    if hasattr(act, 'fcurves'):
        try:
            out += list(act.fcurves)
        except Exception:
            pass
    for layer in getattr(act, 'layers', []):
        for strip in getattr(layer, 'strips', []):
            for slot in getattr(act, 'slots', []):
                try:
                    bag = strip.channelbag(slot)
                except Exception:
                    bag = None
                if bag:
                    out += list(bag.fcurves)
    return out


fcurves = all_fcurves(action)
paths = sorted({fc.data_path for fc in fcurves})
hair = [p for p in paths if '側髪' in p]
print('FCURVES', len(fcurves), 'PATHS', len(paths), flush=True)
print('HAIR_PATHS', hair[:6], flush=True)
print('BAKE_HAIR_OK' if hair else 'BAKE_HAIR_MISSING')
