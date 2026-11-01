import bpy,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'blender'));from companion_video import render_video
O=R/'blender/build/phainon-elysia';bpy.ops.wm.open_mainfile(filepath=str(O/'phainon_wheat_film.blend'));s=bpy.context.scene;s.render.resolution_percentage=100
render_video(s,O/'interactive.mp4',74,O/'soundtrack.wav')
print('ELYSIA_MAIN_RENDERED',flush=True)
