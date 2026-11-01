"""在第二版场景副本重做动作，不覆盖已交付工程和影片。"""
import bpy,json,sys,math,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'))
from phainon_motion import Performance,SecondaryMotion,ramp,pulse,write_channels
from collections import defaultdict
OUT=ROOT/'blender/build/phainon-film-v3';OUT.mkdir(exist_ok=True)
BASE=ROOT/'blender/source/phainon-wheat-base.blend'
cfg=json.loads((ROOT/'data/cinematics/phainon-wheat.json').read_text(encoding='utf-8'));cfg.update(id='phainon-wheat-03',revision=3,output_dir='blender/build/phainon-film-v3')
(ROOT/'data/cinematics/phainon-wheat-v3.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.open_mainfile(filepath=str(BASE));scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE')
# 独立圆凳给长衣摆留下四周的垂落空间，玩家座位放在旁边。
wood=bpy.data.materials['Film_wood']
for obj in list(scene.objects):
 if obj.name.startswith('Bench leg'):bpy.data.objects.remove(obj,do_unlink=True)
bench=bpy.data.objects['Bench seat'];bench.location=(1.02,.32,.43);bench.dimensions=(.86,.58,.12)
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.17,depth=.12,location=(0,.32,.43));stool=bpy.context.object;stool.name='Phainon round stool';stool.data.materials.append(wood);edge=stool.modifiers.new('Rounded stool rim','BEVEL');edge.width=.018;edge.segments=3;stool.modifiers.new('Stool normals','WEIGHTED_NORMAL')
for x,y in [(-.10,.22),(.10,.22),(-.10,.42),(.10,.42),(.69,.13),(1.35,.13),(.69,.51),(1.35,.51)]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,.20));leg=bpy.context.object;leg.name='Separate seat leg';leg.dimensions=(.065,.065,.40);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);leg.data.materials.append(wood)
bpy.context.preferences.filepaths.save_version=0;arm.animation_data_clear();performance=Performance(arm);physics=SecondaryMotion(arm,cfg['fps'])
meshes=[o for o in scene.objects if o.type=='MESH' and o.data.shape_keys]
for obj in meshes:obj.data.shape_keys.animation_data_clear()
disabled=[]
for obj in scene.objects:
 for modifier in obj.modifiers:
  if modifier.type=='ARMATURE' and modifier.show_viewport:modifier.show_viewport=False;disabled.append(modifier)
arm_channels=defaultdict(list);shape_channels={obj.name:defaultdict(list) for obj in meshes}
envelope=json.loads((OUT/'lip-sync.json').read_text(encoding='utf-8'))['values'];body_names=['センター','上半身','上半身1','上半身2','首','頭','両目','目.L','目.R']+[stem+'.'+s for s in ['L','R'] for stem in ['足ＩＫ','腕','ひじ','手首']]
finger_names=[p.name for p in arm.pose.bones if '指' in p.name and not p.name.startswith('_')];animated=set(body_names+finger_names+[p.name for p in physics.bones]);rows=[]
blinks=[7.3,12.05,18.8,24.65,26.85,29.48,33.4,39.5,45.7,49.1,54.6,61.2,67.6,71.2]
for frame in range(1,cfg['duration']*cfg['fps']+1):
 scene.frame_set(frame);t=(frame-1)/cfg['fps'];pose=performance.pose(t,bpy.context.view_layer.update);physics.step(t)
 for name in animated:
  p=arm.pose.bones[name]
  for i,value in enumerate(p.rotation_quaternion):arm_channels[(p.path_from_id('rotation_quaternion'),i)].append((frame,value))
  if name in ['センター','足ＩＫ.L','足ＩＫ.R']:
   for i,value in enumerate(p.location):arm_channels[(p.path_from_id('location'),i)].append((frame,value))
 blink=0
 for at in blinks:
  d=t-at;blink=max(blink,ramp(d,-.085,0)*(1-ramp(d,.025,.16)))
 smile=.055+.065*pulse(t,6,24,1.2)+.10*ramp(t,54.6,57.2)
 shapes={'まばたき':blink,'口角上げ':smile,'喜び':.035+.045*ramp(t,58.5,63),'慈愛':.04+.065*ramp(t,47.8,52.5),'心配する':.035*pulse(t,49,54.7,1.2),'あ':.085*envelope[frame-1],'い':.024*envelope[frame-1],'脸红':.03*ramp(t,53.5,58)}
 for obj in meshes:
  for key in obj.data.shape_keys.key_blocks:
   if key.name=='Basis':continue
   key.value=shapes.get(key.name,0.)
   if key.name in shapes:shape_channels[obj.name][(key.path_from_id('value'),0)].append((frame,key.value))
 if frame%6==1:
  bpy.context.view_layer.update()
  rows.append({'time':round(t,4),**pose,'ankles':{s:list(arm.pose.bones['足首.'+s].head) for s in ['L','R']},'hips':list(arm.pose.bones['足.L'].head),'knees':{s:list(arm.pose.bones['ひざ.'+s].head) for s in ['L','R']}})
 if frame%120==0:print('MOTION_BAKED',frame,flush=True)
write_channels(arm,'Phainon V3 weight and secondary motion',arm_channels)
for obj in meshes:write_channels(obj.data.shape_keys,'Phainon V3 expression '+obj.name,shape_channels[obj.name])
for modifier in disabled:modifier.show_viewport=True
# 摄影机落座跟随身体节奏；后半段略抬高注视点，匹配有支撑的坐姿。
for marker in scene.timeline_markers:
 cam=marker.camera
 if not cam:continue
 if marker.frame>=22*24+1:
  cam.animation_data_clear()
  a=(marker.frame-1)/24;next_marks=[(m.frame-1)/24 for m in scene.timeline_markers if m.frame>marker.frame];end=min(next_marks) if next_marks else cfg['duration']
  for f in range(round(a*24)+1,round(end*24)+1,2):
   t=(f-1)/24;s=ramp(t,26.5,30.5);cam.location=(.45,-2.40+.56*s,1.59-.36*s);target=Vector((0,.25*s,1.43-.25*s));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
   cam.keyframe_insert(data_path='location',frame=f);cam.keyframe_insert(data_path='rotation_euler',frame=f);cam.data.dof.focus_distance=(target-cam.location).length;cam.data.keyframe_insert(data_path='dof.focus_distance',frame=f)
scene.frame_set(1);scene.render.filepath=str(OUT/'frames/frame-');(OUT/'frames').mkdir(exist_ok=True)
from replace_phainon_environment import replace_environment
replace_environment(scene)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'phainon_wheat_film.blend'))
report={'revision':3,'method':'authored weight transfer and planted-foot IK; 4-substep damped spring bone chains with body capsules and seat proxy','secondary_bones':len(physics.bones),'max_secondary_joint_radians':physics.max_angle,'collision_projections':physics.contacts,'full_mesh_cloth_simulation':False,'samples':rows}
(OUT/'motion-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('MOTION_READY',len(physics.bones),physics.max_angle,flush=True)
if '--preview' in sys.argv:
 for t in [26,27,28,29,30,31,54]:
  scene.frame_set(round(t*24)+1);scene.render.filepath=str(OUT/f'preview-{t}.png');bpy.ops.render.render(write_still=True)
  if t!=54:
   cam=bpy.data.objects.get('Motion_review_camera')
   if cam is None:
    cam=bpy.data.objects.new('Motion_review_camera',bpy.data.cameras.new('Motion_review_camera'));scene.collection.objects.link(cam);cam.data.lens=44
   cam.location=(2.6,-3.3,1.75);target=Vector((0,.10,.91));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
   bindings=[(marker,marker.camera) for marker in scene.timeline_markers]
   for marker,_ in bindings:marker.camera=None
   scene.camera=cam;scene.render.filepath=str(OUT/f'body-{t}.png');bpy.ops.render.render(write_still=True)
   for marker,bound in bindings:marker.camera=bound
