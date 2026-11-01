"""客观检查新走路：中心起伏、骨盆/脊柱反向、头部稳定的幅度。"""
import bpy
import json
import math
from pathlib import Path
from mathutils import Quaternion

ROOT = Path(__file__).resolve().parents[1]
CID = 'anaxa'
OUT = ROOT / 'blender/walking/reports'
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'blender/walking' / f'{CID}.blend'))
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
pb = arm.pose.bones


def angle(name):
    """绕局部 Y 的有符号角度（度）。"""
    q = pb[name].rotation_quaternion
    return 2 * math.degrees(math.atan2(q.y, q.w))


samples = []
# 走路段 t=6..9s -> 第 145..217 帧
for f in range(145, 218):
    scene.frame_set(f)
    center = pb['センター'].location
    samples.append({
        'frame': f,
        'center_y': center.y,
        'center_x': center.x,
        'pelvis_deg': angle('下半身'),
        'spine1_deg': angle('上半身1'),
        'spine2_deg': angle('上半身2'),
        'head_deg': angle('首') + angle('頭'),
    })

ys = [s['center_y'] for s in samples]
xs = [s['center_x'] for s in samples]
pelvis = [s['pelvis_deg'] for s in samples]
spine1 = [s['spine1_deg'] for s in samples]
head = [s['head_deg'] for s in samples]

# 相关度：骨盆与脊柱是否反向
def corr(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va == 0 or vb == 0:
        return 0.0
    return sum((a[i] - ma) * (b[i] - mb) for i in range(n)) / math.sqrt(va * vb)


result = {
    'id': CID, 'segment': 't=6..9s (frames 145..217)',
    'center_vertical_range': round(max(ys) - min(ys), 4),
    'center_lateral_range': round(max(xs) - min(xs), 4),
    'pelvis_deg_max': round(max(pelvis), 2),
    'spine1_deg_max': round(max(spine1), 2),
    'head_deg_max': round(max(head), 2),
    'pelvis_spine1_corr': round(corr(pelvis, spine1), 3),
    'note': 'pelvis_spine1_corr 接近 -1 表示脊柱与骨盆反向（教程的脊柱骨要领）',
}
(OUT / 'walk-motion.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('WALK_MOTION ' + json.dumps(result, ensure_ascii=False))
