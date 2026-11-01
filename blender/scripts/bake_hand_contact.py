"""派生坐姿动画的桌面接触修正；采样骨骼旋转，不拉伸网格，也不改原模型。"""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];cid=sys.argv[-1];assert cid in ('castor','phainon')
BASE=ROOT/'blender/build/spatial-repair/characters/classroom';OUT=ROOT/'blender/build/spatial-repair/hand-contact';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/(cid+'.blend')));scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE');pb=arm.pose.bones
meta=json.loads((ROOT/f'blender/animation-reports/{cid}.json').read_text(encoding='utf-8'));scale=meta['target_height']/meta['rest_height'];height=.915/scale+meta['rest_floor'];poses={};max_error=0.
def aim(bone,end,target):
 start=bone.head.copy();q=(end-start).normalized().rotation_difference((target-start).normalized());m=bone.matrix.copy();p=m.translation.copy();m=q.to_matrix().to_4x4()@m;m.translation=p;bone.matrix=m;bpy.context.view_layer.update()
names=[stem+'.'+side for side in ('L','R') for stem in ('腕','ひじ','手首')]
# 动作较慢，六帧/秒的接触控制点再由成品导出器逐帧烘焙；保留原有抬手动作。
for frame in range(scene.frame_start,scene.frame_end+1,4):
 scene.frame_set(frame)
 for side in ('L','R'):
  upper,elbow,hand=[pb[stem+'.'+side] for stem in ('腕','ひじ','手首')];a,b,c=upper.head.copy(),elbow.head.copy(),hand.head.copy()
  if c.z<height:
   target=c.copy();target.z=height;hand_rotation=hand.matrix.to_quaternion();l1,l2=(b-a).length,(c-b).length;direction=target-a;d=min(direction.length,l1+l2-.0001);direction.normalize();target=a+direction*d;along=(l1*l1-l2*l2+d*d)/(2*d);bend=b-a-direction*(b-a).dot(direction)
   if bend.length<.00001:bend=Vector((1 if side=='L' else -1,0,0))
   knee=a+direction*along+bend.normalized()*math.sqrt(max(0,l1*l1-along*along));aim(upper,b,knee);aim(elbow,hand.head.copy(),target);hand.matrix=Matrix.LocRotScale(hand.head.copy(),hand_rotation,hand.matrix.to_scale());bpy.context.view_layer.update();max_error=max(max_error,(hand.head-target).length*scale)
 poses[frame]={n:pb[n].rotation_quaternion.copy() for n in names}
action=arm.animation_data.action
paths={pb[n].path_from_id('rotation_quaternion') for n in names}
for layer in action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in list(bag.fcurves):
    if fc.data_path in paths:bag.fcurves.remove(fc)
for frame,values in poses.items():
 for name,q in values.items():pb[name].rotation_quaternion=q;pb[name].keyframe_insert(data_path='rotation_quaternion',frame=frame)
for layer in action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    if fc.data_path in paths:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
scene.frame_set(scene.frame_start);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(cid+'.blend')))
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers):o.select_set(True)
arm.select_set(True);bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=str(OUT/(cid+'.glb')),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIVE_ACTIONS',export_frame_range=True,export_force_sampling=True,export_skins=True,export_morph=True)
bpy.ops.export_scene.fbx(filepath=str(OUT/(cid+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0.)
sys.path.insert(0,str(ROOT/'blender'));from normalize_motion_glb import normalize;normalize(OUT/(cid+'.glb'))
(OUT/(cid+'.json')).write_text(json.dumps({'character':cid,'control_frames':len(poses),'max_target_error_m':max_error,'fbx':str(OUT/(cid+'.fbx'))},ensure_ascii=False,indent=2),encoding='utf-8');print('HAND_CONTACT_BAKED',cid,max_error)
