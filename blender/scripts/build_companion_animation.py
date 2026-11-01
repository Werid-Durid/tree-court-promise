"""Shared Eevee NPR pipeline: three original outings and four quiet study loops.

blender -b --python blender/build_companion_animation.py -- --character=anaxa --kind=study [--preview]
"""
import bpy,sys,json,math,random,time
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'blender'))
from phainon_motion import Performance,SecondaryMotion,write_channels,smooth_secondary_action,ramp,pulse
from materials.toon_shader import apply_toon
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
CID=next(a.split('=',1)[1] for a in args if a.startswith('--character='));KIND=next(a.split('=',1)[1] for a in args if a.startswith('--kind='))
PREVIEW='--preview' in args
HEIGHT={'anaxa':1.80,'hyacine':1.57,'castor':1.72,'phainon':1.84}[CID]
SLUG={'anaxa':'anaxa-rain','hyacine':'hyacine-tea','castor':'castor-dusk'}
SPEC=json.loads((ROOT/'data/cinematics'/f'{SLUG[CID]}.json').read_text(encoding='utf-8')) if KIND=='outing' else None
OUT=Path(next((a.split('=',1)[1] for a in args if a.startswith('--output=')),str(ROOT/(SPEC['output_dir'] if SPEC else 'blender/build/study-companions/'+CID))))
if not OUT.is_absolute():OUT=ROOT/OUT
OUT=OUT.resolve();OUT.mkdir(parents=True,exist_ok=True)
if not PREVIEW:(OUT/'verification.json').unlink(missing_ok=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/generated/{CID}.blend'))
scene=bpy.context.scene;arm=next(o for o in scene.objects if o.type=='ARMATURE')
meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
for o in list(scene.objects):
 if o!=arm and o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
for o in [arm,*meshes]:
 if o.animation_data:o.animation_data_clear()
 if o.type=='MESH' and o.data.shape_keys:
  o.data.shape_keys.animation_data_clear()
  for key in o.data.shape_keys.key_blocks:key.value=0
for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4);p.rotation_mode='QUATERNION'
bpy.context.view_layer.update()
floor=min((o.matrix_world@Vector(c)).z for o in meshes for c in o.bound_box)
height=max((o.matrix_world@Vector(c)).z for o in meshes for c in o.bound_box)-floor
scale=HEIGHT/height
master=bpy.data.objects.new('CompanionRoot',None);scene.collection.objects.link(master);master.scale=(scale,)*3;master.location.z=-floor*scale;arm.parent=master
if KIND=='study':master.location.y=-.90;master.rotation_euler.z=math.pi
if CID=='castor':
 from materials.opaque_atlas import preserve_opaque_atlas_rgb
 preserve_opaque_atlas_rgb({m for o in meshes for m in o.data.materials if m})
for mat in {m for o in meshes for m in o.data.materials if m}:
 if mat.use_nodes and any(n.type=='BSDF_PRINCIPLED' for n in mat.node_tree.nodes) and mat.get('treecourt_surface_mode','OPAQUE')=='OPAQUE' and mat.get('treecourt_shading_class') in ['face','skin','cloth','hair']:
  apply_toon(mat,rim=False)
  if mat.get('treecourt_shading_class') in ['face','skin']:
   for stop,col in zip(mat.node_tree.nodes['TC_Toon_Ramp'].color_ramp.elements,[(.80,.75,.76,1),(.94,.91,.92,1),(1,.99,.98,1)]):stop.color=col

environment=ROOT/('blender/build/study-room/study_room.blend' if KIND=='study' else f"blender/build/outings/{SPEC['scene']}.blend")
with bpy.data.libraries.load(str(environment),link=False) as (src,dst):dst.objects=[n for n in src.objects]
for obj in dst.objects:
 if obj and obj.type=='MESH':scene.collection.objects.link(obj)
for mat in bpy.data.materials:
 if mat.name.startswith('TC_Study_lamp') and mat.use_nodes:
  node=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if node:node.inputs['Emission Strength'].default_value=.6

def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if p:p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.85
 return m
def box(name,loc,size,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);m=o.modifiers.new('Rounded edges','BEVEL');m.width=.008;m.segments=2;return o
paper=material('Companion ivory paper',(.94,.89,.73));cover=material('Companion book cover',{'anaxa':(.16,.28,.21),'hyacine':(.64,.28,.38),'castor':(.26,.20,.38),'phainon':(.29,.36,.43)}[CID]);gold=material('Companion brass',(.63,.43,.17))
if KIND=='study':
 # The book is on the existing desk, independent of the animated hand mesh.
 for obj in scene.objects:
  if obj.name=='Desk_Top':obj.dimensions.y=1.20;obj.location.y=-.15
 box('Shared reading book cover',(.02,-.40,.866),(.46,.31,.018),cover)
 box('Open left page',(-.105,-.40,.879),(.215,.29,.008),paper);box('Open right page',(.125,-.40,.879),(.215,.29,.008),paper)
 for x in [-.105,.125]:
  for i in range(7):box('Written page line',(x,-.49+i*.029,.884),(.16,.0015,.001),gold)
else:
 # Closer props and a seating place give the existing original environment depth.
 box('Invitation side table',(-.87,.12,.72),(.60,.48,.06),cover)
 for x in [-1.10,-.64]:
  for y in [-.04,.28]:box('Invitation table leg',(x,y,.35),(.04,.04,.70),gold)
 box('Invitation book',(-.88,.10,.762),(.34,.25,.025),paper)
 backdrop=material('Warm corridor stone',(.62,.58,.48));wood=material('Window walnut',(.24,.15,.10));leaf=material('Garden leaves',(.26,.39,.22));sky=material('Dusk window blue',(.48,.63,.68))
 def ball(name,loc,size,mat):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size;o.data.materials.append(mat)
  for face in o.data.polygons:face.use_smooth=True
  return o
 if CID=='anaxa':
  box('Reading corridor backdrop',(0,2.4,1.8),(6,.16,3.6),backdrop)
  for x in [-1.5,1.5]:
   box('Rainlit window',(x,2.30,2.05),(1.15,.04,1.9),sky)
   for dx in [-.59,0,.59]:box('Window vertical frame',(x+dx,2.25,2.05),(.035,.06,1.97),wood)
   for z in [1.08,2.05,3.02]:box('Window cross frame',(x,2.25,z),(1.21,.06,.035),wood)
   for i in range(14):
    px=x-.5+(i%7)*.15;pz=1.3+(i//7)*.8
    rain=box('Rain on window',(px,2.264,pz),(.002,.002,.16),paper)
    for f in [1,49,97,145,193,241,289,337,385,433,481,529,577,625,673,721,769,817,865,913,961,1009,1057,1105,1153,1201,1249,1297,1345,1393,1441]:
     rain.location.z=pz-.12*math.sin(f/24*.9+i);rain.keyframe_insert(data_path='location',frame=f)
  for x in [-1.08,1.08]:
   box('Small reading shelf',(x,1.6,.88),(.65,.32,1.76),wood)
   for z in [.18,.68,1.18,1.68]:box('Reading shelf ledge',(x,1.39,z),(.69,.43,.035),gold)
   for z in [.39,.90,1.40]:
    for i in range(5):box('Annotated volume',(x-.24+i*.12,1.36,z),(.075,.23,.36),cover if i%2 else paper)
 elif CID=='hyacine':
  pinkgarden=material('Rose petals',(.77,.36,.45));leaflight=material('New leaves',(.40,.56,.28))
  for x in [-1.22,1.22]:
   box('Garden planter',(x,1.15,.30),(.62,.56,.60),backdrop)
   for i in range(9):
    a=i*2.4;px=x+.23*math.sin(a);py=1.15+.21*math.cos(a);z=.74+(i%3)*.16
    box('Fine flower stem',(px,py,(z+.6)/2),(.008,.008,z-.6),leaf)
    for petal in range(5):
     b=petal*math.tau/5;ball('Flower in the breeze',(px+.04*math.cos(b),py+.04*math.sin(b),z),(.04,.025,.025),pinkgarden)
   ball('Leaf cluster',(x,1.7,.76),(.60,.42,.55),leaflight)
  for x in [-1.7,1.7]:box('Near pergola post',(x,2.4,1.6),(.11,.11,3.2),wood)
  for z in [1.2,1.6,2.0,2.4,2.8,3.2]:box('Garden trellis',(0,2.4,z),(3.5,.04,.025),wood)
  for x in [-1.6,-1.2,-.8,-.4,0,.4,.8,1.2,1.6]:box('Garden trellis upright',(x,2.4,2.1),(.025,.04,2.2),wood)
  for x in [-2,-1.1,1.1,2]:ball('Garden tree canopy',(x,3.0,2.7),(.65,.5,.7),leaf)
 else:
  mauve=material('Evening hydrangea',(.55,.34,.58));sea=material('Distant lilac hills',(.43,.50,.59))
  for i in range(8):ball('Distant hill',(-12+i*3.5,19,1.0), (3.8,2.2,1.3+(i%3)*.6),sea)
  for x in [-1.25,1.25]:
   box('Terrace flower pot',(x,1.4,.31),(.52,.52,.62),backdrop)
   for i in range(9):
    px=x+.20*math.sin(i*2.4);py=1.4+.19*math.cos(i*2.4);height=.87+.10*(i%3)
    box('Evening flower stem',(px,py,(.60+height)/2),(.008,.008,height-.60),leaf)
    ball('Evening flower',(px,py,height),(.13,.11,.12),mauve)
   box('Lantern pedestal',(x,2.1,.82),(.22,.22,1.64),gold)
   box('Lantern ivory glass',(x,2.1,1.78),(.20,.20,.30),paper)
 if CID=='hyacine':
  tea=material('Warm tea',(.36,.16,.055));ivory=material('Porcelain',(.94,.87,.74));pink=material('Petal pink',(.74,.29,.42));green=material('Stem green',(.20,.35,.18))
  bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.074,depth=.10,location=(-.87,.09,.825));bpy.context.object.data.materials.append(ivory)
  bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.064,depth=.004,location=(-.87,.09,.877));bpy.context.object.data.materials.append(tea)
  bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.045,depth=.10,location=(-.63,.20,.80));bpy.context.object.data.materials.append(ivory)
  for i in range(7):
   angle=i*math.tau/7;bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=1,location=(-.63+.045*math.cos(angle),.20+.045*math.sin(angle),.97));o=bpy.context.object;o.scale=(.040,.025,.012);o.data.materials.append(pink)
  box('Flower stem',(-.63,.20,.90),(.008,.008,.12),green)
 if CID=='castor':
  flutter=bpy.data.objects.new('A butterfly shared with you',None);scene.collection.objects.link(flutter);purple=material('Butterfly violet',(.48,.23,.60))
  for sign in [-1,1]:
   mesh=bpy.data.meshes.new('Butterfly wing');mesh.from_pydata([(0,0,0),(sign*.11,.035,.06),(sign*.095,-.045,.015),(sign*.04,-.055,-.035)],[],[(0,1,2),(0,2,3)]);o=bpy.data.objects.new('Butterfly wing',mesh);scene.collection.objects.link(o);o.parent=flutter;o.data.materials.append(purple)
   for f in range(1441):o.rotation_euler.y=sign*(.18+.5*math.sin(f/24*12));o.keyframe_insert(data_path='rotation_euler',frame=f+1)
  for f in range(1441):
   t=f/24;flutter.location=(.58+.12*math.sin(t*.7),-.08+.08*math.cos(t*.6),1.25+.10*math.sin(t*.9));flutter.keyframe_insert(data_path='location',frame=f+1)

world=bpy.data.worlds.new('Companion dusk world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.47,.55,.65,1);world.node_tree.nodes['Background'].inputs[1].default_value=.55;scene.world=world
def area(name,loc,energy,color,size,target):
 data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.color=color;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 if KIND=='outing':data.use_shadow=False
area('Large soft window',(-3,1.5,4.4),420,(1,.83,.65),4,(0,0,1))
area('Face fill',(1,-3,2.8) if KIND=='outing' else (1,2,2.8),150,(.80,.88,1),3,(0,0,1.3))
area('Hair edge',(2,2,3.5),240,(1,.68,.43),2,(0,0,1.4))
sun=bpy.data.lights.new('Evening sun','SUN');sun.energy=1.7;sun.angle=.10;sun.color=(1,.85,.70);ob=bpy.data.objects.new('Evening sun',sun);scene.collection.objects.link(ob);ob.rotation_euler=(.48,-.36,-.6)
cam=bpy.data.objects.new('Player eye',bpy.data.cameras.new('Player eye'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.lens=47 if KIND=='study' else 53;cam.data.clip_start=.05
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.fps=24;scene.render.film_transparent=False
if hasattr(scene,'eevee'):scene.eevee.taa_render_samples=16 if KIND=='outing' else 32
scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast' if 'Medium High Contrast' in [x.identifier for x in scene.view_settings.bl_rna.properties['look'].enum_items] else 'None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
perf=Performance(arm);rest=perf.rest;pb=arm.pose.bones
if KIND=='study':
 from study_hand_motion import StudyHands
 study_hands=StudyHands(arm,meshes,perf,calibrate=(CID=='castor'))

def pose(t,study,variant=0):
 for p in pb:p.matrix_basis=Matrix.Identity(4);p.rotation_mode='QUATERNION'
 u=math.tau*t/20 if study else t
 lift=pulse(t%20,10.5,15.8,1.6) if study else .65
 if study:
  drop=(.48+.075)/scale-rest['足.L'].translation.z
  perf.move('センター',(.0025/scale*math.sin(u),.001/scale*math.sin(u*2),drop+.0012/scale*math.sin(u*3)))
  perf.rot('上半身',(1,0,0),.10-.035*lift+.004*math.sin(u*3-.2))
  for side,sign in [('L',1),('R',-1)]:
   m=rest['足ＩＫ.'+side].copy();m.translation=Vector((sign*.085/scale,-.40/scale,rest['足ＩＫ.'+side].translation.z));pb['足ＩＫ.'+side].matrix=m
 else:perf.move('センター',(.003*math.sin(t*.7),0,.0015*math.sin(t*1.2)))
 perf.rot('上半身2',(0,0,1),.006*math.sin(u-.25) if study else .008*math.sin(t*.5))
 if study:perf.rot('上半身2',(1,0,0),.003*math.sin(u*3-.5))
 perf.rot('首',(1,0,0),((.29 if CID=='castor' else .22)-(.34 if CID=='castor' else .27)*lift+.006*math.sin(u*2)) if study else -.02+.025*math.sin(t*.55))
 if not study:perf.rot('首',(0,0,1),(.035 if CID=='anaxa' else .055 if CID=='hyacine' else .018)*math.sin(t*.37))
 perf.rot('頭',(0,0,1),(.016*math.sin(u-.5)+.012*lift) if study else (.03 if CID=='hyacine' else -.015)*math.sin(t*.48))
 if study:
  eye_lead=pulse(t%20,10.15,15.45,1.1)
  perf.rot('両目',(1,0,0),(.28*(1-eye_lead)-.015*eye_lead) if CID=='castor' else -.025*eye_lead)
  perf.rot('両目',(0,1,0),.012*math.sin(u*2)*pulse(t%20,1,9,1))
 bpy.context.view_layer.update()
 for side,sign in [('L',1),('R',-1)]:
  shoulder=pb['腕.'+side].head.copy()
  if study:
   trace=pulse(t%20,2.0,8.2,1.2) if side=='R' else 0.
   reposition=pulse(t%20,16.0,19.2,.95) if side=='L' else 0.
   world_target=Vector((-sign*.145+(.008*math.sin(u*2)*trace if side=='R' else -.004*reposition),-.615+.003*trace,.906+.002*lift+.014*reposition))
   target=arm.matrix_world.inverted()@world_target
   study_hands.place(side,target,shoulder+Vector((sign*.30,.09,-.23)),t,lift)
   continue
  gesture=pulse(t%20,3+variant*.6,8+variant*.6,1.3) if side=='R' else .12
  if CID=='hyacine' and side=='L':gesture=.42*pulse(t%20,4.1,9.1,1.5)
  if CID=='castor':gesture=.15+.16*math.sin(t*.25)**2 if side=='R' else .18
  target=Vector((sign*(.20+.07*gesture)/scale,(-.10-.18*gesture)/scale,(.88+.23*gesture)/scale))
  perf.arm_to(side,target,shoulder+Vector((sign*.3,.1,-.25)),bpy.context.view_layer.update)
  for p in pb:
   if ('指' in p.name) and p.name.endswith('.'+side) and not p.name.startswith('_'):perf.rot(p.name,(1,0,0),.12)
 bpy.context.view_layer.update()


def bake(duration,offset=0,branch=None):
 bake_modifiers=[(m,m.show_viewport) for o in meshes for m in o.modifiers if m.type=='ARMATURE']
 if KIND=='study':
  for modifier,_ in bake_modifiers:modifier.show_viewport=False
 physics=SecondaryMotion(arm,24,seat=False);channels=defaultdict(list);shapes={o.name:defaultdict(list) for o in meshes if o.data.shape_keys}
 if arm.animation_data:arm.animation_data_clear()
 for o in meshes:
  if o.data.shape_keys:o.data.shape_keys.animation_data_clear()
 envelope=json.loads((OUT/'lip-sync.json').read_text())['values'] if KIND=='outing' and branch is None and (OUT/'lip-sync.json').is_file() else None
 for frame in range(round(duration*24)+1):
  t=frame/24;pose(t+offset,KIND=='study',0 if branch is None else branch)
  if KIND=='study' and frame%120==0:print('STUDY_POSE_BAKED',CID,frame,round(duration*24),flush=True)
  physics.step(t+offset)
  if KIND=='study':
   gate=ramp(t,0,.8)*(1-ramp(t,duration-.8,duration))
   for p in physics.bones:p.rotation_quaternion=Quaternion().slerp(p.rotation_quaternion,gate)
  for p in pb:
   for i,v in enumerate(p.rotation_quaternion):channels[(p.path_from_id('rotation_quaternion'),i)].append((frame+1,v))
   if p.name in ['センター','足ＩＫ.L','足ＩＫ.R']:
    for i,v in enumerate(p.location):channels[(p.path_from_id('location'),i)].append((frame+1,v))
  blink=max(pulse(t,at,at+.22,.085) for at in ([3.2,7.7,16.4] if KIND=='study' else [2.9,7.6,12.5,18.9,24.2,30.8,36.7,42.4,48.1,54.6,58.9]))
  mouth=(envelope[min(frame,len(envelope)-1)]*.09 if envelope else (.06*abs(math.sin(t*8))*pulse(t,.25,duration-.25,.2) if branch is not None else 0))
  values={'まばたき':blink,'あ':mouth,'口角上げ':.08 if CID!='castor' else .035,'笑い':.025,'慈愛':.035}
  for o in meshes:
   if o.name not in shapes:continue
   for name,v in values.items():
    if name in o.data.shape_keys.key_blocks:shapes[o.name][(o.data.shape_keys.key_blocks[name].path_from_id('value'),0)].append((frame+1,v))
 write_channels(arm,f'{CID}_{KIND}_body',channels)
 continuity=smooth_secondary_action(arm)
 for o in meshes:
  if o.name in shapes and shapes[o.name]:write_channels(o.data.shape_keys,f'{CID}_{KIND}_face_{o.name}',shapes[o.name])
 if cam.animation_data:cam.animation_data_clear()
 for frame in range(round(duration*24)+1):
  t=frame/24
  if KIND=='study':
   angle=math.tau*t/20;cam.location=(.25+.025*math.sin(angle),1.35,1.30+.008*math.sin(angle));target=Vector((0,-.80,1.19))
  else:
   close=.12*pulse(t,10,26,2)+.25*pulse(t,36,60,2) if branch is None else .20
   cam.location=(.24+.08*math.sin(t*.13),-2.55+close,1.59+.012*math.sin(t*.42));target=Vector((0,0,1.39 if CID!='hyacine' else 1.25))
  cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert(data_path='location',frame=frame+1);cam.keyframe_insert(data_path='rotation_euler',frame=frame+1)
 scene.frame_start=1;scene.frame_end=round(duration*24);scene.frame_set(1)
 for modifier,visible in bake_modifiers:modifier.show_viewport=visible
 bpy.context.view_layer.update()
 return dict(secondary_bones=len(physics.bones),full_mesh_cloth_simulation=False,continuity=continuity,**({'hand_contact':study_hands.report(),'media_revision':3 if CID=='castor' else 2} if KIND=='study' else {}))

def render(name,duration,sound=None):
 from companion_video import render_video
 render_video(scene,OUT/name,duration,sound)

started=time.monotonic();duration=(1/24 if '--pose-preview' in args else 20) if KIND=='study' else (8 if PREVIEW else 60)
report=bake(duration)
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'poster.png');scene.frame_set(1 if KIND=='study' else 1+6*24)
bpy.ops.render.render(write_still=True)
if PREVIEW:
 if KIND=='study' and '--review' in args:
  for frame in ([1] if duration<1 else [1,121,289,409]):
   scene.frame_set(frame);scene.render.filepath=str(OUT/f'review-{frame:04d}.png');bpy.ops.render.render(write_still=True)
  review=bpy.data.objects.new('Hand contact review',bpy.data.cameras.new('Hand contact review'));scene.collection.objects.link(review);review.data.lens=58;review.location=(.18,.32,1.24);review.rotation_euler=(Vector((0,-.43,.90))-review.location).to_track_quat('-Z','Y').to_euler();scene.camera=review;scene.frame_set(1);scene.render.filepath=str(OUT/'hand-review.png');bpy.ops.render.render(write_still=True)
 (OUT/'preview-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('COMPANION_PREVIEW_READY',CID,KIND,flush=True)
else:
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{CID}_{KIND}.blend'))
 render('loop.mp4' if KIND=='study' else 'interactive.mp4',duration,OUT/'soundtrack.wav' if KIND=='outing' else None)
 if KIND=='outing':
  for cue in SPEC['interactions']:
   for i,choice in enumerate(cue['choices']):
    report.setdefault('responses',{})[cue['id']+'-'+choice['id']]=bake(choice['duration'],offset=cue['at'],branch=i+1)
    render(cue['id']+'-'+choice['id']+'.mp4',choice['duration'],OUT/'audio'/(cue['id']+'-'+choice['id']+'.wav'))
 report.update(character=CID,kind=KIND,duration=duration,fps=24,resolution=[1280,720],elapsed_seconds=time.monotonic()-started)
 (OUT/'build-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('COMPANION_RENDER_COMPLETE',CID,KIND,flush=True)
