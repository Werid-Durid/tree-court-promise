"""将不同材质的共顶点覆盖面分开，防止导出器 validate 误删实体表面。"""
import bpy
import numpy as np


def isolate_material_surfaces(obj):
    source=obj.data
    group_names=[g.name for g in obj.vertex_groups]
    if source.get('treecourt_material_surfaces_isolated'):
        return {'already_isolated':True,'vertices':len(source.vertices),'faces':len(source.polygons)}
    vertex_source=list(range(len(source.vertices)))
    first_material={}
    lookup={}
    faces=[]
    for polygon in source.polygons:
        face=[]
        for index in polygon.vertices:
            key=(index,polygon.material_index)
            if key not in lookup:
                if index not in first_material:
                    first_material[index]=polygon.material_index
                    lookup[key]=index
                else:
                    lookup[key]=len(vertex_source)
                    vertex_source.append(index)
            face.append(lookup[key])
        faces.append(face)
    positions=np.empty(len(source.vertices)*3,dtype=np.float32)
    source.vertices.foreach_get('co',positions)
    mapped=positions.reshape(-1,3)[vertex_source]
    target=bpy.data.meshes.new(source.name+'_SurfaceSafe')
    target.from_pydata(mapped.tolist(),[],faces)
    for material in source.materials:target.materials.append(material)
    for original,polygon in zip(source.polygons,target.polygons):
        polygon.material_index=original.material_index
        polygon.use_smooth=original.use_smooth
    for layer in source.uv_layers:
        copied=target.uv_layers.new(name=layer.name)
        values=np.empty(len(layer.data)*2,dtype=np.float32)
        layer.data.foreach_get('uv',values)
        copied.data.foreach_set('uv',values)
        copied.active_render=layer.active_render
    target.uv_layers.active_index=source.uv_layers.active_index
    if source.has_custom_normals:
        target.normals_split_custom_set([n.vector for n in source.corner_normals])
    target.update()
    if target.validate(verbose=True,clean_customdata=False):
        raise RuntimeError('分离后的拓扑仍存在无效面，停止导出以免丢面')
    original_keys=list(source.shape_keys.key_blocks) if source.shape_keys else []
    obj.data=target
    obj.vertex_groups.clear()
    for name in group_names:obj.vertex_groups.new(name=name)
    for index,old_index in enumerate(vertex_source):
        for membership in source.vertices[old_index].groups:
            obj.vertex_groups[membership.group].add([index],membership.weight,'REPLACE')
    keys={}
    for block in original_keys:
        copied=obj.shape_key_add(name=block.name,from_mix=False)
        values=np.empty(len(block.data)*3,dtype=np.float32)
        block.data.foreach_get('co',values)
        copied.data.foreach_set('co',values.reshape(-1,3)[vertex_source].ravel())
        copied.slider_min=block.slider_min;copied.slider_max=block.slider_max
        copied.value=block.value;copied.mute=block.mute
        copied.interpolation=block.interpolation
        keys[block.name]=copied
    for block in original_keys:
        keys[block.name].relative_key=keys[block.relative_key.name]
    target['treecourt_material_surfaces_isolated']=True
    assert len(target.polygons)==len(source.polygons)
    assert len(keys)==len(original_keys)
    # 新增顶点均精确复制原顶点位置、权重与每一帧形态键，不做填洞变形。
    return {'already_isolated':False,'source_vertices':len(source.vertices),'vertices':len(target.vertices),
            'faces':len(target.polygons),'morphs':max(0,len(keys)-1),
            'added_seam_vertices':len(vertex_source)-len(source.vertices),
            'surface_positions_unchanged':True,'weights_and_morphs_copied':True}
