"""对比物理版与生产版自习室模型的网格/材质，判断是否需要修复。"""
import bpy
import json

ROOT = r'D:\开发项目\树庭学习室\tree_court'
out = {}
for label, rel in [('physics', r'\blender\physics\anaxa.blend'), ('study', r'\blender\study\anaxa.blend')]:
    bpy.ops.wm.open_mainfile(filepath=ROOT + rel)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    m = next((o for o in meshes if o.data and len(o.data.polygons) > 1000), meshes[0] if meshes else None)
    if m is None:
        out[label] = {'missing': True}
        continue
    mats = [mat.name for mat in m.data.materials if mat]
    dup = len(mats) - len(set(mats))
    out[label] = {
        'objects': len(bpy.data.objects),
        'mesh': m.name,
        'verts': len(m.data.vertices),
        'polys': len(m.data.polygons),
        'materials': len(mats),
        'dup_materials': dup,
        'mat_sample': mats[:12],
        'shape_keys': len(m.data.shape_keys.key_blocks) if m.data.shape_keys else 0,
    }
print('MESH_COMPARE ' + json.dumps(out, ensure_ascii=False))
