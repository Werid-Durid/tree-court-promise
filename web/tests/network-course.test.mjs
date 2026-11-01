import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {evaluateCourseExercise} from '../frontend/course-exercises.js';
import {reduceEvents} from '../frontend/state.js';
const catalog=JSON.parse(fs.readFileSync(new URL('../../data/curriculum/catalog.json',import.meta.url))),policy=JSON.parse(fs.readFileSync(new URL('../../data/teaching-policy.json',import.meta.url)));
const points=catalog.points.filter(p=>p.module_id==='net');
test('56课时规范答案都能判分，数值单位与全角输入正常处理',()=>{
 assert.equal(points.length,56);
 for(const p of points)for(const x of p.course.exercises)assert.equal(evaluateCourseExercise(x,x.answer),true,p.id);
 const x=points.find(p=>p.id==='cs408-net-physical-03').course.exercises[0];
 for(const value of ['１６０００','16000 bit/s','16000.0'])assert.equal(evaluateCourseExercise(x,value),true);
 assert.equal(evaluateCourseExercise(x,'1.6e4'),false);assert.throws(()=>evaluateCourseExercise(x,''));
});
test('迁移题按真实输入重建，不因客户端正确标记改变结果，不提前完成知识点',()=>{
 const pid='cs408-net-physical-03';
 const ev=(response,id)=>({event_id:id,type:'course_attempt',at:'2026-10-22T01:00:00Z',payload:{point_id:pid,exercise_id:'transfer',response,response_ms:3000,correct:true}});
 const s=reduceEvents([ev('12000','wrong'),ev('16000','right')],catalog,policy);
 assert.deepEqual(s.course_attempts[`${pid}:transfer`].map(a=>a.correct),[false,true]);assert.equal(s.attempts[pid],undefined);assert.deepEqual(s.completed,[]);
});
test('迁移练习与机制题共用每日贡献上限，不无限刷好感',()=>{
 const p=points[0],events=Array.from({length:30},(_,i)=>({event_id:String(i),type:'course_attempt',at:'2026-10-22T01:00:00Z',payload:{point_id:p.id,exercise_id:'transfer',response:p.course.exercises[0].answer,response_ms:3000}}));
 const s=reduceEvents(events,catalog,policy);assert.equal(s.practice_count,policy.affection.practice_per_point_per_day);
});
