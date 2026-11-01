"""在动画副本中做坐姿服装接触修形；保留顶点、UV、材质及全部表情。
按蒙皮矩阵逆算模型空间位移，再同量移动全部形态键，防止表情切换还原穿模。
不是布料仿真：仅针对当前固定课堂座位，重新改座位后须重跑采样。
"""
import bpy,json,math,numpy as np,shutil,datetime,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'blender/build/classroom-paired';EXPORT=OUT/'characters';EXPORT.mkdir(parents=True,exist_ok=True)
cfg=json.loads((OUT/'motion.json').read_text(encoding='utf-8'))
layout=json.loads((OUT/'layout.json').read_text(encoding='utf-8'))
backup=ROOT/'blender/animation-backups/seated-clearance-v2';backup.mkdir(parents=True,exist_ok=True)
report=[]
IDS=[a for a in sys.argv[sys.argv.index('--')+1:]] if '--' in sys.argv else ['castor','phainon']
for cid in IDS:
 path=EXPORT/f'{cid}.blend'
 for ext in ['blend','glb','fbx']:
  source=ROOT/f'blender/animated/{cid}.{ext}';target=backup/source.name
  if not target.exists():shutil.copy2(source,target)
 bpy.ops.wm.open_mainfile(filepath=str(backup/path.name))
 spec=cfg['characters'][cid];meta=json.loads((ROOT/f'blender/animation-reports/{cid}.json').read_text(encoding='utf-8'))
 scale=spec['height']/meta['rest_height'];yaw=spec['yaw'];pos=np.array(spec['position']);floor=meta.get('rest_floor',0)
 R=np.array([[math.cos(yaw),-math.sin(yaw),0],[0,0,1],[-math.sin(yaw),-math.cos(yaw),0.]])
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
 total=0;maxshift=0
 for iteration in range(5):
  changed=0
  for seconds in [0,6,12,18,24]:
   bpy.context.scene.frame_set(1+seconds*24);dep=bpy.context.evaluated_depsgraph_get()
   for obj in meshes:
    arm=next(m.object for m in obj.modifiers if m.type=='ARMATURE');evaluated=obj.evaluated_get(dep);mesh=evaluated.to_mesh()
    verts=np.array([obj.matrix_world@v.co for v in mesh.vertices]);pts=verts@R.T*scale+pos;pts[:,1]-=floor*scale
    delta=np.zeros_like(pts)
    for c in layout['colliders']:
     if not any(k in c['name'] for k in ['Desk','Chair']):continue
     center=np.array(c['center']);half=np.array(c['size'])/2+.012
     q=pts+delta-center;inside=np.all(np.abs(q)<half,axis=1)
     for idx in np.where(inside)[0]:
      distances=half-np.abs(q[idx]);axis=int(np.argmin(distances))
      # 坐垫中央优先向上托住皮肤和衣料；边缘允许自然垂到坐垫外。
      if 'Seat' in c['name'] and abs(q[idx,0])<half[0]*.65 and abs(q[idx,2])<half[2]*.65:axis=1
      sign=1 if q[idx,axis]>=0 else -1
      if 'Seat' in c['name'] and axis==1:sign=1
      delta[idx,axis]+=sign*half[axis]-q[idx,axis]
    indices=np.where(np.linalg.norm(delta,axis=1)>.0001)[0]
    if len(indices):
     correction=np.zeros((len(obj.data.vertices),3),dtype=np.float32)
     matrices={g.index:np.array(arm.matrix_world@arm.pose.bones[g.name].matrix@arm.data.bones[g.name].matrix_local.inverted()@arm.matrix_world.inverted()@obj.matrix_world)[:3,:3] for g in obj.vertex_groups if g.name in arm.pose.bones}
     for idx in indices:
      transform=np.zeros((3,3));weight=0
      for g in obj.data.vertices[int(idx)].groups:
       if g.group in matrices:transform+=matrices[g.group]*g.weight;weight+=g.weight
      if weight<.001:continue
      transform/=weight
      correction[idx]=np.linalg.lstsq(transform,delta[idx]@R/scale,rcond=None)[0]
     # 保留所有形态键的相对偏移，改动局限在动画导出副本。
     for key in obj.data.shape_keys.key_blocks if obj.data.shape_keys else []:
      a=np.empty(len(correction)*3,dtype=np.float32);key.data.foreach_get('co',a);a=a.reshape(-1,3)+correction;key.data.foreach_set('co',a.ravel())
     a=np.empty(len(correction)*3,dtype=np.float32);obj.data.vertices.foreach_get('co',a);obj.data.vertices.foreach_set('co',(a.reshape(-1,3)+correction).ravel());obj.data.update()
     changed+=len(indices);total+=len(indices);maxshift=max(maxshift,float(np.linalg.norm(correction,axis=1).max()*scale))
    evaluated.to_mesh_clear()
  if not changed:break
 bpy.context.scene.frame_set(1)
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(path))
 bpy.ops.object.select_all(action='DESELECT')
 for o in meshes:o.select_set(True)
 arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');arm.select_set(True);bpy.context.view_layer.objects.active=arm
 bpy.ops.export_scene.gltf(filepath=str(EXPORT/f'{cid}.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIVE_ACTIONS',export_frame_range=True,export_force_sampling=True,export_skins=True,export_morph=True)
 bpy.ops.export_scene.fbx(filepath=str(EXPORT/f'{cid}.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0.0)
 import sys
 sys.path.insert(0,str(ROOT/'blender'))
 from normalize_motion_glb import normalize
 normalize(EXPORT/f'{cid}.glb')
 report.append({'id':cid,'corrected_vertex_visits':total,'max_step_m':maxshift,'iterations':iteration+1,'backup':str(backup/path.name)})
(OUT/'seated-clearance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(report)
