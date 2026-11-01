"""检查头发骨与刚体的约束关系，确定烘焙方式。"""
import bpy

ROOT = r'D:\开发项目\树庭学习室\tree_court'
bpy.ops.wm.open_mainfile(filepath=ROOT + r'\blender\physics\anaxa.blend')
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
pb = arm.pose.bones

names = [n for n in ('側髪1-1.L', '側髪1-2.L', '前髪1.L', '後髪1.L') if n in pb]
for n in names:
    b = pb[n]
    print('BONE', n, 'constraints=', [(c.type, c.name, getattr(c, 'target', None) and c.target.name, getattr(c, 'subtarget', '')) for c in b.constraints], flush=True)

rb = next(o for o in scene.objects if getattr(o, 'rigid_body', None))
print('RB_OBJ', rb.name, 'type=', rb.mmd_rigid.type, 'bone=', rb.mmd_rigid.bone, flush=True)
print('RB_CONSTRAINTS', [(c.type, c.name, getattr(c, 'target', None) and c.target.name, getattr(c, 'subtarget', '')) for c in rb.constraints], flush=True)
print('HAS_RIGID_BODY', rb.rigid_body is not None, 'kinematic=', getattr(rb.rigid_body, 'kinematic', None) if rb.rigid_body else None, flush=True)
