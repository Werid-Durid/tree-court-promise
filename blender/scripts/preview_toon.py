"""首个单角色材质对照：固定姿势、相机和光照；不导出覆盖运行时角色。"""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'))
from materials.toon_shader import apply_toon,CONFIG
OUT=ROOT/'blender/build/toon-anaxa';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/animated/anaxa.blend'))
scene=bpy.context.scene;scene.frame_set(61)
engines={x.identifier for x in scene.render.bl_rna.properties['engine'].enum_items}
scene.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in engines else 'BLENDER_EEVEE_NEXT';scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.65,.72,.68,1);scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.2
meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
for obj in list(scene.objects):
 if obj.type in {'CAMERA','LIGHT'}:bpy.data.objects.remove(obj,do_unlink=True)
arm=next(o for o in scene.objects if o.type=='ARMATURE');center=arm.matrix_world@arm.pose.bones['頭'].head;center.z-=.20
bpy.ops.object.camera_add(location=center+Vector((.45,-2.5,.08)));camera=bpy.context.object;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=.90;scene.camera=camera
for name,position,energy,size in [('Key',(-3,-4,5),450,4),('Fill',(3,-2,3),120,3)]:
 bpy.ops.object.light_add(type='AREA',location=position);light=bpy.context.object;light.name=name;light.data.energy=energy;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
def render(name):scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
render('before.png')
materials={m for o in meshes for m in o.data.materials if m and m.get('treecourt_surface_mode')=='OPAQUE'}
selected=[]
for group in [('face','skin'),('cloth',)]:
 candidates=sorted((m for m in materials if m.get('treecourt_shading_class') in group),key=lambda m:(group.index(m.get('treecourt_shading_class')),not m.name.startswith('衣'),m.name))
 mat=candidates[0] if candidates else None
 if mat:
  copy=mat.copy();copy.name=mat.name+'_ToonTest'
  for o in meshes:
   for slot in o.material_slots:
    if slot.material==mat:slot.material=copy
  apply_toon(copy,rim=False);selected.append({'original':mat.name,'copy':copy.name,'class':mat.get('treecourt_shading_class')})
assert len(selected)==2,'缺少待测皮肤或布料材质'
render('toon-three-steps.png')
for row in selected:
 if row['class']=='cloth':
  mat=bpy.data.materials[row['copy']]
  # 第三个图用独立边缘光分支，原基础分段不变。
  nodes=mat.node_tree.nodes;links=mat.node_tree.links;emission=next(n for n in nodes if n.type=='EMISSION');base=emission.inputs['Color'].links[0].from_socket
  f=nodes.new('ShaderNodeFresnel');f.inputs['IOR'].default_value=CONFIG['rim_ior'];r=nodes.new('ShaderNodeValToRGB');r.color_ramp.interpolation='CONSTANT';r.color_ramp.elements[1].position=.7;r.color_ramp.elements[1].color=(.08,.075,.066,1)
  add=nodes.new('ShaderNodeMixRGB');add.blend_type='ADD';add.inputs[0].default_value=1;links.new(f.outputs[0],r.inputs[0]);links.new(base,add.inputs[1]);links.new(r.outputs[0],add.inputs[2]);links.new(add.outputs[0],emission.inputs['Color'])
render('toon-rim.png')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'anaxa-material-test.blend'))
(OUT/'report.json').write_text(json.dumps({'status':'preview_ready','materials':selected,'config':CONFIG,'runtime_applied':False,'outline':'deferred: material preview only'},ensure_ascii=False,indent=2),encoding='utf-8')
