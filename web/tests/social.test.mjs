import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {resetProgressStorage} from '../frontend/progress-reset.js';import {applyOuting} from '../frontend/invitation-state.js';import {initialState} from '../frontend/state.js';import {chatText} from '../frontend/character-chat.js';
const c=JSON.parse(fs.readFileSync(new URL('../../data/curriculum/catalog.json',import.meta.url)));
test('重置清除本应用全部草稿和进度，纪元不变不重复清空',()=>{
 const data={'treecourt.web.v1':'old','treecourt.web.v1.examDraft.x':'old','treecourt.web.v1.focus':'old','other-app':'keep'};
 Object.defineProperties(data,{getItem:{value:k=>data[k]??null},setItem:{value:(k,v)=>data[k]=v},removeItem:{value:k=>delete data[k]}});
 assert.equal(resetProgressStorage(data,'epoch-2'),true);assert.equal(data['treecourt.web.v1'],undefined);assert.equal(data['treecourt.web.v1.examDraft.x'],undefined);assert.equal(data['other-app'],'keep');data['treecourt.web.v1']='new';assert.equal(resetProgressStorage(data,'epoch-2'),false);assert.equal(data['treecourt.web.v1'],'new');
});
test('好友路线完整且邀约重玩不增加好感，不能越权恋爱',()=>{
 const s=initialState(c),id='hyacine';for(const [node_id,choice_id] of [['arrival','chat'],['chat','continue'],['task','second'],['second','continue']])applyOuting(s,{character:id,node_id,choice_id},c);
 applyOuting(s,{character:id,node_id:'pause',choice_id:'closer'},c);assert.equal(s.outings[id].node,'pause');applyOuting(s,{character:id,node_id:'pause',choice_id:'goodbye'},c);assert.deepEqual(s.outings[id].endings,['end']);assert.equal(s.affection[id],0);assert.deepEqual(s.completed,[]);
});
test('课堂分支插入实际知识点及记忆线索，不残留模板变量',()=>{
 const p=c.points.find(p=>p.id==='calculus-upper-infinitesimal');for(const x of c.characters.filter(c=>c.classroom_chat?.length))for(const t of x.classroom_chat){assert.ok(chatText(t.opening,p).includes(p.concept));assert.doesNotMatch(chatText(t.opening,p),/\{(topic|hook|boundary)\}/);}
});
