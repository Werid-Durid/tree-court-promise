"""Read saved source scenes back and verify study-loop boundary continuity."""
import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];results=[]
for cid in ['anaxa','hyacine','castor','phainon']:
 path=ROOT/f'blender/build/study-companions/{cid}/{cid}_study.blend'
 bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE')
 states=[]
 for frame in [1,481]:
  scene.frame_set(frame);bpy.context.view_layer.update()
  states.append({p.name:(p.matrix.translation.copy(),p.matrix.to_quaternion()) for p in arm.pose.bones})
 max_position=max((states[0][n][0]-states[1][n][0]).length for n in states[0])
 angles=[states[0][n][1].rotation_difference(states[1][n][1]).angle for n in states[0]]
 # Quaternion q and -q encode the same rotation.
 max_angle=max(min(angle,abs(2*math.pi-angle)) for angle in angles)
 assert max_position<.004,(cid,max_position)
 assert max_angle<.025,(cid,math.degrees(max_angle))
 result=dict(character=cid,bones=len(states[0]),loop_endpoint_position_error_m=max_position,loop_endpoint_rotation_error_degrees=math.degrees(max_angle),passed=True)
 results.append(result)
(ROOT/'blender/build/study-companions/loop-continuity-verification.json').write_text(json.dumps({'passed':True,'characters':results},indent=2),encoding='utf-8')
print('FOUR_STUDY_LOOP_BOUNDARIES_VERIFIED',json.dumps(results),flush=True)
