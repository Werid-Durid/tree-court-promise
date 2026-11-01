import {legDeformFollower} from './deform-contact.js';
import * as THREE from 'three';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {styleCharacter} from './character-style.js';
import {firstPerson} from './first-person.js';
// 邀约使用独立舞台：只加载选择的角色，避免课堂坐姿或走位轨道穿过道具。
export async function mountOuting(host,{character,scene:kind,onStatus=()=>{}}){
 let disposed=false,raf,player,root,resizeObserver,mixer,head,followLegs;const faces=[];
 const scene=new THREE.Scene(),night=kind==='terrace';scene.background=new THREE.Color(night?'#7a80a3':kind==='wheat'?'#dbb780':'#c6d8ca');scene.fog=new THREE.Fog(scene.background,kind==='wheat'?65:18,kind==='wheat'?400:70);
 const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(host.clientWidth,host.clientHeight);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;host.append(renderer.domElement);
 const camera=new THREE.PerspectiveCamera(50,1,.05,600),loader=new GLTFLoader();const draco=new DRACOLoader().setDecoderPath('/static/draco/');loader.setDRACOLoader(draco);scene.add(new THREE.HemisphereLight(night?0xd7dcff:0xfff1d2,0x657257,2));const sun=new THREE.DirectionalLight(night?0xd3caff:0xffddb5,2.2);sun.position.set(-4,6,4);scene.add(sun);
 const clock=new THREE.Clock();let talking=false;
 const api={walk(){player?.mode(true);},focus(){player?.focus(()=>head?.getWorldPosition(new THREE.Vector3())||new THREE.Vector3(0,1.4,0),()=>new THREE.Vector3(0,0,1));},speech(value){talking=value;},dispose(){disposed=true;cancelAnimationFrame(raf);resizeObserver?.disconnect();player?.dispose();scene.traverse(o=>{o.geometry?.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material]){if(!m)continue;for(const v of Object.values(m))if(v?.isTexture)v.dispose();m.dispose();}});draco.dispose();renderer.dispose();renderer.domElement.remove();}};
 function render(){if(disposed)return;raf=requestAnimationFrame(render);const t=clock.getElapsedTime();if(mixer)mixer.setTime(.1+.025*Math.sin(t*.7));followLegs?.();for(const o of faces)for(const [name,i]of Object.entries(o.morphTargetDictionary)){if(/blink|まばたき|眨眼/i.test(name))o.morphTargetInfluences[i]=(t%5.3)<.18?Math.sin(t%5.3/.18*Math.PI)*.8:0;if(/^(あ|a|口あ)$/i.test(name))o.morphTargetInfluences[i]=talking?.12+.1*Math.sin(t*14):0;}player?.update(.016);renderer.render(scene,camera);}render();
 try{
  onStatus('正在准备这次邀约…');const [room,layout,motion]=await Promise.all([loader.loadAsync('/outing-assets/'+kind+'.glb'+(kind==='wheat'?'?v=4':'')),fetch('/outing-assets/'+kind+'.json'+(kind==='wheat'?'?v=4':'')).then(r=>r.json()),fetch('/api/animation-status?motion=walk').then(r=>r.json())]);if(disposed){api.dispose();return api;}room.scene.traverse(o=>{if(o.name==='Elysia_Sky')for(const m of Array.isArray(o.material)?o.material:[o.material])if(m){m.fog=false;m.toneMapped=false;};});scene.add(room.scene);
  const gltf=await loader.loadAsync('/models/'+character+'.glb?motion=walk');if(disposed){api.dispose();return api;}root=gltf.scene;const spec=motion.characters[character];root.scale.setScalar(spec.height/spec.rest_height);root.position.set(...(layout.character_position||[0,0,0]));root.position.y-=(spec.rest_floor||0)*root.scale.x;styleCharacter(root,character,renderer);scene.add(root);followLegs=legDeformFollower(root);
  const clip=gltf.animations.find(c=>c.name===spec.clip);if(clip){mixer=new THREE.AnimationMixer(root);mixer.clipAction(clip).play();mixer.setTime(.1);}root.traverse(o=>{if(o.morphTargetDictionary)faces.push(o);if(o.isBone&&o.name==='頭')head=o;});root.updateMatrixWorld(true);
  player=firstPerson(camera,renderer.domElement,layout,{getObstacles:()=>[{center:[0,.9,0],size:[.8,1.8,.8]}]});api.focus();
  resizeObserver=new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();});resizeObserver.observe(host);host.dataset.ready='true';onStatus('场景已就绪 · '+({grove:'阅览回廊',courtyard:'天井茶座',terrace:'蝶影露台',wheat:'哀丽秘榭 · 麦田'}[kind]));
 }catch(e){onStatus('场景暂不可用，文字邀约仍可继续');console.warn(e.message);}return api;
}
