"""统计刚体类型与名称，确认头发/裙摆是否有物理。"""
import bpy
import json
from collections import Counter

ROOT = r'D:\开发项目\树庭学习室\tree_court'
bpy.ops.wm.open_mainfile(filepath=ROOT + r'\blender\physics\anaxa.blend')
scene = bpy.context.scene
rbs = [o for o in scene.objects if getattr(o, 'rigid_body', None)]
types = Counter(o.mmd_rigid.type for o in rbs)
print('RB_COUNT', len(rbs), 'TYPES', dict(types))
names = [o.name for o in rbs]
for kw in ('髪', 'スカート', '裙', '袖', '胸', '尻', 'マフラー', 'リボン', '剣', '武器'):
    hits = [n for n in names if kw in n]
    print('KW', kw, len(hits), hits[:5])
# dynamic bodies sample
dyn = [o for o in rbs if o.mmd_rigid.type in (1, 2)]
print('DYNAMIC', len(dyn), [o.name for o in dyn[:15]])
