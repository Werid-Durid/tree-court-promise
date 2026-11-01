"""MMD 骨架表演与可烘焙次级运动。位置单位为角色骨架米制空间。"""
import math
from mathutils import Vector,Matrix,Quaternion

def smooth(x):
 x=max(0.,min(1.,x));return x*x*x*(10+x*(-15+6*x))
def ramp(t,a,b):return smooth((t-a)/(b-a))
def pulse(t,a,b,r=.5):return ramp(t,a,a+r)*(1-ramp(t,b-r,b))
def curve(t,points):
 for (a,x),(b,y) in zip(points,points[1:]):
  if t<=b:return x+(y-x)*ramp(t,a,b)
 return points[-1][1]

def write_channels(owner,name,channels):
 """一次写入全部 F 曲线，避免逐帧插入触发重复场景求值。"""
 import bpy
 action=bpy.data.actions.new(name);slot=action.slots.new(owner.id_type,owner.name);bag=action.layers.new('Baked performance').strips.new(type='KEYFRAME').channelbag(slot,ensure=True)
 for (path,index),samples in channels.items():
  fc=bag.fcurves.new(data_path=path,index=index);fc.keyframe_points.add(len(samples));fc.keyframe_points.foreach_set('co',[v for pair in samples for v in pair])
  for point in fc.keyframe_points:point.interpolation='LINEAR'
  fc.update()
 ad=owner.animation_data_create();ad.action=action;ad.action_slot=slot
 return action

def smooth_secondary_action(arm):
 """供回应片段使用相同的四元数连续性与角速度约束。"""
 action=arm.animation_data.action;bag=action.layers[0].strips[0].channelbag(arm.animation_data.action_slot);groups={}
 for fc in bag.fcurves:
  if fc.data_path.endswith('rotation_quaternion') and any(word in fc.data_path for word in ['髪','下摆','披肩']):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
 def delta(a,b):return 2*math.acos(min(1,abs(a.dot(b))))
 before=0.;after=0.
 for path,channels in groups.items():
  if set(channels)!={0,1,2,3}:continue
  values=[Quaternion(tuple(channels[j].keyframe_points[i].co.y for j in range(4))).normalized() for i in range(len(channels[0].keyframe_points))]
  before=max(before,max(delta(a,b) for a,b in zip(values,values[1:])))
  for _ in range(2):values=[values[0]]+[values[i].slerp(values[i-1].slerp(values[i+1],.5),.4) for i in range(1,len(values)-1)]+[values[-1]]
  limit=math.radians(3 if '髪' in path else 4.5)
  for i in range(1,len(values)):
   step=delta(values[i-1],values[i])
   if step>limit:values[i]=values[i-1].slerp(values[i],limit/step)
  after=max(after,max(delta(a,b) for a,b in zip(values,values[1:])))
  for j,fc in channels.items():
   for i,q in enumerate(values):fc.keyframe_points[i].co.y=q[j]
   fc.update()
 return {'bones':len(groups),'max_adjacent_frame_rotation_before_degrees':math.degrees(before),'max_adjacent_frame_rotation_after_degrees':math.degrees(after)}

class Performance:
 def __init__(self,arm):
  self.arm=arm;self.pb=arm.pose.bones;self.rest={b.name:b.matrix_local.copy() for b in arm.data.bones}
  self.lengths={s:((self.rest['ひじ.'+s].translation-self.rest['腕.'+s].translation).length,(self.rest['手首.'+s].translation-self.rest['ひじ.'+s].translation).length) for s in ['L','R']}
 def rot(self,name,axis,angle):
  if name in self.pb:self.pb[name].rotation_quaternion @= Quaternion(axis,angle)
 def move(self,name,delta):
  p=self.pb[name];ref=p.parent.matrix@self.rest[p.parent.name].inverted()@self.rest[name] if p.parent else self.rest[name].copy();ref.translation+=Vector(delta);p.matrix=ref
 def aim(self,name,target):
  p=self.pb[name];ref=p.parent.matrix@self.rest[p.parent.name].inverted()@self.rest[name] if p.parent else self.rest[name]
  q=(ref.to_quaternion()@Vector((0,1,0))).rotation_difference((Vector(target)-p.head).normalized())@ref.to_quaternion();p.matrix=Matrix.LocRotScale(p.head,q,Vector((1,1,1)))
 def arm_to(self,side,target,pole,update):
  shoulder=self.pb['腕.'+side].head.copy();d=Vector(target)-shoulder;l1,l2=self.lengths[side];length=max(abs(l1-l2)+.001,min(d.length,l1+l2-.002));direction=d.normalized();target=shoulder+direction*length
  along=(l1*l1-l2*l2+length*length)/(2*length);bend=Vector(pole)-shoulder;bend-=direction*bend.dot(direction)
  elbow=shoulder+direction*along+bend.normalized()*math.sqrt(max(0,l1*l1-along*along))
  upper=self.pb['腕.'+side];fore=self.pb['ひじ.'+side];ref=upper.parent.matrix@self.rest[upper.parent.name].inverted()@self.rest[upper.name]
  q=(ref.to_quaternion()@Vector((0,1,0))).rotation_difference((elbow-shoulder).normalized())@ref.to_quaternion();upper_world=Matrix.LocRotScale(shoulder,q,Vector((1,1,1)));upper.matrix_basis=ref.inverted()@upper_world
  ref2=upper_world@self.rest[upper.name].inverted()@self.rest[fore.name];fore_head=ref2.translation;q2=(ref2.to_quaternion()@Vector((0,1,0))).rotation_difference((target-fore_head).normalized())@ref2.to_quaternion();fore.matrix_basis=ref2.inverted()@Matrix.LocRotScale(fore_head,q2,Vector((1,1,1)))
  self.pb['手首.'+side].matrix_basis=Matrix.Identity(4)
 def pose(self,t,update):
  for p in self.pb:p.matrix_basis=Matrix.Identity(4);p.rotation_mode='QUATERNION'
  seat=ramp(t,27.0,29.35);settle=.008*math.exp(-max(0,t-29.35)*5)*math.sin(max(0,t-29.35)*10) if t>=29.35 else 0
  drop=.515*seat+settle;back=.275*seat**1.7-.035*pulse(t,26.2,28.4,.8)
  lean=curve(t,[(0,.025),(25.8,.025),(27.0,.23),(28.8,.43),(29.45,.36),(30.7,.09),(74,.09)])
  breath=.0015*math.sin(t*1.45)+.0005*math.sin(t*.63)
  self.move('センター',(.009*math.sin(t*.47),back,-drop+breath));self.rot('上半身',(1,0,0),lean+.025*pulse(t,14,22));self.rot('上半身1',(1,0,0),-.03*seat)
  self.rot('上半身2',(0,0,1),.008*math.sin(t*.63));self.rot('上半身2',(1,0,0),.004*math.sin(t*1.45-.2))
  horizon=pulse(t,38,45,1.4);shy=pulse(t,48.2,53.4,1.2);lookbench=pulse(t,25.6,28.2,.7)
  self.rot('首',(1,0,0),-.20*lean+.04*shy+.07*lookbench);self.rot('頭',(0,0,1),.22*horizon+.009*math.sin(t*.53));self.rot('頭',(1,0,0),-.35*lean+.045*shy+.045*lookbench)
  # 眼神先于头部转动，动作完成后回到玩家附近，避免固定不动的注视。
  self.rot('両目',(0,1,0),.035*pulse(t,37.85,44.8,1.1));self.rot('目.L',(1,0,0),.025*lookbench);self.rot('目.R',(1,0,0),.025*lookbench)
  for side,sgn,start in [('R',-1,26.0),('L',1,26.55)]:
   step=ramp(t,start,start+.55);lift=.024*math.sin(math.pi*max(0,min(1,(t-start)/.55)))
   foot=self.rest['足ＩＫ.'+side].copy();foot.translation+=Vector((sgn*.012*step,-.14*step,lift));self.pb['足ＩＫ.'+side].matrix=foot
  update()
  for side,sgn in [('R',-1),('L',1)]:
   target=Vector((sgn*.28,-.04,1.05-drop*.75));offer=pulse(t,13.2,23.4,1.3);wave=pulse(t,6.1,10.8,.8)
   if side=='R':target=target.lerp(Vector((-.22,-.30,1.15)),offer).lerp(Vector((-.40,-.13,1.62+.015*math.sin(t*3))),wave)
   brace=ramp(t,27.25,28.65)*(1-ramp(t,29.65,31.2));target=target.lerp(Vector((sgn*.15,.31,.565)),brace)
   lap=ramp(t,29.6,31.2);target=target.lerp(Vector((sgn*.15,-.035,.67)),lap)
   self.arm_to(side,target,(sgn*.46,.23,1.05-drop),update)
   self.rot('手首.'+side,(0,1,0),sgn*.06*lap)
   for p in self.pb:
    if p.name.endswith('.'+side) and '指' in p.name and not p.name.startswith('_'):self.rot(p.name,(1,0,0),.05+.045*lap)
  # 衣摆的坐姿基形沿大腿展开，再由次级运动求解器处理惯性和接触。
  for p in self.pb:
   if p.name.startswith('下摆_'):
    _,level,ring=p.name.split('_');level=int(level);root=self.rest[f'下摆_0_{ring}'].translation;front=smooth((-root.y-.006)/.07)
    fold=(-1.32 if level==0 else .17 if 2<=level<=9 else 0)*front*seat
    world_axis=self.rest[p.name].to_quaternion().inverted()@Vector((1,0,0));self.rot(p.name,world_axis,fold)
  update();return {'seat':seat,'drop':drop,'back':back,'lean':lean}

class SecondaryMotion:
 """阻尼弹簧端点、定长骨链、关节角限制与简化身体/座椅碰撞。非全网格布料求解。"""
 def __init__(self,arm,fps,seat=True):
  self.arm=arm;self.fps=fps;self.seat=seat;self.rest={b.name:b.matrix_local.copy() for b in arm.data.bones};self.states={};self.previous_anchors={};self.max_angle=0.;self.contacts=0
  self.bones=[p for p in arm.pose.bones if not p.name.startswith('_') and ('髪' in p.name or p.name.startswith(('下摆_','下摆带_','披肩')))]
  def depth(p):return 1+depth(p.parent) if p.parent else 0
  self.bones.sort(key=depth)
 def project(self,point,a,b,radius):
  ab=b-a;center=a+ab*max(0,min(1,(point-a).dot(ab)/max(1e-8,ab.length_squared)));v=point-center
  if v.length<radius:
   self.contacts+=1;return center+(v.normalized() if v.length>1e-6 else Vector((0,-1,0)))*radius
  return point
 def step(self,t):
  pb=self.arm.pose.bones;solved={};dt=1/self.fps;sub=dt/4
  capsules=[]
  for a,b,r in [('下半身','上半身2',.115),('足.L','ひざ.L',.087),('足.R','ひざ.R',.087),('ひざ.L','足首.L',.065),('ひざ.R','足首.R',.065)]:capsules.append((pb[a].head.copy(),pb[b].head.copy(),r))
  for p in self.bones:
   parent=solved.get(p.parent.name,p.parent.matrix) if p.parent else Matrix.Identity(4);ref=parent@self.rest[p.parent.name].inverted()@self.rest[p.name] if p.parent else self.rest[p.name].copy();base=ref@p.matrix_basis
   anchor=base.translation.copy();direction=base.to_quaternion()@Vector((0,1,0));length=p.bone.length;target=anchor+direction*length;hair='髪' in p.name
   omega=22 if hair else 10;drag=2*.78*omega;limit=.15 if hair else .32
   state=self.states.get(p.name);last=self.previous_anchors.get(p.name,anchor);av=(anchor-last)/dt
   if state is None:pos=target.copy();velocity=Vector((0,0,0))
   else:pos,velocity=state
   wind=Vector((.16*math.sin(t*.8)+.08*math.sin(t*1.7),.11*math.sin(t*.57),0))*(.3 if hair else 1)
   # 弹簧的静态预载抵消造型姿态的重力分量，避免头发失去原来的梳理轮廓。
   gravity=Vector((0,0,-9.81));preload=base.to_quaternion()@self.rest[p.name].to_quaternion().inverted()@(-gravity)
   for _ in range(4):
    velocity+=((target-pos)*omega**2-(velocity-av)*drag+gravity+preload+wind)*sub;pos+=velocity*sub
    for _ in range(3):
     delta=pos-anchor
     if delta.length<1e-8:delta=direction.copy()
     unit=delta.normalized();angle=direction.angle(unit)
     if angle>limit:unit=direction.rotation_difference(unit).slerp(Quaternion(),1-limit/angle)@direction
     pos=anchor+unit*length
     if hair:
      head=pb['頭'];pos=self.project(pos,head.head+Vector((0,.02,.035)),head.tail+Vector((0,.02,-.035)),.067)
     else:
      for a,b,r in capsules:pos=self.project(pos,a,b,r)
      # 座面附近的衣摆只能从座面上方或边缘绕过，不能穿过木板。
      radial=Vector((pos.x,pos.y-.333,0))
      if self.seat and radial.length<.185 and .375<pos.z<.525:
       self.contacts+=1
       outward=radial.normalized() if radial.length>1e-6 else Vector((0,-1,0));pos.x=outward.x*.185;pos.y=.333+outward.y*.185
    v=pos-anchor
    if v.length>1e-8:pos=anchor+v.normalized()*length
   final_dir=(pos-anchor).normalized();q=direction.rotation_difference(final_dir);angle=direction.angle(final_dir)
   # 碰撞投影不能越过关节的活动范围；短骨节处由角度限制优先保持稳定。
   if angle>limit:
    q=q.slerp(Quaternion(),1-limit/angle);final_dir=q@direction;pos=anchor+final_dir*length;angle=limit
   self.max_angle=max(self.max_angle,angle)
   world=Matrix.LocRotScale(anchor,q@base.to_quaternion(),Vector((1,1,1)));p.matrix_basis=ref.inverted()@world;solved[p.name]=world
   velocity=(pos-(state[0] if state else target))/dt
   if velocity.length>2:velocity=velocity.normalized()*2
   self.states[p.name]=(pos.copy(),velocity);self.previous_anchors[p.name]=anchor.copy()
  return len(self.bones)
