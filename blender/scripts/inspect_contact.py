import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];result=[]
for mode,cid,path in [('classroom','anaxa',ROOT/'blender/animated/anaxa.blend'),('classroom','hyacine',ROOT/'blender/animated/hyacine.blend'),('classroom','castor',ROOT/'blender/build/classroom-paired/characters/castor.blend'),('classroom','phainon',ROOT/'blender/build/classroom-paired/characters/phainon.blend'),('study','anaxa',ROOT/'blender/study/anaxa.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 bones={b.name:list(arm.matrix_world@b.head) for b in arm.pose.bones if any(s in b.name for s in ['足首','足ＩＫ','ひざ','手首']) and not b.name.startswith('_')}
 result.append({'mode':mode,'id':cid,'bones':bones})
(ROOT/'blender/build/spatial-repair/blender-contact.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('CONTACT_INSPECTED')
