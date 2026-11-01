import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {pendingCue,normalizeFilmProgress,filmLineAt} from '../frontend/cinema-state.js';
const spec=JSON.parse(fs.readFileSync(new URL('../../data/cinematics/phainon-wheat.json',import.meta.url)));
const film={...spec,duration_seconds:spec.duration};
const revision=film.revision;
test('跳到后面仍先遇到第一处未回应节点，已回应后只拦下一处',()=>{
 assert.equal(pendingCue(film,64,{}).id,'waymark');
 assert.equal(pendingCue(film,64,{waymark:'blank'}).id,'name');
 assert.equal(pendingCue(film,64,{waymark:'blank',name:'stay'}),undefined);
});
test('中途关闭只保留有效选择，恢复不会越过未回应节点',()=>{
 assert.deepEqual(normalizeFilmProgress(film,{revision,time:69,answers:{waymark:'blank',name:'bad'}}),{revision,time:58.4,answers:{waymark:'blank'}});
 assert.deepEqual(normalizeFilmProgress(film,{revision:revision-1,time:55,answers:{waymark:'blank'}}),{revision,time:0,answers:{}});
});
test('53秒对白有足够原速时间窗，字幕可按实际时间读取',()=>{
 const line=filmLineAt(film,55);assert.ok(line.text.includes('只是'));assert.equal(line.end-line.start,5.200000000000003);
 assert.equal(filmLineAt(film,58.4),undefined);
});
