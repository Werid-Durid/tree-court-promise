"""Render the published classroom chair from the side, at seated eye height."""
import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/build/cinematic-classroom/story_classroom.blend'))
scene=bpy.context.scene
camera=bpy.data.objects.new('Chair structure review',bpy.data.cameras.new('Chair structure review'));scene.collection.objects.link(camera)
camera.location=(1.65,-1.95,.85);target=Vector((.6,-.62,.48));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=55;scene.camera=camera
data=bpy.data.lights.new('Review soft light','AREA');data.energy=600;data.size=5;light=bpy.data.objects.new('Review soft light',data);scene.collection.objects.link(light);light.location=(0,-2,4);light.rotation_euler=(Vector((.6,-.62,.4))-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1100;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=16;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'blender/build/cinematic-classroom/chair-repair-review.png')
bpy.ops.render.render(write_still=True)
