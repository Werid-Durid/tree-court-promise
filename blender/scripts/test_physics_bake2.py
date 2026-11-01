"""物理验证 2：只转上身，测头发相对头顶的摆动（排除父级带动）。"""
import bpy
import json
from pathlib import Path
from mathutils import Quaternion

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/physics/anaxa.blend'))
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
pb = arm.pose.bones

ik = [(b.name, [c.mute for c in b.constraints if c.type == 'IK']) for b in pb if any(c.type == 'IK' for c in b.constraints)]
print('IK_CONSTRAINTS', len(ik), flush=True)
print('IK_SAMPLE', ik[:5], flush=True)
rb_objs = [o for o in scene.objects if getattr(o, 'rigid_body', None)]
print('RB_OBJS', len(rb_objs), 'with_child_of', sum(1 for o in rb_objs if any(c.type == 'CHILD_OF' for c in o.constraints)), flush=True)

# 只转上身，头部不主动动
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

head = pb.get('頭')
hair = [b for b in pb if '髪' in b.name][:8]
rel = {b.name: [] for b in hair}
for f in range(1, 49):
    scene.frame_set(f)
    h = arm.matrix_world @ head.head if head else arm.matrix_world @ pb['上半身'].head
    for b in hair:
        rel[b.name].append(((arm.matrix_world @ b.head) - h).copy())
ranges = {n: round(max((p - rel[n][0]).length for p in rel[n]), 5) for n in rel}
print('HAIR_REL_MOTION ' + json.dumps(ranges, ensure_ascii=False), flush=True)
print('PHYSICS_SWING_OK' if max(ranges.values(), default=0) > 0.005 else 'PHYSICS_SWING_WEAK')
