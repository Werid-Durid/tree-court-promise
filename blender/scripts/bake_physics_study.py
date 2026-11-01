"""把物理烘焙进自习室写字循环：追加动作 -> 刚体缓存 -> 视觉烘焙 -> 导出 GLB。"""
import bpy
import json
import re
import math as _math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTION = 'TC_Anaxa_StudyWrite'


def freeze_physics(action, names):
    """物理骨骼归零到静止：极端碰撞下的烘焙结果会炸开披肩/发饰，宁可静止。"""
    for layer in getattr(action, 'layers', []):
        for strip in getattr(layer, 'strips', []):
            for slot in getattr(action, 'slots', []):
                try:
                    bag = strip.channelbag(slot)
                except Exception:
                    bag = None
                if not bag:
                    continue
                for fc in bag.fcurves:
                    m = re.match(r'pose\.bones\["(.+)"\]\.(rotation_quaternion|location)', fc.data_path)
                    if not m or m.group(1) not in names:
                        continue
                    target = 1.0 if (m.group(2) == 'rotation_quaternion' and fc.array_index == 3) else 0.0
                    for kp in fc.keyframe_points:
                        kp.co[1] = target
                    fc.update()
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/physics/anaxa.blend'))
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')

with bpy.data.libraries.load(str(ROOT / 'blender/study/anaxa.blend'), link=False) as (src, dst):
    dst.actions = [n for n in src.actions if n == ACTION]
act = dst.actions[0]
if arm.animation_data is None:
    arm.animation_data_create()
arm.animation_data.action = act
try:
    if getattr(act, 'slots', None) and not arm.animation_data.action_slot:
        arm.animation_data.action_slot = act.slots[0]
except Exception as exc:
    print('SLOT_WARN', exc, flush=True)

scene.frame_start = 1
scene.frame_end = 577
scene.render.fps = 24
if scene.rigidbody_world:
    scene.rigidbody_world.enabled = True
bpy.ops.ptcache.bake_all(bake=True)
print('CACHE_BAKED', flush=True)

bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.nla.bake(frame_start=1, frame_end=577, step=1, only_selected=False,
                 visual_keying=True, clear_constraints=False, use_current_action=True,
                 bake_types={'POSE'})
action = arm.animation_data.action
physics = {b.name for b in arm.pose.bones
           if any(h in b.name for h in ('披肩', '前領', '下摆', '髪', '劉海', '袖', '裾', 'D.', '手捩'))}
# 导出前摘掉这些骨骼的全部约束：否则采样时会把约束结果重新盖回。
for b in arm.pose.bones:
    if b.name in physics:
        for c in list(b.constraints):
            b.constraints.remove(c)


def all_fcurves(a):
    out = []
    for layer in getattr(a, 'layers', []):
        for strip in getattr(layer, 'strips', []):
            for slot in getattr(a, 'slots', []):
                try:
                    bag = strip.channelbag(slot)
                except Exception:
                    bag = None
                if bag:
                    out += list(bag.fcurves)
    if not out and hasattr(a, 'fcurves'):
        out = list(a.fcurves)
    return out


fcurves = all_fcurves(action)
freeze_physics(action, physics)
hair = [fc.data_path for fc in fcurves if '髪' in fc.data_path]
print('BAKED_FCURVES', len(fcurves), 'HAIR', len(hair), flush=True)

bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        o.select_set(True)
    elif o.type == 'MESH' and (getattr(o, 'mmd_type', '') or 'NONE') in ('NONE', ''):
        o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.gltf(filepath=str(ROOT / 'blender/physics/anaxa_study.glb'),
                          use_selection=True, export_format='GLB', export_animations=True,
                          export_animation_mode='ACTIONS')
print('EXPORTED', ROOT / 'blender/physics/anaxa_study.glb', flush=True)
(ROOT / 'blender/physics/report_study.json').write_text(json.dumps(
    {'action': ACTION, 'fcurves': len(fcurves), 'hair_curves': len(hair)}, ensure_ascii=False, indent=2),
    encoding='utf-8')
