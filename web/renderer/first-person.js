import * as THREE from 'three';
// 玩家位置独立于剧情镜头。对话只改变视线和焦距，不传送身体。
export function firstPerson(camera,canvas,layout,{onInteract=()=>{},onMode=()=>{},getObstacles=()=>[]}={}){
 const keys=new Set(),position=new THREE.Vector3(...layout.player_start),velocity=new THREE.Vector3();
 let yaw=0,pitch=0,walking=false,focus=null,focusFront=null,drag=null,disposed=false;
 const limits=layout.bounds,radius=layout.radius||.24;
 function groundAt(x,z){
  return Math.max(layout.ground_height||0,...(layout.walkable_surfaces||[]).filter(s=>Math.abs(x-s.center[0])<=s.size[0]/2&&Math.abs(z-s.center[2])<=s.size[2]/2).map(s=>s.center[1]+s.size[1]/2));
 }
 function blocked(x,z){
  if(x<limits[0]||x>limits[1]||z<limits[2]||z>limits[3])return true;
  const floor=groundAt(x,z);
  return [...layout.colliders,...getObstacles()].some(c=>c.center[1]+c.size[1]/2>floor+.04&&c.center[1]-c.size[1]/2<floor+(layout.eye_height??1.65)+.1&&Math.abs(x-c.center[0])<c.size[0]/2+radius&&Math.abs(z-c.center[2])<c.size[2]/2+radius);
 }
 function cameraBlocked(v){return v.x<limits[0]||v.x>limits[1]||v.z<limits[2]||v.z>limits[3]||[...layout.colliders,...getObstacles()].some(c=>[v.x,v.y,v.z].every((x,i)=>Math.abs(x-c.center[i])<c.size[i]/2+.06));}
 function clearCameraPath(a,b){const count=Math.ceil(a.distanceTo(b)/.08),v=new THREE.Vector3();for(let i=1;i<=count;i++)if(cameraBlocked(v.lerpVectors(a,b,i/count)))return false;return true;}
 function mode(value){walking=value;focus=null;keys.clear();velocity.set(0,0,0);if(!value&&document.pointerLockElement===canvas)document.exitPointerLock();onMode(value);}
 function keydown(e){if(/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)||e.target.isContentEditable||document.querySelector('dialog[open]'))return;
  if(e.code==='Escape'){mode(false);return;}if(e.code==='KeyE'){onInteract();return;}
  if(walking&&['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft'].includes(e.code)){e.preventDefault();keys.add(e.code);}
 }
 function up(e){keys.delete(e.code);}function blur(){keys.clear();velocity.set(0,0,0);}
 function look(dx,dy){yaw-=dx*.0022;pitch=THREE.MathUtils.clamp(pitch-dy*.0022,-1.15,1.15);focus=null;}
 function mouse(e){if(walking&&document.pointerLockElement===canvas)look(e.movementX,e.movementY);}
 function down(e){if(!walking)return;drag={x:e.clientX,y:e.clientY};if(e.pointerType==='mouse')canvas.requestPointerLock?.()?.catch(()=>{});else canvas.setPointerCapture(e.pointerId);}
 function move(e){if(!walking||!drag||document.pointerLockElement===canvas)return;look(e.clientX-drag.x,e.clientY-drag.y);drag={x:e.clientX,y:e.clientY};}
 function release(){drag=null;}function lock(){if(!document.pointerLockElement){keys.clear();velocity.set(0,0,0);}}
 window.addEventListener('keydown',keydown);window.addEventListener('keyup',up);window.addEventListener('blur',blur);document.addEventListener('mousemove',mouse);document.addEventListener('pointerlockchange',lock);
 canvas.addEventListener('pointerdown',down);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',release);
 camera.rotation.order='YXZ';camera.position.copy(position);
 return {get position(){return position;},get walking(){return walking;},mode,
  focus(getTarget,getFront){mode(false);focus=getTarget;focusFront=getFront||null;},
  update(dt){
   if(disposed)return;
   if(walking){let f=Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown')),s=Number(keys.has('KeyD')||keys.has('ArrowRight'))-Number(keys.has('KeyA')||keys.has('ArrowLeft'));
    const desired=new THREE.Vector3(s,0,-f).normalize().applyAxisAngle(new THREE.Vector3(0,1,0),yaw).multiplyScalar(keys.has('ShiftLeft')?3.2:2.0);
    velocity.lerp(desired,1-Math.exp(-12*dt));const count=Math.max(1,Math.ceil(velocity.length()*dt/.08));
    for(let i=0;i<count;i++){const dx=velocity.x*dt/count,dz=velocity.z*dt/count;if(!blocked(position.x+dx,position.z))position.x+=dx;if(!blocked(position.x,position.z+dz))position.z+=dz;}
   }
   let fov=layout.field_of_view??68;
   const camPos=position.clone();
   if(focus){const target=focus();if(target){
    const front=focusFront?focusFront():null;
    // 只有调用方提供人物正面方向时启用独立谈话镜头；普通关注保持玩家视点。
   if(front){
    // 从人物正面取镜；若候选镜头被墙/家具占据，先试轻微侧偏，再退回玩家位置。
    const direction=front.clone();direction.y=0;direction.normalize();
    for(const angle of [0,-.35,.35,-.7,.7]){
     const candidate=target.clone().addScaledVector(direction.clone().applyAxisAngle(new THREE.Vector3(0,1,0),angle),2.35);
     if(!cameraBlocked(candidate)&&clearCameraPath(position,candidate)){camPos.copy(candidate);break;}
    }
   }
    const d=target.clone().sub(camPos);
    fov=THREE.MathUtils.clamp(2*Math.atan(.78/d.length())*180/Math.PI,20,58);
    d.y-=.30;const targetYaw=Math.atan2(-d.x,-d.z);
    yaw+=Math.atan2(Math.sin(targetYaw-yaw),Math.cos(targetYaw-yaw))*(1-Math.exp(-6*dt));
    pitch=THREE.MathUtils.lerp(pitch,Math.atan2(d.y,Math.hypot(d.x,d.z)),1-Math.exp(-6*dt));
   }}
   position.y=THREE.MathUtils.lerp(position.y,(layout.eye_height??1.65)+groundAt(position.x,position.z),1-Math.exp(-12*dt));
   if(focus){const next=camera.position.clone().lerp(camPos,1-Math.exp(-6*dt));if(cameraBlocked(next)||!clearCameraPath(camera.position,next))camera.position.copy(position);else camera.position.copy(next);}else camera.position.copy(position);camera.rotation.set(pitch,yaw,0);camera.fov=THREE.MathUtils.lerp(camera.fov,fov,1-Math.exp(-5*dt));camera.updateProjectionMatrix();
   canvas.parentElement.dataset.player=JSON.stringify(position.toArray().map(v=>+v.toFixed(3)));canvas.parentElement.dataset.mode=walking?'walk':'dialogue';
  },moveInput(code,pressed){if(pressed)keys.add(code);else keys.delete(code);},blocked,
  dispose(){disposed=true;if(document.pointerLockElement===canvas)document.exitPointerLock();window.removeEventListener('keydown',keydown);window.removeEventListener('keyup',up);window.removeEventListener('blur',blur);document.removeEventListener('mousemove',mouse);document.removeEventListener('pointerlockchange',lock);canvas.removeEventListener('pointerdown',down);canvas.removeEventListener('pointermove',move);canvas.removeEventListener('pointerup',release);}
 };
}
