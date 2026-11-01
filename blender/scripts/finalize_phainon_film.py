"""把对齐后的真实对白包络写入口型，添加音轨并从已审看工程渲染全部帧。"""
import bpy,json,sys,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];CFG=json.loads((ROOT/os.environ.get('TREECOURT_FILM_SPEC','data/cinematics/phainon-wheat.json')).read_text(encoding='utf-8'));OUT=ROOT/CFG.get('output_dir','blender/build/phainon-film')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'phainon_wheat_film.blend'))
scene=bpy.context.scene;envelope=json.loads((OUT/'lip-sync.json').read_text(encoding='utf-8'))['values']
table_camera=bpy.data.objects.get('03 Your table')
if table_camera:
 table_camera.animation_data_clear();table_camera.data.animation_data_clear();table_camera.data.lens=40
 for seconds,position,target in [(14,(.52,-1.98,1.50),(.14,-.70,.79)),(22-1/CFG['fps'],(.49,-1.88,1.47),(.14,-.72,.77))]:
  table_camera.location=position;table_camera.rotation_euler=(Vector(target)-table_camera.location).to_track_quat('-Z','Y').to_euler()
  table_camera.keyframe_insert(data_path='location',frame=1+seconds*CFG['fps']);table_camera.keyframe_insert(data_path='rotation_euler',frame=1+seconds*CFG['fps'])
  table_camera.data.dof.focus_distance=(Vector(target)-table_camera.location).length;table_camera.data.keyframe_insert(data_path='dof.focus_distance',frame=1+seconds*CFG['fps'])
for o in scene.objects:
 if o.type!='MESH' or not o.data.shape_keys:continue
 keys=o.data.shape_keys.key_blocks
 for frame in range(1,CFG['duration']*CFG['fps']+1,2):
  for name,weight in [('あ',.085*envelope[frame-1]),('い',.024*envelope[frame-1])]:
   if name in keys:keys[name].value=weight;keys[name].keyframe_insert(data_path='value',frame=frame)
editor=scene.sequence_editor_create()
strips=getattr(editor,'strips',None)
if strips is None:strips=editor.sequences
if not any(s.type=='SOUND' for s in strips):strips.new_sound('Phainon original AI dialogue and ambient',str(OUT/'soundtrack.wav'),channel=1,frame_start=1)
for sound in bpy.data.sounds:
 if sound.filepath and Path(bpy.path.abspath(sound.filepath)).is_file() and not sound.packed_file:sound.pack()
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_perspective='CAMERA'
   area.spaces.active.shading.type='MATERIAL'
   area.spaces.active.shading.use_scene_world=True
   area.spaces.active.shading.use_scene_lights=True
scene.render.use_sequencer=False
scene.frame_set(1);scene.render.filepath=str(OUT/'frames/frame-')
(OUT/'frames').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'phainon_wheat_film.blend'))
print('FILM_LIP_SYNC_AND_SOUND_READY',flush=True)
if '--preview' in sys.argv:
 scene.frame_set(1+17*CFG['fps']);scene.render.filepath=str(OUT/'preview-17.png');bpy.ops.render.render(write_still=True)
if '--render' in sys.argv:
 scene.render.use_overwrite=False
 # 续渲只跳过已完整写入的 PNG；保留工程原始起始帧。
 start=1
 while start<=scene.frame_end:
  existing=OUT/'frames'/f'frame-{start:04d}.png'
  if not existing.exists() or existing.stat().st_size<1000:break
  start+=1
 if start<=scene.frame_end:
  scene.frame_start=start;bpy.ops.render.render(animation=True)
