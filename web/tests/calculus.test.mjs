import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {evaluateCourseExercise} from '../frontend/course-exercises.js';
import {allChapters,pointSearchText,createCourseUI} from '../frontend/course-ui.js';
import {reduceEvents} from '../frontend/state.js';
const c=JSON.parse(fs.readFileSync(new URL('../../data/curriculum/catalog.json',import.meta.url))),policy=JSON.parse(fs.readFileSync(new URL('../../data/teaching-policy.json',import.meta.url)));
const points=c.points.filter(p=>p.subject==='calculus');
test('高数上下册14章64课时在统一导航中可达',()=>{
 const chapters=allChapters(c).filter(ch=>ch.subject_id==='calculus');assert.equal(chapters.length,14);assert.equal(points.length,64);
 assert.deepEqual(new Set(chapters.flatMap(ch=>ch.points)),new Set(points.map(p=>p.id)));
 assert.ok(points.filter(p=>pointSearchText(p).includes('无界')).length);
 assert.ok(chapters.every(ch=>!/(学习方法|串讲)/.test(ch.title)));
 const ui=createCourseUI({catalog:()=>c,state:()=>({}),show:()=>{},close:()=>{},start:()=>{},record:()=>{},storageKey:'qa',write:()=>{},read:(k,f)=>f});
 assert.equal(ui.chapter('calculus-upper-ode-review').id,'calculus-upper-ode');
 assert.equal(ui.chapter('calculus-lower-overview').id,'calculus-lower-multiple-integrals');
 assert.equal(ui.chapter('calculus-upper-study-methods').subject_id,'calculus');
});
test('高数有理数响应与服务器规则一致，输入不是可执行表达式',()=>{
 for(const p of points)for(const e of p.course.exercises)assert.equal(evaluateCourseExercise(e,e.answer),true,p.id);
 const e=points.find(p=>p.id==='calculus-upper-taylor-errors').course.exercises[0];
 for(const s of ['1/6','2/12','１６／９６'])assert.equal(evaluateCourseExercise(e,s),true);
 for(const s of ['1/0','0.1667','1e-1','Math.random()'])assert.equal(evaluateCourseExercise(e,s),false);
 const half=points.find(p=>p.id==='calculus-upper-taylor').course.exercises[0];assert.equal(evaluateCourseExercise(half,'0.5000'),true);
});
test('高数练习按真实输入记录，不因画图参数变动生成完成记录',()=>{
 const p=points[0],events=[{event_id:'calculus-test',type:'course_attempt',at:'2026-10-24T01:00:00+08:00',payload:{point_id:p.id,exercise_id:'transfer',response:'999',response_ms:3000,correct:true}}];
 const state=reduceEvents(events,c,policy);assert.equal(state.course_attempts[p.id+':transfer'][0].correct,false);assert.deepEqual(state.completed,[]);
});
