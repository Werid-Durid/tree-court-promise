"""style_characters.py —— Step 4：把 Paper Anime Render Helper 基线应用到四位角色。

输入：blender/animated/{cid}.blend（含课堂动画）
输出：assets/characters/styled/{cid}.{blend,glb,fbx} + pics/previews/styled-{cid}-{front,back}.png
不覆盖原始模型；每角色记录处理/跳过的材质数与描边对象数。
"""
import bpy
import math
import json
import addon_utils
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'characters' / 'styled'
OUT.mkdir(parents=True, exist_ok=True)
PREVIEW = ROOT / 'pics' / 'previews'
PREVIEW.mkdir(parents=True, exist_ok=True)

EXT = "bl_ext.user_default.Paperzhu_animehelper_extension"
IDS = ['anaxa', 'castor', 'hyacine', 'phainon']
BASELINE = {
    'color_look': 'AGX_HIGH', 'color_exposure': 0.0,
    'outline_thickness': 0.002, 'toon_threshold': 0.45, 'toon_softness': 0.08,
    'toon_strength': 0.35, 'toon_light_influence': 0.8, 'toon_min_brightness': 0.12,
}
# 同族微调：暗部偏移（style_baseline.md 的角色微调规则）
SHADOW_TINT = {
    'anaxa': (0.60, 0.62, 0.64),   # 冷绿
    'castor': (0.64, 0.60, 0.66),  # 淡紫
    'hyacine': (0.66, 0.62, 0.64), # 粉灰
    'phainon': (0.60, 0.63, 0.68), # 蓝灰
}


def ensure_extension():
    if not hasattr(bpy.types.Scene, 'paper_render_helper'):
        addon_utils.enable(EXT, default_set=True, persistent=True)
    if not hasattr(bpy.types.Scene, 'paper_render_helper'):
        raise RuntimeError('Paper Anime Render Helper 未注册')


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def make_lights(scene):
    for o in [o for o in scene.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(o, do_unlink=True)
    sun_data = bpy.data.lights.new('PortraitSun', 'SUN')
    sun_data.energy = 3.4; sun_data.color = (1.0, 0.94, 0.87)
    sun = bpy.data.objects.new('PortraitSun', sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
    fill_data = bpy.data.lights.new('PortraitFill', 'AREA')
    fill_data.energy = 80.0; fill_data.color = (0.64, 0.78, 0.92); fill_data.size = 5.0
    fill = bpy.data.objects.new('PortraitFill', fill_data)
    scene.collection.objects.link(fill)
    fill.location = (-2.5, 2.5, 2.2); look_at(fill, (0, 0, 1.2))
    return [sun, fill]


report = {}
ensure_extension()

for cid in IDS:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/animated' / f'{cid}.blend'))
    ensure_extension()
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.frame_set(1)
    meshes = [o for o in scene.objects if o.type == 'MESH']
    arm = next((o for o in scene.objects if o.type == 'ARMATURE'), None)

    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]

    st = scene.paper_render_helper
    st.auto_switch_eevee = True
    st.color_look = BASELINE['color_look']; st.color_exposure = BASELINE['color_exposure']
    st.outline_thickness = BASELINE['outline_thickness']
    st.toon_threshold = BASELINE['toon_threshold']; st.toon_softness = BASELINE['toon_softness']
    st.toon_shadow_strength = BASELINE['toon_strength']
    st.toon_light_influence = BASELINE['toon_light_influence']
    st.toon_min_brightness = BASELINE['toon_min_brightness']
    tint = SHADOW_TINT[cid]
    st.toon_shadow_color = (*tint, 1.0)

    bpy.ops.paper_helper.apply_color()
    bpy.ops.paper_helper.apply_toon_shadow()
    bpy.ops.paper_helper.apply_outline()

    outlined = sum(1 for o in meshes if any(m.type == 'SOLIDIFY' for m in o.modifiers))
    materials = {slot.material.name for o in meshes for slot in o.material_slots if slot.material}
    report[cid] = {'meshes': len(meshes), 'materials': len(materials), 'outlined_objects': outlined,
                   'shadow_tint': tint, 'bones': len(arm.data.bones) if arm else 0}

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f'{cid}.blend'))

    # 导出（含动画）
    for o in scene.objects:
        o.select_set(o.type in ('MESH', 'ARMATURE'))
    bpy.context.view_layer.objects.active = arm or meshes[0]
    scene.frame_set(1)
    bpy.ops.export_scene.gltf(filepath=str(OUT / f'{cid}.glb'), use_selection=True, export_format='GLB',
                              export_animations=True, export_animation_mode='ACTIONS',
                              export_force_sampling=True, export_frame_range=True, export_morph=True)
    bpy.ops.export_scene.fbx(filepath=str(OUT / f'{cid}.fbx'), use_selection=True,
                             object_types={'MESH', 'ARMATURE'}, add_leaf_bones=False, bake_anim=True,
                             bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                             bake_anim_simplify_factor=.1, path_mode='COPY', embed_textures=True)

    # 半身头像：前/后 3/4 各一张
    head = None
    if arm:
        pb = arm.pose.bones.get('頭')
        if pb:
            head = arm.matrix_world @ pb.head
    if head is None:
        bb = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
        head = Vector((sum(v.x for v in bb) / len(bb), sum(v.y for v in bb) / len(bb), max(v.z for v in bb) - 0.15))
    cam_data = bpy.data.cameras.new(f'PortraitCam_{cid}'); cam_data.lens = 65
    cam = bpy.data.objects.new(f'PortraitCam_{cid}', cam_data)
    scene.collection.objects.link(cam); scene.camera = cam
    lights = make_lights(scene)
    scene.render.resolution_x = 900; scene.render.resolution_y = 1200
    scene.render.image_settings.file_format = 'PNG'
    target = head + Vector((0, 0, 0.05))
    for view, off in (('front', Vector((0.55, -1.05, 0.10))), ('back', Vector((0.55, 1.05, 0.10)))):
        cam.location = target + off
        look_at(cam, target)
        scene.render.filepath = str(PREVIEW / f'styled-{cid}-{view}.png')
        bpy.ops.render.render(write_still=True)
    for light in lights:
        bpy.data.objects.remove(light, do_unlink=True)
    bpy.data.objects.remove(cam, do_unlink=True)

    print('STYLED', cid, flush=True)

(OUT / 'manifest.json').write_text(json.dumps({
    'version': 1, 'baseline': BASELINE, 'shadow_tint': SHADOW_TINT,
    'characters': report, 'note': '输入为 blender/animated/*.blend；原始 PMX/贴图与 generated 未被覆盖',
}, ensure_ascii=False, indent=2), encoding='utf-8')
print('STYLE_CHARACTERS_OK', json.dumps(report, ensure_ascii=False))
