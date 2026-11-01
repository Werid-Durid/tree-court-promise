"""Check evaluated hand meshes against the book and desk on every rendered study frame."""
import bpy,json,math,sys,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
BASE=Path(next((a.split('=',1)[1] for a in args if a.startswith('--directory=')),str(ROOT/'blender/build/study-revision')))
if not BASE.is_absolute():BASE=ROOT/BASE
results=[]
characters=[a.split('=',1)[1] for a in args if a.startswith('--character=')] or ['anaxa','hyacine','castor','phainon']
for cid in characters:
 out=BASE/cid;bpy.ops.wm.open_mainfile(filepath=str(out/f'{cid}_study.blend'));scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE');tracked=[]
 for obj in scene.objects:
  if obj.type!='MESH' or not any(m.type=='ARMATURE' for m in obj.modifiers):continue
  groups={g.index:g.name for g in obj.vertex_groups};ids=[]
  for v in obj.data.vertices:
   if sum(g.weight for g in v.groups if '手首' in groups.get(g.group,'') or '指' in groups.get(g.group,''))>.35:ids.append(v.index)
  if ids:tracked.append((obj,np.asarray(ids,dtype=np.int32)))
 page_min=10.;desk_min=10.;previous=None;maximum_step=0.;checked=0;boundary=[]
 for frame in range(1,482):
  scene.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
  joints=np.asarray([tuple(arm.matrix_world@arm.pose.bones['手首.'+side].head) for side in ['L','R']])
  if previous is not None:maximum_step=max(maximum_step,float(np.linalg.norm(joints-previous,axis=1).max()))
  previous=joints
  if frame in [1,481]:boundary.append({p.name:(p.matrix.translation.copy(),p.matrix.to_quaternion()) for p in arm.pose.bones})
  for obj,ids in tracked:
   ev=obj.evaluated_get(dg);mesh=ev.to_mesh();co=np.empty(len(mesh.vertices)*3,dtype=np.float64);mesh.vertices.foreach_get('co',co)
   xyz=co.reshape(-1,3)[ids];matrix=np.asarray(ev.matrix_world,dtype=np.float64);world=xyz@matrix[:3,:3].T+matrix[:3,3];ev.to_mesh_clear()
   book=(world[:,0]>-.223)&(world[:,0]<.243)&(world[:,1]>-.555)&(world[:,1]<-.245)
   desk=(world[:,0]>-.85)&(world[:,0]<.85)&(world[:,1]>-.75)&(world[:,1]<.45)
   if book.any():page_min=min(page_min,float(world[book,2].min())-.885)
   if desk.any():desk_min=min(desk_min,float(world[desk,2].min())-.845)
   checked+=len(ids)
  if frame%120==1:print('HAND_MESH_AUDIT',cid,frame,flush=True)
 position=max((boundary[0][n][0]-boundary[1][n][0]).length for n in boundary[0]);angles=[boundary[0][n][1].rotation_difference(boundary[1][n][1]).angle for n in boundary[0]];angle=max(min(a,abs(2*math.pi-a)) for a in angles)
 assert page_min>=.0027,(cid,'page clearance',page_min)
 assert desk_min>=.0027,(cid,'desk clearance',desk_min)
 assert maximum_step<.006,(cid,'wrist jump',maximum_step)
 assert position<.004 and angle<.025,(cid,'loop seam',position,angle)
 result=dict(character=cid,passed=True,source_sha256=hashlib.sha256((out/f'{cid}_study.blend').read_bytes()).hexdigest(),frames_checked=481,hand_vertices_checked=checked,minimum_page_clearance_mm=page_min*1000,minimum_desk_clearance_mm=desk_min*1000,maximum_frame_wrist_displacement_mm=maximum_step*1000,loop_endpoint_position_error_m=position,loop_endpoint_rotation_error_degrees=math.degrees(angle),method='independent evaluated Blender mesh, all rendered frames plus loop endpoint')
 (out/'hand-contact-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');results.append(result);print('HAND_CONTACT_VERIFIED',json.dumps(result),flush=True)
reports=[BASE/cid/'hand-contact-verification.json' for cid in ['anaxa','hyacine','castor','phainon']]
if all(p.is_file() for p in reports):
 (BASE/'hand-contact-verification.json').write_text(json.dumps({'passed':True,'characters':[json.loads(p.read_text(encoding='utf-8')) for p in reports]},indent=2),encoding='utf-8')
 print('FOUR_HAND_CONTACTS_AND_LOOPS_VERIFIED',flush=True)
