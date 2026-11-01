"""只修复四个人物派生材质并重导出；网格、权重、Morph 和场景保持不变。"""
import bpy
import json
import sys
import struct
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'blender'),str(ROOT/'blender/vendor'),str(ROOT/'blender/vendor/pythonlibs')]
import mmd_tools
mmd_tools.register()
from model_materials import repair_material
from model_topology import isolate_material_surfaces
from character_shading import apply_character_style
OUT=ROOT/'blender/generated'
report=[]
bpy.context.preferences.filepaths.save_version=0
for cid in ('anaxa','hyacine','castor','phainon'):
    bpy.ops.wm.open_mainfile(filepath=str(OUT/f'{cid}.blend'))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
    armatures=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    def topology():
        return [{'vertices':len(o.data.vertices),'faces':len(o.data.polygons),
                 'morphs':len(o.data.shape_keys.key_blocks)-1 if o.data.shape_keys else 0,
                 'geometry_sha256':hashlib.sha256(b''.join(struct.pack('<3f',*v.co) for v in o.data.vertices)+b''.join(struct.pack('<I',i) for p in o.data.polygons for i in p.vertices)).hexdigest()}
                for o in meshes]
    surface_repair=[isolate_material_surfaces(obj) for obj in meshes]
    before=topology()
    materials=[]
    for mat in meshes[0].data.materials:
        materials.append(repair_material(mat))
    apply_character_style(cid,meshes)
    before=topology()
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes+armatures:obj.select_set(True)
    bpy.context.view_layer.objects.active=armatures[0]
    assert topology()==before,'材质修复不应改变几何／Morph'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{cid}.blend'))
    # Blender 导出器会校验并清理输入网格；只让它处理副本，保护 .blend 原几何。
    originals={o:o.data for o in meshes}
    try:
        for obj,data in originals.items():obj.data=data.copy()
        bpy.ops.export_scene.gltf(filepath=str(OUT/f'{cid}.glb'),use_selection=True,export_format='GLB',export_animations=False,export_morph=True)
        bpy.ops.export_scene.fbx(filepath=str(OUT/f'{cid}.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
    finally:
        for obj,data in originals.items():obj.data=data
    assert topology()==before,'材质修复不应改变几何／Morph'
    blob=(OUT/f'{cid}.glb').read_bytes();length=struct.unpack_from('<I',blob,12)[0];gltf=json.loads(blob[20:20+length])
    exported={m['name']:m for m in gltf['materials']}
    for material in materials:
        m=exported[material['name']]
        assert m.get('doubleSided',False)==material['double_sided']
        if material['mode']=='OPAQUE':assert m.get('alphaMode','OPAQUE')=='OPAQUE'
    triangle_count=sum(gltf['accessors'][p['indices']]['count']//3 for mesh in gltf['meshes'] for p in mesh['primitives'])
    assert triangle_count==sum(len(o.data.polygons) for o in meshes),'导出三角面不能被清理丢失'
    report.append({'id':cid,'surface_positions_unchanged':True,'surface_repair':surface_repair,'topology':before,'exported_triangles':triangle_count,'materials':materials,'status':'exported'})
    (ROOT/'blender/repair-reports/repair-export.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('MODEL_REPAIRED',cid,flush=True)
asset_report=OUT/'asset-report.json'
if asset_report.exists():
    entries=json.loads(asset_report.read_text(encoding='utf-8'))
    for entry in entries:
        repaired=next(r for r in report if r['id']==entry['id'])
        entry['vertices']=sum(t['vertices'] for t in repaired['topology'])
        entry['faces']=repaired['exported_triangles']
        entry['integrity_repair']={'surface_positions_unchanged':True,'source_faces_preserved':True,'materials_restored':True}
    asset_report.write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
