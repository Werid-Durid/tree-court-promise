import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {pointSearchText} from '../frontend/course-ui.js';
import {evaluateCourseExercise} from '../frontend/course-exercises.js';
const c=JSON.parse(fs.readFileSync(new URL('../../data/curriculum/catalog.json',import.meta.url)));
test('合并细目仍可查到正确课时，而不是只能搜旧标题',()=>{
 for(const [term,id] of [['Flash','cs408-co-memory-02'],['段页式虚存','cs408-co-memory-08'],['条件变量','cs408-os-synchronization-07'],['树森林与二叉树转换','cs408-ds-trees-01']]){
  const hit=c.points.filter(p=>pointSearchText(p).toLowerCase().includes(term.toLowerCase()));
  assert.ok(hit.some(p=>p.id===id),term);
 }
});
test('三本教材160课时迁移题规范答案前端可判分，保留中英文简称',()=>{
 const points=c.points.filter(p=>p.course?.source.kind==='textbook');assert.equal(points.length,160);
 for(const p of points)for(const e of p.course.exercises)assert.equal(evaluateCourseExercise(e,e.answer),true,p.id);
 const p=points.find(p=>p.id==='cs408-co-overview-01');assert.equal(evaluateCourseExercise(p.course.exercises[0],'程序计数器'),true);
 assert.equal(evaluateCourseExercise(p.course.exercises[0],'IR'),false);
});
