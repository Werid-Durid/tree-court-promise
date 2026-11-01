"""只审看坐姿，不等待整条时间轴的物理烘焙。"""
import bpy,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'))
from phainon_motion import Performance,SecondaryMotion
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/source/phainon-wheat-base.blend'))
scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE');arm.animation_data_clear();perf=Performance(arm)
for marker in list(scene.timeline_markers):scene.timeline_markers.remove(marker)
cam=bpy.data.objects.new('Side motion review',bpy.data.cameras.new('Side motion review'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.lens=43
cam.location=(2.6,-3.3,1.75);cam.rotation_euler=(Vector((0,.1,.91))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_percentage=60;scene.eevee.taa_render_samples=12
out=ROOT/'blender/build/phainon-film-v3/pose-check';out.mkdir(exist_ok=True)
for t in [26,28,30,31]:
 scene.frame_set(1+24*t);perf.pose(t,bpy.context.view_layer.update);physics=SecondaryMotion(arm,24)
 for _ in range(8):
  perf.pose(t,bpy.context.view_layer.update);physics.step(t)
 scene.render.filepath=str(out/f'side-{t}.png');bpy.ops.render.render(write_still=True)
