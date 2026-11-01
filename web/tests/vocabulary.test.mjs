import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {gradeVocabulary} from '../frontend/vocabulary-grade.js';import {reduceEvents} from '../frontend/state.js';
const C=JSON.parse(fs.readFileSync(new URL('../../data/curriculum/catalog.json',import.meta.url))),P=JSON.parse(fs.readFileSync(new URL('../../data/teaching-policy.json',import.meta.url))),B=C.vocabulary_banks.cet4,by=new Map(B.entries.map(e=>[e.word,e]));
test('全书词头与变体拼写正常判分，自评保持非客观评分',()=>{for(const e of B.entries)assert.equal(gradeVocabulary(e,'spelling',e.word),true,e.word);assert.equal(gradeVocabulary(by.get('program(me)'),'spelling','programme'),true);assert.equal(gradeVocabulary(by.get('space'),'self_review','remembered'),null);assert.equal(gradeVocabulary(by.get('space'),'spelling','spaces'),false);});
test('词库复习独立保存，共用每日上限，不伪造旧课程完成或正确率',()=>{
 const id=by.get('space').id,ev=(mode,response,i)=>({event_id:String(i),type:'vocabulary_attempt',at:'2026-10-22T03:00:00Z',payload:{word_id:id,mode,response,response_ms:3000,correct:true}});
 const s=reduceEvents([ev('spelling','spaces',0),ev('spelling','space',1),...Array.from({length:20},(_,i)=>ev('self_review','remembered',i+2))],C,P);
 assert.deepEqual(s.vocabulary_attempts[id].slice(0,2).map(x=>x.correct),[false,true]);assert.equal(s.vocabulary_attempts[id].at(-1).correct,null);assert.equal(s.practice_count,P.affection.practice_per_point_per_day);assert.deepEqual(s.completed,[]);assert.deepEqual(s.attempts,{});
});

test('新课堂逐词可达，课堂与词卡共用同词每日练习贡献',()=>{
 const points=C.points.filter(p=>p.vocabulary_lesson);assert.equal(points.length,2327);
 assert.deepEqual(new Set(points.map(p=>p.vocabulary_lesson.word_id)),new Set(B.entries.map(e=>e.id)));
 const p=points[0],wid=p.vocabulary_lesson.word_id,at='2026-10-22T03:00:00Z';
 const events=Array.from({length:P.affection.practice_per_point_per_day},(_,i)=>({event_id:`v${i}`,type:'vocabulary_attempt',at,payload:{word_id:wid,mode:'self_review',response:'again',response_ms:3000}}));
 events.push({event_id:'class',type:'attempt',at,payload:{point_id:p.id,clue_id:p.clues[0].id,response_ms:3000,study_ms:0}});
 const s=reduceEvents(events,C,P);assert.equal(s.practice_count,P.affection.practice_per_point_per_day);assert.equal(s.attempts[p.id].length,1);assert.deepEqual(s.completed,[]);
});
