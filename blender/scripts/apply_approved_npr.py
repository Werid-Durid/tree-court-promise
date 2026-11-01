"""在构建副本应用确认材质，保留课堂动作、权重、形态键及原始模型。"""
import bpy,json,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'blender'))
from materials.toon_shader import apply_toon
CFG=json.loads((ROOT/'blender/materials/approved_npr.json').read_text(encoding='utf-8'))
OUT=ROOT/'blender/build/approved-npr';OUT.mkdir(parents=True,exist_ok=True)
report=[]
for cid in ['anaxa','hyacine','castor','phainon']:
 source=ROOT/f'blender/build/classroom-paired/characters/{cid}.blend'
 if not source.exists():source=ROOT/f'blender/animated/{cid}.blend'
 bpy.ops.wm.open_mainfile(filepath=str(source))
 rows=[]
 for mat in list(bpy.data.materials):
  cls=mat.get('treecourt_shading_class')
  if cls not in ('face','skin','cloth') or mat.get('treecourt_surface_mode')!='OPAQUE':continue
  if cls=='cloth' and not re.search(CFG['cloth_name_pattern'],mat.name):continue
  if not mat.use_nodes or not any(n.type=='BSDF_PRINCIPLED' for n in mat.node_tree.nodes):continue
  apply_toon(mat,rim=cls=='cloth');rows.append({'name':mat.name,'class':cls,'rim':cls=='cloth'})
 assert any(r['class']=='face' for r in rows),(cid,'缺少脸部材质')
 engines={x.identifier for x in bpy.context.scene.render.bl_rna.properties['engine'].enum_items}
 bpy.context.scene.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in engines else 'BLENDER_EEVEE_NEXT'
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{cid}.blend'))
 report.append({'id':cid,'source':str(source),'output':str(OUT/f'{cid}.blend'),'materials':rows})
(OUT/'report.json').write_text(json.dumps({'status':'built','characters':report},ensure_ascii=False,indent=2),encoding='utf-8')
