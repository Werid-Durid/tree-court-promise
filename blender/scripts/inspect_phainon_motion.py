import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/build/phainon-film-v3/phainon_wheat_film.blend'))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
report={'arm':arm.name,'scale':list(arm.matrix_world.to_scale()),'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'constraints':[{'type':c.type,'name':c.name,'mute':c.mute} for c in arm.pose.bones[b.name].constraints]} for b in arm.data.bones],'objects':[{'name':o.name,'type':o.type,'modifiers':[m.type for m in o.modifiers],'rigid_body':bool(o.rigid_body)} for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)],'shapes':sorted({k.name for o in bpy.context.scene.objects if o.type=='MESH' and o.data.shape_keys for k in o.data.shape_keys.key_blocks})}
(ROOT/'blender/build/phainon-motion-inspection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('MOTION_INSPECTED',len(report['bones']))
