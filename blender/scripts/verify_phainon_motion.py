"""从保存后的工程读回动作，检查植足、关节范围和手部/木牌间隙。"""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'blender/build/phainon-film-v3'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'phainon_wheat_film.blend'));scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE');pb=arm.pose.bones
token=bpy.data.objects['Keepsake wooden waymark']
meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)];indices={}
for obj in meshes:
 ids={g.index for g in obj.vertex_groups if '手首' in g.name or '指' in g.name};indices[obj.name]=[v.index for v in obj.data.vertices if any(g.group in ids and g.weight>.15 for g in v.groups)]
contacts=[];feet=[];pose=[];scale=arm.matrix_world.to_scale().x
for t in [i/4 for i in range(104,129)]+[i*2 for i in range(37)]:
 scene.frame_set(1+round(t*24));bpy.context.view_layer.update()
 if 27.25<=t<=32:feet.append({'time':t,**{s:list(arm.matrix_world@pb['足首.'+s].head) for s in ['L','R']}})
 if 26<=t<=32:
  knee={s:math.degrees(math.pi-(pb['足.'+s].head-pb['ひざ.'+s].head).angle(pb['足首.'+s].head-pb['ひざ.'+s].head)) for s in ['L','R']}
  pose.append({'time':t,'knee_flexion_degrees':knee,'hip_world':list(arm.matrix_world@pb['足.L'].head)})
 if t%2:continue
 inv=token.matrix_world.inverted();minimum=100.;inside=0;deps=bpy.context.evaluated_depsgraph_get()
 for obj in meshes:
  ev=obj.evaluated_get(deps);mesh=ev.to_mesh();transform=inv@ev.matrix_world
  for index in indices[obj.name]:
   point=transform@mesh.vertices[index].co;gap=Vector((max(0,abs(point.x)-.09),max(0,abs(point.y)-.06),max(0,abs(point.z)-.009)));minimum=min(minimum,gap.length);inside+=int(gap.length<.0001)
  ev.to_mesh_clear()
 contacts.append({'seconds':t,'hand_to_waymark_min_m':round(minimum,5),'penetrating_vertices':inside})
slip={s:max((Vector(f[s])-Vector(feet[0][s])).length for f in feet) for s in ['L','R']}
report={'revision':3,'foot_plant_max_displacement_m':slip,'pose_samples':pose,'hand_prop_contacts':contacts,'limits':'contact proxies and hand/prop mesh samples; not full mesh cloth validation'}
assert max(slip.values())<.006,slip
assert all(r['penetrating_vertices']==0 for r in contacts)
assert all(65<r['knee_flexion_degrees'][s]<120 for r in pose if r['time']>=30 for s in ['L','R'])
(OUT/'motion-readback.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
build=json.loads((OUT/'build-report.json').read_text(encoding='utf-8'));build.pop('max_hand_target_error',None);build.pop('build_seconds',None);build.update(revision=3,hand_prop_contacts=contacts,motion_readback='motion-readback.json',source_scene='blender/source/phainon-wheat-base.blend');(OUT/'build-report.json').write_text(json.dumps(build,ensure_ascii=False,indent=2),encoding='utf-8')
print('MOTION_READBACK_PASSED',json.dumps(slip),flush=True)
