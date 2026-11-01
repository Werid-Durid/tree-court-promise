"""把物理烘焙进课堂四人的动作：追加动作 -> 刚体缓存 -> 视觉烘焙 -> 导出角色 GLB。"""
import bpy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIPS = {
    'anaxa': 'TC_Anaxa_TeachPace',
    'hyacine': 'TC_Hyacine_Assist',
    'castor': 'TC_Castorice_Seated',
    'phainon': 'TC_Phainon_Seated',
}
OUT = ROOT / 'blender/physics'
OUT.mkdir(parents=True, exist_ok=True)

import re
import math as _math


def all_fcurves_global(a):
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


def clamp_physics(action, names, max_deg=32, max_loc=.05):
    """把物理骨骼的烘焙结果钳制到可信范围，避免发饰/披风在极端碰撞下炸开。"""
    groups = {}
    for fc in all_fcurves_global(action):
        m = re.match(r'pose\.bones\["(.+)"\]\.(rotation_quaternion|location)', fc.data_path)
        if not m or m.group(1) not in names:
            continue
        groups.setdefault((m.group(1), m.group(2)), {})[fc.array_index] = fc
    for (bone, path), fcs in groups.items():
        if path == 'rotation_quaternion' and set(fcs) == {0, 1, 2, 3}:
            n = min(len(fcs[i].keyframe_points) for i in range(4))
            lim = _math.radians(max_deg)
            for k in range(n):
                q = [fcs[i].keyframe_points[k].co[1] for i in range(4)]
                w, v = q[3], q[:3]
                vlen = _math.sqrt(sum(x * x for x in v))
                if 2 * _math.atan2(vlen, abs(w)) > lim:
                    s = _math.sin(lim / 2) / max(vlen, 1e-6)
                    v = [x * s for x in v]
                    w = _math.copysign(_math.cos(lim / 2), w)
                    q = v + [w]
                    for i in range(4):
                        fcs[i].keyframe_points[k].co[1] = q[i]
        elif path == 'location' and set(fcs) == {0, 1, 2}:
            n = min(len(fcs[i].keyframe_points) for i in range(3))
            for k in range(n):
                for i in range(3):
                    kp = fcs[i].keyframe_points[k]
                    kp.co[1] = max(-max_loc, min(max_loc, kp.co[1]))
    for fcs in groups.values():
        for fc in fcs.values():
            fc.update()


def freeze_physics(action, names):
    """物理骨骼归零到静止：极端碰撞下的烘焙结果会炸开披肩/发饰，宁可静止。"""
    for fc in all_fcurves_global(action):
        m = re.match(r'pose\.bones\["(.+)"\]\.(rotation_quaternion|location)', fc.data_path)
        if not m or m.group(1) not in names:
            continue
        target = 1.0 if (m.group(2) == 'rotation_quaternion' and fc.array_index == 3) else 0.0
        for kp in fc.keyframe_points:
            kp.co[1] = target
        fc.update()


reports = []
IDS = [a for a in sys.argv[sys.argv.index('--') + 1:]] if '--' in sys.argv else list(CLIPS)
for cid in IDS:
    action_name = CLIPS[cid]
    start = time.time()
    try:
        bpy.ops.wm.open_mainfile(filepath=str(OUT / f'{cid}.blend'))
        scene = bpy.context.scene
        arm = next(o for o in scene.objects if o.type == 'ARMATURE')
        with bpy.data.libraries.load(str(ROOT / 'blender/animated' / f'{cid}.blend'), link=False) as (src, dst):
            dst.actions = [n for n in src.actions if n == action_name]
        act = dst.actions[0]
        if arm.animation_data is None:
            arm.animation_data_create()
        arm.animation_data.action = act
        try:
            if getattr(act, 'slots', None) and not arm.animation_data.action_slot:
                arm.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
        scene.frame_start = 1
        scene.frame_end = 577
        scene.render.fps = 24
        if scene.rigidbody_world:
            scene.rigidbody_world.enabled = True
        bpy.ops.ptcache.bake_all(bake=True)
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
        bpy.ops.object.select_all(action='DESELECT')
        for o in bpy.data.objects:
            if o.type == 'ARMATURE':
                o.select_set(True)
            elif o.type == 'MESH' and (getattr(o, 'mmd_type', '') or 'NONE') in ('NONE', ''):
                o.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.export_scene.gltf(filepath=str(OUT / f'{cid}_classroom.glb'),
                                  use_selection=True, export_format='GLB',
                                  export_animations=True, export_animation_mode='ACTIONS')
        bpy.ops.export_scene.fbx(filepath=str(OUT / f'{cid}_classroom.fbx'),
                                 use_selection=True, object_types={'MESH', 'ARMATURE'},
                                 add_leaf_bones=False, bake_anim=True, path_mode='COPY',
                                 embed_textures=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f'{cid}_baked.blend'))
        reports.append({'id': cid, 'clip': action_name, 'status': 'exported',
                        'fcurves': len(fcurves), 'hair_curves': len(hair),
                        'elapsed': round(time.time() - start, 1)})
        print('CLASSROOM_PHYSICS ' + json.dumps(reports[-1], ensure_ascii=False), flush=True)
    except Exception as exc:
        reports.append({'id': cid, 'status': 'error', 'error': str(exc)})
        print('CLASSROOM_ERROR ' + cid + ' ' + str(exc), flush=True)
    (OUT / 'report_classroom.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf-8')
print('CLASSROOM_DONE')
