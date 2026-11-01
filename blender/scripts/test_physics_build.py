"""完整物理链路：build_rig -> 动画 -> 物理缓存 -> 姿态烘焙 -> 检查头发 F-Curve。"""
import bpy
import json
from pathlib import Path
from mathutils import Quaternion

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/physics/anaxa.blend'))
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
root = next((o for o in bpy.data.objects if getattr(o, 'mmd_type', None) == 'ROOT'), None)
print('ROOT', root.name if root else None, flush=True)

# 1) 构建物理 rig
if root:
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    try:
        bpy.ops.mmd_tools.build_rig()
        print('BUILD_RIG_OK', flush=True)
    except Exception as exc:
        print('BUILD_RIG_ERR', exc, flush=True)

ik = [(b.name, [c.mute for c in b.constraints if c.type == 'IK']) for b in arm.pose.bones if any(c.type == 'IK' for c in b.constraints)]
print('IK_TOTAL', sum(len(v) for _, v in ik), flush=True)
print('IK_HAIR', [n for n, _ in ik if '髪' in n][:5], flush=True)

# 2) 动画：上身左右转
for f, ang in [(1, 0.0), (12, 0.6), (24, 0.0), (36, -0.6), (48, 0.0)]:
    scene.frame_set(f)
    pb = arm.pose.bones
    pb['上半身'].rotation_mode = 'QUATERNION'
    pb['上半身'].rotation_quaternion = Quaternion((0, 0, 1), ang)
    pb['上半身'].keyframe_insert('rotation_quaternion')

scene.frame_start = 1
scene.frame_end = 48
if scene.rigidbody_world:
    scene.rigidbody_world.enabled = True
bpy.ops.ptcache.bake_all(bake=True)
print('CACHE_BAKED', True, flush=True)

# 3) 测头发骨的局部旋转（排除父级带动）
hair = [b for b in arm.pose.bones if '髪' in b.name][:6]
rot_range = {}
for b in hair:
    rot_range[b.name] = []
for f in range(1, 49):
    scene.frame_set(f)
    for b in hair:
        q = b.rotation_quaternion
        rot_range[b.name].append(abs(q.x) + abs(q.y) + abs(q.z))
ranges = {n: round(max(v) - min(v), 5) for n, v in rot_range.items()}
print('HAIR_ROT_RANGE ' + json.dumps(ranges, ensure_ascii=False), flush=True)

# 4) 姿态烘焙
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.nla.bake(frame_start=1, frame_end=48, step=1, only_selected=True,
                 visual_keying=True, clear_constraints=False, use_current_action=False,
                 bake_types={'POSE'})
action = arm.animation_data.action


def all_fcurves(act):
    out = []
    for layer in getattr(act, 'layers', []):
        for strip in getattr(layer, 'strips', []):
            for slot in getattr(act, 'slots', []):
                try:
                    bag = strip.channelbag(slot)
                except Exception:
                    bag = None
                if bag:
                    out += list(bag.fcurves)
    if not out and hasattr(act, 'fcurves'):
        out = list(act.fcurves)
    return out


fcurves = all_fcurves(action)
paths = sorted({fc.data_path for fc in fcurves})
hair_paths = [p for p in paths if '髪' in p]
print('FCURVES', len(fcurves), 'HAIR_PATHS', len(hair_paths), flush=True)
print('BAKE_HAIR_OK' if hair_paths else 'BAKE_HAIR_MISSING')
