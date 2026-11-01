import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=next(ROOT.glob('哀丽秘榭*/*白天*.blend'))
def replace_environment(scene):
 prefixes=('Earth','Footpath','Path worn stone','Wind_Wheat_Patch','Fence ','Tree trunk','Autumn leaf crown','Village house','Tiled farmhouse roof','Warm doorway','Window','Windmill','Distant hills','Evening cloud','Distant setting sun')
 if scene.get('treecourt_environment')=='哀丽秘榭的麦田':return {'already_replaced':True}
 removed=[]
 for o in list(scene.objects):
  if o.name.startswith(prefixes):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
 with bpy.data.libraries.load(str(SOURCE),link=False) as (src,dst):
  dst.objects=list(src.objects);dst.worlds=list(src.worlds)
 objects=[o for o in dst.objects if o]
 col=bpy.data.collections.new('Elysia • 小二今天吃啥啊 • 邀约场景');scene.collection.children.link(col)
 skip=[]
 for o in objects:
  # Legacy particle emitters duplicate the supplied modern wind-driven field.
  if o.type=='CAMERA' or any(m.type=='PARTICLE_SYSTEM' for m in o.modifiers):skip.append(o);continue
  col.objects.link(o);o['treecourt_environment']='elysia';o['source_author']='小二今天吃啥啊'
 for o in skip:bpy.data.objects.remove(o,do_unlink=True)
 # Keep a clear picnic space and omit plants behind every invitation camera.
 import bmesh
 for o in col.objects:
  if o.name in ('麦田空间风浪与人物避让','中景山坡短麦穗与自然簇'):
   o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
   cut=[v for v in bm.verts if (v.co.x/3.2)**2+((v.co.y+.5)/4.0)**2<1 or v.co.y < -5 or abs(v.co.x)>65 or v.co.y>85]
   bmesh.ops.delete(bm,geom=cut,context='VERTS');bm.to_mesh(o.data);bm.free()
 # Solid soil beneath the planting-point rings and the shared picnic clearing.
 bpy.ops.mesh.primitive_plane_add(size=240,location=(0,0,-.12))
 soil=bpy.context.object;soil.name='Elysia_Solid_Ground';soil['treecourt_environment']='elysia'
 mat=bpy.data.materials.new('Elysia_Soil');mat.use_nodes=True;p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.30,.20,.075,1);p.inputs['Roughness'].default_value=.95;mat.diffuse_color=(.30,.20,.075,1);soil.data.materials.append(mat)
 bpy.ops.mesh.primitive_circle_add(vertices=96,radius=1,fill_type='NGON',location=(0,-.5,-.004))
 clearing=bpy.context.object;clearing.name='Elysia_Picnic_Clearing';clearing.scale=(3.2,4,1);clearing['treecourt_environment']='elysia';clearing.data.materials.append(mat)
 if dst.worlds:scene.world=dst.worlds[0]
 for o in col.objects:
  if o.type=='LIGHT':o.data.use_shadow=False
  if o.name.startswith(('体积光','日光束')):o.hide_render=True
 prototype=next((o for o in col.objects if o.name=='麦穗零'),None)
 if prototype:
  bpy.context.view_layer.objects.active=prototype;prototype.hide_set(False)
  modifier=prototype.modifiers.new('Distant stalk silhouette LOD','DECIMATE');modifier.ratio=.30
  bpy.ops.object.modifier_apply(modifier=modifier.name)
 scene.eevee.taa_render_samples=16
 # The original sun illuminates the environment; retain the film's soft portrait fill.
 for o in scene.objects:
  if o.type=='LIGHT' and o not in objects and o.data.type=='SUN':o.hide_render=True
 scene['treecourt_environment']='哀丽秘榭的麦田';scene['treecourt_environment_source']=str(SOURCE.relative_to(ROOT))
 bpy.context.view_layer.update()
 return dict(source=str(SOURCE.relative_to(ROOT)),author='小二今天吃啥啊',removed=removed,imported=[o.name for o in col.objects])
if __name__=='__main__':
 out=ROOT/'blender/build/phainon-elysia';out.mkdir(exist_ok=True)
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/build/phainon-film-v3/phainon_wheat_film.blend'));scene=bpy.context.scene
 report=replace_environment(scene);scene.render.engine='CYCLES' if '--cycles' in sys.argv else 'CYCLES' if scene.render.engine=='CYCLES' else 'BLENDER_EEVEE'
 scene.eevee.taa_render_samples=16;scene.render.use_sequencer=False;bpy.context.preferences.filepaths.save_version=0
 (out/'scene-replacement.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'phainon_wheat_film.blend'))
 for sec in [7,32,51]:
  scene.frame_set(sec*24+1);scene.render.resolution_percentage=65;scene.render.filepath=str(out/f'preview-{sec}.png');bpy.ops.render.render(write_still=True)

