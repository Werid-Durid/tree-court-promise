"""为每个选项单独渲染角色回应，不以同一静帧代替分支演出。"""
import bpy,json,math,sys,os
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1];CFG=json.loads((ROOT/os.environ.get('TREECOURT_FILM_SPEC','data/cinematics/phainon-wheat.json')).read_text(encoding='utf-8'));OUT=ROOT/CFG['output_dir'];FPS=CFG['fps']
sys.path.insert(0,str(ROOT/'blender'))
from phainon_motion import SecondaryMotion,write_channels,smooth_secondary_action,ramp
from collections import defaultdict
for cue in CFG['interactions']:
 for choice in cue['choices']:
  ident=cue['id']+'-'+choice['id'];folder=OUT/'responses'/ident;frames=folder/'frames';frames.mkdir(parents=True,exist_ok=True)
  bpy.ops.wm.open_mainfile(filepath=str(OUT/'phainon_wheat_film.blend'));scene=bpy.context.scene;scene.frame_set(round(cue['at']*FPS)+1);bpy.context.view_layer.update()
  arm=next(o for o in scene.objects if o.type=='ARMATURE');basis={p.name:p.matrix_basis.copy() for p in arm.pose.bones};head=arm.pose.bones.get('頭');neck=arm.pose.bones.get('首')
  if arm.animation_data:arm.animation_data_clear()
  for p in arm.pose.bones:p.matrix_basis=basis[p.name];p.rotation_mode='QUATERNION'
  hq=head.rotation_quaternion.copy();nq=neck.rotation_quaternion.copy()
  chest=arm.pose.bones.get('上半身2');cq=chest.rotation_quaternion.copy()
  for marker in list(scene.timeline_markers):scene.timeline_markers.remove(marker)
  cam=bpy.data.objects.new('Player_response_camera',bpy.data.cameras.new('Player_response_camera'));scene.collection.objects.link(cam)
  cam.location=(.45,-2.35,1.60) if cue['id']=='waymark' else (.43,-1.76,1.16);target=Vector((0,0,1.43 if cue['id']=='waymark' else 1.08));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=56 if cue['id']=='waymark' else 60
  cam.data.dof.use_dof=True;cam.data.dof.focus_distance=(target-cam.location).length;cam.data.dof.aperture_fstop=5.6;scene.camera=cam
  if CFG.get('revision',1)>=3 and cue['id']=='name':
   cam.location=(.45,-1.84,1.23);target=Vector((0,.25,1.18));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.dof.focus_distance=(target-cam.location).length
  face_objects=[o for o in scene.objects if o.type=='MESH' and o.data.shape_keys]
  for obj in face_objects:
   obj.data.shape_keys.animation_data_clear()
  envelope=json.loads((folder/'lip-sync.json').read_text(encoding='utf-8'))['values'];count=round(choice['duration']*FPS)
  secondary=SecondaryMotion(arm,FPS) if CFG.get('revision',1)>=3 else None
  channels=defaultdict(list);disabled=[]
  if secondary:
   for obj in scene.objects:
    for modifier in obj.modifiers:
     if modifier.type=='ARMATURE' and modifier.show_viewport:modifier.show_viewport=False;disabled.append(modifier)
  for f in range(1,count+1,1 if secondary else 2):
   scene.frame_set(f)
   if secondary:
    for p in arm.pose.bones:p.matrix_basis=basis[p.name]
   t=(f-1)/FPS;phase=math.sin(math.pi*t/choice['duration'])
   head.rotation_quaternion=hq@Quaternion((1,0,0),(.05 if choice['pose']!='shy_nod' else .085)*phase)@Quaternion((0,0,1),.04*phase if choice['pose']=='gentle_tilt' else 0)
   neck.rotation_quaternion=nq@Quaternion((1,0,0),.018*math.sin(t*1.5)*phase)
   if secondary:chest.rotation_quaternion=cq@Quaternion((1,0,0),.003*math.sin(t*1.45)*phase)
   if secondary:
    bpy.context.view_layer.update();secondary.step(t)
    for p in [head,neck,chest,*secondary.bones]:
     for i,value in enumerate(p.rotation_quaternion):channels[(p.path_from_id('rotation_quaternion'),i)].append((f,value))
   else:
    head.keyframe_insert(data_path='rotation_quaternion',frame=f);neck.keyframe_insert(data_path='rotation_quaternion',frame=f)
   for obj in face_objects:
    keys=obj.data.shape_keys.key_blocks
    blink=ramp(t,1.38,1.47)*(1-ramp(t,1.50,1.66))
    for name,value in {'あ':.085*envelope[f-1],'い':.024*envelope[f-1],'まばたき':blink,'口角上げ':.11+.05*phase,'慈愛':.10,'喜び':.06+.05*phase}.items():
     if name in keys:keys[name].value=value;keys[name].keyframe_insert(data_path='value',frame=f)
  if secondary:
   write_channels(arm,'Phainon response '+ident,channels);continuity=smooth_secondary_action(arm);(folder/'motion-continuity.json').write_text(json.dumps(continuity,indent=2),encoding='utf-8')
  for modifier in disabled:modifier.show_viewport=True
  scene.frame_start=1;scene.frame_end=count;scene.render.use_sequencer=False;scene.render.filepath=str(frames/'frame-');scene.frame_set(1)
  print('RESPONSE_RENDER_START',ident,flush=True)
  if '--stream' in sys.argv:
   from companion_video import render_video
   bpy.context.preferences.filepaths.save_version=0
   bpy.ops.wm.save_as_mainfile(filepath=str(folder/'response.blend'))
   render_video(scene,OUT/(ident+'.mp4'),choice['duration'],folder/'soundtrack.wav')
  else:bpy.ops.render.render(animation=True)
  print('RESPONSE_RENDER_DONE',ident,flush=True)
