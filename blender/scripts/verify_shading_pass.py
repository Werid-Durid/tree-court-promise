"""验证表情仅更换中性基准，其余形态键增量、拓扑、UV、蒙皮均保留。"""
import bpy,json,numpy as np,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'blender/shading-reports'
baseline=json.loads((OUT/'baseline.json').read_text(encoding='utf-8'))
backup=Path(baseline['backup']);results=[]
def mesh():return next(o for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys)
def coords(key):
    a=np.empty(len(key.data)*3,dtype=np.float32);key.data.foreach_get('co',a);return a
def inspect():
    obj=mesh();keys=obj.data.shape_keys.key_blocks
    base=coords(keys[0])
    return {'topology':[(p.material_index,tuple(p.vertices)) for p in obj.data.polygons],
      'groups':[g.name for g in obj.vertex_groups],
      'weights':[[(g.group,g.weight) for g in v.groups] for v in obj.data.vertices],
      'uvs':[[tuple(v.uv) for v in layer.data] for layer in obj.data.uv_layers],
      'base':base,'morphs':{k.name:coords(k)-base for k in keys},
      'bones':[b.name for o in bpy.data.objects if o.type=='ARMATURE' for b in o.data.bones],
      'visibility':[(m.use_backface_culling,float(m.diffuse_color[3])) for m in obj.data.materials]}
for cid in ('anaxa','hyacine','castor','phainon'):
    bpy.ops.wm.open_mainfile(filepath=str(backup/f'{cid}.blend'));old=inspect()
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/generated/{cid}.blend'));new=inspect()
    for k in ('topology','groups','weights','uvs','bones','visibility'):assert new[k]==old[k],f'{cid}: {k} changed'
    assert list(old['morphs'])==list(new['morphs'])
    error=max(float(np.max(np.abs(old['morphs'][k]-new['morphs'][k]))) for k in old['morphs'])
    assert error<2e-6,f'{cid}: morph delta changed {error}'
    results.append({'id':cid,'faces':len(new['topology']),'morphs':len(new['morphs'])-1,
      'topology_uv_weights_bones_visibility_preserved':True,'max_morph_delta_error':error,
      'neutral_expression_changed':bool(np.any(new['base']!=old['base']))})
allowed={'web/renderer/scene.js','web/frontend/scene.bundle.js'}
changes=[path for path,digest in baseline['hashes'].items() if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest]
unexpected=[path for path in changes if path not in allowed and not path.startswith('data/runtime/')]
assert not unexpected,f'超出角色渲染范围: {unexpected}'
(OUT/'verification.json').write_text(json.dumps({'passed':True,'characters':results,'changed_existing_files':changes,'unrelated_changes':unexpected},ensure_ascii=False,indent=2),encoding='utf-8')
print('SHADING_VERIFIED',len(results))
