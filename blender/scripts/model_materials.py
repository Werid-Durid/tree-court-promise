"""保留 PMX 正反面与显隐语义，避免共面内外层同时渲染产生假洞。"""
def repair_material(mat):
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    alpha=float(mat.mmd_material.alpha)
    double_sided=bool(mat.mmd_material.is_double_sided)
    # 身体、衣物图集的 Alpha 不一律当作实体表面的透明遮罩。
    # PMX 已有独立反面和覆盖层；重复双面渲染会造成深度争抢。
    for link in list(shader.inputs['Alpha'].links):
        mat.node_tree.links.remove(link)
    shader.inputs['Alpha'].default_value=alpha
    mat.use_backface_culling=not double_sided
    rgba=list(mat.diffuse_color);rgba[3]=alpha;mat.diffuse_color=rgba
    mode='HIDDEN' if alpha<=0.001 else 'OPAQUE' if alpha>=0.999 else 'BLEND'
    mat['treecourt_surface_mode']=mode
    mat['treecourt_double_sided']=double_sided
    return {'name':mat.name,'alpha':alpha,'mode':mode,'double_sided':double_sided}
