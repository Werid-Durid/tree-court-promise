"""那刻夏「坐姿写字」循环动画：复用课堂已验证的坐姿 IK，改为低头书写 + 连续运笔。原模型不覆盖。"""
import bpy, sys, json, math, struct
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / 'blender/study_motion.json').read_text(encoding='utf-8'))
OUT = ROOT / 'blender/study'
OUT.mkdir(exist_ok=True)
REPORT = ROOT / 'blender/study/reports'
REPORT.mkdir(exist_ok=True)
TAU = 2 * math.pi


def ease(x):
    x = max(0, min(1, x))
    return x * x * x * (10 + x * (-15 + 6 * x))


def bell(t, start, end):
    if not start < t < end:
        return 0.0
    return math.sin(math.pi * (t - start) / (end - start)) ** 2


class Performer:
    def __init__(self, arm, height):
        self.arm = arm
        self.pb = arm.pose.bones
        self.spec = CFG['characters']['anaxa']
        self.scale = self.spec['height'] / height
        self.changed = set()
        self.rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
        self.foot = {s: self.rest['足ＩＫ.' + s].translation.copy() for s in ('L', 'R')}
        self.lengths = {s: ((self.rest['ひじ.' + s].translation - self.rest['腕.' + s].translation).length,
                            (self.rest['手首.' + s].translation - self.rest['ひじ.' + s].translation).length)
                        for s in ('L', 'R')}
        self.metrics = []
        for p in self.pb:
            p.rotation_mode = 'QUATERNION'
        if arm.animation_data:
            arm.animation_data_clear()

    def rotate(self, name, axis, angle):
        if name not in self.pb:
            return
        self.pb[name].rotation_quaternion = Quaternion(Vector(axis), angle)
        self.changed.add(name)

    def translate_world(self, name, translation):
        p = self.pb[name]
        m = self.rest[name].copy()
        if p.parent:
            m = p.parent.matrix @ p.parent.bone.matrix_local.inverted() @ m
        m.translation += Vector(translation)
        p.matrix = m
        self.changed.add(name)

    def aim(self, name, target):
        p = self.pb[name]
        ref = p.parent.matrix @ p.parent.bone.matrix_local.inverted() @ p.bone.matrix_local if p.parent else p.bone.matrix_local.copy()
        head = p.head.copy()
        direction = (Vector(target) - head).normalized()
        rotation = (ref.to_quaternion() @ Vector((0, 1, 0))).rotation_difference(direction) @ ref.to_quaternion()
        p.matrix = Matrix.LocRotScale(head, rotation, Vector((1, 1, 1)))
        self.changed.add(name)

    def arm_to(self, side, target, pole):
        a = self.pb['腕.' + side]
        start = a.head.copy()
        target = Vector(target)
        l1, l2 = self.lengths[side]
        delta = target - start
        distance = min(max(delta.length, abs(l1 - l2) + .005), l1 + l2 - .003)
        direction = delta.normalized()
        target = start + direction * distance
        along = (l1 * l1 - l2 * l2 + distance * distance) / (2 * distance)
        bend = Vector(pole) - start
        bend -= direction * bend.dot(direction)
        if bend.length < .001:
            bend = Vector((0, 1, 0))
        elbow = start + direction * along + bend.normalized() * math.sqrt(max(0, l1 * l1 - along * along))
        self.aim('腕.' + side, elbow)
        bpy.context.view_layer.update()
        self.aim('ひじ.' + side, target)
        bpy.context.view_layer.update()
        wrist = self.pb['手首.' + side]
        hand_direction = (target - elbow).normalized()
        self.aim('手首.' + side, wrist.head + hand_direction * .08)
        return (wrist.head - target).length

    def pose(self, t):
        for p in self.pb:
            p.matrix_basis = Matrix.Identity(4)
        self.changed = set()
        root = self.pb['全ての親']
        # 坐姿在 rest 朝向烘焙；运行时由网站按 yaw=π 转身面向书桌/镜头。
        root.matrix = self.rest[root.name]
        self.changed.add(root.name)
        bpy.context.view_layer.update()
        breath = math.sin(TAU * t / 5)
        # 抬头看你：14–18.5 秒抬头、停一下、再低头；其余时间书写。
        lift = ease((t - 14.0) / 1.3) * ease((18.5 - t) / 1.3)
        hip = self.rest['足.L'].translation.z
        center_drop = (CFG['seat_height'] + .075) / self.scale - hip
        # 骨盆坐定；身体微微前倾书写，随呼吸起伏。
        self.translate_world('センター', (0, 0, center_drop + .002 * breath / self.scale))
        self.rotate('上半身', (1, 0, 0), .11 - .05 * lift + .004 * breath)
        self.rotate('上半身1', (0, 1, 0), .015 * math.sin(TAU * t / 7))
        self.rotate('上半身2', (0, 0, 1), .01 * math.sin(TAU * t / 9))
        # 低头看书/写字：颈前倾 + 轻微点头与侧摆；抬头时颈回到水平并略偏向你。
        self.rotate('首', (1, 0, 0), .24 - .36 * lift + .015 * math.sin(TAU * t / 8))
        self.rotate('頭', (0, 0, 1), .02 * math.sin(TAU * t / 11) + .06 * lift)
        bpy.context.view_layer.update()
        # 双脚着地（与课堂坐姿一致）。
        for side, sign in (('L', 1), ('R', -1)):
            rest = self.foot[side]
            target = Vector((sign * .085 / self.scale, -.40 / self.scale, rest.z))
            m = Matrix.LocRotScale(target, self.rest['足ＩＫ.' + side].to_quaternion(), Vector((1, 1, 1)))
            self.pb['足ＩＫ.' + side].matrix = m
            self.changed.add('足ＩＫ.' + side)
        bpy.context.view_layer.update()
        errors = []
        for side, sign in (('L', 1), ('R', -1)):
            shoulder = self.pb['腕.' + side].head.copy()
            l1, l2 = self.lengths[side]
            target = Vector((sign * .16 / self.scale, -.38 / self.scale, .885 / self.scale))
            if side == 'R':
                # 连续运笔：小幅八字 + 周期蘸墨提笔；抬头时停笔并抬起一点。
                writing = .012 / self.scale * math.sin(TAU * t * 1.25)
                writing += .006 / self.scale * math.sin(TAU * t * 2.35)
                target.x += writing * (1 - lift)
                target.z += .008 / self.scale * math.sin(TAU * t * 1.9) * (1 - lift) + .022 / self.scale * lift
                target.y += .010 / self.scale * bell(t % 6, 0, .4) * (1 - lift)
            else:
                # 左手压住书页，几乎不动，只随呼吸微动。
                target.x += .004 / self.scale * math.sin(TAU * t / 6)
            pole = shoulder + Vector((sign * .28, .10, -.24))
            errors.append(self.arm_to(side, target, pole))
            for p in self.pb:
                if p.name.endswith('.' + side) and ('指' in p.name or '小指' in p.name) and not p.name.startswith('_'):
                    self.rotate(p.name, (1, 0, 0), .10)
        bpy.context.view_layer.update()
        if max(errors) > .025:
            raise RuntimeError(f'anaxa 手臂解算误差 {max(errors)}')
        self.metrics.append(max(errors))
        for name in self.changed:
            p = self.pb[name]
            for channel in ('location', 'rotation_quaternion', 'scale'):
                p.keyframe_insert(data_path=channel)


bpy.context.preferences.filepaths.save_version = 0
cid = 'anaxa'
bpy.ops.wm.open_mainfile(filepath=str(ROOT / f'blender/generated/{cid}.blend'))
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers)]
floor = min((o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box)
height = max((o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box) - floor
triangles = sum(len(o.data.polygons) for o in meshes)
scene = bpy.context.scene
scene.render.fps = CFG['fps']
scene.frame_start = 1
scene.frame_end = 1 + CFG['duration'] * CFG['fps']
performer = Performer(arm, height)
for frame in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(frame)
    performer.pose((frame - 1) / CFG['fps'])
arm.animation_data.action.name = CFG['characters'][cid]['clip'] + '_Controls'
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.nla.bake(frame_start=scene.frame_start, frame_end=scene.frame_end, step=1, only_selected=False,
                 visual_keying=True, clear_constraints=True, use_current_action=False, bake_types={'POSE'})
action = arm.animation_data.action
action.name = CFG['characters'][cid]['clip']
for fc in action.layers[0].strips[0].channelbag(action.slots[0]).fcurves:
    for key in fc.keyframe_points:
        key.interpolation = 'LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f'{cid}.blend'))
for obj in meshes:
    obj.select_set(True)
scene.frame_set(1)
bpy.ops.export_scene.fbx(filepath=str(OUT / f'{cid}.fbx'), use_selection=True,
                        object_types={'MESH', 'ARMATURE'}, add_leaf_bones=False, bake_anim=True,
                        bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                        bake_anim_simplify_factor=.1, path_mode='COPY', embed_textures=True)
bpy.ops.export_scene.gltf(filepath=str(OUT / f'{cid}.glb'), use_selection=True, export_format='GLB',
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_range=True, export_morph=True)
sys.path.insert(0, str(ROOT / 'blender'))
from normalize_motion_glb import normalize
normalize(OUT / f'{cid}.glb')
blob = (OUT / f'{cid}.glb').read_bytes()
length = struct.unpack_from('<I', blob, 12)[0]
gltf = json.loads(blob[20:20 + length])
exported = sum(gltf['accessors'][p['indices']]['count'] // 3 for m in gltf['meshes'] for p in m['primitives'])
assert exported == triangles, '动画导出不可减少原面片'
assert len(gltf.get('animations', [])) >= 1, '没有导出动画'
info = {'id': cid, 'status': 'animated', 'clip': action.name, 'duration': CFG['duration'],
        'rest_height': height, 'rest_floor': floor, 'target_height': CFG['characters'][cid]['height'],
        'triangles': triangles, 'max_arm_target_error_m': max(performer.metrics), 'bones': len(arm.data.bones),
        'animations': [a['name'] for a in gltf['animations']],
        'glb': str(OUT / f'{cid}.glb'), 'fbx': str(OUT / f'{cid}.fbx')}
(REPORT / f'{cid}.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
print('STUDY_ANIMATED', cid, flush=True)
