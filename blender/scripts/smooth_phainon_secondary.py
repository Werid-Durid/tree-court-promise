"""对物理骨链烘焙曲线做四元数连续性和平滑检查，保留原有坐姿基形。"""
import bpy,json,math
from pathlib import Path
from mathutils import Quaternion,Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'blender/build/phainon-film-v3'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'phainon_wheat_film.blend'));scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE');action=arm.animation_data.action
bag=action.layers[0].strips[0].channelbag(arm.animation_data.action_slot);groups={}
for fc in bag.fcurves:
 if fc.data_path.endswith('rotation_quaternion') and any(word in fc.data_path for word in ['髪','下摆','披肩']):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
def delta(a,b):return 2*math.acos(min(1,abs(a.dot(b))))
before=0.;after=0.
for path,channels in groups.items():
 if set(channels)!={0,1,2,3}:continue
 values=[Quaternion(tuple(channels[j].keyframe_points[i].co.y for j in range(4))).normalized() for i in range(len(channels[0].keyframe_points))]
 before=max(before,max(delta(a,b) for a,b in zip(values,values[1:])))
 for _ in range(2):values=[values[0]]+[values[i].slerp(values[i-1].slerp(values[i+1],.5),.4) for i in range(1,len(values)-1)]+[values[-1]]
 limit=math.radians(3 if '髪' in path else 4.5)
 for i in range(1,len(values)):
  step=delta(values[i-1],values[i])
  if step>limit:values[i]=values[i-1].slerp(values[i],limit/step)
 after=max(after,max(delta(a,b) for a,b in zip(values,values[1:])))
 for j,fc in channels.items():
  for i,q in enumerate(values):fc.keyframe_points[i].co.y=q[j]
  fc.update()
bpy.context.preferences.filepaths.save_version=0;scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'phainon_wheat_film.blend'))
report={'bones':len(groups),'max_adjacent_frame_rotation_before_degrees':math.degrees(before),'max_adjacent_frame_rotation_after_degrees':math.degrees(after),'method':'two-pass quaternion smoothing plus per-frame angular speed limit'}
(OUT/'motion-continuity.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('CONTINUITY_CHECKED',report,flush=True)
# 重新审看经过平滑后的最终动作，工程中的镜头标记保持不变。
for marker in list(scene.timeline_markers):scene.timeline_markers.remove(marker)
cam=bpy.data.objects.new('Final motion readback view',bpy.data.cameras.new('Final motion readback view'));scene.collection.objects.link(cam);cam.data.lens=43;cam.location=(2.6,-3.3,1.75);cam.rotation_euler=(Vector((0,.1,.91))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
for t in [28,30,31]:
 scene.frame_set(1+24*t);scene.render.filepath=str(OUT/f'body-{t}.png');bpy.ops.render.render(write_still=True)
