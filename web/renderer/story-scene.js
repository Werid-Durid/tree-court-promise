import {ROOM_SCALE,FRONT_X,BOARD_WIDTH,BOARD_HEIGHT,BOARD_X,BOARD_Y,BOARD_Z,characterPosition,compactPoint,upgradeRoom,addExterior} from './classroom-upgrade.mjs';
import {legDeformFollower,deskHandContact} from './deform-contact.js';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {styleCharacter} from './character-style.js';
import performanceProfile from '../../blender/classroom_performance.json';
import {firstPerson} from './first-person.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {BokehPass} from 'three/addons/postprocessing/BokehPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
let active;
export function destroyScene(){active?.dispose();active=null;}
export async function mountScene(container,{onStatus=()=>{},onInteract=()=>{},onMode=()=>{},quiet=false,walkPreview=false}={}){
 destroyScene();let disposed=false,raf,speaker='anaxa',speaking=false,level=null,emotion='neutral',motionPaused=false;
 const scene=new THREE.Scene();scene.background=new THREE.Color('#e9d9bd');scene.fog=new THREE.Fog('#e9d9bd',16,42);
 const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.12;
 renderer.domElement.setAttribute('aria-label','第一人称树庭课堂，WASD移动，鼠标观察，E交谈');renderer.domElement.tabIndex=0;container.prepend(renderer.domElement);
 // 挂载尚未结束也可取消，避免快速切页遗留画布和 GPU 资源。
 active={dispose(){disposed=true;renderer.dispose();renderer.domElement.remove();}};
 const camera=new THREE.PerspectiveCamera(68,1,.05,60);
 const composer=new EffectComposer(renderer);composer.addPass(new RenderPass(scene,camera));
 const dof=new BokehPass(scene,camera,{focus:4,aperture:.000035,maxblur:.004});composer.addPass(dof);composer.addPass(new OutputPass());
 scene.add(new THREE.HemisphereLight(0xfff3e0,0x8a9a86,1.9));const sun=new THREE.DirectionalLight(0xffd39a,3.3);sun.position.set(-7,6.5,2);scene.add(sun);const fill=new THREE.DirectionalLight(0xbfd4ff,.7);fill.position.set(5,3,-3);scene.add(fill);
 const loader=new GLTFLoader(),loaded=new Map(),mixers=new Map(),faces=new Map(),heads=new Map(),fronts=new Map(),legFollowers=new Map(),handContacts=new Map();
 const [layout,motion]=await Promise.all([fetch('/environment/layout.json').then(r=>{if(!r.ok)throw Error('教室布局尚未生成');return r.json();}),fetch('/api/animation-status'+(walkPreview?'?motion=walk':'')).then(r=>r.json())]);
 if(disposed)return null;
 const room=await loader.loadAsync('/environment/story_classroom.glb');if(disposed)return;scene.add(room.scene);
 const door=walkPreview?null:upgradeRoom(THREE,room.scene,layout);if(!walkPreview)addExterior(THREE,room.scene);
 const doorButton=document.createElement('button');doorButton.type='button';doorButton.textContent='打开教室门';doorButton.style.cssText='position:absolute;right:18px;bottom:24px;z-index:5;padding:10px 16px;border:1px solid #bfa784;border-radius:10px;background:#fff5e4;color:#51432e;cursor:pointer';doorButton.hidden=!door;container.append(doorButton);
 function toggleDoor(){door?.toggle();doorButton.textContent=door?.open?'关闭教室门':'打开教室门';container.dataset.doorOpen=String(!!door?.open);}
 doorButton.addEventListener('click',toggleDoor);
 function clickDoor(ev){if(!door)return;const r=renderer.domElement.getBoundingClientRect(),v=document.pointerLockElement===renderer.domElement?new THREE.Vector2():new THREE.Vector2((ev.clientX-r.left)/r.width*2-1,-(ev.clientY-r.top)/r.height*2+1),ray=new THREE.Raycaster();ray.setFromCamera(v,camera);const hits=ray.intersectObject(room.scene,true);if(hits[0]&&door.parts.some(p=>p===hits[0].object))toggleDoor();}
 renderer.domElement.addEventListener('click',clickDoor);
 if(walkPreview){room.scene.visible=false;layout.player_start=[.5,1.35,4.6];layout.eye_height=1.35;layout.field_of_view=50;layout.colliders=[];const floor=new THREE.Mesh(new THREE.PlaneGeometry(30,30),new THREE.MeshStandardMaterial({color:0xb8c7bc,roughness:1}));floor.rotation.x=-Math.PI/2;scene.add(floor);scene.add(new THREE.GridHelper(30,30,0x759182,0x94ab9d));}
 const player=firstPerson(camera,renderer.domElement,layout,{onInteract:()=>{if(door&&player.position.distanceTo(door.pivot.getWorldPosition(new THREE.Vector3()))<2.6){toggleDoor();return;}let best=null,dist=3.3;for(const [id,root]of loaded){const p=heads.get(id)?.getWorldPosition(new THREE.Vector3())||root.getWorldPosition(new THREE.Vector3());p.y=1.65;const d=p.distanceTo(player.position);if(d<dist){dist=d;best=id;}}onInteract(best);},onMode,getObstacles:()=>[...heads.entries()].map(([id,head])=>{const p=head.getWorldPosition(new THREE.Vector3());return {center:[p.x,.9,p.z],size:[id==='hyacine'?.62:.72,1.8,.72]};})});
 function faceTarget(id){const root=loaded.get(id);if(!root)return new THREE.Vector3(0,1.6,-4.8);root.updateMatrixWorld(true);return heads.get(id)?.getWorldPosition(new THREE.Vector3())||root.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0,1.4,0));}
 function focus(id){speaker=id;container.dataset.speaker=id;player.focus(()=>faceTarget(id),()=>fronts.get(id));}
 // 动态粉笔层位于实体黑板前，避免 z-fighting；不覆盖木框与托槽。
 const boardCanvas=document.createElement('canvas');boardCanvas.width=1536;boardCanvas.height=640;const ctx=boardCanvas.getContext('2d');const texture=new THREE.CanvasTexture(boardCanvas);texture.colorSpace=THREE.SRGBColorSpace;
 const board=new THREE.Mesh(new THREE.PlaneGeometry(BOARD_WIDTH,BOARD_HEIGHT),new THREE.MeshBasicMaterial({map:texture}));board.position.set(BOARD_X,BOARD_Y,BOARD_Z+.025);scene.add(board);
 if(walkPreview)board.visible=false;
 function writeBoard(word,line){ctx.fillStyle='#254e3b';ctx.fillRect(0,0,1536,640);ctx.fillStyle='#dddabb';ctx.font='26px sans-serif';ctx.fillText('神悟树庭  /  今日的思考',64,65);ctx.font='100px Georgia';ctx.fillStyle='#faf0ce';ctx.fillText(word||'TREE COURT',64,230);ctx.font='32px Microsoft YaHei';let row='',y=340;for(const c of line||'观察，追问，再用自己的话解释。'){if(ctx.measureText(row+c).width>1370){ctx.fillText(row,64,y);row='';y+=55;}row+=c;}ctx.fillText(row,64,y);ctx.strokeStyle='#c0d0ad88';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(64,530);ctx.lineTo(1450,530);ctx.stroke();ctx.font='25px sans-serif';ctx.fillText('思考 → 联想 → 理解',64,585);texture.needsUpdate=true;}
 writeBoard(quiet?'QUIET STUDY':null,quiet?'留一点空白，给专注，也给自己。':null);
 // 暖色窗光使用透明地面投影，不改变角色原有材质和肤色。
 const sunlight=new THREE.MeshBasicMaterial({color:0xffe8b2,transparent:true,opacity:.17,depthWrite:false});
 for(const z of [-3.8,0,3.8])for(const dz of [-.55,.55]){const patch=new THREE.Mesh(new THREE.PlaneGeometry(3.9,.90),sunlight);patch.rotation.x=-Math.PI/2;patch.rotation.z=-.25;patch.position.set(-4.7*ROOM_SCALE,.012,(z+dz)*ROOM_SCALE);patch.scale.setScalar(ROOM_SCALE);scene.add(patch);}
  // 空气中的暖色尘埃：弱化空旷感，也呼应窗外光柱。
  const dust=(()=>{const N=120,pos=new Float32Array(N*3);for(let i=0;i<N;i++){pos[i*3]=-6+Math.random()*8.2;pos[i*3+1]=.3+Math.random()*2.7;pos[i*3+2]=-6+Math.random()*12;}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));const m=new THREE.PointsMaterial({color:0xfff1cf,size:.014,transparent:true,opacity:.45,blending:THREE.AdditiveBlending,depthWrite:false});const pts=new THREE.Points(g,m);scene.add(pts);return{pts,N};})();
 function resize(){const {width,height}=container.getBoundingClientRect();if(!width||!height)return;renderer.setSize(width,height,false);composer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();}const observer=new ResizeObserver(resize);observer.observe(container);resize();
 // 全屏与设备旋转时同步绘制缓冲区，避免只放大外壳而留下空白。
 const resizeViewport=()=>requestAnimationFrame(()=>{if(!disposed)resize();});
 document.addEventListener('fullscreenchange',resizeViewport);window.addEventListener('resize',resizeViewport);
 const clock=new THREE.Clock();function animate(){if(disposed)return;raf=requestAnimationFrame(animate);const dt=Math.min(clock.getDelta(),.06),t=clock.elapsedTime;
  door?.update(dt);for(const [id,m] of mixers){if(quiet){const pace=id==='anaxa'?.15:.28;m.setTime(2.1+.08*Math.sin(t*pace));}else if(!motionPaused)m.update(dt);}
  for(const follow of legFollowers.values())follow();
  for(const contact of handContacts.values())contact();
  const amplitude=speaking?(level?level():.2+.18*Math.sin(t*17)):0;
  for(const [id,list]of faces){const offset={anaxa:0,hyacine:1.1,castor:2.4,phainon:3.3}[id],profile=performanceProfile[id];const blink=(t+offset)%profile.blink_period;for(const o of list){for(const [name,index]of Object.entries(o.morphTargetDictionary)){
   if(/まばたき|blink|眨眼/i.test(name))o.morphTargetInfluences[index]=blink<profile.blink_duration?Math.sin(blink/profile.blink_duration*Math.PI)*.9:0;
   if(/^(あ|a|口あ)$/i.test(name))o.morphTargetInfluences[index]=id===speaker?Math.min(profile.mouth_limit,amplitude*1.7):0;
   if(/^(笑い|笑|にこり|喜び|口角上げ|慈愛)$/i.test(name))o.morphTargetInfluences[index]=id===speaker&&emotion==='warm'?profile.warm_smile:0;
    if(/^(悲しい|sad|泣き)$/i.test(name))o.morphTargetInfluences[index]=id===speaker&&emotion==='sad'?profile.sad_face:0;
    if(/^涙$/i.test(name))o.morphTargetInfluences[index]=id===speaker&&emotion==='sad'?profile.tears:0;
    if(/^口角下げ$/i.test(name))o.morphTargetInfluences[index]=id===speaker&&emotion==='sad'?profile.sad_mouth:0;
  }}}
  player.update(dt);
  const dp=dust.pts.geometry.attributes.position.array;
  for(let i=0;i<dust.N;i++){dp[i*3+1]+=dt*.05;dp[i*3]+=Math.sin(t*.4+i)*.0012;if(dp[i*3+1]>3.1)dp[i*3+1]=.25;}
  dust.pts.geometry.attributes.position.needsUpdate=true;
  // 以当前动画为底，有限角度地转头回应玩家；不会让脖颈追随镜头无限扭转。
  const head=heads.get(speaker),root=loaded.get(speaker);
  if(head&&root&&!player.walking&&!quiet&&!walkPreview){root.updateMatrixWorld(true);const local=root.worldToLocal(player.position.clone()),headLocal=root.worldToLocal(head.getWorldPosition(new THREE.Vector3()));const d=local.sub(headLocal);const angle=THREE.MathUtils.clamp(Math.atan2(d.x,d.z),-performanceProfile[speaker].head_yaw,performanceProfile[speaker].head_yaw);head.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),angle*.7));}
  dof.enabled=!player.walking&&!quiet&&!walkPreview;dof.uniforms.focus.value=camera.position.distanceTo(faceTarget(speaker));composer.render(dt);
 }animate();
 const api={setMotionTime(seconds){for(const m of mixers.values())m.setTime(seconds);},pauseMotion(value){motionPaused=value;},update({word,line,character='anaxa'}){writeBoard(word,line);focus(character);},focus,
  speech(id,value,getLevel=null,mood='neutral'){speaker=id;speaking=value;level=getLevel;emotion=mood;if(value)focus(id);},walk(){speaking=false;player.mode(true);},moveInput:(code,pressed)=>player.moveInput(code,pressed),
  view(id){if(id==='classroom')player.mode(true);else focus({teacher:'anaxa',assistant:'hyacine',classmates:'castor'}[id]||id);},
  dispose(){disposed=true;cancelAnimationFrame(raf);observer.disconnect();doorButton.remove();renderer.domElement.removeEventListener('click',clickDoor);document.removeEventListener('fullscreenchange',resizeViewport);window.removeEventListener('resize',resizeViewport);player.dispose();for(const m of mixers.values()){m.stopAllAction();m.uncacheRoot(m.getRoot());}scene.traverse(o=>{o.geometry?.dispose();for(const mat of Array.isArray(o.material)?o.material:[o.material]){if(!mat)continue;for(const value of Object.values(mat))if(value?.isTexture)value.dispose();mat.dispose();}});dof.dispose();composer.dispose();renderer.dispose();renderer.domElement.remove();}
 };active=api;
 (async()=>{for(const [id,spec]of Object.entries(motion.characters)){
  if(disposed)break;onStatus(`正在邀请${{anaxa:'那刻夏老师',hyacine:'风堇助教',castor:'遐蝶同学',phainon:'白厄同学'}[id]}进入教室…`);
  try{const gltf=await loader.loadAsync(`/models/${id}.glb${walkPreview?'?motion=walk':''}`);if(disposed)break;const root=gltf.scene;root.scale.setScalar(spec.height/spec.rest_height);root.position.set(...(walkPreview?spec.position:characterPosition(id,spec.position)));root.position.y-=(spec.rest_floor||0)*root.scale.x;root.rotation.y=spec.yaw;fronts.set(id,new THREE.Vector3(0,0,1).applyQuaternion(root.quaternion).normalize());styleCharacter(root,id,renderer);scene.add(root);loaded.set(id,root);legFollowers.set(id,legDeformFollower(root));
   if(!walkPreview&&spec.role==='student')handContacts.set(id,deskHandContact(root,.915));
   const list=[];root.traverse(o=>{if(o.morphTargetDictionary)list.push(o);if(o.isBone&&o.name==='頭')heads.set(id,o);});faces.set(id,list);
   const clip=gltf.animations.find(c=>c.name===spec.clip);if(clip){const mixer=new THREE.AnimationMixer(root);mixer.clipAction(clip).play();mixers.set(id,mixer);}
  }catch(e){console.warn('角色载入失败',id,e.message);}
 }if(!disposed){container.dataset.animated=String(mixers.size);container.dataset.ready='true';onStatus(`${walkPreview?'步态预览':'3D 课堂'} · ${loaded.size}/4 位角色已到场`);if(walkPreview){for(const m of mixers.values())m.setTime(6);}else if(!quiet&&!player.walking)focus(speaker);}})();
 if(quiet){player.mode(false);container.dataset.quiet='true';}
 return api;
}


