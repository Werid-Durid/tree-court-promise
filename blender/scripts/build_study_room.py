"""生成「自习室」场景几何，输出同源 GLB/FBX/blend + layout.json。全部几何本地生成，不覆盖原角色与正式课堂。"""
import bpy, math, json, random, sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'blender'))
from spatial_assets import capture_parts,cup

OUT = Path(next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--output=')),
                str(ROOT / 'blender/build/study-room')))
OUT.mkdir(exist_ok=True, parents=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
random.seed(47)

palette = {
    'plaster': (0.90, 0.84, 0.72),   # 暖石膏
    'wainscot': (0.62, 0.42, 0.28),  # 护墙板暖木
    'walnut': (0.30, 0.19, 0.12),    # 深胡桃木
    'oak': (0.72, 0.49, 0.25),
    'gold': (0.78, 0.60, 0.28),
    'paper': (0.94, 0.87, 0.68),     # 羊皮纸
    'sage': (0.38, 0.62, 0.51),
    'leaf': (0.24, 0.49, 0.26),
    'dusk': (0.95, 0.62, 0.40),      # 黄昏天空（发光）
    'lamp': (1.00, 0.78, 0.42),      # 台灯（发光）
    'tea': (0.95, 0.92, 0.85),
    'rug': (0.16, 0.30, 0.24),       # 墨绿绒毯
    'rose': (0.70, 0.32, 0.29),
    'ink': (0.18, 0.24, 0.21),
    'glass': (0.69, 0.91, 0.91),
    'sky': (0.55, 0.78, 0.85),
}
mats = {}
parts = []
colliders = []
for name, rgb in palette.items():
    m = bpy.data.materials.new('TC_Study_' + name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'),None)
    if p is None:
        p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = 0.82
    if name == 'dusk':
        p.inputs['Emission Color'].default_value = (*rgb, 1)
        p.inputs['Emission Strength'].default_value = 1.4
    elif name == 'lamp':
        p.inputs['Emission Color'].default_value = (1.0, 0.82, 0.5, 1)
        p.inputs['Emission Strength'].default_value = 3.0
    elif name in ('sky', 'glass'):
        p.inputs['Emission Color'].default_value = (*rgb, 1)
        p.inputs['Emission Strength'].default_value = 0.3
    mats[name] = m


def xyz(v):
    return (v[0], -v[2], v[1])


def box(name, pos, size, mat='walnut', bevel=.025, solid=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz(pos))
    o = bpy.context.object
    o.name = name
    o.dimensions = (size[0], size[2], size[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mats[mat])
    parts.append(o)
    if bevel:
        mod = o.modifiers.new('柔化边缘', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if solid:
        colliders.append({'name': name, 'center': list(pos), 'size': list(size)})
    return o


def ball(name, pos, size, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, location=xyz(pos))
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[2], size[1])
    o.data.materials.append(mats[mat])
    parts.append(o)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def rod(name, a, b, r, mat):
    va, vb = Vector(xyz(a)), Vector(xyz(b))
    delta = vb - va
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=r, depth=delta.length, location=(va + vb) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = delta.to_track_quat('Z', 'Y').to_euler()
    o.data.materials.append(mats[mat])
    parts.append(o)
    return o


def label(name, text, pos, size, mat='ink', front=True):
    bpy.ops.object.text_add(location=xyz(pos))
    o = bpy.context.object
    o.name = name
    o.data.body = text
    o.data.size = size
    o.data.align_x = 'CENTER'
    o.rotation_euler = (math.pi / 2, 0, 0) if front else (0, 0, 0)
    o.data.materials.append(mats[mat])
    bpy.ops.object.convert(target='MESH')
    parts.append(o)


# ---------- 房间外壳 ----------
W, D, H = 7.5, 6.8, 3.4
box('Floor', (0, -.12, .2), (W, .24, D), 'oak', 0)
for x in range(-3, 4):
    box('Floor_Inlay', (x, .004, .2), (.012, .006, D), 'walnut', 0)
for z in range(-3, 4):
    box('Floor_Seam', (0, .006, z), (W, .005, .012), 'walnut', 0)
for x in (-3.75, 3.75):
    box('Side_Wall', (x, 1.7, .2), (.20, 3.4, D), 'plaster', 0, True)
    box('Wainscot', (x + (.115 if x < 0 else -.115), .65, .2), (.035, 1.3, D), 'wainscot', 0)
    box('Dado_Rail', (x + (.15 if x < 0 else -.15), 1.32, .2), (.06, .07, D), 'gold')
for z in (-3.2, 3.6):
    box('End_Wall', (0, 1.7, z), (W, 3.4, .18), 'plaster', 0, True)
    box('End_Wainscot', (0, .65, z + (.11 if z < 0 else -.11)), (W, 1.3, .04), 'wainscot', 0)
box('Ceiling', (0, 3.4, .2), (W, .12, D), 'plaster', 0)
for z in (-1.5, .5, 2.5):
    box('Ceiling_Beam', (0, 3.33, z), (W - .2, .14, .16), 'walnut')

# ---------- 左墙：黄昏窗 + 纱帘 ----------
box('Window_Sky', (-3.755, 1.95, -.2), (.025, 2.1, 2.5), 'dusk')
for dz in (-1.0, 0, 1.0):
    box('Window_Mullion', (-3.70, 1.95, -.2 + dz), (.10, 2.20, .075), 'walnut')
for y in (0.9, 1.95, 3.0):
    box('Window_Rail', (-3.68, y, -.2), (.15, .08, 2.68), 'walnut')
box('Window_Sill', (-3.55, 0.82, -.2), (.40, .10, 2.75), 'paper')
for dz in (-.6, .5):
    ball('Cloud', (-3.73, 2.9, -.2 + dz), (.02, .14, .38), 'paper')
rod('Curtain_Rod', (-3.45, 3.1, -1.45), (-3.45, 3.1, 1.05), .025, 'gold')
for side in (-1, 1):
    for fold in range(5):
        box('Curtain_Fold', (-3.45 + (.045 if fold % 2 else 0), 2.25, -.2 + side * (1.05 + fold * .05)),
            (.07, 1.9, .07), 'paper', .025)

# ---------- 右墙：挂画 + 边柜 + 绿植 ----------
box('Art_Frame', (3.70, 2.45, .4), (.06, 1.3, .95), 'gold', .02)
box('Art_Paper', (3.66, 2.45, .4), (.04, 1.16, .83), 'paper')
for y in (2.0, 2.45, 2.9):
    box('Art_Line', (3.65, y, .4), (.02, .02, .55), 'rose', 0)
box('Side_Cabinet', (3.45, .47, 1.6), (.5, .94, .7), 'walnut', .03, True)
box('Cabinet_Top', (3.45, .98, 1.6), (.55, .06, .76), 'oak', .02)
for k in range(3):
    box('Cabinet_Book', (3.42, 1.03 + k * .04, 1.52), (.34, .04, .22), ('sage', 'rose', 'gold')[k], .008)
box('Plant_Pot', (3.4, .25, 2.6), (.4, .5, .4), 'paper', .06, True)
for n in range(7):
    a = n * 2.6
    h = .75 + random.random() * .5
    end = (3.4 + math.cos(a) * .3, h, 2.6 + math.sin(a) * .3)
    rod('Plant_Stem', (3.4, .5, 2.6), end, .015, 'leaf')
    ball('Plant_Leaf', end, (.12, .3, .06), 'leaf')

# ---------- 后墙：通顶书架 ----------
for xi, x in enumerate((-2.9, -0.97, 0.97, 2.9)):
    box('Shelf_Unit', (x, 1.675, 3.55), (1.72, 3.35, .22), 'walnut', .02, True)
    for y in (.3, .9, 1.5, 2.1, 2.7, 3.3):
        box('Shelf_Board', (x, y, 3.42), (1.66, .05, .36), 'oak')
        if y > 2.8:
            continue
        for n in range(8):
            h=random.uniform(.26,.38)
            box('Shelf_Book', (x - .62 + n * .18, y + .025 + h/2, 3.42), (.13, h, .26),
                ['sage', 'paper', 'rose', 'gold', 'wainscot'][(n + xi) % 5], .006)

# ---------- 前墙（镜头后）：门与挂钟 ----------
box('Door', (-1.6, 1.2, -3.2), (.9, 2.4, .08), 'oak', .02)
box('Door_Panel', (-1.6, 1.2, -3.16), (.7, 1.6, .02), 'wainscot', .01)
ball('Door_Knob', (-1.95, 1.15, -3.14), (.05, .05, .05), 'gold')
ball('Clock_Frame', (1.5, 2.5, -3.16), (.32, .32, .05), 'walnut')
ball('Clock_Face', (1.5, 2.5, -3.12), (.27, .27, .02), 'paper')
for i in range(12):
    a = i * math.tau / 12
    ball('Clock_Tick', (1.5 + .23 * math.sin(a), 2.5 + .23 * math.cos(a), -3.11), (.011, .016, .006), 'ink')
rod('Clock_Hand', (1.5, 2.5, -3.10), (1.5 + .13, 2.62, -3.10), .01, 'ink')
rod('Clock_Hand', (1.5, 2.5, -3.09), (1.5, 2.72, -3.09), .008, 'ink')

# ---------- 地毯 ----------
box('Rug', (0, .012, .9), (2.8, .024, 2.2), 'rug', .02)
box('Rug_Border', (0, .006, .9), (2.9, .012, 2.3), 'gold', 0)

# ---------- 书桌（沿用课堂已验证的坐姿几何：桌面 0.845，座椅 0.44~0.48） ----------
box('Desk_Top', (0, .815, 0), (1.7, .06, .85), 'walnut', .02, True)
box('Desk_Apron', (0, .71, -.30), (1.5, .12, .045), 'oak', .01, True)
for dx in (-.72, .72):
    for dz in (-.32, .32):
        box('Desk_Leg', (dx, .395, dz), (.05, .79, .05), 'walnut', .01, True)
box('Desk_Drawer', (0, .62, -.30), (.42, .14, .5), 'oak', .01)
box('Drawer_Handle', (.35, .62, -.30), (.08, .03, .02), 'gold', .004)

# 摊开的书（天体物理教材）：封面 + 左右两页
box('Book_Cover', (0, .860, 0), (.62, .03, .44), 'wainscot', .006)
for side in (-1, 1):
    box('Book_Page', (side * .16, .882, 0), (.30, .014, .42), 'paper', .004)
    for k in range(5):
        box('Page_Text', (side * .16, .890, -.16 + k * .08), (.24, .002, .012), 'ink', 0)
box('Book_Spine', (0, .882, 0), (.02, .014, .42), 'ink', 0)

# 纸张与笔
box('Paper', (.48, .848, -.19), (.24, .006, .34), 'paper', .003)
for k in range(4):
    box('Paper_Line', (.48, .852, -.28 + k * .06), (.2, .0016, .006), 'sage', 0)
rod('Pen', (.70, .854, -.12), (.70, .854, .12), .009, 'gold')
box('Pen_Tip', (.70, .854, .12), (.02, .02, .05), 'ink', .003)

# 茶杯与灯
cup('Tea_Cup',(.62,.845,.28),.075,.11,mats['tea'],mats['walnut'],parts)
rod('Tea_Handle', (.69, .91, .28), (.74, .97, .28), .012, 'tea')
rod('Lamp_Neck', (-.68, .875, .25), (-.68, 1.18, .25), .015, 'gold')
ball('Lamp_Shade', (-.68, 1.26, .25), (.20, .16, .20), 'lamp')
box('Lamp_Base', (-.68, .860, .25), (.16, .03, .16), 'gold', .012)
box('Lamp_Glow', (-.68, 1.26, .25), (.14, .12, .14), 'lamp', .02)

# ---------- 座椅（与课堂坐姿一致：座面 0.44） ----------
box('Chair_Seat', (0, .44, .9), (.54, .08, .50), 'oak', .025, True)
for sign in (-1, 1):
    box('Chair_Back_Post', (sign * .28, .63, 1.26), (.045, .84, .045), 'walnut', .008, True)
    box('Chair_Back_LowerLeg', (sign * .28, .1275, 1.40), (.045, .255, .045), 'walnut', .008, True)
    box('Chair_Back_Runner', (sign * .28, .235, 1.33), (.045, .045, .185), 'walnut', .008, True)
for y in (.72, .9):
    box('Chair_Back_Slat', (0, y, 1.26), (.59, .12, .045), 'oak', solid=True)
for dx in (-.21, .21):
    box('Chair_Leg', (dx, .20, .70), (.04, .40, .04), 'walnut', solid=True)
for dx in (-.24,.24):
    box('Chair_Seat_Rail',(dx,.43,1.04),(.045,.025,.56),'walnut',solid=True)

# ---------- 桌面摆件点缀 ----------
for xi, x in enumerate((-.28, -.08, .12)):
    box('Desk_Stack', (x-.25, .861, .26), (.16, .032, .16), ('sage', 'rose', 'gold')[xi % 3], .006)

# ---------- 顶灯（暖） ----------
rod('Pendant', (0, 3.4, .2), (0, 3.06, .2), .015, 'gold')
box('Ceiling_Lamp', (0, 3.0, .2), (1.0, .10, .36), 'paper', .04)
ball('Ceiling_Bulb', (0, 2.94, .2), (.14, .14, .14), 'lamp')

# ---------- 合并同材质 + 导出 ----------
capture_parts(OUT/'part-manifest.json')
for material in mats.values():
    group = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.materials and o.data.materials[0] == material]
    if not group:
        continue
    bpy.ops.object.select_all(action='DESELECT')
    for o in group:
        o.select_set(True)
    bpy.context.view_layer.objects.active = group[0]
    bpy.ops.object.join()
    group[0].name = material.name

bpy.ops.object.select_all(action='SELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'study_room.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT / 'study_room.glb'), export_format='GLB', export_animations=False)
bpy.ops.export_scene.fbx(filepath=str(OUT / 'study_room.fbx'), use_selection=True, object_types={'MESH'},
                        bake_anim=False, add_leaf_bones=False)
(OUT / 'study_room_layout.json').write_text(json.dumps({
    'version': 1,
    'room': 'study',
    'player_start': [-1.9, 1.5, -2.3],
    'eye_height': 1.5,
    'radius': .24,
    'bounds': [-3.75, 3.75, -3.2, 3.6],
    'desk_center': [0, .845, 0],
    'seat_center': [0, .48, .9],
    'colliders': colliders,
}, ensure_ascii=False, indent=2), encoding='utf-8')
print('STUDY_ROOM_READY', len(colliders))
