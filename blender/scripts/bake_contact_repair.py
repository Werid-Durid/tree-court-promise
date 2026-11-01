"""将 D 腿骨的绑定姿态跟随烘焙到派生动画，供 UE5/非网页播放器使用。原文件不覆盖。"""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'blender/build/spatial-repair/characters';OUT.mkdir(parents=True,exist_ok=True)
JOBS=[('classroom','anaxa',ROOT/'blender/animated/anaxa.blend'),('classroom','hyacine',ROOT/'blender/animated/hyacine.blend'),('classroom','castor',ROOT/'blender/build/classroom-paired/characters/castor.blend'),('classroom','phainon',ROOT/'blender/build/classroom-paired/characters/phainon.blend'),('study','anaxa',ROOT/'blender/study/anaxa.blend')]
report=[]
for mode,cid,path in JOBS:
 bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE');action=arm.animation_data.action;name=action.name
 links=[(arm.pose.bones.get(stem+'D.'+side),arm.pose.bones.get(stem+'.'+side)) for stem in ['足','ひざ','足首'] for side in ['L','R']];links=[(a,b) for a,b in links if a and b]
 offsets={a.name:b.bone.matrix_local.inverted()@a.bone.matrix_local for a,b in links}
 for frame in range(scene.frame_start,scene.frame_end+1):
  scene.frame_set(frame)
  for target,source in links:
   target.matrix=source.matrix@offsets[target.name];bpy.context.view_layer.update()
   for prop in ('location','rotation_quaternion','scale'):target.keyframe_insert(data_path=prop,frame=frame)
 folder=OUT/mode;folder.mkdir(exist_ok=True);scene.frame_set(scene.frame_start)
 # 仅导出当前已烘焙动作，避免控制动作与成品动作在播放器中混用。
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(folder/(cid+'.blend')))
 bpy.ops.object.select_all(action='DESELECT')
 for o in scene.objects:
  if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers):o.select_set(True)
 arm.select_set(True);bpy.context.view_layer.objects.active=arm
 bpy.ops.export_scene.gltf(filepath=str(folder/(cid+'.glb')),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIVE_ACTIONS',export_frame_range=True,export_force_sampling=True,export_skins=True,export_morph=True)
 bpy.ops.export_scene.fbx(filepath=str(folder/(cid+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0.)
 sys.path.insert(0,str(ROOT/'blender'));from normalize_motion_glb import normalize;normalize(folder/(cid+'.glb'),name)
 report.append(dict(mode=mode,character=cid,clip=name,frames=scene.frame_end-scene.frame_start+1,corrected_bones=len(links),glb=str(folder/(cid+'.glb')),fbx=str(folder/(cid+'.fbx'))))
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('CONTACT_BAKED',report)
