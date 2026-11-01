"""build_rig 后检查头发骨完整约束，并测物理驱动的世界矩阵变化。"""
import bpy

ROOT = r'D:\开发项目\树庭学习室\tree_court'
bpy.ops.wm.open_mainfile(filepath=ROOT + r'\blender\physics\anaxa.blend')
root = next(o for o in bpy.data.objects if getattr(o, 'mmd_type', None) == 'ROOT')
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.mmd_tools.build_rig()
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
pb = arm.pose.bones

for name in [b.name for b in pb if '髪' in b.name][:3]:
    b = pb[name]
    print('BONE', name, [(c.type, c.name, c.mute, getattr(c, 'target', None) and c.target.name) for c in b.constraints], flush=True)

# 动态刚体 -> 目标骨头
rb = next(o for o in scene.objects if getattr(o, 'rigid_body', None) and '髪' in o.name)
print('HAIR_RB', rb.name, 'type=', rb.mmd_rigid.type, 'bone=', rb.mmd_rigid.bone, flush=True)
print('RB_CONS', [(c.type, c.name, c.mute, getattr(c, 'target', None) and c.target.name, getattr(c, 'subtarget', '')) for c in rb.constraints], flush=True)

# 跑物理后看头发骨世界坐标
from mathutils import Quaternion
for f, ang in [(1, 0.0), (12, 0.6), (24, 0.0), (36, -0.6), (48, 0.0)]:
    scene.frame_set(f)
    pb['上半身'].rotation_mode = 'QUATERNION'
    pb['上半身'].rotation_quaternion = Quaternion((0, 0, 1), ang)
    pb['上半身'].keyframe_insert('rotation_quaternion')
scene.frame_start = 1
scene.frame_end = 48
scene.rigidbody_world.enabled = True
bpy.ops.ptcache.bake_all(bake=True)
head = pb['頭']
hair = [b for b in pb if '髪' in b.name][:4]
for f in (1, 12, 24, 36):
    scene.frame_set(f)
    h = arm.matrix_world @ head.head
    print('F', f, [(b.name, round((((arm.matrix_world @ b.head) - h).length), 4)) for b in hair], flush=True)
