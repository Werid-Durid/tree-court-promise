import * as THREE from 'three';
// MMD 的 D 腿骨是变形跟随骨。部分 glTF 动作遗漏了其复制变换约束，需在采样后同步。
export function legDeformFollower(root){
 const bones=new Map(),bindInverse=new Map();root.traverse(o=>{if(o.isBone)bones.set(o.name,o);if(o.isSkinnedMesh)o.skeleton.bones.forEach((b,i)=>bindInverse.set(b,o.skeleton.boneInverses[i]));});const links=[];
 for(const stem of ['足','ひざ','足首'])for(const side of ['L','R']){
  const target=bones.get(stem+'D'+side),source=bones.get(stem+side);if(target&&source){const offset=bindInverse.has(source)&&bindInverse.has(target)?new THREE.Matrix4().multiplyMatrices(bindInverse.get(source),bindInverse.get(target).clone().invert()):new THREE.Matrix4();links.push({target,source,offset});}
 }
 const inverse=new THREE.Matrix4(),local=new THREE.Matrix4();
 return ()=>{root.updateMatrixWorld(true);for(const {target,source,offset}of links){source.updateWorldMatrix(true,false);target.parent.updateWorldMatrix(true,false);inverse.copy(target.parent.matrixWorld).invert();local.multiplyMatrices(inverse,source.matrixWorld).multiply(offset);local.decompose(target.position,target.quaternion,target.scale);target.updateMatrixWorld(true);}};
}
// 手腕接触桌面时使用两段骨链旋转解算，保留上臂与前臂长度，不把手网格直接拉长。
export function deskHandContact(root,height){
 const bones=new Map();root.traverse(o=>{if(o.isBone)bones.set(o.name,o);});
 const q=new THREE.Quaternion(),parentQ=new THREE.Quaternion(),worldQ=new THREE.Quaternion();
 function aim(bone,end,target){const start=bone.getWorldPosition(new THREE.Vector3()),a=end.clone().sub(start).normalize(),b=target.clone().sub(start).normalize();bone.getWorldQuaternion(worldQ);q.setFromUnitVectors(a,b).multiply(worldQ);bone.parent.getWorldQuaternion(parentQ);bone.quaternion.copy(parentQ.invert().multiply(q));bone.updateMatrixWorld(true);}
 return ()=>{root.updateMatrixWorld(true);for(const side of ['L','R']){
  const upper=bones.get('腕'+side),elbow=bones.get('ひじ'+side),hand=bones.get('手首'+side);if(!upper||!elbow||!hand)continue;
  const a=upper.getWorldPosition(new THREE.Vector3()),b=elbow.getWorldPosition(new THREE.Vector3()),c=hand.getWorldPosition(new THREE.Vector3());if(c.y>=height)continue;
  const target=c.clone();target.y=height;const handQ=hand.getWorldQuaternion(new THREE.Quaternion()),l1=a.distanceTo(b),l2=b.distanceTo(c),direction=target.clone().sub(a),length=Math.min(direction.length(),l1+l2-.0001);direction.normalize();target.copy(a).addScaledVector(direction,length);
  const along=(l1*l1-l2*l2+length*length)/(2*length),bend=b.clone().sub(a).addScaledVector(direction,-b.clone().sub(a).dot(direction));if(bend.length()<.00001)bend.set(side==='L'?1:-1,0,0);bend.normalize();const knee=a.clone().addScaledVector(direction,along).addScaledVector(bend,Math.sqrt(Math.max(0,l1*l1-along*along)));
  aim(upper,b,knee);elbow.updateWorldMatrix(true,true);aim(elbow,hand.getWorldPosition(new THREE.Vector3()),target);hand.parent.getWorldQuaternion(parentQ);hand.quaternion.copy(parentQ.invert().multiply(handQ));hand.updateMatrixWorld(true);
 }};
}
