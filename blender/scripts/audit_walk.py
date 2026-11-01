"""逐帧检查烘焙行走的支撑脚滑动与循环接缝；不等于布料碰撞验证。"""
import bpy,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
report=[]
ids=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['anaxa','hyacine','castor','phainon']
for cid in ids:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/walking/{cid}.blend'))
    arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    meta=json.loads((ROOT/f'blender/walking/reports/{cid}.json').read_text(encoding='utf-8'))
    scale=meta['target_height']/meta['rest_height'];previous={};slip=0.;samples=0
    for f in range(1,578):
        bpy.context.scene.frame_set(f);t=(f-1)/24
        for side,first in [('L',0),('R',1)]:
            support=True
            for start in [6,18]:
                if start<=t<start+3:
                    elapsed=t-start
                    support=not any(step*.5<elapsed<(step+1)*.5 for step in range(first,6,2))
            # 转身允许抬脚换支撑，单独排除转身段。
            support &= not any(a<=t<=b for a,b in [(5,6),(9,10),(17,18),(21,22)])
            foot=arm.pose.bones['足首.'+side]
            pos=(arm.matrix_world@foot.head)*scale
            if side in previous and support and previous[side][1]:
                slip=max(slip,(pos-previous[side][0]).length);samples+=1
            previous[side]=(pos.copy(),support)
    bpy.context.scene.frame_set(1)
    initial={b.name:b.matrix.copy() for b in arm.pose.bones}
    bpy.context.scene.frame_set(577)
    seam=max(max(abs(b.matrix[i][j]-initial[b.name][i][j]) for i in range(4) for j in range(4)) for b in arm.pose.bones)
    report.append({'id':cid,'sampled_frames':577,'support_pairs':samples,'max_support_ankle_shift_m_per_frame':slip,'max_loop_matrix_difference':seam,'passed':slip<.006 and seam<.001})
(ROOT/'blender/walking/reports/quality.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
if not all(x['passed'] for x in report):raise RuntimeError('Walking quality threshold failed')
