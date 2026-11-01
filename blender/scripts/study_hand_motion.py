"""Study hand placement, anatomical palm orientation and skinned-mesh page clearance."""
import math
import numpy as np
from mathutils import Vector,Matrix,Quaternion
from phainon_motion import pulse

class StudyHands:
 def __init__(self,arm,meshes,performance,calibrate=False):
  self.arm=arm;self.perf=performance;self.pb=arm.pose.bones;self.rest=performance.rest;self.minimum=10.;self.minimum_desk=10.;self.max_correction=0.;self.samples=0
  self.calibrate=calibrate;self.calibration={};self.finger_points={}
  self.skin={};self.source={};self.rest_inverse={b.name:b.matrix_local.inverted() for b in arm.data.bones}
  for side in ['L','R']:
   wrist=self.rest['手首.'+side].translation
   forward=(self.rest['中指先.'+side].translation-wrist).normalized()
   across=self.rest['人指１.'+side].translation-self.rest['小指１.'+side].translation
   normal=forward.cross(across).normalized()*(1 if side=='R' else -1)
   across=forward.cross(normal).normalized();normal=across.cross(forward).normalized()
   source=Matrix((across,forward,normal)).transposed().to_quaternion()
   self.source[side]=(source,self.rest['手首.'+side].to_quaternion())
   points=[];weights=[]
   for obj in meshes:
    groups={g.index:g.name for g in obj.vertex_groups};to_arm=arm.matrix_world.inverted()@obj.matrix_world
    for v in obj.data.vertices:
     bindings=[(groups[g.group],g.weight) for g in v.groups if groups.get(g.group) in self.pb and self.pb[groups[g.group]].bone.use_deform and g.weight>.00001]
     hand=sum(w for n,w in bindings if ('手首' in n or '指' in n) and n.endswith('.'+side))
     if hand>.35:
      points.append(tuple(to_arm@v.co)+(1.,));weights.append(bindings)
   positions=np.asarray(points,dtype=np.float64);by_bone={}
   for index,bindings in enumerate(weights):
    total=sum(w for _,w in bindings)
    for name,weight in bindings:by_bone.setdefault(name,[]).append((index,weight/total))
   self.skin[side]=(positions,{name:(np.asarray([i for i,_ in entries]),np.asarray([w for _,w in entries])[:,None]) for name,entries in by_bone.items()})
   if calibrate:self.finger_points[side]={finger:np.asarray([i for i,bindings in enumerate(weights) if sum(w for name,w in bindings if name.startswith(finger))>.35],dtype=np.int32) for finger in ['人指','中指','薬指','小指','親指']}

 def cloud(self,side):
  positions,bindings=self.skin[side];posed=np.zeros_like(positions)
  for name,(indices,weights) in bindings.items():
   transform=np.asarray(self.pb[name].matrix@self.rest_inverse[name],dtype=np.float64)
   posed[indices]+=(positions[indices]@transform.T)*weights
  return posed@np.asarray(self.arm.matrix_world,dtype=np.float64).T

 def lowest(self,side):
  world=self.cloud(side)
  mask=(world[:,0]>-.223)&(world[:,0]<.243)&(world[:,1]>-.555)&(world[:,1]<-.245)
  desk=(world[:,0]>-.85)&(world[:,0]<.85)&(world[:,1]>-.75)&(world[:,1]<.45)
  return (float(world[mask,2].min()) if mask.any() else 10.,float(world[desk,2].min()) if desk.any() else 10.)

 def place(self,side,target,pole,t,lift):
  update=__import__('bpy').context.view_layer.update
  sign=1 if side=='L' else -1;u=math.tau*t/20
  trace=pulse(t%20,2.0,8.2,1.2) if side=='R' else 0.
  wrist_name='手首.'+side
  forward=Vector((-sign*(.11+.025*math.sin(u)), -1., -.015)).normalized()
  normal=Vector((0,0,1));across=forward.cross(normal).normalized();normal=across.cross(forward).normalized()
  target_basis=Matrix((across,forward,normal)).transposed().to_quaternion()
  source,rest_rotation=self.source[side];rotation=target_basis@source.inverted()@rest_rotation
  def solve():
   for bone in self.pb:
    if '指' in bone.name and bone.name.endswith('.'+side):bone.matrix_basis=Matrix.Identity(4)
   self.perf.arm_to(side,target,pole,update);update()
   wrist=self.pb[wrist_name];position=wrist.head.copy();fore=self.pb['ひじ.'+side]
   axis=(position-fore.head).normalized();difference=rotation@wrist.matrix.to_quaternion().inverted()
   projection=axis*Vector((difference.x,difference.y,difference.z)).dot(axis)
   twist=Quaternion((difference.w,*projection)).normalized()
   fore.matrix=Matrix.LocRotScale(fore.head,twist@fore.matrix.to_quaternion(),Vector((1,1,1)));update()
   wrist.matrix=Matrix.LocRotScale(position,rotation,Vector((1,1,1)));update()
   for finger,base in [('人指',.012 if side=='R' else .020),('中指',.025),('薬指',.035),('小指',.045)]:
    for level in ['１','２','３']:
     name=finger+level+'.'+side
     if name not in self.pb:continue
     bone=self.pb[name];reference=rotation@rest_rotation.inverted()@self.rest[name].to_quaternion();axis=reference.inverted()@across
     curl=base+(.008*math.sin(u*2+len(finger)+int(level.translate(str.maketrans('１２３','123')))))
     if finger=='人指':curl*=1-.55*trace
     self.perf.rot(name,axis,-curl)
   thumb='親指１.'+side
   if thumb in self.pb:
    reference=rotation@rest_rotation.inverted()@self.rest[thumb].to_quaternion();axis=reference.inverted()@normal
    self.perf.rot(thumb,axis,sign*.08)
   for level,angle in [('１',.45),('２',.25)]:
    name='親指'+level+'.'+side
    if name in self.pb:
     reference=rotation@rest_rotation.inverted()@self.rest[name].to_quaternion()
     direction=reference@Vector((0,1,0));axis=direction.cross(normal).normalized()
     self.perf.rot(name,reference.inverted()@axis,angle)
   update()
   if self.calibrate:
    if side not in self.calibration:
     adjustments={}
     for i,finger in enumerate(['人指','中指','薬指','小指','親指']):
      name=finger+('０' if finger=='親指' else '１')+'.'+side;ids=self.finger_points[side][finger]
      if name not in self.pb or not len(ids):continue
      bone=self.pb[name];base=bone.rotation_quaternion.copy();goal=.8888+i*.0003
      def height():
       points=self.cloud(side)[ids];mask=(points[:,0]>-.223)&(points[:,0]<.243)&(points[:,1]>-.555)&(points[:,1]<-.245)
       return float(points[mask,2].min()) if mask.any() else goal
      for _ in range(3):
       low=height()
       if abs(low-goal)<.00012:break
       reference=bone.matrix.to_quaternion();direction=reference@Vector((0,1,0));axis=reference.inverted()@direction.cross(normal).normalized();q=bone.rotation_quaternion.copy()
       bone.rotation_quaternion=q@Quaternion(axis,.02);update();slope=(height()-low)/.02
       bone.rotation_quaternion=q
       if abs(slope)<.003:break
       angle=max(-.35,min(.35,(goal-low)/slope));candidate=q@Quaternion(axis,angle)
       extent=base.rotation_difference(candidate).angle
       bone.rotation_quaternion=base.slerp(candidate,min(1.,.60/max(extent,.00001)));update()
      adjustments[name]=base.inverted()@bone.rotation_quaternion
     self.calibration[side]=adjustments
    else:
     for name,adjustment in self.calibration[side].items():self.pb[name].rotation_quaternion @= adjustment
     update()
  solve();correction=0.
  for _ in range(4):
   lowest,desk=self.lowest(side);missing=max(.888-lowest,.848-desk)
   if missing<.00003:break
   delta=self.arm.matrix_world.inverted().to_3x3()@Vector((0,0,missing+.00015));target+=delta;correction+=missing;solve()
  lowest,desk=self.lowest(side);self.minimum=min(self.minimum,lowest);self.minimum_desk=min(self.minimum_desk,desk);self.max_correction=max(self.max_correction,correction);self.samples+=1
  if lowest<.8878 or desk<.8478:raise RuntimeError(f'Unresolved hand/book contact {side} {t}: {lowest}, desk {desk}')

 def report(self):
  return dict(page_top_m=.885,desk_top_m=.845,clearance_target_m=.003,minimum_skinned_hand_height_m=self.minimum,minimum_page_clearance_m=self.minimum-.885,minimum_desk_clearance_m=self.minimum_desk-.845,maximum_wrist_correction_m=self.max_correction,sampled_hands=self.samples,method='weighted skin vertices, anatomical palm frame, two-bone arm solve')
