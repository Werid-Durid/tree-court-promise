"""物理烘焙验证 3：build_rig -> 物理 -> nla.bake(only_selected=False) -> 统计头发 F-Curve。"""
import bpy
from mathutils import Quaternion

ROOT = r'D:\开发项目\树庭学习室\tree_court'
bpy.ops.wm.open_mainfile(filepath=ROOT + r'\blender\physics\anaxa.blend')
root = next(o for o in bpy.data.objects if getattr(o, 'mmd_type', None) == 'ROOT')
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.mmd_tools.build_rig()
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
pb = arm.pose.bones

for f, ang in [(1, 0.0), (12, 0.6), (24, 0.0), (36, -0.6), (48, 0.0)]:
    scene.frame_set(f)
    pb['上半身'].rotation_mode = 'QUATERNION'
    pb['上半身'].rotation_quaternion = Quaternion((0, 0, 1), ang)
    pb['上半身'].keyframe_insert('rotation_quaternion')

scene.frame_start = 1
scene.frame_end = 48
scene.rigidbody_world.enabled = True
bpy.ops.ptcache.bake_all(bake=True)

bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.nla.bake(frame_start=1, frame_end=48, step=1, only_selected=False,
                 visual_keying=True, clear_constraints=False, use_current_action=True,
                 bake_types={'POSE'})
action = arm.animation_data.action


def all_fcurves(act):
    out = []
    for layer in getattr(act, 'layers', []):
        for strip in getattr(layer, 'strips', []):
            for slot in getattr(act, 'slots', []):
                try:
                    bag = strip.channelbag(slot)
                except Exception:
                    bag = None
                if bag:
                    out += list(bag.fcurves)
    if not out and hasattr(act, 'fcurves'):
        out = list(act.fcurves)
    return out


fcurves = all_fcurves(action)
paths = sorted({fc.data_path for fc in fcurves})
hair = [p for p in paths if '側髪' in p or '前髪' in p or '後髪' in p]
print('FCURVES', len(fcurves), 'PATHS', len(paths), flush=True)
print('HAIR_PATHS', len(hair), hair[:4], flush=True)
print('BAKE_HAIR_OK' if hair else 'BAKE_HAIR_MISSING')
