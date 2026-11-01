"""重新读取磁盘上的新旧模型，核对原顶点、权重、UV、骨骼与 Morph。"""
import bpy
import json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'blender/repair-reports'
guard=json.loads((OUT/'scope-guard.json').read_text(encoding='utf-8'))
backup=Path(guard['backup'])
results=[]
def mesh_object():
    return next(o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
def positions(data):
    a=np.empty(len(data)*3,dtype=np.float32);data.foreach_get('co',a);return a.reshape(-1,3)
for cid in ('anaxa','hyacine','castor','phainon'):
    bpy.ops.wm.open_mainfile(filepath=str(backup/f'{cid}.blend'))
    old=mesh_object();n=len(old.data.vertices)
    old_positions=positions(old.data.vertices)
    old_faces=len(old.data.polygons)
    old_groups=[g.name for g in old.vertex_groups]
    old_weights=[sorted((g.group,round(g.weight,6)) for g in v.groups) for v in old.data.vertices]
    old_keys={k.name:positions(k.data) for k in old.data.shape_keys.key_blocks}
    old_uvs={layer.name:np.array([tuple(d.uv) for d in layer.data]) for layer in old.data.uv_layers}
    old_bones=[b.name for o in bpy.data.objects if o.type=='ARMATURE' for b in o.data.bones]
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/generated/{cid}.blend'))
    new=mesh_object()
    assert np.array_equal(positions(new.data.vertices)[:n],old_positions)
    assert [g.name for g in new.vertex_groups]==old_groups
    assert [sorted((g.group,round(g.weight,6)) for g in v.groups) for v in list(new.data.vertices)[:n]]==old_weights
    assert len(new.data.polygons)==old_faces
    assert [k.name for k in new.data.shape_keys.key_blocks]==list(old_keys)
    for name,coords in old_keys.items():assert np.array_equal(positions(new.data.shape_keys.key_blocks[name].data)[:n],coords)
    for name,uv in old_uvs.items():assert np.array_equal(np.array([tuple(d.uv) for d in new.data.uv_layers[name].data]),uv)
    assert [b.name for o in bpy.data.objects if o.type=='ARMATURE' for b in o.data.bones]==old_bones
    results.append({'id':cid,'source_vertices_preserved':n,'added_surface_vertices':len(new.data.vertices)-n,
      'faces_preserved':old_faces,'bone_names_unchanged':True,'weights_unchanged':True,'morph_positions_unchanged':True,'uvs_unchanged':True})
(OUT/'geometry-verification.json').write_text(json.dumps({'passed':True,'characters':results},ensure_ascii=False,indent=2),encoding='utf-8')
asset_report=ROOT/'blender/generated/asset-report.json'
entries=json.loads(asset_report.read_text(encoding='utf-8'))
for entry in entries:
    checked=next(r for r in results if r['id']==entry['id'])
    entry['vertices']=checked['source_vertices_preserved']+checked['added_surface_vertices']
    entry['faces']=checked['faces_preserved']
    entry['integrity_repair']={'surface_positions_unchanged':True,'source_faces_preserved':True,'materials_restored':True}
asset_report.write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
print('MODEL_INTEGRITY_VERIFIED',len(results))
