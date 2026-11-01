"""只读审计四人绑定骨架，动作通过原蒙皮骨骼制作，不假定共用骨架。"""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'blender/animation-reports';out.mkdir(exist_ok=True)
report=[]
for cid in ('anaxa','hyacine','castor','phainon'):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/generated/{cid}.blend'))
    arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    report.append({'id':cid,'armature':arm.name,'matrix':[[float(v) for v in row] for row in arm.matrix_world],
      'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'deform':b.use_deform}
        for b in arm.data.bones],
      'constraints':[{ 'bone':p.name,'constraints':[{'type':c.type,'name':c.name} for c in p.constraints]} for p in arm.pose.bones if p.constraints]})
(out/'rigs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=list),encoding='utf-8')
