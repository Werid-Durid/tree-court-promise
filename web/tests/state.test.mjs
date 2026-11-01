import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {initialState,reduceEvents,eligibleForRomance} from '../frontend/state.js';
const catalog=JSON.parse(readFileSync(new URL('../../data/curriculum/catalog.json',import.meta.url)));
const policy=JSON.parse(readFileSync(new URL('../../data/teaching-policy.json',import.meta.url)));
const attempt=(p,correct)=>({type:'attempt',at:new Date().toISOString(),payload:{point_id:p.id,clue_id:p.clues.find(c=>c.correct===correct).id,response_ms:1000,study_ms:1000}});
test('首章十二词、重复复习和完成事件使用同一规则',()=>{
  const events=catalog.points.filter(p=>p.chapter==='cet4-01').map(p=>attempt(p,true));
  events.push(attempt(catalog.points[0],true),{type:'chapter_complete',payload:{chapter_id:'cet4-01'}});
  const s=reduceEvents(events,catalog,policy);
  assert.deepEqual(s.affection,{anaxa:0,hyacine:0,castor:0,phainon:0});
  assert.deepEqual(s.completed,['cet4-01']);assert.equal(s.study_ms,13000);
});
test('先未匹配、后回顾匹配也不刷好感',()=>{
  const p=catalog.points[0],s=reduceEvents([attempt(p,false),attempt(p,true)],catalog,policy);
  assert.equal(s.affection.anaxa,0);assert.equal(s.attempts[p.id].at(-1).correct,true);
});
test('关系邀请需阈值、章节完成且从未选择；拒绝后不再邀请',()=>{
  const s=initialState(catalog);s.affection.anaxa=85;
  assert.equal(eligibleForRomance(s,'anaxa',policy),false);
  s.completed=['cet4-01'];assert.equal(eligibleForRomance(s,'anaxa',policy),true);
  s.relationships.anaxa='friend';assert.equal(eligibleForRomance(s,'anaxa',policy),false);assert.equal(s.affection.anaxa,85);
});
test('未完成全部词笺不能提前取得章节完成记录',()=>{
  assert.deepEqual(reduceEvents([{type:'chapter_complete',payload:{chapter_id:'cet4-01'}}],catalog,policy).completed,[]);
});
test('高好感时用户可分别选择恋爱或好友，拒绝后邀请不重开',()=>{
  // 通过真实测试、有效练习和时长达到阈值，拒绝好友路线后不重复邀请。
  const extended=structuredClone(catalog);
  for(let i=0;i<22;i++)extended.points.push({...structuredClone(catalog.points[0]),id:`future-${i}`});
  const base=extended.points.map(p=>{const e=attempt(p,true);e.payload.response_ms=2000;return e;});
  for(const ch of catalog.subjects[0].chapters)base.push({type:'chapter_test',at:new Date().toISOString(),payload:{chapter_id:ch.id,answers:Object.fromEntries(ch.test_points.map(id=>[id,catalog.points.find(p=>p.id===id).test.answer]))}});
  base.push({type:'focus_session',at:new Date().toISOString(),payload:{seconds:14400,interruptions:0}});
  const before=reduceEvents(base,extended,policy);assert.ok(before.affection.anaxa>=85);
  assert.equal(eligibleForRomance(before,'anaxa',policy),true);
  for(const choice of ['friend','romance']){
    const chosen=reduceEvents([...base,{type:'relationship',payload:{character:'anaxa',choice}}],extended,policy);
    assert.equal(chosen.relationships.anaxa,choice);assert.equal(chosen.affection.anaxa,before.affection.anaxa);
    assert.equal(eligibleForRomance(chosen,'anaxa',policy),false);
    const repeated=reduceEvents([...base,{type:'relationship',payload:{character:'anaxa',choice}},{type:'relationship',payload:{character:'anaxa',choice:'romance'}}],extended,policy);
    assert.equal(repeated.relationships.anaxa,choice);
  }
});
