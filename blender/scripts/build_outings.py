"""四处原创邀约空间：借鉴角色关联场所的意象，不改原模型，不宣称复刻游戏地图。"""
import bpy,math,json,random,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'blender/build/outings';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'blender'))
from spatial_assets import cup,capture_parts
random.seed(47)
COLORS={'stone':(.72,.68,.52),'ivory':(.9,.85,.70),'gold':(.55,.4,.15),'wood':(.27,.16,.08),'leaf':(.25,.43,.23),'water':(.18,.34,.40),'pink':(.69,.33,.44),'purple':(.37,.28,.49),'paper':(.95,.9,.73),'wheat':(.76,.54,.20),'sky':(.42,.63,.70)}
def build(kind):
 bpy.ops.wm.read_factory_settings(use_empty=True);materials={};colliders=[]
 for name,color in COLORS.items():
  m=bpy.data.materials.new('Outing_'+name);m.diffuse_color=(*color,1);m.use_nodes=True;n=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if n is None:
   n=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');output=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(n.outputs['BSDF'],output.inputs['Surface'])
  n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.85;materials[name]=m
 def loc(v):return(v[0],-v[2],v[1])
 def box(name,pos,size,mat,solid=False):
  bpy.ops.mesh.primitive_cube_add(size=1,location=loc(pos));o=bpy.context.object;o.name=name;o.dimensions=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(materials[mat])
  if solid:colliders.append(dict(name=name,center=pos,size=size))
  return o
 def rod(name,a,b,r,mat):
  pa,pb=a,b;a,b=Vector(loc(a)),Vector(loc(b));d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=d.length,location=(a+b)/2);o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(materials[mat])
  if name in ('Column','Pergola_Post','Tree','Shade_Tree'):colliders.append(dict(name=name,center=[(pa[k]+pb[k])/2 for k in range(3)],size=[max(2*r,abs(pa[0]-pb[0])),abs(pa[1]-pb[1]),max(2*r,abs(pa[2]-pb[2]))]))
  return o
 def ball(name,p,r,mat):
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=r,location=loc(p));o=bpy.context.object;o.name=name;o.data.materials.append(materials[mat]);return o
 def book(p,mat='purple'):
  box('Book_Cover',p,(.30,.055,.22),mat);box('Book_Pages',(p[0],p[1]+.036,p[2]),(.28,.026,.20),'paper')
 def table(x,z):
  box('Table',(x,.75,z),(1.5,.10,.80),'wood',True)
  for dx in (-.62,.62):
   for dz in (-.3,.3):box('Table_Leg',(x+dx,.35,z+dz),(.075,.70,.075),'gold')
 def pot(x,z,mat='pink'):
  box('Planter',(x,.25,z),(.7,.5,.7),'stone',True)
  for i in range(5):
   a=i*math.tau/5;tip=(x+.2*math.cos(a),.9+i*.08,z+.2*math.sin(a));rod('Flower_Stem',(x,.5,z),tip,.016,'leaf');ball('Petal',tip,.12,mat)
 box('Ground',(0,-.12,1.3) if kind=='terrace' else (0,-.12,0),(9,.24,12) if kind=='terrace' else (16,.24,18),'stone')
 # 连续石径为站位提供平坦区域；装饰边界与碰撞分离。
 for z in range(-5,7):box('Path_Tile',(0,.006,z),(3.6,.015,.94),'ivory')
 if kind=='grove':
  for x in (-3.5,3.5):
   for z in (-3,1,5):
    rod('Column',(x,0,z),(x,3.7,z),.20,'ivory');box('Column_Base',(x,.12,z),(.65,.24,.65),'gold',True)
   box('Colonnade_Beam',(x,3.8,1),(.5,.30,10),'stone')
  table(-1.9,-1.1)
  for i in range(5):book((-2.4+i*.23,.8275,-1.1),'purple' if i%2 else 'leaf')
  for x in (-3,3):
   box('Shelf_Back',(x,1.25,-4.22),(1.7,2.5,.06),'wood',True)
   for dx in (-.80,.80):box('Shelf_Post',(x+dx,1.25,-4),(.10,2.5,.5),'wood',True)
   for y in (.38,1.08,1.78,2.48):box('Shelf_Board',(x,y,-4),(1.7,.04,.5),'wood')
   for y in (.4,1.1,1.8):
    for i in range(9):box('Library_Book',(x-.66+i*.16,y+.17,-4),(.11,.34,.24),'paper' if i%3 else 'purple')
  rod('Tree',(0,0,-5.5),(0,5,-5.5),.45,'wood')
  for x,z in [(-2,-5),(1,-5),(2.5,-6),(-1,-7)]:rod('Bough',(0,3.5,-5.5),(x,5,z),.13,'wood');ball('Canopy',(x,5,z),1.6,'leaf')
 elif kind=='courtyard':
  for x in (-3,3):
   for z in (-3,3):rod('Pergola_Post',(x,0,z),(x,3.4,z),.12,'ivory')
   box('Pergola_Long',(x,3.4,0),(.2,.15,6.4),'wood')
  for z in (-3,-2,-1,0,1,2,3):box('Pergola_Rafter',(0,3.55,z),(6.4,.12,.14),'wood')
  table(-1.5,-.8)
  for x in (-1.9,-1.15):
   cup('Tea_Cup',(x,.815,-.8),.075,.11,materials['ivory'],materials['wood']);box('Coaster',(x,.8075,-.8),(.23,.015,.23),'pink')
  for x in (-3.8,3.8):
   for z in (-3,-.8,1.5):pot(x,z)
  box('Pool_Rim',(0,.08,-4.5),(4,.16,1.8),'ivory',True);box('Still_Water',(0,.17,-4.5),(3.6,.025,1.4),'water')
 elif kind=='terrace':
  box('Water_Horizon',(0,-.35,-22.35),(80,.08,35.3),'water')
  for x in (-4.4,4.4):box('Balustrade',(x,.55,1.3),(.2,1.1,12),'ivory',True)
  box('Terrace_Rail_Base',(0,.15,-4.6),(9,.3,.24),'stone')
  box('Terrace_Handrail',(0,1.05,-4.6),(9,.10,.16),'ivory')
  colliders.append(dict(name='Terrace_Guard',center=[0,.55,-4.6],size=[9,1.1,.24]))
  for i in range(55):
   x=-4.32+i*.16;rod('Rail_Pillar',(x,.3,-4.6),(x,1.05,-4.6),.035,'gold')
  table(-1.8,-.6)
  book((-2,.8275,-.6));book((-1.5,.8275,-.6),'pink')
  for x in (-3.3,3.3):pot(x,-3,'purple')
  for i in range(15):
   x=random.uniform(-3,3);y=random.uniform(1.8,3.5);z=random.uniform(-3.5,-1)
   for sign in (-1,1):o=ball('Butterfly_Wing',(x+sign*.055,y,z),.075,'purple');o.scale=(1,.28,.6)
 else:
  for x in (-5.5,5.5):
   for i in range(70):
    px=x+random.uniform(-1.7,1.7);pz=random.uniform(-7,7);h=random.uniform(.6,1.25)
    rod('Wheat_Stem',(px,0,pz),(px+.06,h,pz),.012,'wheat')
    for j in range(3):ball('Wheat_Grain',(px+.06+(j%2-.5)*.07,h-j*.065,pz),.045,'gold')
  box('Picnic_Stone',(-1.9,.3,-1.2),(1.8,.6,.8),'stone',True);box('Basket',(-1.9,.71,-1.2),(.48,.22,.32),'wood');ball('Bread',(-2.4,.76,-1.2),.16,'wheat')
  for x in (-5,5):
   box('Village_House',(x,1.5,-7),(3,3,2.5),'ivory',True);roof=box('Village_Roof',(x,3.1,-7),(3.7,.4,3.1),'wood');roof.rotation_euler[1]=.12
   box('House_Door',(x,.9,-5.73),(.8,1.8,.04),'wood')
  rod('Shade_Tree',(3.7,0,1),(3.7,4.2,1),.25,'wood');ball('Shade_Canopy',(3.7,4.1,1),2.0,'leaf')
 capture_parts(OUT/(kind+'-part-manifest.json'))
 for m in materials.values():
  objects=[o for o in bpy.data.objects if o.type=='MESH' and o.data.materials and o.data.materials[0]==m]
  if objects:
   bpy.ops.object.select_all(action='DESELECT')
   for o in objects:o.select_set(True)
   bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();objects[0].name=m.name
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(kind+'.blend')))
 bpy.ops.export_scene.gltf(filepath=str(OUT/(kind+'.glb')),export_format='GLB',export_animations=False)
 bpy.ops.export_scene.fbx(filepath=str(OUT/(kind+'.fbx')),object_types={'MESH'},bake_anim=False,add_leaf_bones=False)
 (OUT/(kind+'.json')).write_text(json.dumps(dict(scene=kind,player_start=[0,1.6635,3.2],eye_height=1.65,bounds=[-4.1,4.1,-4.1,6.5],colliders=colliders,character_position=[0,.0135,0],walkable_surfaces=[dict(center=[0,.006,.5],size=[3.6,.015,12])],origin='原创场所意象，非原游戏地图提取'),ensure_ascii=False,indent=2),encoding='utf-8')
 return dict(scene=kind,colliders=len(colliders),glb_bytes=(OUT/(kind+'.glb')).stat().st_size)
report=[build(x) for x in ['grove','courtyard','terrace','wheat']]
(OUT/'build-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('OUTING_SCENES_READY',report)
