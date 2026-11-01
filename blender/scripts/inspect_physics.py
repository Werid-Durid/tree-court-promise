"""检查角色 blend 是否带 MMD 物理（刚体/关节/物理骨）。"""
import bpy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CID = 'anaxa'
report = {}
for rel in [f'blender/generated/{CID}.blend', f'blender/animated/{CID}.blend']:
    p = ROOT / rel
    if not p.is_file():
        report[rel] = {'missing': True}
        continue
    bpy.ops.wm.open_mainfile(filepath=str(p))
    scene = bpy.context.scene
    objs = list(bpy.data.objects)
    info = {
        'objects': len(objs),
        'armatures': [o.name for o in objs if o.type == 'ARMATURE'],
        'rigidbody_world': scene.rigidbody_world is not None,
        'rigid_bodies': sum(1 for o in objs if getattr(o, 'rigid_body', None)),
        'rigid_body_constraints': sum(1 for o in objs if getattr(o, 'rigid_body_constraint', None)),
        'constraints_total': sum(len(o.constraints) for o in objs),
        'physics_modifiers': sum(1 for o in objs for m in o.modifiers if m.type in {'CLOTH', 'SOFT_BODY', 'COLLISION'}),
        'vertex_groups': sum(len(o.vertex_groups) for o in objs if o.type == 'MESH'),
    }
    if info['armatures']:
        arm = bpy.data.objects[info['armatures'][0]]
        info['bones'] = len(arm.data.bones)
        physics_bones = [b.name for b in arm.data.bones if b.name.startswith(('_dummy_', '物理'))]
        info['physics_bones_sample'] = physics_bones[:10]
    report[rel] = info

print('PHYSICS_REPORT ' + json.dumps(report, ensure_ascii=False))
