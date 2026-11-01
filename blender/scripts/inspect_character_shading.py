"""只读检查皮肤图集、材质与表情，供风格校准使用。"""
import bpy, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'blender/vendor'),str(ROOT/'blender/vendor/pythonlibs')]
import mmd_tools
mmd_tools.register()
report=[]
for cid in ('anaxa','hyacine','castor','phainon'):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/generated/{cid}.blend'))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.shape_keys]
    report.append({'id':cid,'morphs':[k.name for k in meshes[0].data.shape_keys.key_blocks],
      'materials':[{'name':m.name,'color':list(m.diffuse_color),'nodes':[
        {'type':n.type,'image':n.image.filepath if n.type=='TEX_IMAGE' and n.image else None,
         'size':list(n.image.size) if n.type=='TEX_IMAGE' and n.image else None,
         'values':{s.name:list(s.default_value) if s.type=='RGBA' else s.default_value for s in n.inputs if s.name in ('Roughness','Metallic','Base Color','Specular IOR Level','Emission Strength') and not s.is_linked}}
        for n in m.node_tree.nodes]} for m in meshes[0].data.materials]})
(ROOT/'blender/repair-reports/shading-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
