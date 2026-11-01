import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {allChapters,createCourseUI} from '../frontend/course-ui.js';
const c=JSON.parse(readFileSync(new URL('../../data/curriculum/catalog.json',import.meta.url)));
test('跨科章节检索不会把 408 章节回退为四级第一章',()=>{
 const ui=createCourseUI({catalog:()=>c,read:(_,fallback)=>fallback});
 for(const s of c.subjects.filter(x=>x.status==='available'))for(const ch of s.chapters){const found=ui.chapter(ch.id);assert.equal(found.id,ch.id);assert.equal(found.subject_id,s.id);}
 assert.equal(ui.chapter('cet4-01').id,'cet4-01');
});
test('四科章节点全部进入同一课程索引，章节 ID 保持唯一',()=>{
 const chapters=allChapters(c);assert.equal(new Set(chapters.map(ch=>ch.id)).size,chapters.length);
 const modules=new Set(chapters.filter(ch=>ch.subject_id==='cs408').map(ch=>ch.module_id));assert.deepEqual([...modules],['net','co','os','ds']);
});
