"""重建「新海诚风」卡通教室：在同一坐标体系内提高建筑线脚、家具、道具与窗光细节。

参考：BV1ku411Z7oe《Blender 新海诚卡通风格教室场景建模渲染教学》（椅子/桌子/教室结构/道具/窗户/贴图/公告板/书本/渲染合成/窗帘）。
输出：blender/build/cinematic-classroom/{story_classroom.glb,fbx,blend,layout.json}
"""
import bpy
import math
import json
import random
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'blender'))
from spatial_assets import capture_parts,cup

OUT = Path(next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--output=')),
                str(ROOT / 'blender/build/cinematic-classroom')))
OUT.mkdir(exist_ok=True, parents=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
random.seed(20261022)

# 暖色新海诚调色板
palette = {
    'plaster': (0.93, 0.88, 0.76),
    'plaster_warm': (0.97, 0.90, 0.77),
    'sage': (0.42, 0.58, 0.47),
    'sage_dark': (0.33, 0.47, 0.39),
    'wood_dark': (0.30, 0.20, 0.13),
    'wood_mid': (0.52, 0.35, 0.20),
    'wood_light': (0.70, 0.50, 0.29),
    'oak': (0.63, 0.44, 0.25),
    'oak_light': (0.76, 0.57, 0.35),
    'gold': (0.80, 0.63, 0.32),
    'board': (0.10, 0.26, 0.18),
    'paper': (0.96, 0.91, 0.76),
    'paper_shade': (0.90, 0.84, 0.68),
    'leaf': (0.27, 0.51, 0.27),
    'leaf_dark': (0.17, 0.36, 0.21),
    'sky_warm': (1.0, 0.76, 0.46),
    'sky_pale': (0.93, 0.88, 0.80),
    'rose': (0.78, 0.35, 0.31),
    'ink': (0.15, 0.19, 0.17),
    'lamp': (1.0, 0.88, 0.58),
    'dust': (1.0, 0.94, 0.78),
    'glass': (0.72, 0.90, 0.92),
    'chalk': (0.95, 0.95, 0.88),
}
mats = {}
parts = []
colliders = []
seats = []

for name, rgb in palette.items():
    m = bpy.data.materials.new('TC_Cine_' + name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'),None)
    if p is None:
        p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = 0.82
    if name in ('sky_warm', 'lamp', 'dust'):
        p.inputs['Emission Color'].default_value = (*rgb, 1)
        p.inputs['Emission Strength'].default_value = 1.6 if name != 'lamp' else 2.6
    mats[name] = m


def xyz(v):
    return (v[0], -v[2], v[1])


def box(name, pos, size, mat='wood_mid', bevel=.02, solid=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz(pos))
    o = bpy.context.object
    o.name = name
    o.dimensions = (size[0], size[2], size[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mats[mat])
    parts.append(o)
    if bevel:
        mod = o.modifiers.new('柔边', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if solid:
        colliders.append({'name': name, 'center': list(pos), 'size': list(size)})
    return o


def ball(name, pos, size, mat, seg=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=max(6, seg // 2), location=xyz(pos))
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[2], size[1])
    o.data.materials.append(mats[mat])
    parts.append(o)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def rod(name, a, b, r, mat, verts=12):
    va, vb = Vector(xyz(a)), Vector(xyz(b))
    d = vb - va
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(va + vb) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
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


# ============ 房间壳体 ============
W, Z0, Z1, H = 15.5, -6.4, 6.6, 4.5
# 地板：逐条木板 + 色差
random.seed(7)
for i in range(-8, 8):
    tone = ['oak', 'oak_light', 'wood_light', 'oak'][(i + 8) % 4]
    box('Floor_Plank', (i * .96, -.015, .1), (.94, .03, Z1 - Z0), tone, .006)
box('Floor_Border', (0, -.008, .1), (W, .012, Z1 - Z0), 'wood_dark', 0)
for i in range(-8, 8):
    box('Floor_Seam', (i * .96 + .48, .002, .1), (.012, .004, Z1 - Z0), 'wood_dark', 0)

# 墙体 + 护墙板 + 线脚
for x in (-7.75, 7.75):
    box('Side_Wall', (x, 2.25, .1), (.22, 4.5, Z1 - Z0), 'plaster', 0, True)
    box('Wainscot', (x + (.12 if x < 0 else -.12), .62, .1), (.05, 1.24, Z1 - Z0), 'sage', 0)
    box('Wainscot_Dark', (x + (.13 if x < 0 else -.13), .10, .1), (.06, .18, Z1 - Z0), 'sage_dark', 0)
    box('Chair_Rail', (x + (.15 if x < 0 else -.15), 1.27, .1), (.07, .08, Z1 - Z0), 'gold', .006)
    box('Crown_Molding', (x + (.14 if x < 0 else -.14), 4.30, .1), (.09, .16, Z1 - Z0), 'wood_light', .01)
    box('Crown_Molding2', (x + (.14 if x < 0 else -.14), 4.42, .1), (.12, .08, Z1 - Z0), 'wood_dark', .01)
    # 护墙板竖向分格
    for z in range(int(Z0) + 1, int(Z1), 3):
        box('Wainscot_Stile', (x + (.14 if x < 0 else -.14), .62, z), (.02, 1.22, .05), 'sage_dark', 0)

for z, name in ((Z0, 'Back_Wall'), (Z1, 'Front_Wall')):
    box(name, (0, 2.25, z), (W, 4.5, .20), 'plaster', 0, True)
    box('End_Wainscot', (0, .62, z + (.12 if z < 0 else -.12)), (W, 1.24, .05), 'sage', 0)
    box('End_Rail', (0, 1.27, z + (.13 if z < 0 else -.13)), (W, .08, .06), 'gold', .006)
    box('End_Crown', (0, 4.30, z + (.12 if z < 0 else -.12)), (W, .16, .08), 'wood_light', .01)

box('Ceiling', (0, 4.5, .1), (W, .14, Z1 - Z0), 'plaster_warm', 0)
for z in (-4.5, -1.5, 1.5, 4.5):
    box('Ceiling_Beam', (0, 4.40, z), (W - .1, .18, .30), 'wood_mid', .015)
    box('Ceiling_BeamTrim', (0, 4.31, z), (W - .1, .05, .38), 'wood_light', .008)

# ============ 左墙：三扇深窗 + 窗帘 ============
for zc in (-3.6, 0.0, 3.6):
    # 天空面贴在侧墙内表面（不做布尔开洞，沿用既有「贴片窗」做法）
    box('Window_Sky', (-7.62, 2.55, zc), (.02, 2.80, 2.95), 'sky_warm', 0)
    # 窗套
    for dy in (-1.45, 1.45):
        box('Window_Casing', (-7.48, 2.55, zc + dy), (.22, 3.0, .16), 'wood_light', .012)
    for y in (1.05, 2.55, 4.05):
        box('Window_Casing_H', (-7.48, y, zc), (.22, .16, 2.98), 'wood_light', .012)
    # 窗棂
    for dz in (-1.0, 0, 1.0):
        box('Window_Mullion', (-7.40, 2.55, zc + dz), (.10, 2.75, .075), 'wood_mid', .008)
    for y in (1.85, 3.25):
        box('Window_Transom', (-7.40, y, zc), (.12, .08, 2.72), 'wood_mid', .008)
    # 窗台 + 盆栽
    box('Window_Sill', (-7.28, 1.02, zc), (.55, .11, 3.1), 'paper', .015)
    box('Sill_Lip', (-7.12, 1.00, zc), (.06, .05, 3.1), 'wood_light', .008)
    # 窗帘：两侧多褶
    rod('Curtain_Rod', (-7.10, 4.18, zc - 1.62), (-7.10, 4.18, zc + 1.62), .028, 'gold')
    for side in (-1, 1):
        for fold in range(7):
            xoff = .02 * (fold % 2)
            box('Curtain_Fold', (-7.10 + xoff, 2.55, zc + side * (1.18 + fold * .052)),
                (.10, 2.85, .06), 'paper_shade', .02)
    # 窗外云影（简化）
    ball('Cloud', (-7.61, 3.55, zc - .7), (.02, .18, .38), 'sky_pale')
    ball('Cloud', (-7.61, 3.30, zc + .55), (.02, .14, .30), 'sky_pale')

# ============ 后墙：黑板 ============
box('Board_Frame', (0, 2.30, Z0 + .18), (6.7, 2.95, .22), 'wood_dark', .05)
box('Board_Wood', (0, 2.30, Z0 + .30), (6.45, 2.72, .05), 'wood_mid', 0)
box('Board_Surface', (0, 2.30, Z0 + .34), (6.25, 2.55, .035), 'board', .02)
box('Board_Tray', (0, 1.00, Z0 + .42), (6.6, .09, .28), 'wood_light', .012)
for i in range(5):
    box('Chalk', (-2.4 + i * .13, 1.06, Z0 + .40), (.09, .022, .022), 'chalk', .005)
box('Eraser', (2.4, 1.07, Z0 + .40), (.20, .07, .09), 'sage', .008)
# 黑板边框装饰
for dx in (-3.2, 3.2):
    box('Board_Pilaster', (dx, 2.30, Z0 + .12), (.16, 2.95, .10), 'wood_light', .01)
# 后墙两侧：书柜/公告栏
for dx in (-5.6, 5.6):
    box('Back_Cabinet', (dx, .55, Z0 + .35), (1.9, 1.0, .5), 'wood_dark', .02, True)
    box('Back_Cabinet_Top', (dx, 1.08, Z0 + .35), (2.0, .06, .56), 'wood_light', .01)
    for k in range(4):
        box('Back_Cabinet_Book', (dx - .6 + k * .4, 1.26, Z0 + .35), (.28, .30, .22),
            ['sage', 'paper', 'rose', 'gold'][k], .006)

# ============ 讲台 + 讲桌 ============
box('Platform', (0, .09, -4.8), (8.4, .18, 3.2), 'wood_light', .03)
box('Platform_Step', (0, .045, -3.05), (5.0, .09, .4), 'wood_mid', .02)
box('Lectern_Base', (-.1, .24, -4.25), (1.30, .14, .86), 'wood_dark', .02)
box('Lectern_Body', (-.1, .70, -4.25), (1.15, .90, .70), 'wood_mid', .03, True)
box('Lectern_Top', (-.1, 1.19, -4.25), (1.42, .12, .98), 'wood_light', .02)
box('Lectern_Inlay', (-.1, .72, -3.88), (.86, .48, .018), 'gold', .004)
box('Lectern_Panel', (-.1, .72, -3.87), (.80, .42, .015), 'sage', .004)
box('Teacher_Book', (-.1, 1.2675, -4.2), (.62, .035, .40), 'paper', .006)
for i in range(3):
    box('Teacher_BookStack', (-.62, 1.27 + i * .04, -4.42), (.24, .04, .30),
        ['sage', 'rose', 'gold'][i], .005)

# ============ 课桌椅（两排 × 三组 × 两张） ============
def desk(x, z, row, side):
    box(f'Desk_Top_{row}_{side}', (x, .845, z), (.80, .05, .58), 'oak_light', .012, True)
    box('Desk_Apron', (x, .74, z - .22), (.70, .10, .04), 'wood_mid', .008, True)
    for dx in (-.30, .30):
        for dz in (-.20, .20):
            box('Desk_Leg', (x + dx, .41, z + dz), (.045, .82, .045), 'wood_dark', .006, True)
    for dz in (-.20, .20):
        box('Desk_Crossbar', (x, .12, z + dz), (.62, .04, .036), 'wood_mid', .005, True)
    box('Desk_Drawer', (x, .64, z - .22), (.46, .12, .46), 'wood_light', .008)
    box('Drawer_Handle', (x + .20, .64, z - .22), (.07, .025, .02), 'gold', .004)
    # 桌面道具
    box('Notebook', (x, .878, z + .08), (.44, .016, .30), 'paper', .004)
    for k in range(3):
        box('Page_Line', (x, .886, z + .02 + k * .055), (.34, .002, .003), 'sage', 0)
    box('Pencil', (x + .28, .8765, z + .12), (.013, .013, .22), 'gold', .003)
    # 书本/资料（部分座位）
    if (row + side) % 2 == 0:
        for k in range(2):
            box('Desk_Book', (x - .22, .884 + k * .028, z - .12), (.26, .028, .20),
                ['sage', 'rose', 'paper', 'gold'][(row + side + k) % 4], .005)
    box('Desk_Nameplate', (x, .876, z + .24), (.20, .012, .07), 'paper_shade', .003)


def chair(x, z):
    box('Chair_Seat', (x, .44, z), (.64, .08, .54), 'oak_light', .015, True)
    for dx in (-.28, .28):
        box('Chair_Leg', (x + dx, .21, z - .19), (.045, .42, .045), 'wood_dark', .006, True)
    # 后腿与靠背使用同一根落地立柱，穿过座面两后角，消除旧阶梯脚的悬空间隙。
    for dx in (-.28,.28):
        box('Chair_Back_Post',(x+dx,.525,z+.24),(.045,1.05,.045),'wood_dark',.006,True)
        box('Chair_Seat_Rail',(x+dx,.39,z+.025),(.045,.045,.47),'wood_mid',.004,True)
    for y in (.66, .84, 1.00):
        box('Chair_Back_Slat', (x, y, z + .24), (.60, .10, .045), 'wood_mid', .006, True)
    for sign in (-1,1):
        rod('Chair_Stretcher',(x+sign*.28,.17,z-.19),(x+sign*.28,.17,z+.24),.016,'wood_mid')
        colliders.append({'name':'Chair_Stretcher','center':[x+sign*.28,.17,z+.025],'size':[.032,.032,.462]})


random.seed(11)
for row, z in enumerate((0.0, 1.7)):
    for side, x in enumerate((-3.58, -2.82, -0.38, 0.38, 2.82, 3.58)):
        desk(x, z, row + 1, side)
        chair(x, z + .62)
        seats.append({'row': row + 1, 'pair': side // 2, 'side': side % 2,
                      'desk_center': [x, .845, z], 'seat_center': [x, .48, z + .62]})

# ============ 右墙：书柜 + 公告栏 + 挂钟 ============
for zc in (-3.2, 0.0, 3.2):
    box('Bookcase_Back', (7.55, 1.5, zc), (.16, 3.0, 2.2), 'wood_dark', .02, True)
    for dz in (-1.05, 1.05):
        box('Bookcase_Post', (7.38, 1.5, zc + dz), (.46, 3.0, .06), 'wood_light', .01)
    for y in (.22, .88, 1.54, 2.20, 2.86):
        box('Bookcase_Shelf', (7.38, y, zc), (.50, .05, 2.24), 'wood_light', .008)
        if y > 2.3:
            continue
        for n in range(12):
            h = random.uniform(.26, .40)
            box('Library_Book', (7.36, y + .025 + h / 2, zc - .92 + n * .17), (.34, h, .115),
                ['sage', 'paper', 'rose', 'gold', 'wood_light'][(n + int(zc)) % 5], .006)
box('Notice_Frame', (7.62, 3.75, .6), (.06, 1.0, 2.2), 'gold', .012)
box('Notice_Board', (7.56, 3.75, .6), (.04, .90, 2.05), 'sage_dark', .006)
for i in range(6):
    x = .6 - .75 + (i % 3) * .75
    y = 3.42 + (i // 3) * .62
    box('Pinned_Note', (7.53, y, x), (.02, .48, .60), 'paper', .003)
    for k in range(3):
        box('Pinned_Line', (7.51, y - .12 + k * .12, x), (.004, .012, .40), 'ink', 0)
ball('Clock_Frame', (7.62, 3.9, -4.5), (.06, .40, .40), 'wood_dark')
ball('Clock_Face', (7.58, 3.9, -4.5), (.02, .34, .34), 'paper')
for i in range(12):
    a = i * math.tau / 12
    ball('Clock_Tick', (7.57, 3.9 + .27 * math.cos(a), -4.5 + .27 * math.sin(a)), (.006, .018, .012), 'ink', 8)
rod('Clock_Hand', (7.56, 3.9, -4.5), (7.56, 4.0, -4.38), .01, 'ink')
# 挂画/海报
for zc, mat in ((-5.0, 'sage'), (-1.6, 'rose'), (1.8, 'gold'), (4.8, 'sage')):
    box('Poster_Frame', (7.62, 2.9, zc), (.04, 1.1, .8), 'wood_light', .008)
    box('Poster', (7.59, 2.9, zc), (.02, .98, .68), mat, .004)

# ============ 植物 ============
def plant(x, z, scale=1.0, pot='paper'):
    box('Plant_Pot', (x, .24 * scale, z), (.46 * scale, .48 * scale, .46 * scale), pot, .05, True)
    for n in range(11):
        a = n * 2.399
        h = (.75 + random.random() * .55) * scale
        end = (x + math.cos(a) * .38 * scale, h, z + math.sin(a) * .38 * scale)
        rod('Plant_Stem', (x, .46 * scale, z), end, .016, 'leaf')
        leaf = ball('Plant_Leaf', end, (.15 * scale, .34 * scale, .06 * scale), 'leaf')
        leaf.rotation_euler = (.35, math.cos(a), a)


for pos in ((-6.9, -5.5), (-6.9, 5.7), (6.9, -5.8), (6.9, 5.7), (-7.0, 2.6)):
    plant(*pos, scale=random.uniform(.9, 1.15))

# ============ 吊灯 ============
for zc in (-3.6, 0.2, 3.8):
    rod('Pendant_Rod', (0, 4.5, zc), (0, 3.86, zc), .014, 'gold')
    box('Pendant_Shade', (0, 3.80, zc), (1.05, .12, .42), 'paper', .03)
    ball('Pendant_Bulb', (0, 3.73, zc), (.11, .11, .11), 'lamp', 10)
    box('Pendant_Cap', (0, 4.42, zc), (.18, .06, .18), 'gold', .008)

# ============ 合并 + 导出 ============
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
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'story_classroom.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT / 'story_classroom.glb'), export_format='GLB', export_animations=False)
bpy.ops.export_scene.fbx(filepath=str(OUT / 'story_classroom.fbx'), use_selection=True,
                        object_types={'MESH'}, bake_anim=False, add_leaf_bones=False)
(OUT / 'layout.json').write_text(json.dumps({
    'version': 4, 'style': 'shinkai-warm', 'seats': seats,
    'player_start': [1.8, 1.65, 2.4], 'eye_height': 1.65, 'radius': .24,
    'bounds': [-7.45, 7.45, -6.2, 6.4], 'colliders': colliders,
    'walkable_surfaces':[{'center':[0,.09,-4.8],'size':[8.4,.18,3.2]},{'center':[0,.045,-3.05],'size':[5,.09,.4]}],
}, ensure_ascii=False, indent=2), encoding='utf-8')
print('CINEMATIC_CLASSROOM_READY', len(parts), len(colliders))
