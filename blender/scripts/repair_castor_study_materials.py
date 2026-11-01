"""Repair saved Castor study materials and rerender the already verified animation."""
import bpy,sys,json,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'))
from materials.opaque_atlas import preserve_opaque_atlas_rgb
from companion_video import render_video
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=ROOT/'blender/build/castor-material-fix/castor';OUT.mkdir(parents=True,exist_ok=True);SOURCE=ROOT/'blender/build/study-companions/castor'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'castor_study.blend'));bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.frame_set(1)
meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
# Material repair must preserve every authored animation channel.
def animation_digest():
 data=[]
 for action in bpy.data.actions:
  for layer in action.layers:
   for strip in layer.strips:
    if not hasattr(strip,'channelbags'):continue
    for bag in strip.channelbags:
     for fc in bag.fcurves:data.append((action.name,fc.data_path,fc.array_index,[(float(k.co.x),float(k.co.y)) for k in fc.keyframe_points]))
 return hashlib.sha256(json.dumps(data,separators=(',',':')).encode()).hexdigest()
before=animation_digest();repairs=preserve_opaque_atlas_rgb({m for o in meshes for m in o.data.materials if m});assert repairs
assert before==animation_digest()
report=json.loads((SOURCE/'build-report.json').read_text(encoding='utf-8'));report['media_revision']=3;report['material_fix']={'repairs':repairs,'animation_sha256':before,'animation_unchanged':True,'cause':'premultiplied transparent RGB on opaque alternate clothing atlas'}
(OUT/'build-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'poster.png');bpy.ops.render.render(write_still=True)
for frame in [265,409]:
 scene.frame_set(frame);scene.render.filepath=str(OUT/f'review-{frame}.png');bpy.ops.render.render(write_still=True)
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'castor_study.blend'))
print('CASTOR_MATERIAL_PREVIEW_READY',len(repairs),flush=True)
if '--render' in args:render_video(scene,OUT/'loop.mp4',20);print('CASTOR_MATERIAL_VIDEO_RENDERED',flush=True)
