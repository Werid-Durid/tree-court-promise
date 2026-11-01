import test from 'node:test';import assert from 'node:assert/strict';import {alarmPosterior} from '../frontend/probability-math.js';
test('报警后验保留基础发生率，条件概率和检出率分开',()=>{const r=alarmPosterior(.01,.9,.05);assert.ok(Math.abs(r.posterior-2/13)<1e-12);assert.ok(Math.abs(r.total-.0585)<1e-12);assert.notEqual(r.posterior,.9);});
test('不可能报警的条件不伪造后验，概率边界与非法输入明确处理',()=>{assert.equal(alarmPosterior(0,1,0).posterior,null);assert.equal(alarmPosterior(1,1,0).posterior,1);assert.throws(()=>alarmPosterior(-.1,.9,.1));assert.throws(()=>alarmPosterior(NaN,.9,.1));});
