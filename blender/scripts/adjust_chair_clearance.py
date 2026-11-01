"""对已生成教室的独立椅架构件调整尺寸，保留其他几何，避免重做角色。"""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];ROOM=ROOT/'blender/build/classroom-fuller'
layout=json.loads((ROOM/'layout.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(ROOM/'story_classroom.blend'))
changes=[];newlegs=[]
final_pass=any(c['name']=='Chair_Back_LowerRunner' for c in layout['colliders'])
for item in layout['colliders']:
 if item['name'] not in ('Chair_Back_Post','Chair_Seat_Back_Rail','Chair_Back_LowerLeg'):continue
 if final_pass and item['name']!='Chair_Seat_Back_Rail':continue
 old={'center':item['center'][:],'size':item['size'][:]}
 seat=min(layout['seats'],key=lambda s:abs(s['seat_center'][0]-item['center'][0])+abs(s['seat_center'][2]-item['center'][2]))
 x=seat['seat_center'][0];sign=1 if item['center'][0]>x else -1
 if item['name']=='Chair_Back_Post':
  item['center'][0]=x+sign*.28;item['center'][1]=.63;item['size'][1]=.84
  newlegs.append({'name':'Chair_Back_LowerRunner','center':[x+sign*.28,.235,seat['seat_center'][2]+.43],'size':[.045,.045,.185]})
 elif item['name']=='Chair_Back_LowerLeg':
  item['center']=[x+sign*.28,.1275,seat['seat_center'][2]+.50];item['size']=[.045,.255,.045]
 else:
  item['center'][0]=x+sign*.24;item['center'][1]=.47;item['size']=[.04,.02,.56]
 changes.append((old,item))
for item in layout['colliders']:
 if item['name']=='Chair_Back_Slat':changes.append(({'center':item['center'][:],'size':item['size'][:]},dict(item,size=[.59,.12,.045])));item['size']=[.59,.12,.045]
matched=0
for obj in list(bpy.context.scene.objects):
 if obj.type!='MESH':continue
 mesh=obj.data;neighbors=[set() for v in mesh.vertices]
 for edge in mesh.edges:
  a,b=edge.vertices;neighbors[a].add(b);neighbors[b].add(a)
 remaining=set(range(len(mesh.vertices)));inv=obj.matrix_world.inverted()
 while remaining:
  todo=[remaining.pop()];island=[]
  while todo:
   i=todo.pop();island.append(i)
   for j in neighbors[i]:
    if j in remaining:remaining.remove(j);todo.append(j)
  points=[obj.matrix_world@mesh.vertices[i].co for i in island]
  web=[Vector((p.x,p.z,-p.y)) for p in points]
  lo=Vector(tuple(min(p[k] for p in web) for k in range(3)));hi=Vector(tuple(max(p[k] for p in web) for k in range(3)));center=(hi+lo)/2;size=hi-lo
  match=next(((old,new) for old,new in changes if (center-Vector(old['center'])).length<.001 and (size-Vector(old['size'])).length<.001),None)
  if not match:continue
  old,new=match
  for i,p in zip(island,web):
   q=Vector(tuple((p[k]-old['center'][k])*new['size'][k]/old['size'][k]+new['center'][k] for k in range(3)))
   mesh.vertices[i].co=inv@Vector((q.x,-q.z,q.y))
  matched+=1
 mesh.update()
assert matched==len(changes),(matched,len(changes))
wood=bpy.data.materials['TC_Room_wood'];wood_obj=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.materials and o.data.materials[0]==wood)
objects=[wood_obj]
for leg in newlegs:
 x,y,z=leg['center'];sx,sy,sz=leg['size']
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,-z,y));obj=bpy.context.object;obj.dimensions=(sx,sz,sy);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);obj.data.materials.append(wood);objects.append(obj)
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=wood_obj
if len(objects)>1:bpy.ops.object.join()
layout['colliders'].extend(newlegs)
(ROOM/'layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'story_classroom.blend'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(ROOM/'story_classroom.glb'),export_format='GLB',export_animations=False)
bpy.ops.export_scene.fbx(filepath=str(ROOM/'story_classroom.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,add_leaf_bones=False)
print('CHAIR_CLEARANCE_UPDATED',matched,len(newlegs))
