"""从已修复完整面的模型生成新的材质与神态，并验证三角面未减少。"""
import bpy,sys,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'blender'),str(ROOT/'blender/vendor'),str(ROOT/'blender/vendor/pythonlibs')]
import mmd_tools
mmd_tools.register()
from character_shading import apply_character_style
OUT=ROOT/'blender/generated'
report=[]
bpy.context.preferences.filepaths.save_version=0
for cid in ('anaxa','hyacine','castor','phainon'):
    bpy.ops.wm.open_mainfile(filepath=str(OUT/f'{cid}.blend'))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
    armatures=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    before=sum(len(o.data.polygons) for o in meshes)
    info=apply_character_style(cid,meshes)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes+armatures:o.select_set(True)
    bpy.context.view_layer.objects.active=armatures[0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{cid}.blend'))
    originals={o:o.data for o in meshes}
    try:
        for obj,data in originals.items():obj.data=data.copy()
        bpy.ops.export_scene.gltf(filepath=str(OUT/f'{cid}.glb'),use_selection=True,export_format='GLB',export_animations=False,export_morph=True)
        bpy.ops.export_scene.fbx(filepath=str(OUT/f'{cid}.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
    finally:
        for obj,data in originals.items():obj.data=data
    blob=(OUT/f'{cid}.glb').read_bytes();length=struct.unpack_from('<I',blob,12)[0];gltf=json.loads(blob[20:20+length])
    triangles=sum(gltf['accessors'][p['indices']]['count']//3 for mesh in gltf['meshes'] for p in mesh['primitives'])
    assert triangles==before,'材质优化不可丢失任何面'
    info.update(triangles=triangles,status='exported')
    report.append(info)
    (ROOT/'blender/shading-reports/export.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('STYLE_EXPORTED',cid,flush=True)
