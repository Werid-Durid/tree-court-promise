import test from 'node:test';import assert from 'node:assert/strict';
import {PerspectiveCamera,Vector3} from '../renderer/node_modules/three/build/three.module.js';
import {firstPerson} from '../renderer/first-person.js';
function fixture(){globalThis.window=new EventTarget();globalThis.document=new EventTarget();document.querySelector=()=>null;document.exitPointerLock=()=>{};const canvas=new EventTarget();canvas.parentElement={dataset:{}};const camera=new PerspectiveCamera();const control=firstPerson(camera,canvas,{player_start:[0,1.65,0],bounds:[-5,5,-5,5],radius:.24,colliders:[{center:[0,.8,-2],size:[2,1.6,.2]}]});return {camera,control,canvas};}
test('玩家不能穿过桌墙碰撞，松键后减速停止',()=>{const {control}=fixture();control.mode(true);control.moveInput('KeyW',true);for(let i=0;i<240;i++)control.update(1/60);assert.ok(control.position.z>=-1.661);assert.ok(control.position.z<-.5);control.moveInput('KeyW',false);const before=control.position.clone();for(let i=0;i<120;i++)control.update(1/60);assert.ok(before.distanceTo(control.position)<.17);assert.equal(control.position.y,1.65);control.dispose();});
test('对话镜头只转动和变焦，不传送玩家；再进入行走可恢复控制',()=>{const {control,camera}=fixture();const p=control.position.clone();control.focus(()=>new Vector3(3,1.7,-3));for(let i=0;i<180;i++)control.update(1/60);assert.deepEqual(control.position.toArray(),p.toArray());assert.ok(camera.rotation.y<-.6);assert.ok(camera.fov<30);control.mode(true);control.moveInput('KeyD',true);for(let i=0;i<30;i++)control.update(1/60);assert.ok(control.position.distanceTo(p)>.3);control.dispose();});
test('失焦清除已按下方向；玩家不能走出房间边界',()=>{const {control}=fixture();control.mode(true);control.moveInput('KeyD',true);window.dispatchEvent(new Event('blur'));for(let i=0;i<60;i++)control.update(1/60);assert.deepEqual(control.position.toArray(),[0,1.65,0]);assert.equal(control.blocked(5.01,0),true);control.dispose();});

test('动态角色碰撞随当前位置移动，不将旧位置永久封住',()=>{
 const {control:old,canvas,camera}=fixture();old.dispose();let x=0;
 const control=firstPerson(camera,canvas,{player_start:[0,1.65,0],bounds:[-5,5,-5,5],colliders:[]},{getObstacles:()=>[{center:[x,.9,-1],size:[.7,1.8,.7]}]});
 assert.equal(control.blocked(0,-1),true);x=2;assert.equal(control.blocked(0,-1),false);assert.equal(control.blocked(2,-1),true);control.dispose();
});
