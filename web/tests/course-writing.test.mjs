import test from 'node:test';import assert from 'node:assert/strict';import {englishWordCount} from '../frontend/course-writing.js';
test('开放练笔只统计英文词，不把汉字、标点和数字伪造成词数',()=>{assert.equal(englishWordCount("Don't give up. 保留中文提示 2026"),3);assert.equal(englishWordCount('a well-designed plan'),3);assert.equal(englishWordCount(''),0);});
