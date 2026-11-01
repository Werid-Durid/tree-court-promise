"""对烘焙后的真实蒙皮顶点做家具 AABB 穿入采样；不是衣料物理仿真。"""
import bpy,json,math,numpy as np,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
PAIRED='--paired' in sys.argv
ROOM=ROOT/('blender/build/classroom-paired' if PAIRED else 'blender/classroom')
ROOM=Path(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--room=')),str(ROOM)))
cfg=json.loads((ROOM/'motion.json' if PAIRED else ROOT/'blender/classroom_motion.json').read_text(encoding='utf-8'))
layout=json.loads((ROOM/'layout.json').read_text(encoding='utf-8'))
report=[]
for cid in ['anaxa','hyacine','castor','phainon']:
 model=ROOM/f'characters/{cid}.blend' if PAIRED and cid in ['castor','phainon'] else ROOT/f'blender/animated/{cid}.blend'
 if not model.exists() and PAIRED:model=ROOT/f'blender/build/classroom-paired/characters/{cid}.blend'
 bpy.ops.wm.open_mainfile(filepath=str(model))
 spec=cfg['characters'][cid]
 # 原身高读生成报告，以站姿定尺度，不能从坐姿包围盒计算。
 data=json.loads((ROOT/f'blender/animation-reports/{cid}.json').read_text(encoding='utf-8'))
 scale=spec['height']/data['rest_height'];yaw=spec['yaw'];pos=np.array(spec['position']);floor=data.get('rest_floor',0)
 results={}
 for seconds in range(0,25,2):
  bpy.context.scene.frame_set(1+seconds*24);dep=bpy.context.evaluated_depsgraph_get()
  for obj in bpy.context.scene.objects:
   if obj.type!='MESH' or not any(m.type=='ARMATURE' for m in obj.modifiers):continue
   evaluated=obj.evaluated_get(dep);mesh=evaluated.to_mesh()
   a=np.array([obj.matrix_world@v.co for v in mesh.vertices])*scale
   # Blender X,Y,Z -> web X,Z,-Y，再应用角色朝向和站位。
   pts=np.stack([a[:,0]*math.cos(yaw)-a[:,1]*math.sin(yaw),a[:,2]-floor*scale,-a[:,0]*math.sin(yaw)-a[:,1]*math.cos(yaw)],axis=1)+pos
   for c in layout['colliders']:
    if not any(k in c['name'] for k in ['Desk','Chair','Lectern']):continue
    delta=np.abs(pts-np.array(c['center']));half=np.array(c['size'])/2-.004
    inside=np.all(delta<half,axis=1)
    if inside.any():
     key=c['name']+'@'+str(c['center']);n=int(inside.sum());old=results.get(key,{'vertices':0})
     if n>old['vertices']:
      indices=np.where(inside)[0];groups={};materials={}
      for idx in indices:
       for g in obj.data.vertices[int(idx)].groups:
        name=obj.vertex_groups[g.group].name;groups[name]=round(groups.get(name,0)+g.weight,3)
      for poly in mesh.polygons:
       if any(inside[idx] for idx in poly.vertices):
        name=obj.data.materials[poly.material_index].name;materials[name]=materials.get(name,0)+1
      results[key]={'vertices':n,'seconds':seconds,'groups':dict(sorted(groups.items(),key=lambda x:-x[1])[:12]),'materials':materials,'bounds':[pts[inside].min(0).tolist(),pts[inside].max(0).tolist()]}
   evaluated.to_mesh_clear()
 report.append({'id':cid,'samples':13,'penetrations':results})
target=ROOM/'furniture-audit.json' if PAIRED else ROOT/'blender/animation-reports/furniture-audit.json'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
