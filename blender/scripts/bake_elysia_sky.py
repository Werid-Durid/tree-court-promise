"""Bake the supplied Blender world for the browser's unlit sky dome."""
import bpy,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'blender/build/phainon-elysia'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'phainon_wheat_film.blend'));scene=bpy.context.scene
for obj in scene.objects:obj.hide_render=True
camera=bpy.data.objects.new('Elysia Sky Bake',bpy.data.cameras.new('Elysia Sky Bake'));scene.collection.objects.link(camera);camera.rotation_euler=(math.pi/2,0,0);camera.data.type='PANO';camera.data.panorama_type='EQUIRECTANGULAR';scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.resolution_x=2048;scene.render.resolution_y=1024;scene.render.resolution_percentage=100;scene.render.filepath=str(OUT/'sky.png');bpy.ops.render.render(write_still=True)
