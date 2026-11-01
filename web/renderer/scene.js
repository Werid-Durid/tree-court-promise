import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {styleCharacter} from './character-style.js';

let active=null;
export function destroyScene(){active?.dispose();active=null;}
// 同一批 Blender 派生模型用于浏览器和 UE；渲染失败时保留课堂选择与存档。
export async function mountScene(container,{onStatus=()=>{}}={}){
 destroyScene();
 const scene=new THREE.Scene();scene.background=new THREE.Color('#152e29');scene.fog=new THREE.Fog('#152e29',17,45);
 const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
 renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.3;
 renderer.domElement.setAttribute('aria-label','可拖动视角的三维树庭课堂');container.prepend(renderer.domElement);
 const camera=new THREE.PerspectiveCamera(48,1,.05,80);camera.position.set(0,2.4,7.8);
 const controls=new OrbitControls(camera,renderer.domElement);controls.target.set(0,1.25,-1.2);controls.enableDamping=true;controls.minDistance=1.2;controls.maxDistance=16;controls.maxPolarAngle=Math.PI*.49;controls.minPolarAngle=.25;
 scene.add(new THREE.HemisphereLight(0xfff7df,0x364e40,2.4));
 const sun=new THREE.DirectionalLight(0xffe1aa,3.6);sun.position.set(-5,9,5);scene.add(sun);
 const fill=new THREE.DirectionalLight(0xb9e3df,1.5);fill.position.set(5,5,-7);scene.add(fill);
 const mats={stone:new THREE.MeshStandardMaterial({color:0xb3a98d,roughness:.94}),wood:new THREE.MeshStandardMaterial({color:0x563c29,roughness:.8}),gold:new THREE.MeshStandardMaterial({color:0xaa8b4b,roughness:.45,metalness:.3}),green:new THREE.MeshStandardMaterial({color:0x214b38,roughness:.9}),paper:new THREE.MeshStandardMaterial({color:0xdfd4ab,roughness:1})};
 function box(x,y,z,w,h,d,mat){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mats[mat]);m.position.set(x,y,z);scene.add(m);return m;}
 box(0,-.13,-1.6,16,.25,15,'stone');box(0,.08,-4.8,7,.18,3.2,'wood');box(0,2.25,-6.2,6.2,2.6,.16,'green');
 box(0,3.58,-6.1,6.4,.07,.2,'gold');box(0,.92,-6.1,6.4,.07,.2,'gold');
 for(const side of [-1,1]){
  for(let z=-6;z<=5;z+=3.5){const column=new THREE.Mesh(new THREE.CylinderGeometry(.24,.32,4.5,18),mats.stone);column.position.set(side*6.8,2.15,z);scene.add(column);box(side*6.8,4.42,z,.85,.18,.85,'gold');}
  for(let z=-4.8;z<=3;z+=3.2){for(let y=.45;y<3;y+=.8){box(side*7.2,y,z,.65,.08,2.7,'wood');for(let n=0;n<9;n++)box(side*7.2,y+.29,z-1.12+n*.27,.38,.48,.14,n%3?'green':'paper');}}
 }
 for(const z of [0,2.7])for(const x of [-2.7,.6]){box(x,.78,z,2.2,.13,1.2,'wood');for(const dx of [-.85,.85])box(x+dx,.37,z,.08,.72,.85,'gold');box(x,.859,z,.5,.018,.65,'paper');}
 // 椅子朝向黑板；座面 48 cm，与动画里的髋、膝、脚底目标共同标定。
 for(const [x,z]of [[.6,.98],[-2.7,3.68]]){
  box(x,.44,z,.48,.08,.46,'wood');box(x,.78,z+.24,.48,.60,.06,'wood');
  for(const dx of [-.19,.19])for(const dz of [-.16,.16])box(x+dx,.21,z+dz,.045,.42,.045,'gold');
 }
 box(-.15,.75,-4.3,.9,1.35,.7,'wood');
 const boardCanvas=document.createElement('canvas');boardCanvas.width=1536;boardCanvas.height=640;const ctx=boardCanvas.getContext('2d');
 const boardTexture=new THREE.CanvasTexture(boardCanvas);boardTexture.colorSpace=THREE.SRGBColorSpace;
 const board=new THREE.Mesh(new THREE.PlaneGeometry(5.8,2.4),new THREE.MeshBasicMaterial({map:boardTexture}));board.position.set(0,2.25,-6.105);scene.add(board);
 function writeBoard(word='TREE COURT',line='在理解之前，先把问题说清楚。'){
  ctx.fillStyle='#214b38';ctx.fillRect(0,0,1536,640);ctx.fillStyle='#b6c399';ctx.font='25px sans-serif';ctx.fillText('神悟树庭  /  阿那克萨戈拉斯的课堂',80,75);ctx.fillStyle='#f0e1b0';ctx.font='100px Georgia';ctx.fillText(word,80,235);ctx.font='31px "Microsoft YaHei",sans-serif';let row='',y=345;for(const c of line){if(ctx.measureText(row+c).width>1350){ctx.fillText(row,80,y);row='';y+=53;}row+=c;}ctx.fillText(row,80,y);ctx.font='22px sans-serif';ctx.fillStyle='#c1caa7';ctx.fillText('观察  →  辨析  →  用自己的话解释',80,565);boardTexture.needsUpdate=true;
 }
 writeBoard();
 const loaded=new Map(),mixers=new Map(),loader=new GLTFLoader(),positions={anaxa:[-1.8,.18,-4.95],hyacine:[2.5,.18,-4.9],castor:[.6,0,.98],phainon:[-2.7,0,3.68]};
 let motion={characters:{}};try{motion=await(await fetch('/api/animation-status')).json();}catch{}
 const frameClock=new THREE.Clock();let disposed=false,raf,speaker='anaxa';
 function resize(){const {width,height}=container.getBoundingClientRect();if(!width||!height)return;renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();}
 const resizeObserver=new ResizeObserver(resize);resizeObserver.observe(container);resize();
 function animate(){if(disposed)return;raf=requestAnimationFrame(animate);const dt=Math.min(frameClock.getDelta(),.1),t=frameClock.elapsedTime;controls.update();for(const mixer of mixers.values())mixer.update(dt);for(const [id,root]of loaded){root.traverse(o=>{if(!o.morphTargetDictionary)return;for(const [name,index]of Object.entries(o.morphTargetDictionary)){if(/まばたき|blink|眨眼/i.test(name))o.morphTargetInfluences[index]=(t%5.7)<.13?.8:0;if(/^(あ|a|口あ)$/i.test(name))o.morphTargetInfluences[index]=id===speaker&&window.speechSynthesis?.speaking?Math.max(0,Math.sin(t*16))*.25:0;}});}renderer.render(scene,camera);}
 animate();
 active={dispose(){disposed=true;cancelAnimationFrame(raf);resizeObserver.disconnect();controls.dispose();for(const [id,mixer]of mixers){mixer.stopAllAction();mixer.uncacheRoot(loaded.get(id));}scene.traverse(o=>{o.geometry?.dispose();const ms=Array.isArray(o.material)?o.material:[o.material];for(const m of ms){if(!m)continue;for(const v of Object.values(m))if(v?.isTexture)v.dispose();m.dispose();}});renderer.dispose();renderer.domElement.remove();},update({word,line,character='anaxa'}){speaker=character;writeBoard(word,line);},view(id){const poses={classroom:[[0,2.4,7.8],[0,1.25,-1.2]],teacher:[[-1.3,1.9,-.6],[-1.3,1.3,-4.95]],assistant:[[2.5,1.9,-.7],[2.5,1.25,-4.9]],classmates:[[3.4,1.9,2.5],[-.4,.9,1.4]]};const pose=poses[id]||poses.classroom;camera.position.fromArray(pose[0]);controls.target.fromArray(pose[1]);controls.update();}};
 const api=active;
 (async()=>{for(const [i,id]of Object.keys(positions).entries()){
   if(disposed)break;onStatus(`正在请${{anaxa:'那刻夏老师',hyacine:'风堇助教',castor:'遐蝶同学',phainon:'白厄同学'}[id]}入座 · ${i+1}/4`);
   try{const gltf=await loader.loadAsync(`/models/${id}.glb`);if(disposed){gltf.scene.traverse(o=>o.geometry?.dispose());break;}
    const model=gltf.scene,bounds=new THREE.Box3().setFromObject(model),size=bounds.getSize(new THREE.Vector3()),spec=motion.characters[id];
    model.scale.setScalar(spec?.available?spec.height/spec.rest_height:(id==='hyacine'?1.6:1.78)/size.y);
    const scaled=new THREE.Box3().setFromObject(model),pos=spec?.position||positions[id];model.position.set(pos[0],pos[1]-(spec?.available?(spec.rest_floor||0)*model.scale.x:Math.min(0,scaled.min.y)),pos[2]);model.rotation.y=spec?.yaw||0;
    // 保留 GLB 中的正反面设置；透明覆盖层不写深度，防止共面层互相挖空。
    styleCharacter(model,id,renderer);scene.add(model);loaded.set(id,model);
    const clip=gltf.animations.find(c=>c.name===spec?.clip);
    if(clip){const mixer=new THREE.AnimationMixer(model);mixer.clipAction(clip).play();mixer.update(0);mixers.set(id,mixer);model.userData.motion=clip.name;}
   }catch(error){onStatus(`${id} 模型暂未载入，课堂可继续`);console.warn('TreeCourt model load:',id,error.message);}
  }if(!disposed){container.dataset.animated=String(mixers.size);onStatus(`3D 课堂 · ${loaded.size}/4 位角色已到场 · ${mixers.size}/4 位角色动作已载入 · 拖动看向四周`);}
 })();
 return api;
}
