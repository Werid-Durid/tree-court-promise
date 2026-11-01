"""原创白厄麦田短片：真实骨架表演、九组运镜、风动麦田与可编辑工程。

blender -b --python blender/build_phainon_film.py -- --preview
blender -b --python blender/build_phainon_film.py -- --render
"""
import bpy, sys, json, math, random, time
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'data/cinematics/phainon-wheat.json').read_text(encoding='utf-8'))
OUT=ROOT/CFG.get('output_dir','blender/build/phainon-film');OUT.mkdir(parents=True,exist_ok=True)
ARGS=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
FPS=CFG['fps'];N=CFG['duration']*FPS
random.seed(1031)
sys.path.insert(0,str(ROOT/'blender'))

def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
def window(t,a,b,r=.7):return ease((t-a)/r)*ease((b-t)/r)
def look(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def material(name,color,rough=.8):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if p is None:
  p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs[0],out.inputs['Surface'])
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
 return m
def cube(name,loc,scale,mat,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:m=o.modifiers.new('Soft edges','BEVEL');m.width=bevel;m.segments=2;o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
 return o
def uvball(name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
def rod(name,a,b,r,mat,vertices=8):
 a,b=Vector(a),Vector(b);d=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=d.length,location=(a+b)/2);o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat);return o
def mesh_object(name,verts,faces,mat):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.data.materials.append(mat);return o
def animate(o,channel,values):
 for seconds,value in values:setattr(o,channel,value);o.keyframe_insert(data_path=channel,frame=1+seconds*FPS)

started=time.monotonic()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/generated/phainon.blend'))
scene=bpy.context.scene
arm=next(o for o in scene.objects if o.type=='ARMATURE')
meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
for o in list(scene.objects):
 if o not in meshes and o!=arm and o.type in ('LIGHT','CAMERA'):bpy.data.objects.remove(o,do_unlink=True)
for o in meshes:
 o.hide_render=False
 if o.animation_data:o.animation_data_clear()
 if o.data.shape_keys:
  o.data.shape_keys.animation_data_clear()
  for k in o.data.shape_keys.key_blocks:k.value=0
height=max((o.matrix_world@Vector(c)).z for o in meshes for c in o.bound_box)-min((o.matrix_world@Vector(c)).z for o in meshes for c in o.bound_box)
scale=1.84/height
master=bpy.data.objects.new('Phainon_Film_Root',None);scene.collection.objects.link(master);master.scale=(scale,)*3;arm.parent=master
if arm.animation_data:arm.animation_data_clear()
pb=arm.pose.bones;rest={b.name:b.matrix_local.copy() for b in arm.data.bones}
for p in pb:p.rotation_mode='QUATERNION'

# 原始图集与材质类别保持；只在短片副本上应用既有卡通明暗。
from materials.toon_shader import apply_toon
styled=[]
for mat in {m for o in meshes for m in o.data.materials if m}:
 if mat.use_nodes and any(n.type=='BSDF_PRINCIPLED' for n in mat.node_tree.nodes):
  if mat.get('treecourt_shading_class') in ('face','skin','cloth') and mat.get('treecourt_surface_mode','OPAQUE')=='OPAQUE':
   apply_toon(mat,rim=False);styled.append(mat.name)
   # 教程强调脸部与普通衣料分开处理。现模型没有可核验的脸部 SDF，
   # 因而只柔化脸部色阶，不伪造 SDF 或修改已批准的全局材质。
   if mat.get('treecourt_shading_class')=='face':
    ramp=mat.node_tree.nodes.get('TC_Toon_Ramp')
    if ramp:
     for stop,color in zip(ramp.color_ramp.elements,[(.88,.82,.82,1),(.96,.93,.93,1),(1,.99,.98,1)]):stop.color=color

M={k:material('Film_'+k,c) for k,c in {
 'soil':(.25,.21,.13),'path':(.51,.40,.24),'stone':(.55,.49,.38),'wood':(.24,.13,.065),
 'pale_wood':(.56,.33,.13),'cream':(.92,.83,.64),'roof':(.32,.19,.15),'green':(.25,.31,.13),
 'wheat':(.64,.39,.075),'grain':(.9,.65,.22),'grain_pale':(.98,.78,.38),
 'cloth':(.52,.24,.20),'teal':(.16,.32,.35),'leaf':(.64,.23,.075),'leaf2':(.85,.40,.10),
 'mountain':(.39,.43,.42),'mountain2':(.53,.53,.47),'cloud':(.94,.71,.43)
}.items()}
for key in ['soil','path','wood','pale_wood']:
 mat=M[key];nodes=mat.node_tree.nodes;links=mat.node_tree.links;p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
 noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=5 if key in ['soil','path'] else 22
 ramp=nodes.new('ShaderNodeValToRGB');base=mat.diffuse_color
 ramp.color_ramp.elements[0].color=tuple(c*.80 for c in base[:3])+(1,)
 ramp.color_ramp.elements[1].color=tuple(min(1,c*1.10) for c in base[:3])+(1,)
 links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],p.inputs['Base Color'])
cube('Earth',(0,12,-.1),(110,110,.2),M['soil'])
cube('Footpath',(0,1,-.006),(1.5,44,.02),M['path'])
for i in range(22):
 y=-9+i*.85
 uvball('Path worn stone',(random.uniform(-.45,.45),y,.003),(random.uniform(.22,.45),random.uniform(.14,.27),.025),M['stone'])

# 麦田采用分区网格，每个分区有独立相位的风动画，前景保留完整麦芒。
def wheat_patch(x,y,count,near=False):
 verts=[];faces=[]
 def tube(a,b,r):
  a,b=Vector(a),Vector(b);direction=(b-a).normalized();u=direction.cross(Vector((0,1,0))).normalized();v=direction.cross(u);start=len(verts)
  for center,rr in [(a,r),(b,r*.64)]:
   for j in range(4):verts.append(center+rr*(u*math.cos(j*math.tau/4)+v*math.sin(j*math.tau/4)))
  for j in range(4):faces.append((start+j,start+(j+1)%4,start+4+(j+1)%4,start+4+j))
 def grain(center,width,height,turn):
  z=len(verts);c=Vector(center);d=Vector((math.cos(turn),math.sin(turn),0));p=Vector((-math.sin(turn),math.cos(turn),0))
  verts.extend([c+Vector((0,0,height)),c-Vector((0,0,height)),c+d*width,c-d*width,c+p*width*.60,c-p*width*.60])
  faces.extend([(z,z+2,z+4),(z,z+4,z+3),(z,z+3,z+5),(z,z+5,z+2),(z+1,z+4,z+2),(z+1,z+3,z+4),(z+1,z+5,z+3),(z+1,z+2,z+5)])
 for i in range(count):
  xx=x+random.uniform(-1.35,1.35);yy=y+random.uniform(-1.35,1.35)
  if abs(xx)<1.10 and yy<14:continue
  if -.95<xx<2 and -1.35<yy<1.1:continue
  h=random.uniform(.62,1.03);lean=random.uniform(.045,.13);tip=Vector((xx+lean,yy,h));tube((xx,yy,0),tip,.008 if near else .006)
  for j in range(4):
   c=tip+Vector((lean*j*.14,0,j*.046));turn=j*2.4
   grain(c+Vector((math.cos(turn)*.023,math.sin(turn)*.023,0)),.021,.055,turn)
   if near:tube(c,c+Vector((math.cos(turn)*.05,math.sin(turn)*.05,.17)),.0018)
  for sign in [-1,1]:
   base=Vector((xx,yy,h*.45));start=len(verts)
   verts.extend([base,base+Vector((sign*.012,.012,h*.12)),base+Vector((sign*.13,.03,h*.24))]);faces.append((start,start+1,start+2))
 o=mesh_object('Wind_Wheat_Patch',verts,faces,M['grain_pale'] if near else M['grain'])
 # Rotate about each patch center, so roots remain near the ground.
 for v in o.data.vertices:v.co-=Vector((x,y,0))
 o.location=(x,y,0)
 phase=random.uniform(0,math.tau)
 for frame in range(1,N+1,12):
  t=(frame-1)/FPS;o.rotation_euler=(.017*math.sin(t*1.1+phase),.025*math.sin(t*.85+phase)+.012,0);o.keyframe_insert(data_path='rotation_euler',frame=frame)
 return o
for xx in [-11,-8,-5,-2.3,2.3,5,8,11]:
 for yy in [-4,-.6,3,6.5,10,14,18,22]:wheat_patch(xx,yy,76,near=yy<0 and abs(xx)<6)

# 树荫、矮篱、村屋、慢转的风车，形成有生活痕迹的后景。
for xx in [-2.25,2.25]:
 for yy in [4,7,10,13]:
  rod('Fence post',(xx,yy,0),(xx,yy,.73),.045,M['wood'])
  for z in [.30,.60]:rod('Fence rail',(xx,yy,z),(xx,yy+3,z),.028,M['pale_wood'])
rod('Tree trunk',(-3.5,3.5,0),(-3.4,3.5,4),.19,M['wood'])
for i in range(20):
 p=(-3.4+random.uniform(-1.4,1.4),3.5+random.uniform(-1,1),3.6+random.uniform(-.5,.8))
 uvball('Autumn leaf crown',p,(random.uniform(.5,.9),random.uniform(.5,.9),random.uniform(.35,.65)),M['leaf'] if i%3 else M['leaf2'])
for x,y,s in [(-6,18,1),(8,24,.8)]:
 cube('Village house',(x,y,1.1*s),(3*s,2.4*s,2.2*s),M['cream'],.05)
 verts=[(x-1.7*s,y-1.4*s,2.15*s),(x+1.7*s,y-1.4*s,2.15*s),(x,y-1.4*s,3.2*s),(x-1.7*s,y+1.4*s,2.15*s),(x+1.7*s,y+1.4*s,2.15*s),(x,y+1.4*s,3.2*s)]
 mesh_object('Tiled farmhouse roof',verts,[(0,1,2),(3,5,4),(0,2,5,3),(2,1,4,5)],M['roof'])
 cube('Warm doorway',(x,y-1.215*s,.65*s),(.65*s,.04,1.3*s),M['wood'])
 for dx in [-.9,.9]:cube('Window',(x+dx*s,y-1.22*s,1.35*s),(.42*s,.04,.55*s),M['teal'])
bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=1.1,radius2=.55,depth=4.6,location=(3.8,20,2.3));mill=bpy.context.object;mill.name='Windmill tower';mill.data.materials.append(M['cream'])
rotor=bpy.data.objects.new('Windmill_Rotor',None);scene.collection.objects.link(rotor);rotor.location=(3.8,19.3,3.8)
for angle in [0,math.pi/2,math.pi,math.pi*1.5]:
 o=cube('Windmill sail',(0,0,0),(.19,.06,2.7),M['pale_wood']);o.parent=rotor;o.location=(math.sin(angle)*1.15,0,math.cos(angle)*1.15);o.rotation_euler[1]=angle
animate(rotor,'rotation_euler',[(0,(0,0,0)),(CFG['duration'],(0,math.pi*1.6,0))])
for layer,y in enumerate([33,43,58]):
 verts=[(-70,y,-.05),(70,y,-.05)]+[(70-i*5,y,2+layer*1.3+random.uniform(0,3)) for i in range(29)]
 mesh_object('Distant hills '+str(layer),verts,[tuple(range(len(verts)))],M['mountain'] if layer==0 else M['mountain2'])

# 两个座位与两只杯子让第一人称空间可见，玩家本体不被固定外观。
bench=cube('Bench seat',(.38,.32,.43),(2.05,.58,.12),M['wood'],.04)
for xx in [-.37,1.1]:
 for yy in [.12,.52]:cube('Bench leg',(xx,yy,.20),(.09,.09,.4),M['wood'],.02)
cube('Folded scarf on player seat',(1.02,.29,.52),(.45,.35,.055),M['cloth'],.02)
cube('Picnic linen',(1.45,-.55,.018),(1.0,.8,.025),M['cloth'],.025)
for x in [1.17,1.63]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=28,radius=.08,depth=.09,location=(x,-.57,.075));bpy.context.object.name='Two cups';bpy.context.object.data.materials.append(M['cream'])
 bpy.ops.mesh.primitive_torus_add(major_radius=.081,minor_radius=.006,major_segments=24,minor_segments=8,location=(x,-.57,.122));bpy.context.object.data.materials.append(M['pale_wood'])
 uvball('Tea surface',(x,-.57,.119),(.073,.073,.003),M['wood'])
cube('Basket',(1.7,.10,.17),(.42,.32,.29),M['pale_wood'],.045)
for x in [1.56,1.74]:uvball('Bread',(x,.08,.32),(.13,.09,.08),M['grain_pale'])

# 共享的小桌处于玩家前景。木牌稳定放在桌面，手不再夹住穿过指缝的薄片。
cube('Shared little table',(.20,-.82,.66),(.90,.60,.075),M['wood'],.025)
for xx in [-.14,.54]:
 for yy in [-1.03,-.61]:cube('Shared table leg',(xx,yy,.32),(.045,.045,.64),M['wood'],.01)
cube('Woven table runner',(.20,-.82,.704),(.76,.40,.012),M['cloth'],.009)
token=cube('Keepsake wooden waymark',(.12,-.82,.722),(.18,.12,.018),M['pale_wood'],.008)
token.rotation_mode='QUATERNION'
for sign in [-1,1]:
 for dx,dy in [(-.035,0),(0,.012),(.035,0)]:
  mark=cube('Carved waymark',(0,0,0),(.028,.003,.002),M['cream']);mark.parent=token;mark.location=(dx,dy,sign*.011);mark.rotation_euler[2]=-.32 if dx<0 else .32 if dx>0 else 0

lengths={s:((rest['ひじ.'+s].translation-rest['腕.'+s].translation).length,(rest['手首.'+s].translation-rest['ひじ.'+s].translation).length) for s in ['L','R']}
changed=set();errors=[];contact_rows=[]
hand_indices={}
for obj in meshes:
 group_ids={g.index for g in obj.vertex_groups if '手首' in g.name or '指' in g.name}
 hand_indices[obj.name]=[v.index for v in obj.data.vertices if any(g.group in group_ids and g.weight>.15 for g in v.groups)]
def rotate(name,axis,angle):
 if name in pb:pb[name].rotation_quaternion=pb[name].rotation_quaternion@Quaternion(Vector(axis),angle);changed.add(name)
def translate(name,delta):
 p=pb[name];m=p.parent.matrix@p.parent.bone.matrix_local.inverted()@rest[name] if p.parent else rest[name].copy();m.translation+=Vector(delta);p.matrix=m;changed.add(name)
def aim(name,target):
 p=pb[name];ref=p.parent.matrix@p.parent.bone.matrix_local.inverted()@p.bone.matrix_local if p.parent else p.bone.matrix_local.copy()
 direction=(Vector(target)-p.head).normalized();q=(ref.to_quaternion()@Vector((0,1,0))).rotation_difference(direction)@ref.to_quaternion()
 p.matrix=Matrix.LocRotScale(p.head.copy(),q,Vector((1,1,1)));changed.add(name)
def arm_to(side,target,pole):
 shoulder=pb['腕.'+side].head.copy();target=Vector(target);v=target-shoulder;l1,l2=lengths[side]
 distance=max(abs(l1-l2)+.001,min(v.length,l1+l2-.002));direction=v.normalized();target=shoulder+direction*distance
 along=(l1*l1-l2*l2+distance*distance)/(2*distance);bend=Vector(pole)-shoulder;bend-=direction*bend.dot(direction)
 if bend.length<.001:bend=Vector((0,.1,0))
 elbow=shoulder+direction*along+bend.normalized()*math.sqrt(max(0,l1*l1-along*along))
 aim('腕.'+side,elbow);bpy.context.view_layer.update();aim('ひじ.'+side,target);bpy.context.view_layer.update()
 # 保留手腕相对前臂的原始朝向，避免旧版强制朝镜头扭腕。
 wrist=pb['手首.'+side];wrist.matrix_basis=Matrix.Identity(4);changed.add(wrist.name)
 bpy.context.view_layer.update();errors.append((wrist.head-target).length)

for frame in range(1,N+1,2):
 scene.frame_set(frame);t=(frame-1)/FPS;changed.clear()
 for p in pb:p.matrix_basis=Matrix.Identity(4)
 seat=ease((t-27)/3.5);drop=.56*seat;breath=.0025*math.sin(t*1.55)
 translate('センター',(0,0,-drop+breath));rotate('上半身',(1,0,0),.025+.08*seat+.035*window(t,14,22));rotate('上半身2',(0,0,1),.015*math.sin(t*.7))
 horizon=window(t,38,45,1.5);shy=window(t,48,53,1)
 rotate('首',(1,0,0),.025+.06*shy-.04*seat);rotate('頭',(0,0,1),.25*horizon+.018*math.sin(t*.6));rotate('頭',(1,0,0),.02+.08*shy)
 bpy.context.view_layer.update()
 for side,sign in [('L',1),('R',-1)]:
  foot=rest['足ＩＫ.'+side].copy();foot.translation+=Vector((0,-.36*seat,0));pb['足ＩＫ.'+side].matrix=foot;changed.add('足ＩＫ.'+side)
 bpy.context.view_layer.update()
 for side,sign in [('L',1),('R',-1)]:
  target=Vector((sign*.28,-.04,1.05-drop*.75))
  if side=='R':
   offer=window(t,13.2,23.4,1.3);wave=window(t,6.1,10.8,.8)
   target=target.lerp(Vector((-.22,-.30,1.15)),offer)
   target=target.lerp(Vector((-.40,-.13,1.62+.022*math.sin(t*3))),wave)
   if seat:target=target.lerp(Vector((-.34,-.20,.72)),seat)
  else:
   target=target.lerp(Vector((.34,-.20,.72)),seat)
  arm_to(side,target,(sign*.45,.20,1.05-drop))
  for p in pb:
   if p.name.endswith('.'+side) and '指' in p.name and not p.name.startswith('_'):rotate(p.name,(1,0,0),.035)
 for p in pb:
  if p.name.startswith('髪') and len(p.name)>2:rotate(p.name,(1,0,0),.009*math.sin(t*1.8+len(p.name)))
 bpy.context.view_layer.update()
 if (frame-1)%48==0:
  inv=token.matrix_world.inverted();minimum=100;inside=0;deps=bpy.context.evaluated_depsgraph_get()
  for obj in meshes:
   ev=obj.evaluated_get(deps);em=ev.to_mesh();transform=inv@ev.matrix_world
   for index in hand_indices[obj.name]:
    point=transform@em.vertices[index].co;gap=Vector((max(0,abs(point.x)-.09),max(0,abs(point.y)-.06),max(0,abs(point.z)-.009)))
    minimum=min(minimum,gap.length);inside+=int(gap.length<.0001)
   ev.to_mesh_clear()
  contact_rows.append({'seconds':t,'hand_to_waymark_min_m':round(minimum,5),'penetrating_vertices':inside})
 for name in changed:
  for channel in ['location','rotation_quaternion','scale']:pb[name].keyframe_insert(data_path=channel,frame=frame)
 for o in meshes:
  keys=o.data.shape_keys.key_blocks if o.data.shape_keys else {}
  blink=sum(window(t,s,s+.17,.075) for s in [7.3,12.1,18.8,25.2,32.3,39.7,47.8,54.2,61.4,68])
  speaking=next((line for line in CFG['lines'] if line['start']<=t<=line['end']),None)
  shapes={'まばたき':min(1,blink),'口角上げ':.06+.07*window(t,6,26)+.09*window(t,55,CFG['duration']),'喜び':.05+.07*window(t,58,CFG['duration']),'慈愛':.10*window(t,48,CFG['duration']),'あ':(.025+.055*(.5+.5*math.sin(t*16))) if speaking else 0,'い':.018*(.5+.5*math.sin(t*13)) if speaking else 0,'脸红':.045*window(t,50,72)}
  for name,value in shapes.items():
   if name in keys:keys[name].value=value;keys[name].keyframe_insert(data_path='value',frame=frame)
print('FILM_ANIMATION_KEYED',len(errors),'hand_error',max(errors),flush=True)

# 镜头是 Blender timeline marker 绑定的真实相机，剪辑可直接在工程中调整。
def camera(name,start,end,p0,p1,target0,target1,lens=48):
 data=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,data);scene.collection.objects.link(cam);data.lens=lens
 data.clip_end=180;data.dof.use_dof=True;data.dof.aperture_fstop=5.6
 for seconds,p,target in [(start,p0,target0),(end-1/FPS,p1,target1)]:
  cam.location=p;look(cam,target);cam.keyframe_insert(data_path='location',frame=1+seconds*FPS);cam.keyframe_insert(data_path='rotation_euler',frame=1+seconds*FPS)
  data.dof.focus_distance=(Vector(p)-Vector(target)).length;data.keyframe_insert(data_path='dof.focus_distance',frame=1+seconds*FPS)
 mark=scene.timeline_markers.new(name,frame=1+round(start*FPS));mark.camera=cam;return cam
camera('01 Your arrival',0,6,(.45,-3.7,1.64),(.45,-2.75,1.62),(0,0,1.43),(0,0,1.43),49)
camera('02 He sees you',6,14,(.45,-2.55,1.60),(.43,-2.4,1.60),(0,0,1.43),(0,0,1.43),53)
camera('03 Your table',14,22,(.52,-1.98,1.50),(.49,-1.88,1.47),(.14,-.70,.79),(.14,-.72,.77),40)
camera('04 Sit down together',22,31,(.45,-2.4,1.59),(.48,-1.82,1.15),(0,0,1.43),(0,0,1.08),51)
camera('05 Across from him',31,38,(.48,-1.82,1.15),(.45,-1.78,1.15),(0,0,1.08),(0,0,1.08),55)
camera('06 Shared horizon',38,48,(.48,-1.80,1.15),(.47,-1.75,1.15),(0,0,1.08),(0,0,1.08),57)
camera('07 Just your name',48,58.4,(.43,-1.76,1.16),(.40,-1.70,1.16),(0,0,1.08),(0,0,1.08),60)
camera('08 Your reply',58.4,67,(.45,-1.78,1.15),(.42,-1.74,1.15),(0,0,1.08),(0,0,1.08),57)
camera('09 Stay in your seat',67,CFG['duration'],(.45,-1.80,1.15),(.45,-1.94,1.16),(0,0,1.08),(0,0,1.08),55)

sun_data=bpy.data.lights.new('Golden hour sun','SUN');sun_data.energy=2.2;sun_data.color=(1,.80,.56);sun_data.angle=.16
sun=bpy.data.objects.new('Golden hour sun',sun_data);scene.collection.objects.link(sun);sun.rotation_euler=(math.radians(68),math.radians(-20),math.radians(-35))
for name,location,energy,color,size in [('Sky soft fill',(0,-4,5),180,(.77,.86,1),6),('Warm rim',(-4,3,4),240,(1,.59,.28),5)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.color=color;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=location;look(o,(0,0,1))
world=bpy.data.worlds.new('Amber evening');world.use_nodes=True
bg=next((n for n in world.node_tree.nodes if n.type=='BACKGROUND'),None)
if bg is None:
 bg=world.node_tree.nodes.new('ShaderNodeBackground');wo=world.node_tree.nodes.new('ShaderNodeOutputWorld');world.node_tree.links.new(bg.outputs[0],wo.inputs['Surface'])
tc=world.node_tree.nodes.new('ShaderNodeTexCoord');sep=world.node_tree.nodes.new('ShaderNodeSeparateXYZ');ramp=world.node_tree.nodes.new('ShaderNodeValToRGB');mapping=world.node_tree.nodes.new('ShaderNodeMapRange')
mapping.inputs['From Min'].default_value=-.12;mapping.inputs['From Max'].default_value=.8
ramp.color_ramp.elements[0].color=(.92,.59,.35,1);ramp.color_ramp.elements[1].color=(.28,.43,.58,1);ramp.color_ramp.elements.new(.38).color=(.75,.66,.58,1)
world.node_tree.links.new(tc.outputs['Normal'],sep.inputs[0]);world.node_tree.links.new(sep.outputs['Z'],mapping.inputs['Value']);world.node_tree.links.new(mapping.outputs[0],ramp.inputs[0]);world.node_tree.links.new(ramp.outputs[0],bg.inputs['Color'])
bg.inputs['Strength'].default_value=.85;scene.world=world
for i in range(14):
 uvball('Evening cloud',(random.uniform(-23,24),38+random.uniform(-2,2),random.uniform(5.8,10)),(random.uniform(1.7,4),.25,random.uniform(.13,.32)),M['cloud'])
# A large luminous sun disk, placed above the distant hill line.
sun_mat=material('Soft sun disk',(1,.73,.38));p=next(n for n in sun_mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Emission Color'].default_value=(1,.48,.14,1);p.inputs['Emission Strength'].default_value=1.5
uvball('Distant setting sun',(-15,48,10),(2.5,.35,2.5),sun_mat)

scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=24
scene.render.resolution_x,scene.render.resolution_y=CFG.get('resolution',[960,540]);scene.render.resolution_percentage=100
scene.render.fps=FPS;scene.frame_start=1;scene.frame_end=N
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.film_transparent=False;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=-.15
scene.render.use_file_extension=True
scene.frame_set(1);scene.camera=scene.timeline_markers[0].camera
for image in bpy.data.images:
 if image.source=='FILE' and image.has_data and not image.packed_file:
  try:image.pack()
  except Exception:pass
from replace_phainon_environment import replace_environment
replace_environment(scene)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'phainon_wheat_film.blend'))
report={'title':CFG['title'],'revision':CFG.get('revision',1),'duration_seconds':CFG['duration'],'fps':FPS,'frames':N,'resolution':CFG.get('resolution',[960,540]),'shots':len(CFG['shots']),'max_hand_target_error':max(errors),'materials_styled':styled,'source_model':'blender/generated/phainon.blend','original_assets_preserved':True,'hand_prop_contacts':contact_rows,'build_seconds':round(time.monotonic()-started,2)}
assert all(row['penetrating_vertices']==0 for row in contact_rows),'Hand/waymark intersection detected'
(OUT/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if '--preview' in ARGS:
 for seconds in [8,17,33,42,51,52,54,56,61]:
  scene.frame_set(1+seconds*FPS);scene.render.filepath=str(OUT/f'preview-{seconds:02d}.png');bpy.ops.render.render(write_still=True)
  print('PREVIEW_RENDERED',seconds,flush=True)
if '--render' in ARGS:
 frames=OUT/'frames';frames.mkdir(exist_ok=True);scene.render.filepath=str(frames/'frame-');bpy.ops.render.render(animation=True)
print('PHAINON_FILM_BUILT',json.dumps(report,ensure_ascii=True),flush=True)
