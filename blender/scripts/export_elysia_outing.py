import bpy,json,sys,math,bmesh
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'blender/build/phainon-elysia';bpy.ops.wm.open_mainfile(filepath=str(O/'phainon_wheat_film.blend'));s=bpy.context.scene;s.frame_set(1)
# Export a browser LOD from the supplied meshes, retaining the original atlas RGB.
selected=[];materials={};stats=[]
for o in list(s.objects):
 if o.get('treecourt_environment')!='elysia' or o.type!='MESH' or o.hide_render or any(k in o.name for k in ['日光束','体积光','尘埃','太阳与','原型七十七','麦穗零','参考地面']):continue
 if o.name in ('麦田空间风浪与人物避让','中景山坡短麦穗与自然簇'):
  bm=bmesh.new();bm.from_mesh(o.data);cut=[v for i,v in enumerate(bm.verts) if v.co.y>65 or abs(v.co.x)>48 or (i%3!=0 and v.co.length>12)];bmesh.ops.delete(bm,geom=cut,context='VERTS');bm.to_mesh(o.data);bm.free()
  for mod in o.modifiers:
   if mod.type=='NODES':
    ng=mod.node_group.copy();mod.node_group=ng;out=next(n for n in ng.nodes if n.type=='GROUP_OUTPUT');socket=out.inputs[0];link=socket.links[0];orig=link.from_socket;ng.links.remove(link);real=ng.nodes.new('GeometryNodeRealizeInstances');ng.links.new(orig,real.inputs[0]);ng.links.new(real.outputs[0],socket)
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=bpy.data.meshes.new_from_object(ev);new=bpy.data.objects.new('Elysia_'+o.name,mesh);s.collection.objects.link(new);new.matrix_world=o.matrix_world.copy();selected.append(new);stats.append([o.name,len(mesh.vertices)])
 for i,mat in enumerate(mesh.materials):
  if not mat:continue
  if mat.name not in materials:
   m=bpy.data.materials.new('Elysia_Web_'+mat.name);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=mat.diffuse_color;p.inputs['Roughness'].default_value=.9
   images=[n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if mat.use_nodes else []
   color=next((im for im in images if '基础' in im.name or '基色' in im.name or '麦穗' in im.name),None)
   if not color and ('麦' in mat.name or '穗' in mat.name):p.inputs['Base Color'].default_value=(.65,.40,.10,1)
   if color:
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=color;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
    if '透明' in color.name:m.node_tree.links.new(tex.outputs['Alpha'],p.inputs['Alpha']);m.surface_render_method='DITHERED';m.use_backface_culling=False
   materials[mat.name]=m
  mesh.materials[i]=materials[mat.name]
# Put the supplied panoramic sky inside the browser scene as an unlit dome.
image=bpy.data.images.load(str(O/'sky.png'),check_existing=True)
if image:
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=450)
 sky=bpy.context.object;sky.name='Elysia_Sky';bm=bmesh.new();bm.from_mesh(sky.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(sky.data);bm.free()
 mat=bpy.data.materials.new('Elysia_Panorama');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();tex=n.new('ShaderNodeTexImage');tex.image=image;em=n.new('ShaderNodeEmission');out=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(tex.outputs['Color'],em.inputs[0]);mat.node_tree.links.new(em.outputs[0],out.inputs['Surface']);sky.data.materials.append(mat);selected.append(sky)
bpy.ops.object.select_all(action='DESELECT')
for o in selected:o.select_set(True)
bpy.ops.export_scene.gltf(export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,filepath=str(O/'wheat.glb'),export_format='GLB',use_selection=True,export_animations=False,export_materials='EXPORT',export_cameras=False,export_lights=False)
layout=dict(scene='wheat',environment='elysia',media_revision=4,source_author='小二今天吃啥啊',player_start=[0,1.65,3.2],character_position=[0,0,0],eye_height=1.65,bounds=[-2.6,2.6,-1.8,3.8],colliders=[],ground_height=0)
(O/'wheat.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8');(O/'web-scene-report.json').write_text(json.dumps(dict(meshes=stats,vertices=sum(x[1] for x in stats),bytes=(O/'wheat.glb').stat().st_size),ensure_ascii=False,indent=2),encoding='utf-8');print('ELYSIA_WEB_EXPORTED',flush=True)
