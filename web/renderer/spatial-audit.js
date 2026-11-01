import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {legDeformFollower,deskHandContact} from './deform-contact.js';
// 对发布的 GLB 实际蒙皮求值；只测脚部，不把头发、裙摆包围盒当作落地高度。
export async function auditActors({modes=['classroom','study','walk','outing'],repair=true,animationSource=null}={}){
 const loader=new GLTFLoader(),report=[];
 for(const mode of modes){
  const motion=await (await fetch('/api/animation-status?motion='+(mode==='outing'?'walk':mode))).json();
  for(const [id,spec] of Object.entries(motion.characters)){
   const gltf=await loader.loadAsync('/models/'+id+'.glb?motion='+(mode==='outing'?'walk':mode)),root=gltf.scene;
   const outingLayout=mode==='outing'?await(await fetch('/outing-assets/'+({anaxa:'grove',hyacine:'courtyard',castor:'terrace',phainon:'wheat'}[id])+'.json')).json():null;
   root.scale.setScalar(spec.height/spec.rest_height);root.position.set(...(mode==='outing'?outingLayout.character_position:spec.position));root.position.y-=(spec.rest_floor||0)*root.scale.x;root.rotation.y=mode==='outing'?0:spec.yaw;
   const motionAsset=animationSource?await loader.loadAsync(animationSource+'/'+mode+'/'+id+'.glb'):gltf;
   const mixer=new THREE.AnimationMixer(root),clip=motionAsset.animations.find(c=>c.name===spec.clip);if(!clip)throw Error(mode+'/'+id+' 缺少指定动画 '+spec.clip);mixer.clipAction(clip).play();
   const feet=[],joints={};root.traverse(o=>{
    if(o.isBone&&/足首|手首|ひざ|下半身|^頭$/.test(o.name))joints[o.name]=o;
    if(!o.isSkinnedMesh)return;const a=o.geometry.attributes,indices=[];
    for(let i=0;i<a.position.count;i++)for(let j=0;j<4;j++)if(a.skinWeight.getComponent(i,j)>.3&&/足首|つま先|ankle|toe/i.test(o.skeleton.bones[a.skinIndex.getComponent(i,j)]?.name||'')){indices.push(i);break;}
    if(indices.length)feet.push({mesh:o,indices});
   });
   const room=mode==='classroom'||mode==='study'?await (await fetch(mode==='study'?'/environment/study_room_layout.json':'/environment/layout.json')).json():null;
   const furniture=(room?.colliders||[]).filter(c=>/Desk|Chair|Lectern/.test(c.name)&&Math.abs(c.center[0]-spec.position[0])<1.5&&Math.abs(c.center[2]-spec.position[2])<1.5),penetrations={};
   const follow=repair?legDeformFollower(root):()=>{},hands=repair&&mode==='classroom'&&spec.role==='student'?deskHandContact(root,.915):()=>{},frames=[],times=mode==='outing'?[.075,.1,.125]:[0,3,6,9,12,15,18,21,23.8];
   for(const t of times){mixer.setTime(t);follow();hands();root.updateMatrixWorld(true);root.traverse(o=>{if(o.isSkinnedMesh)o.skeleton.update();});const b=new THREE.Box3(),v=new THREE.Vector3();
    for(const {mesh,indices}of feet)for(const i of indices){mesh.getVertexPosition(i,v);v.applyMatrix4(mesh.matrixWorld);b.expandByPoint(v);}
    if([0,12,23.8].includes(t)&&furniture.length)root.traverse(mesh=>{if(!mesh.isSkinnedMesh)return;for(let i=0;i<mesh.geometry.attributes.position.count;i+=3){mesh.getVertexPosition(i,v);v.applyMatrix4(mesh.matrixWorld);for(const c of furniture){const depth=Math.min(...[v.x,v.y,v.z].map((x,j)=>c.size[j]/2-Math.abs(x-c.center[j])));if(depth>.02){const key=c.name+'@'+c.center.join(',');const item=penetrations[key]||={name:c.name,center:c.center,samples:0,max_depth:0};item.samples++;item.max_depth=Math.max(item.max_depth,depth);}}}});
    frames.push({time:t,foot_min_y:b.isEmpty()?null:b.min.y,foot_max_y:b.isEmpty()?null:b.max.y,joints:Object.fromEntries(Object.entries(joints).map(([k,b])=>[k,b.getWorldPosition(new THREE.Vector3()).toArray()]))});
   }
   report.push({mode,id,height:spec.height,floor:mode==='outing'?outingLayout.character_position[1]:spec.position[1],foot_vertices:feet.reduce((n,x)=>n+x.indices.length,0),frames,penetrations:Object.values(penetrations)});
   mixer.stopAllAction();root.traverse(o=>{o.geometry?.dispose();for(const m of Array.isArray(o.material)?o.material:[o.material]){if(!m)continue;for(const v of Object.values(m))if(v?.isTexture)v.dispose();m.dispose();}});
  }
 }
 return report;
}
