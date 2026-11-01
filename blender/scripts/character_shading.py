"""可移植材质与克制的默认神态；不改源 PMX 或图集。"""
import json,re
from pathlib import Path
import numpy as np
CONFIG=json.loads((Path(__file__).with_name('character_style.json')).read_text(encoding='utf-8'))

def material_class(name):
    name=re.sub(r'\.\d+$','',name)
    if name=='颜':return 'face'
    if '肌' in name or name=='指甲':return 'skin'
    if name in ('白目','目','目光','齿'):return 'eye'
    if '髪' in name:return 'hair'
    if re.search('金属|宝石|链|肩甲',name):return 'metal'
    return 'cloth'

def apply_character_style(cid,meshes):
    info={'id':cid,'expression':{},'materials':[]}
    for obj in meshes:
        # 默认表情的位移同时加在所有键上，保留每个动画键相对中性脸的增量。
        keys=obj.data.shape_keys.key_blocks if obj.data.shape_keys else None
        if keys and not obj.data.get('treecourt_expression_v1'):
            size=len(keys[0].data)*3
            base=np.empty(size,dtype=np.float32);keys[0].data.foreach_get('co',base)
            delta=np.zeros_like(base)
            for name,weight in CONFIG['characters'][cid]['expression'].items():
                if name not in keys:raise RuntimeError(f'{cid} 缺少表情 {name}')
                coords=np.empty(size,dtype=np.float32);keys[name].data.foreach_get('co',coords)
                delta+=(coords-base)*weight
            for key in keys:
                coords=np.empty(size,dtype=np.float32);key.data.foreach_get('co',coords)
                key.data.foreach_set('co',coords+delta)
                key.value=0.0
            obj.data.vertices.foreach_set('co',base+delta)
            obj.data['treecourt_expression_v1']=True
        info['expression']=CONFIG['characters'][cid]['expression']
        for mat in obj.data.materials:
            cls=material_class(mat.name);p=CONFIG['classes'][cls]
            shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            shader.inputs['Roughness'].default_value=p['roughness']
            shader.inputs['Specular IOR Level'].default_value=.18 if cls in ('face','skin') else .3
            shader.inputs['Metallic'].default_value=0
            # 通用 GLB/PBR 查看器的保底柔光；网站与 UE 使用各自的卡通明暗。
            shader.inputs['Emission Strength'].default_value=p['emission']
            if shader.inputs['Base Color'].is_linked:
                texture=shader.inputs['Base Color'].links[0].from_socket
                mat.node_tree.links.new(texture,shader.inputs['Emission Color'])
            if cls in ('face','skin'):
                shader.inputs['Subsurface Weight'].default_value=.035
                shader.inputs['Subsurface Radius'].default_value=(1.0,.45,.3)
            mat['treecourt_shading_class']=cls
            info['materials'].append({'name':mat.name,'class':cls,'roughness':p['roughness'],'emission':p['emission']})
    return info
