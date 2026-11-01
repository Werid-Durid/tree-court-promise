"""将参考图中的现代教室元素转为同源 GLB/FBX；全部几何由本地 Blender 生成。"""
import bpy,math,json,random,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--output=')),str(ROOT/'blender/build/classroom-paired')));OUT.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.read_factory_settings(use_empty=True);random.seed(47)
palette={'plaster':(0.88,.85,.73),'sage':(.38,.62,.51),'wood':(.49,.29,.13),'oak':(.72,.49,.25),'gold':(.72,.58,.29),'board':(.075,.21,.15),'paper':(.94,.87,.68),'leaf':(.24,.49,.26),'sky':(.48,.84,.91),'glass':(.69,.91,.91),'rose':(.70,.32,.29),'ink':(.18,.24,.21)}
mats={};parts=[];colliders=[]
for name,rgb in palette.items():
 m=bpy.data.materials.new('TC_Room_'+name);m.diffuse_color=(*rgb,1);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.82
 if name in ('sky','glass'):p.inputs['Emission Color'].default_value=(*rgb,1);p.inputs['Emission Strength'].default_value=.3
 mats[name]=m
def xyz(v):return (v[0],-v[2],v[1])
def box(name,pos,size,mat='wood',bevel=.025,solid=False):
 bpy.ops.mesh.primitive_cube_add(size=1,location=xyz(pos));o=bpy.context.object;o.name=name;o.dimensions=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(mats[mat]);parts.append(o)
 if bevel:
  mod=o.modifiers.new('柔化边缘','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 if solid:colliders.append({'name':name,'center':pos,'size':size})
 return o
def ball(name,pos,size,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=xyz(pos));o=bpy.context.object;o.name=name;o.scale=(size[0],size[2],size[1]);o.data.materials.append(mats[mat]);parts.append(o)
 for p in o.data.polygons:p.use_smooth=True
 return o
def rod(name,a,b,r,mat):
 va,vb=Vector(xyz(a)),Vector(xyz(b));delta=vb-va;bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=delta.length,location=(va+vb)/2);o=bpy.context.object;o.name=name;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();o.data.materials.append(mats[mat]);parts.append(o);return o
def label(name,text,pos,size,mat='ink',front=True):
 bpy.ops.object.text_add(location=xyz(pos));o=bpy.context.object;o.name=name;o.data.body=text;o.data.size=size;o.data.align_x='CENTER';o.rotation_euler=(math.pi/2,0,0) if front else (0,0,0);o.data.materials.append(mats[mat]);bpy.ops.object.convert(target='MESH');parts.append(o)
box('Floor',(0,-.12,-.8),(15.5,.24,14.8),'paper',0)
for x in range(-7,8):box('Floor_Inlay',(x, .004,-.8),(.012,.006,14.6),'oak',0)
for z in range(-7,7,2):box('Floor_Seam',(0,.006,z),(15.4,.005,.012),'oak',0)
for x in (-7.65,7.65):
 box('Side_Wall',(x,2.25,-.8),(.20,4.5,14.8),'plaster',0,True)
 box('Sage_Wainscot',(x+(.115 if x<0 else -.115),.65,-.8),(.035,1.3,14.7),'sage',0)
 box('Dado_Rail',(x+(.15 if x<0 else -.15),1.32,-.8),(.06,.07,14.7),'gold')
for z in (-8.1,6.6):box('End_Wall',(0,2.25,z),(15.5,4.5,.18),'plaster',0,True);box('End_Panel',(0,.65,z+(.11 if z<0 else -.11)),(15.5,1.3,.04),'sage',0)
box('Ceiling',(0,4.6,-.8),(15.5,.12,14.8),'plaster',0)
for z in (-5,-.5,4):box('Ceiling_Beam',(0,4.45,z),(15.3,.16,.18),'oak')
box('Platform',(0,.08,-4.8),(7,.18,3.2),'oak',.04)
box('Platform_Step',(0,.035,-3.05),(4,.07,.35),'wood')
box('Board_Frame',(0,2.25,-6.25),(6.5,2.85,.20),'gold',.07)
box('Board_Wood',(0,2.25,-6.125),(6.30,2.66,.06),'wood')
box('Board_Surface',(0,2.25,-6.08),(6.12,2.48,.035),'board',.03)
box('Chalk_Ledge',(0,.98,-5.98),(6.4,.10,.24),'oak')
for i in range(4):box('Chalk',(-2.6+i*.12,1.05,-5.96),(.08,.025,.025),'paper',.008)
box('Eraser',(2.6,1.07,-5.96),(.19,.07,.09),'sage')
# 框架分层与枝状装饰，保留树庭身份，同时加入参考图中的课堂日常感。
for x in (-3.8,3.8):
 box('Wall_Pilaster',(x,2.4,-7.92),(.16,4.3,.18),'oak')
 rod('Tree_Branch',(x,3.7,-7.7),(x*.58,4.3,-7.7),.055,'gold')
for x in (-2.4,-1.2,1.2,2.4):
 box('Certificate_Frame',(x,3.95,-7.94),(.84,.54,.06),'rose');box('Certificate_Paper',(x,3.95,-7.89),(.73,.43,.02),'paper')
 for y in (3.88,4.0):box('Certificate_Line',(x,y,-7.87),(.46,.018,.006),'gold',0)
ball('Clock_Frame',(0,4,-7.89),(.38,.38,.06),'wood');ball('Clock_Face',(0,4,-7.81),(.33,.33,.025),'paper')
for i in range(12):
 a=i*math.tau/12;ball('Clock_Tick',(.28*math.sin(a),4+.28*math.cos(a),-7.77),(.013,.019,.008),'ink')
rod('Clock_Hand',(0,4,-7.75),(.16,4.15,-7.75),.012,'ink');rod('Clock_Hand',(0,4,-7.74),(0,4.25,-7.74),.009,'ink')
for z in (-4.7,-1,2.7):
 box('Window_Sky',(-7.515,2.73,z),(.025,2.3,2.7),'sky')
 for dz in (-1.4,0,1.4):box('Window_Mullion',(-7.45,2.73,z+dz),(.10,2.50,.075),'oak')
 for y in (1.48,2.73,3.98):box('Window_Rail',(-7.43,y,z),(.15,.08,2.88),'oak')
 box('Window_Sill',(-7.30,1.43,z),(.40,.10,3.05),'paper')
 for dz in (-.8,.5):ball('Cloud',(-7.48,3.35,z+dz),(.02,.13,.36),'paper')
 # 窗帘集中在窗框两侧，保留采光面与窗边行走空间。
 rod('Curtain_Rod',(-7.20,4.12,z-1.52),(-7.20,4.12,z+1.52),.025,'gold')
 for side in (-1,1):
  for fold in range(5):
   box('Curtain_Fold',(-7.20+(.045 if fold%2 else 0),2.89,z+side*(1.24+fold*.055)),(.07,2.4,.07),'paper',.025)
for x,z in ((-6.7,-6.4),(6.65,-6.4),(6.8,4.9)):
 box('Plant_Pot',(x,.29,z),(.52,.58,.52),'paper',.09,True)
 for n in range(9):
  a=n*2.399;h=.85+random.random()*.55;end=(x+math.cos(a)*.4,h,z+math.sin(a)*.4)
  rod('Plant_Stem',(x,.52,z),end,.018,'leaf');leaf=ball('Plant_Leaf',end,(.15,.39,.07),'leaf');leaf.rotation_euler=(.4,math.cos(a),a)
# 两排同桌，每排两张独立课桌边缘相接；角色的坐姿高度和手腕接触高度保持一致。
seats=[]
for row,z in enumerate((0,1.7)):
 for side,x in enumerate((-3.58,-2.82,-.38,.38,2.82,3.58)):
  box(f'Student_Desk_R{row}_{side}',(x,.815,z),(.76,.06,.56),'oak',.015,True)
  box('Desk_Apron',(x,.71,z-.20),(.64,.12,.045),'wood',.01,True)
  for dx in (-.29,.29):
   for dz in (-.20,.20):box('Desk_Leg',(x+dx,.395,z+dz),(.045,.79,.045),'wood',.01,True)
  box('Notebook',(x,.859,z+.11),(.46,.018,.28),'paper',.005)
  for k in range(4):box('Page_Rules',(x,.87,z+.03+k*.055),(.34,.002,.002),'sage',0)
  box('Pencil',(x+.27,.862,z+.10),(.014,.014,.24),'gold',.004)
  # 中间第一组保留既有手腕/讲义接触区，其他座位增加课本与储书托架。
  occupied=row==0 and side in (2,3)
  if not occupied:
   for k in range(2+(side+row)%2):
    box('Desk_Textbook',(x-.20,.89+k*.035,z-.10),(.24,.032,.25),('sage','rose','gold')[(side+k)%3],.006)
   box('Desk_Book_Tray',(x,.59,z-.04),(.57,.035,.38),'wood',.01)
   box('Desk_Stored_Book',(x,.63,z-.04),(.42,.04,.29),'paper',.005)
  chair_z=z+.62
  box(f'Chair_Seat_R{row}_{side}',(x,.44,chair_z),(.54,.08,.50),'oak',.025,True)
  # 后腿一直延伸为椅背立柱，座下纵梁跨过原来的 11cm 空隙并咬合椅面。
  for sign in (-1,1):
   # 下段略外移避让垂落衣摆，上段与下段实体重叠连接，不修改角色网格。
   box('Chair_Back_LowerLeg',(x+sign*.28,.1275,chair_z+.50),(.045,.255,.045),'wood',.008,True)
   box('Chair_Back_LowerRunner',(x+sign*.28,.235,chair_z+.43),(.045,.045,.185),'wood',.008,True)
   box('Chair_Back_Post',(x+sign*.28,.63,chair_z+.36),(.045,.84,.045),'wood',.008,True)
   box('Chair_Seat_Back_Rail',(x+sign*.24,.47,chair_z+.105),(.04,.02,.56),'wood',.008,True)
  for y in (.72,.9):box('Chair_Back_Slat',(x,y,chair_z+.36),(.59,.12,.045),'oak',solid=True)
  for dx in (-.21,.21):
   box('Chair_Leg',(x+dx,.21,chair_z-.18),(.04,.42,.04),'wood',solid=True)
  seats.append({'row':row+1,'pair':side//2,'side':side%2,'desk_center':[x,.845,z],'seat_center':[x,.48,chair_z],'desk_size':[.76,.06,.56],'chair_size':[.54,.08,.50]})
box('Lectern_Base',(-.1,.23,-4.25),(1.2,.12,.80),'wood')
box('Lectern_Body',(-.1,.66,-4.25),(1.06,.78,.67),'oak',.04,True)
box('Lectern_Top',(-.1,1.09,-4.25),(1.3,.12,.91),'wood')
box('Lectern_Inlay',(-.1,.68,-3.90),(.80,.46,.016),'gold')
box('Lectern_Panel',(-.1,.68,-3.885),(.75,.41,.015),'sage')
box('Teacher_OpenBook',(-.1,1.16,-4.2),(.6,.03,.39),'paper')
for i in range(4):box('Teacher_Book',(-.51,1.17+i*.045,-4.45),(.23,.04,.29),'sage' if i%2 else 'rose')
for z in (-3,1.2,4.7):
 box('Bookcase_Back',(7.32,1.35,z),(.14,2.7,2.0),'wood',.02,True)
 for dz in (-1.02,1.02):box('Bookcase_Post',(7.10,1.35,z+dz),(.52,2.7,.06),'oak')
 for y in (.18,.85,1.52,2.19,2.85):
  box('Bookcase_Shelf',(7.10,y,z),(.55,.06,2.1),'oak')
  if y>2.2:continue
  for n in range(11):box('Library_Book',(7.08,y+.22,z-.88+n*.17),(.34,random.uniform(.30,.43),.11),['sage','paper','rose','gold'][n%4],.009)
box('Notice_Frame',(7.48,3.65,.7),(.06,.9,2),'gold');box('Notice_Paper',(7.43,3.65,.7),(.04,.80,1.9),'paper')
# 后墙阅读储物区，避免把第三排课桌塞进玩家通道。
box('Rear_Cabinet',(0,.47,5.68),(9.4,.94,.62),'wood',.035,True)
box('Rear_Counter',(0,.98,5.68),(9.55,.08,.73),'oak',.025)
for x in (-3.7,-1.85,0,1.85,3.7):
 box('Cabinet_Door',(x,.48,5.35),(1.77,.78,.04),'sage',.015)
 box('Cabinet_Handle',(x+.60,.64,5.31),(.15,.025,.025),'gold',.006)
 for k in range(4):
  box('Rear_Book_Stack',(x-.4,1.06+k*.045,5.62),(.45,.04,.29),('rose','paper','sage','gold')[k],.008)
 for k in range(5):
  box('Rear_Upright_Book',(x+.13+k*.105,1.19,5.74),(.08,.34+(k%2)*.05,.25),('sage','gold','paper','rose')[k%4],.008)
box('Rear_Notice_Frame',(0,2.58,6.46),(4.1,1.64,.06),'oak',.035)
box('Rear_Notice_Board',(0,2.58,6.41),(3.94,1.48,.025),'sage',.01)
for i in range(8):
 x=-1.45+(i%4)*.94;y=2.23+(i//4)*.70
 box('Pinned_Notes',(x,y,6.38),(.65,.51,.01),'paper',.002)
 for k in range(4):box('Pinned_Writing',(x,y-.13+k*.075,6.37),(.43,.012,.003),'wood',0)
for z in (-4,0,4):
 rod('Pendant',(0,4.5,z),(0,3.92,z),.015,'gold');box('Ceiling_Lamp',(0,3.86,z),(1.2,.10,.40),'paper',.04)
label('Room_Title','TREE COURT',(0,3.73,-6.06),.17,'gold')
# 合并同材质，减少浏览器绘制批次；独立 JSON 保存碰撞盒，装饰不参与碰撞。
for material in mats.values():
 group=[o for o in bpy.data.objects if o.type=='MESH' and o.data.materials and o.data.materials[0]==material]
 if not group:continue
 bpy.ops.object.select_all(action='DESELECT')
 for o in group:o.select_set(True)
 bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join();group[0].name=material.name
bpy.ops.object.select_all(action='SELECT');bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'story_classroom.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'story_classroom.glb'),export_format='GLB',export_animations=False)
bpy.ops.export_scene.fbx(filepath=str(OUT/'story_classroom.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,add_leaf_bones=False)
(OUT/'layout.json').write_text(json.dumps({'version':3,'seats':seats,'chair_construction':'continuous rear legs + under-seat rails + back slats','player_start':[1.8,1.65,2.4],'eye_height':1.65,'radius':.24,'bounds':[-7.25,7.25,-7.6,6.1],'colliders':colliders},ensure_ascii=False,indent=2),encoding='utf-8')
motion=json.loads((ROOT/'blender/classroom_motion.json').read_text(encoding='utf-8'))
motion['characters']['castor']['position']=[-.38,0,.62]
motion['characters']['phainon']['position']=[.38,0,.62]
(OUT/'motion.json').write_text(json.dumps(motion,ensure_ascii=False,indent=2),encoding='utf-8')
print('STORY_CLASSROOM_READY',len(colliders))
