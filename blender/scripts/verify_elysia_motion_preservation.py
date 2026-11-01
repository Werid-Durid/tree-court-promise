import bpy,json,hashlib,struct
from pathlib import Path
R=Path(r'D:/开发项目/树庭学习室/tree_court');O=R/'blender/build/phainon-elysia';results=[]
def curves(obj):
 data=obj.animation_data
 if not data or not data.action:return None
 h=hashlib.sha256()
 for layer in data.action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     h.update(fc.data_path.encode());h.update(struct.pack('i',fc.array_index))
     for k in fc.keyframe_points:h.update(struct.pack('ff',*k.co))
 return h.hexdigest()
for file in [R/'blender/build/phainon-film-v3/phainon_wheat_film.blend',O/'phainon_wheat_film.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(file));s=bpy.context.scene;rows={}
 for o in s.objects:
  if o.name.startswith(('星穹铁道—白厄','Phainon_Film_Root')) or o.type=='CAMERA':
   rows[o.name]=dict(transform=list(sum((list(r) for r in o.matrix_world),[])),action=curves(o))
   if o.type=='MESH' and o.data.shape_keys:rows[o.name]['shapes']=curves(o.data.shape_keys)
 results.append(rows)
assert results[0]==results[1], 'Authored character/camera animation changed during environment replacement'
report=dict(passed=True,character_and_camera_unchanged=True,channels=results[1],environment=bpy.context.scene.get('treecourt_environment'))
(O/'motion-preservation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('ENVIRONMENT_ONLY_CHANGE_VERIFIED',flush=True)
