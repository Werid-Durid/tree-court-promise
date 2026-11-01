"""验证 MMD 物理：给 Anaxa 加头/上身动作，跑刚体模拟，测量头发骨位移。"""
import bpy
import json
from pathlib import Path
from mathutils import Quaternion

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/physics/anaxa.blend'))
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
pb = arm.pose.bones

rbw = scene.rigidbody_world
print('RIGIDBODY_WORLD', rbw is not None, rbw.enabled if rbw else None, flush=True)
child_of = sum(1 for b in pb for c in b.constraints if c.type == 'CHILD_OF')
print('CHILD_OF_CONSTRAINTS', child_of, flush=True)
hair = [b for b in pb if '髪' in b.name][:8]
print('HAIR_BONES', [b.name for b in hair], flush=True)

# 简单动作：上身左右转 + 点头
for f, ang in [(1, 0.0), (12, 0.5), (24, 0.0), (36, -0.5), (48, 0.0)]:
    scene.frame_set(f)
    for name, axis, mult in (('上半身', (0, 0, 1), 1.0), ('首', (1, 0, 0), 0.6)):
        if name in pb:
            pb[name].rotation_mode = 'QUATERNION'
            pb[name].rotation_quaternion = Quaternion(axis, ang * mult)
            pb[name].keyframe_insert('rotation_quaternion')

scene.frame_start = 1
scene.frame_end = 48
if rbw:
    rbw.enabled = True
    try:
        scene.frame_set(1)
        bpy.ops.ptcache.bake_all(bake=True)
        print('CACHE_BAKED', True, flush=True)
    except Exception as exc:
        print('CACHE_BAKE_ERR', exc, flush=True)

positions = {b.name: [] for b in hair}
for f in range(1, 49):
    scene.frame_set(f)
    for b in hair:
        positions[b.name].append((arm.matrix_world @ b.head).copy())
ranges = {n: round(max((p - positions[n][0]).length for p in positions[n]), 5) for n in positions}
print('HAIR_MOTION ' + json.dumps(ranges, ensure_ascii=False), flush=True)
print('PHYSICS_MOTION_OK' if max(ranges.values(), default=0) > 0.005 else 'PHYSICS_MOTION_WEAK')
