"""在 Blender 后台导入项目 PMX，生成派生 GLB/FBX；绝不修改原始素材。"""
import bpy
import hashlib
import json
import sys
import time
import traceback
import zipfile
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "blender/generated"
OUT.mkdir(parents=True, exist_ok=True)
VENDOR = ROOT / "blender/vendor"
ADDON = VENDOR / "mmd_tools"
ZIP = Path("D:/Blender插件/01_插件_addons/mmd_tools-v4.5.13-bl4.2.zip")
if not ADDON.exists():
    ADDON.mkdir(parents=True)
    with zipfile.ZipFile(ZIP) as archive:
        for item in archive.infolist():
            target = (ADDON / item.filename).resolve()
            if not target.is_relative_to(ADDON.resolve()):
                raise RuntimeError("插件压缩包路径越界")
            archive.extract(item, ADDON)
sys.path.insert(0, str(VENDOR))
LIBS = VENDOR / "pythonlibs"
LIBS.mkdir(exist_ok=True)
for wheel in (ADDON / "wheels").glob("*.whl"):
    with zipfile.ZipFile(wheel) as archive:
        for item in archive.infolist():
            if not (LIBS / item.filename).resolve().is_relative_to(LIBS.resolve()):
                raise RuntimeError("依赖压缩包路径越界")
            archive.extract(item, LIBS)
sys.path.insert(0, str(LIBS))
import mmd_tools
mmd_tools.register()
sys.path.insert(0,str(ROOT/'blender'))
from model_materials import repair_material
from model_topology import isolate_material_surfaces
from character_shading import apply_character_style

MODELS = {
    "anaxa": ("那刻夏", "teacher"), "hyacine": ("风堇", "assistant"),
    "castor": ("遐蝶", "classmate"), "phainon": ("白厄", "classmate")
}
reports = []
for cid, (label, role) in MODELS.items():
    start = time.time()
    report = {"id": cid, "name": label, "role": role, "blender": bpy.app.version_string}
    try:
        # 最短匹配路径避开角色文件夹中意外嵌套的重复资源包。
        candidates = [p for p in ROOT.glob("星穹铁道*/**/*.pmx") if label in p.name and "变身" not in str(p)]
        source = min(candidates, key=lambda p: len(str(p)))
        report.update(source=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        bpy.ops.mmd_tools.import_model(filepath=str(source), scale=0.08, types={"MESH", "ARMATURE", "MORPHS"})
        armatures = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)]
        if not meshes or not armatures:
            raise RuntimeError("没有导入有效骨骼或蒙皮网格")
        # 转为跨引擎可用的基础材质；MMD 的特殊卡通着色仍需在引擎端继续调校。
        missing = []
        textured_materials=0
        for mat in {m for o in meshes for m in o.data.materials if m}:
            images = [n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image] if mat.node_tree else []
            base_node=mat.node_tree.nodes.get("mmd_base_tex") if mat.node_tree else None
            image = base_node.image if base_node and base_node.type=="TEX_IMAGE" else next((i for i in images if "toon" not in i.name.lower() and "sph" not in i.name.lower()), None)
            diffuse = tuple(mat.diffuse_color)
            mat.use_nodes = True
            mat.node_tree.nodes.clear()
            output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
            shader = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
            shader.inputs["Base Color"].default_value = diffuse
            shader.inputs["Roughness"].default_value = 0.83
            mat.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
            if image:
                textured_materials+=1
                texture = mat.node_tree.nodes.new("ShaderNodeTexImage")
                texture.image = image
                mat.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
                mat.node_tree.links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
                if image.source == "FILE" and not Path(bpy.path.abspath(image.filepath)).exists():
                    missing.append(image.filepath)
            mat.use_backface_culling = False
            repair_material(mat)
        surface_repair=[isolate_material_surfaces(o) for o in meshes]
        apply_character_style(cid,meshes)
        bounds = [o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
        report.update(meshes=len(meshes), vertices=sum(len(o.data.vertices) for o in meshes),
                      bones=sum(len(o.data.bones) for o in armatures),
                      morphs=sum(max(0,len(o.data.shape_keys.key_blocks)-1) if o.data.shape_keys else 0 for o in meshes),
                      height_m=max(v.z for v in bounds)-min(v.z for v in bounds),missing_textures=missing,
                      animations=[a.name for a in bpy.data.actions],textured_materials=textured_materials,
                      limitations=["基础 PBR 材质，不是原游戏着色器", "未烘焙 MMD 物理", "无官方动作或配音"])
        bpy.ops.object.select_all(action="DESELECT")
        for o in meshes + armatures:
            o.select_set(True)
        bpy.context.view_layer.objects.active = armatures[0]
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"{cid}.blend"))
        bpy.ops.export_scene.gltf(filepath=str(OUT / f"{cid}.glb"), use_selection=True,
                                  export_format="GLB", export_animations=False, export_morph=True)
        bpy.ops.export_scene.fbx(filepath=str(OUT / f"{cid}.fbx"), use_selection=True,
                                 object_types={"MESH", "ARMATURE"}, add_leaf_bones=False,
                                 bake_anim=False, path_mode="COPY", embed_textures=True)
        report["status"] = "exported"
    except Exception:
        report["status"] = "failed"
        report["error"] = traceback.format_exc()
    report["elapsed_seconds"] = round(time.time()-start, 2)
    reports.append(report)
    (OUT / "asset-report.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TREECOURT_ASSET=" + json.dumps(report, ensure_ascii=False), flush=True)
if any(r["status"] != "exported" for r in reports):
    raise RuntimeError("部分角色导出失败，请检查 asset-report.json")
