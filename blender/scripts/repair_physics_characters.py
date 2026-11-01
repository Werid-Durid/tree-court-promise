"""给物理版角色补生产版材质/拓扑处理，使导出的 GLB 与生产版一致。"""
import bpy
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blender'))
from model_materials import repair_material  # noqa: E402
from model_topology import isolate_material_surfaces  # noqa: E402
from character_shading import apply_character_style  # noqa: E402

IDS = ['anaxa', 'hyacine', 'castor', 'phainon']
for cid in IDS:
    start = time.time()
    path = ROOT / 'blender/physics' / f'{cid}.blend'
    if not path.is_file():
        print('MISSING', cid, flush=True)
        continue
    bpy.ops.wm.open_mainfile(filepath=str(path))
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and any(m.type == 'ARMATURE' for m in o.modifiers)]
    if not meshes:
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    for mat in {m for o in meshes for m in o.data.materials if m}:
        images = [n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image] if mat.node_tree else []
        base_node = mat.node_tree.nodes.get('mmd_base_tex') if mat.node_tree else None
        image = base_node.image if base_node and base_node.type == 'TEX_IMAGE' else next(
            (i for i in images if 'toon' not in i.name.lower() and 'sph' not in i.name.lower()), None)
        diffuse = tuple(mat.diffuse_color)
        mat.use_nodes = True
        mat.node_tree.nodes.clear()
        output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
        shader = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        shader.inputs['Base Color'].default_value = diffuse
        shader.inputs['Roughness'].default_value = 0.83
        mat.node_tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])
        if image:
            texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
            texture.image = image
            mat.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
            mat.node_tree.links.new(texture.outputs['Alpha'], shader.inputs['Alpha'])
        mat.use_backface_culling = False
        repair_material(mat)
    for o in meshes:
        isolate_material_surfaces(o)
    apply_character_style(cid, meshes)
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    verts = sum(len(o.data.vertices) for o in meshes)
    print('REPAIRED ' + cid + ' verts=' + str(verts) + ' elapsed=' + str(round(time.time() - start, 1)), flush=True)
print('REPAIR_DONE')
