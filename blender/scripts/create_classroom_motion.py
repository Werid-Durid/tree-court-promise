"""在各自原骨架上制作课堂表演，并输出同源 GLB/FBX 动画。原模型不覆盖。"""
import bpy,sys,json,math,struct,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'blender/classroom_motion.json').read_text(encoding='utf-8'))
OUT=ROOT/'blender/animated';OUT.mkdir(exist_ok=True)
REPORT=ROOT/'blender/animation-reports';REPORT.mkdir(exist_ok=True)
IDS=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(CFG['characters'])
WALK_LIBRARY='--walk-library' in IDS
if WALK_LIBRARY:
    IDS=[x for x in IDS if x!='--walk-library'] or list(CFG['characters'])
    OUT=ROOT/'blender/walking';OUT.mkdir(exist_ok=True)
    REPORT=ROOT/'blender/walking/reports';REPORT.mkdir(exist_ok=True)
    for cid,spec in CFG['characters'].items():
        spec['role']='teacher';spec['clip']='TC_'+cid+'_Walk'
STYLE={'anaxa':(.018,.045,.075),'hyacine':(.014,.035,.055),
       'castor':(.012,.028,.045),'phainon':(.022,.052,.095)}
TAU=2*math.pi
def ease(x):
    x=max(0,min(1,x));return x*x*x*(10+x*(-15+6*x))
def bell(t,start,end):
    if not start<t<end:return 0.0
    return math.sin(math.pi*(t-start)/(end-start))**2

def keyed(phase,keys):
    """按关键帧相位插值（0..1 循环，smoothstep 中间帧）。"""
    p=float(phase)%1.0;pts=list(keys)+[(1.0,keys[0][1])]
    for i in range(len(pts)-1):
        p0,v0=pts[i];p1,v1=pts[i+1]
        if p0<=p<=p1:
            u=0.0 if p1==p0 else (p-p0)/(p1-p0)
            u=u*u*(3-2*u)
            return v0+(v1-v0)*u
    return keys[0][1]

# 走路关键帧：相位 0=左脚接触，0.5=右脚接触；接触后下沉、经过支撑腿时抬起。
WALK_KEYS={
    'bob':[(0.00,-0.55),(0.12,-1.00),(0.25,0.45),(0.38,0.05),
           (0.50,-0.55),(0.62,-1.00),(0.75,0.45),(0.88,0.05)],
    'sway':[(0.00,0.00),(0.12,0.90),(0.25,1.00),(0.38,0.45),
            (0.50,0.00),(0.62,-0.90),(0.75,-1.00),(0.88,-0.45)],
    'pelvis':[(0.00,1.00),(0.25,0.00),(0.50,-1.00),(0.75,0.00)],
    'chest':[(0.00,0.00),(0.12,0.75),(0.25,1.00),(0.38,0.45),
             (0.50,0.00),(0.62,-0.75),(0.75,-1.00),(0.88,-0.45)],
    'head':[(0.00,-0.35),(0.25,0.00),(0.50,0.35),(0.75,0.00)],
}

def keyed_t(t,keys):
    """按秒插值的关键帧（0..24s，smoothstep 中间帧）。"""
    if t<=keys[0][0]:return keys[0][1]
    for i in range(len(keys)-1):
        t0,v0=keys[i];t1,v1=keys[i+1]
        if t0<=t<=t1:
            u=0.0 if t1==t0 else (t-t0)/(t1-t0)
            u=u*u*(3-2*u)
            return v0+(v1-v0)*u
    return keys[-1][1]

# 待机表演：头部注视方向（秒 -> 弧度）
IDLE={
 'anaxa':{'yaw':[(0,0),(2.8,-.26),(5.4,-.26),(6.4,.05),(9,.05),(11,.12),(13,0),(14.6,.20),(17,.20),(18.6,.05),(21,.05),(24,0)],
          'pitch':[(0,-.02),(2.8,-.10),(6.4,.10),(9,.10),(11,0),(13,-.05),(14.6,-.02),(18.6,.08),(21,.02),(24,0)]},
 'hyacine':{'yaw':[(0,0),(3,.12),(6,.12),(8,-.06),(11,-.06),(13,.10),(16,.10),(18,0),(24,0)],
            'pitch':[(0,0),(4,.04),(8,-.02),(12,.03),(16,0),(24,0)]},
 'castor':{'yaw':[(0,.05),(4,.05),(6,-.08),(9,-.08),(11,.04),(14,.04),(17,-.04),(20,-.04),(24,.05)],
           'pitch':[(0,.12),(4,.12),(6,-.02),(9,-.02),(11,.10),(14,.10),(17,.02),(20,.02),(24,.12)]},
 'phainon':{'yaw':[(0,0),(3,-.10),(6,.06),(9,.06),(12,-.08),(15,-.08),(18,.05),(21,.05),(24,0)],
            'pitch':[(0,.06),(3,.06),(6,-.04),(9,-.04),(12,.08),(15,.08),(18,-.02),(21,-.02),(24,.06)]},
}
# 手势窗口：(起, 止, 类型, 强度)，两端用 ease 包络，中间帧由 IK 完成。
GESTURES={
 'anaxa':{'R':[(2.8,5.6,'point',1.0),(6.8,9.2,'book',1.0),(14.8,17.2,'point',1.0),(17.2,19.4,'book',1.0)],
          'L':[(6.8,9.2,'book',0.7),(12.8,15.0,'behind',0.8)]},
 'hyacine':{'R':[(8.8,11.0,'sleeve',0.9),(3.2,5.2,'clasp',0.7),(13.2,15.4,'clasp',0.6)],
            'L':[(3.2,5.2,'clasp',0.7),(13.2,15.4,'clasp',0.6)]},
 'castor':{'R':[(11.8,14.4,'hair',0.9)],'L':[]},
 'phainon':{'R':[(5.8,9.0,'chin',1.0),(15.8,18.0,'stretch',0.8)],
            'L':[(15.8,18.2,'stretch',0.7)]},
}
# 手势偏移（目标空间：x 前，y 侧，z 上）
GEST_OFFSETS={
 'point':(0.10,-0.05,0.30),'book':(0.16,-0.10,-0.06),'behind':(-0.12,-0.08,-0.04),
 'clasp':(0.10,-0.05,-0.18),'sleeve':(0.06,0.14,0.00),'hair':(0.02,-0.05,0.30),
 'chin':(0.04,-0.02,0.26),'stretch':(-0.02,-0.20,0.38),
}
def gesture_at(cid,side,t):
    best=None
    for a,b,kind,s in GESTURES.get(cid,{}).get(side,[]):
        if a<=t<=b:
            env=ease((t-a)/.35)*ease((b-t)/.35)
            best=(kind,s*env)
    return best

class Performer:
    def __init__(self,cid,arm,height):
        self.cid=cid;self.arm=arm;self.pb=arm.pose.bones;self.spec=CFG['characters'][cid]
        self.scale=self.spec['height']/height;self.changed=set()
        self.rest={b.name:b.matrix_local.copy() for b in arm.data.bones}
        self.foot={s:self.rest['足ＩＫ.'+s].translation.copy() for s in ('L','R')}
        self.lengths={s:((self.rest['ひじ.'+s].translation-self.rest['腕.'+s].translation).length,
                       (self.rest['手首.'+s].translation-self.rest['ひじ.'+s].translation).length) for s in ('L','R')}
        self.metrics=[]
        for p in self.pb:
            p.rotation_mode='QUATERNION'
            # 原 MMD 的物理/驱动不作为运行时依赖；约束将在烘焙后移除。
        if arm.animation_data:arm.animation_data_clear()
    def rotate(self,name,axis,angle):
        if name not in self.pb:return
        self.pb[name].rotation_quaternion=Quaternion(Vector(axis),angle);self.changed.add(name)
    def translate_world(self,name,translation):
        p=self.pb[name];m=self.rest[name].copy()
        if p.parent:m=p.parent.matrix@p.parent.bone.matrix_local.inverted()@m
        m.translation+=Vector(translation);p.matrix=m;self.changed.add(name)
    def aim(self,name,target):
        p=self.pb[name]
        ref=p.parent.matrix@p.parent.bone.matrix_local.inverted()@p.bone.matrix_local if p.parent else p.bone.matrix_local.copy()
        head=p.head.copy();direction=(Vector(target)-head).normalized()
        rotation=(ref.to_quaternion()@Vector((0,1,0))).rotation_difference(direction)@ref.to_quaternion()
        p.matrix=Matrix.LocRotScale(head,rotation,Vector((1,1,1)));self.changed.add(name)
    def arm_to(self,side,target,pole):
        a=self.pb['腕.'+side];start=a.head.copy();target=Vector(target)
        l1,l2=self.lengths[side];delta=target-start;distance=min(max(delta.length,abs(l1-l2)+.005),l1+l2-.003)
        direction=delta.normalized();target=start+direction*distance
        along=(l1*l1-l2*l2+distance*distance)/(2*distance)
        bend=Vector(pole)-start;bend-=direction*bend.dot(direction)
        if bend.length<.001:bend=Vector((0,1,0))
        elbow=start+direction*along+bend.normalized()*math.sqrt(max(0,l1*l1-along*along))
        self.aim('腕.'+side,elbow);bpy.context.view_layer.update()
        self.aim('ひじ.'+side,target);bpy.context.view_layer.update()
        wrist=self.pb['手首.'+side]
        hand_direction=Vector((0,-1,-.06)) if self.spec['role']=='student' else (target-elbow).normalized()
        self.aim('手首.'+side,wrist.head+hand_direction*.08)
        err=(wrist.head-target).length
        return err
    def locomotion(self,t):
        x=0.;yaw=0.;walk=None;turn=None
        if 5<=t<6:yaw=ease(t-5)*math.pi/2;turn=(5,0.,math.pi/2,0.)
        elif 6<=t<9:x=1.1*ease((t-6)/3);yaw=math.pi/2;walk=(6,0.,1.)
        elif 9<=t<10:x=1.1;yaw=(1-ease(t-9))*math.pi/2;turn=(9,math.pi/2,0.,1.1)
        elif 10<=t<17:x=1.1
        elif 17<=t<18:x=1.1;yaw=-ease(t-17)*math.pi/2;turn=(17,0.,-math.pi/2,1.1)
        elif 18<=t<21:x=1.1*(1-ease((t-18)/3));yaw=-math.pi/2;walk=(18,1.1,-1.)
        elif 21<=t<22:yaw=-(1-ease(t-21))*math.pi/2;turn=(21,-math.pi/2,0.,0.)
        return x,yaw,walk,turn
    def pose(self,t):
        for p in self.pb:p.matrix_basis=Matrix.Identity(4)
        self.changed=set();role=self.spec['role'];student=role=='student'
        x,yaw,walk,turn=self.locomotion(t) if role=='teacher' else (0.,0.,None,None)
        root=self.pb['全ての親']
        # MMD 根骨局部 Y 轴朝上；必须在骨架空间绕 Z 转身，不能把局部 Z 当竖轴。
        root.matrix=Matrix.Translation((x,0,0))@Quaternion((0,0,1),yaw).to_matrix().to_4x4()@self.rest[root.name]
        self.changed.add(root.name);bpy.context.view_layer.update()
        breath=math.sin(TAU*t/4)
        center_drop=0.
        if student:
            hip=self.rest['足.L'].translation.z
            center_drop=(CFG['seat_height']+.075)/self.scale-hip
        elif role=='teacher':
            # 预先屈膝降低重心，为跨步留足腿长；否则 IK 伸直到极限时支撑脚会被拖走。
            weight=max(ease(t-5)*(1-ease(t-9)),ease(t-17)*(1-ease(t-21)))
            center_drop=-.065*weight/self.scale
        walking=1. if walk else 0.
        sway,twist,arm_swing=STYLE[self.cid]
        elapsed=t-walk[0] if walk else 0.
        # 起停包络防止从讲课姿势切到步态时骨盆瞬间横跳。
        envelope=ease(elapsed/.3)*ease((3-elapsed)/.3) if walk else 0.
        stride=TAU*elapsed
        phase=elapsed%1.0
        if walk:
            bob_f=keyed(phase,WALK_KEYS['bob'])
            sway_f=keyed(phase,WALK_KEYS['sway'])
            pelvis_f=keyed(phase,WALK_KEYS['pelvis'])
            chest_f=keyed(phase,WALK_KEYS['chest'])
            head_f=keyed(phase,WALK_KEYS['head'])
        else:
            bob_f=sway_f=pelvis_f=chest_f=head_f=0.
        # 重心：接触后下沉、经过支撑腿时抬起，一个步幅两次起伏；脚由独立地面目标约束。
        bob=(.016*bob_f*envelope)/self.scale
        lateral=Quaternion((0,0,1),yaw)@Vector((-sway*sway_f*envelope/self.scale,0,0))
        self.translate_world('センター',(lateral.x,lateral.y,center_drop+bob))
        # 骨盆主导；脊柱逐节反向并带相位延迟，胸腔再落后一点，形成「脊柱骨 + 中间帧」的顺动。
        self.rotate('下半身',(0,1,0),twist*pelvis_f*envelope)
        self.rotate('上半身',(1,0,0),(.045 if student else 0)+.003*breath+.02*envelope)
        self.rotate('上半身1',(0,1,0),.008*math.sin(TAU*t/6)*(1 if role=='teacher' else .4)
                    -twist*.75*pelvis_f*envelope)
        self.rotate('上半身2',(0,0,1),sway*.70*chest_f*envelope)
        idle=IDLE[self.cid]
        nod=.03*math.sin(TAU*t/5.2)+keyed_t(t,idle['pitch'])
        self.rotate('首',(1,0,0),nod)
        self.rotate('頭',(0,0,1),head_f*.35*sway*envelope+keyed_t(t,idle['yaw']))
        bpy.context.view_layer.update()
        rootq=Quaternion((0,0,1),yaw);rootpos=Vector((x,0,0))
        for side,sign in (('L',1),('R',-1)):
            rest=self.foot[side];target=rootpos+rootq@rest;fq=rootq.copy();planted=True
            if student:
                target=Vector((sign*(.105 if self.cid=='phainon' else .085)/self.scale,-.40/self.scale,rest.z))
            elif walk:
                start,base,direction=walk;elapsed=t-start
                first=0 if side=='L' else 1
                lastpos=base;nextpos=base
                for step in range(first,6,2):
                    begin=step*.5;end=begin+.5
                    landing=base+direction*min(1.1,(step+1)*.22)
                    if elapsed>=end:lastpos=landing;continue
                    if elapsed>=begin:
                        phase=(elapsed-begin)/.5
                        nextpos=lastpos+(landing-lastpos)*ease(phase)
                        target=Vector((nextpos,0,0))+rootq@rest
                        # 脚先提起，再沿弧线前送；落脚速度归零，支撑期保持世界位置。
                        target.z+=.055/self.scale*math.sin(math.pi*phase)**2
                        fq=rootq@Quaternion((1,0,0),.16*math.sin(TAU*phase)*math.sin(math.pi*phase))
                        planted=False
                    else:target=Vector((lastpos,0,0))+rootq@rest
                    break
                else:target=Vector((lastpos,0,0))+rootq@rest
            elif turn:
                begin,q0,q1,base=turn;u=(t-begin)*2-(0 if side=='R' else 1)
                u=max(0,min(1,u));phase=ease(u)
                qa=Quaternion((0,0,1),q0);qb=Quaternion((0,0,1),q1)
                target=Vector((base,0,0))+(qa@rest).lerp(qb@rest,phase)
                target.z+=.025/self.scale*math.sin(math.pi*u)**2;fq=qa.slerp(qb,phase)
                planted=u<=0 or u>=1
            m=Matrix.LocRotScale(target,fq@self.rest['足ＩＫ.'+side].to_quaternion(),Vector((1,1,1)))
            self.pb['足ＩＫ.'+side].matrix=m;self.changed.add('足ＩＫ.'+side)
        bpy.context.view_layer.update()
        errors=[]
        for side,sign in (('L',1),('R',-1)):
            shoulder=self.pb['腕.'+side].head.copy();local_shoulder=rootq.inverted()@(shoulder-rootpos) if role=='teacher' else shoulder
            l1,l2=self.lengths[side]
            if student:
                target=Vector((sign*.16/self.scale,-.38/self.scale,.885/self.scale))
                if side=='R':
                    writing=bell(t,4,8) if self.cid=='castor' else bell(t,9,15)
                    target.x+=.012/self.scale*math.sin(TAU*t*1.5)*writing
                    target.y+=.008/self.scale*math.sin(TAU*t*3)*writing
                if self.cid=='phainon' and side=='R':target.y-=.025/self.scale*bell(t,12,15);target.z+=.05/self.scale*bell(t,12,15)
            elif role=='assistant':
                target=Vector((sign*.115/self.scale,-.22/self.scale,shoulder.z-.28/self.scale))
                if side=='R':target.z+=.035/self.scale*bell(t,9,13)
            else:
                target=Vector((local_shoulder.x+sign*.02,local_shoulder.y-.02,local_shoulder.z-(l1+l2)*.96))
                gesture=0 if WALK_LIBRARY or walk or turn else bell(t,0,5)+bell(t,10,16)+bell(t,22,24)
                if side=='R':target=target.lerp(Vector((-.27/self.scale,-.30/self.scale,local_shoulder.z-.12/self.scale)),gesture*.9)
                if walk:
                    target.y+=sign*arm_swing/self.scale*math.sin(stride)*envelope
                    target.z+=.012/self.scale*(1-math.cos(stride))*envelope
            # 手势：在基础目标上叠加关键帧窗口，手势结束自然回到待机。
            g=gesture_at(self.cid,side,t)
            if g:
                kind,strength=g;off=GEST_OFFSETS[kind]
                base=local_shoulder if role=='teacher' else shoulder
                target=target.lerp(base+Vector(off),max(0.,min(1.,strength)))
            target=rootpos+rootq@target if role=='teacher' else target
            # 肘朝外且略靠后，保证二段链在同一解剖弯曲平面内。
            pole=shoulder+rootq@Vector((sign*.28,.10,-.24))
            errors.append(self.arm_to(side,target,pole))
            for p in self.pb:
                if p.name.endswith('.'+side) and ('指' in p.name or '小指' in p.name) and not p.name.startswith('_'):
                    self.rotate(p.name,(1,0,0),.12 if role=='teacher' else .08)
        bpy.context.view_layer.update()
        if max(errors)>.025:raise RuntimeError(f'{self.cid} 手臂解算误差 {max(errors)}')
        self.metrics.append(max(errors))
        for name in self.changed:
            p=self.pb[name]
            for channel in ('location','rotation_quaternion','scale'):p.keyframe_insert(data_path=channel)

bpy.context.preferences.filepaths.save_version=0
for cid in IDS:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/generated/{cid}.blend'))
    arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
    floor=min((o.matrix_world@Vector(c)).z for o in meshes for c in o.bound_box)
    height=max((o.matrix_world@Vector(c)).z for o in meshes for c in o.bound_box)-floor
    triangles=sum(len(o.data.polygons) for o in meshes)
    scene=bpy.context.scene;scene.render.fps=CFG['fps'];scene.frame_start=1;scene.frame_end=1+CFG['duration']*CFG['fps']
    performer=Performer(cid,arm,height)
    for frame in range(scene.frame_start,scene.frame_end+1):
        scene.frame_set(frame);performer.pose((frame-1)/CFG['fps'])
    arm.animation_data.action.name=CFG['characters'][cid]['clip']+'_Controls'
    bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm
    bpy.ops.nla.bake(frame_start=scene.frame_start,frame_end=scene.frame_end,step=1,only_selected=False,visual_keying=True,clear_constraints=True,use_current_action=False,bake_types={'POSE'})
    action=arm.animation_data.action;action.name=CFG['characters'][cid]['clip']
    for fc in action.layers[0].strips[0].channelbag(action.slots[0]).fcurves:
        for key in fc.keyframe_points:key.interpolation='LINEAR'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{cid}.blend'))
    for obj in meshes:obj.select_set(True)
    scene.frame_set(1)
    bpy.ops.export_scene.fbx(filepath=str(OUT/f'{cid}.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=.1,path_mode='COPY',embed_textures=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/f'{cid}.glb'),use_selection=True,export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=True,export_morph=True)
    sys.path.insert(0,str(ROOT/'blender'))
    from normalize_motion_glb import normalize
    normalize(OUT/f'{cid}.glb')
    blob=(OUT/f'{cid}.glb').read_bytes();length=struct.unpack_from('<I',blob,12)[0];gltf=json.loads(blob[20:20+length])
    exported=sum(gltf['accessors'][p['indices']]['count']//3 for m in gltf['meshes'] for p in m['primitives'])
    assert exported==triangles,'动画导出不可减少原面片'
    assert len(gltf.get('animations',[]))>=1,'没有导出动画'
    info={'id':cid,'status':'animated','clip':action.name,'duration':CFG['duration'],'rest_height':height,'rest_floor':floor,'target_height':CFG['characters'][cid]['height'],
      'triangles':triangles,'max_arm_target_error_m':max(performer.metrics),'bones':len(arm.data.bones),'animations':[a['name'] for a in gltf['animations']],
      'glb':str(OUT/f'{cid}.glb'),'fbx':str(OUT/f'{cid}.fbx')}
    (REPORT/f'{cid}.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CLASSROOM_ANIMATED',cid,flush=True)
