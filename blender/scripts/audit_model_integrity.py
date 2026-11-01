"""只读检查派生角色网格、材质 Alpha、UV 和权重，定位镂空；不保存模型。"""
import bpy
import json
from pathlib import Path
import numpy as np
import sys
from collections import Counter,defaultdict

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"blender/repair-reports"
OUT.mkdir(exist_ok=True)
sys.path[:0]=[str(ROOT/"blender/vendor"),str(ROOT/"blender/vendor/pythonlibs")]
import mmd_tools
mmd_tools.register()
report=[]
for cid in ("anaxa","hyacine","castor","phainon"):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f"blender/generated/{cid}.blend"))
    meshes=[o for o in bpy.data.objects if o.type=="MESH" and any(m.type=="ARMATURE" for m in o.modifiers)]
    item={"id":cid,"meshes":[],"materials":[]}
    images={}
    for obj in meshes:
        mesh=obj.data
        edges={}
        for poly in mesh.polygons:
            for e in poly.edge_keys:
                edges[e]=edges.get(e,0)+1
        coincident=defaultdict(list)
        for poly in mesh.polygons:
            key=tuple(sorted(tuple(round(x,6) for x in mesh.vertices[i].co) for i in poly.vertices))
            coincident[key].append(poly.material_index)
        pairs=Counter()
        for group in coincident.values():
            if len(group)>1:
                pairs[' | '.join(sorted(set(mesh.materials[i].name for i in group)))]+=1
        item["meshes"].append({"name":obj.name,"vertices":len(mesh.vertices),"polygons":len(mesh.polygons),
          "boundary_edges":sum(v==1 for v in edges.values()),"loose_vertices":sum(not v.groups for v in mesh.vertices),
          "coincident_face_groups":sum(len(v)>1 for v in coincident.values()),"coincident_material_pairs":dict(pairs),
          "modifiers":[{"type":m.type,"viewport":m.show_viewport,"render":m.show_render} for m in obj.modifiers]})
        for mat in obj.data.materials:
            if not mat:continue
            shader=next((n for n in mat.node_tree.nodes if n.type=="BSDF_PRINCIPLED"),None)
            nodes=[n for n in mat.node_tree.nodes if n.type=="TEX_IMAGE" and n.image]
            image=nodes[0].image if nodes else None
            image_stats=None
            if image:
                if image.name not in images:
                    values=np.empty(len(image.pixels),dtype=np.float32)
                    image.pixels.foreach_get(values)
                    alpha=values[3::4]
                    images[image.name]={"name":image.name,"size":list(image.size),"alpha_min":float(alpha.min()),"alpha_max":float(alpha.max()),
                      "alpha_below_02":round(float((alpha<.2).mean()),5),"alpha_nonopaque":round(float((alpha<.999).mean()),5)}
                image_stats=images[image.name]
            item["materials"].append({"name":mat.name,"pmx_alpha":mat.mmd_material.alpha,"pmx_double_sided":mat.mmd_material.is_double_sided,"alpha_value":shader.inputs["Alpha"].default_value if shader else None,
              "alpha_linked":shader.inputs["Alpha"].is_linked if shader else None,"backface_culling":mat.use_backface_culling,
              "image":image_stats})
    report.append(item)
(OUT/"before-audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("TREECOURT_AUDIT_COMPLETE",[(r["id"],len(r["materials"])) for r in report])
