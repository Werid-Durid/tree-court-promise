"""以成片相同设置渲染 25–33 秒连续动作；后续全片复用这些帧。"""
import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'blender/build/phainon-film-v3'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'phainon_wheat_film.blend'))
scene=bpy.context.scene;scene.frame_start=601;scene.frame_end=792;scene.render.use_sequencer=False;scene.render.filepath=str(OUT/'frames/frame-');bpy.ops.render.render(animation=True)
for marker in list(scene.timeline_markers):scene.timeline_markers.remove(marker)
cam=bpy.data.objects.new('Full body motion proof',bpy.data.cameras.new('Full body motion proof'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.lens=43
cam.location=(2.6,-3.3,1.75);cam.rotation_euler=(Vector((0,.1,.91))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_percentage=60;scene.eevee.taa_render_samples=12;folder=OUT/'motion-review';folder.mkdir(exist_ok=True);scene.render.filepath=str(folder/'frame-');bpy.ops.render.render(animation=True)
