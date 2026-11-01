"""rig_check.py —— Step 4 前置检查：口型骨骼与表情形态键缺口，只记录不修改绑定。

输出：characters/rig_report.md
"""
import bpy
import json
import re
import addon_utils
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLED = ROOT / 'assets' / 'characters' / 'styled'
OUT = ROOT / 'characters' / 'rig_report.md'
IDS = ['anaxa', 'castor', 'hyacine', 'phainon']

EXT = "bl_ext.user_default.Paperzhu_animehelper_extension"
if not hasattr(bpy.types.Scene, 'paper_render_helper'):
    addon_utils.enable(EXT, default_set=True, persistent=True)

MOUTH_BONE = re.compile(r'(?<!袖)口|唇|舌|jaw|mouth', re.I)
EXPR = re.compile(r'まばたき|眨眼|笑|にこり|喜|怒|悲|困|照|あ|い|う|え|お|口|舌|目|じと|照れ', re.I)


def inspect(cid):
    bpy.ops.wm.open_mainfile(filepath=str(STYLED / f'{cid}.blend'))
    scene = bpy.context.scene
    arm = next((o for o in scene.objects if o.type == 'ARMATURE'), None)
    bones = [b.name for b in arm.data.bones] if arm else []
    mouth_bones = sorted({n for n in bones if MOUTH_BONE.search(n)})
    meshes = [o for o in scene.objects if o.type == 'MESH']
    all_keys = []
    for o in meshes:
        if o.data.shape_keys:
            all_keys += [kb.name for kb in o.data.shape_keys.key_blocks]
    all_keys = sorted(set(all_keys))
    expr_keys = sorted({k for k in all_keys if EXPR.search(k)})
    return {'bones': len(bones), 'meshes': len(meshes), 'mouth_bones': mouth_bones,
            'shape_keys': len(all_keys), 'expr_keys': expr_keys[:80]}


data = {cid: inspect(cid) for cid in IDS}

lines = ['# 角色 Rig 检查报告（Step 4 前置，只检查不修改）', '',
         '更新：2026-10-22。检查对象为 `assets/characters/styled/*.blend`；**未重建或改动任何骨骼/形态键**。', '',
         '## 汇总', '', '| 角色 | 骨骼数 | 网格数 | 口型骨骼 | 形态键总数 | 表情类形态键 |', '| --- | --- | --- | --- | --- | --- |']
for cid in IDS:
    d = data[cid]
    lines.append(f"| {cid} | {d['bones']} | {d['meshes']} | {len(d['mouth_bones'])} | {d['shape_keys']} | {len(d['expr_keys'])} |")
lines += ['', '## 明细', '']
for cid in IDS:
    d = data[cid]
    lines += [f'### {cid}', '']
    lines.append(f"- 口型骨骼：{', '.join(d['mouth_bones'][:20]) if d['mouth_bones'] else '**未发现**'}")
    lines.append(f"- 表情类形态键（前 80）：{', '.join(d['expr_keys'][:80]) if d['expr_keys'] else '**未发现**'}")
    lines.append('')
lines += ['## 结论与缺口', '',
          '- 本轮只做检查；未新增口型骨骼、未重排形态键、未改权重。',
          '- 若上表「口型骨骼」为空：说明模型未提供独立口型骨骼，后续口型同步需依赖形态键或音素映射，不能假定骨骼存在。',
          '- 若「表情类形态键」为空：说明缺少可用表情形态键，微表情精修需要另行制作，不属于本轮范围。',
          '- 具体缺口以逐角色明细为准；未核实项不臆断。', '']
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('RIG_REPORT_OK')
print(json.dumps(data, ensure_ascii=False)[:1200])
