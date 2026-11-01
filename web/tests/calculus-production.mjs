// 正式服务只读复核：独立浏览器，不提交答案、时长或 UE 场景事件。
import {createRequire} from 'node:module';
import {join,resolve} from 'node:path';
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const require=createRequire(join(process.env.TREECOURT_NODE_MODULES||join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'),'package.json'));
const {chromium}=require('playwright');
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000}});
const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
const base='http://127.0.0.1:8765',out=resolve('web/.runtime/calculus-browser');
try{
 await context.route('**/api/**',r=>r.request().method()==='GET'?r.continue():r.abort());
 await page.goto(base+'/#home');await page.locator('[data-subject="calculus"]').click();
 assert.equal(page.url(),base+'/#home');assert.equal(await page.locator('.course-card').count(),14);assert.equal(await page.locator('[data-progress] option').count(),64);
 assert.doesNotMatch(await page.locator('.course-card h3').allTextContents().then(t=>t.join(' ')),/学习方法|串讲/);
 const {catalog}=await (await context.request.get(base+'/api/catalog')).json();
 for(const [chapter,id] of [['calculus-upper-ode','calculus-upper-linear-ode'],['calculus-lower-multiple-integrals','calculus-lower-lower-practice'],['calculus-lower-multivariable','calculus-lower-lower-map']]){
  const point=catalog.points.find(p=>p.id===id);assert.equal(point.chapter,chapter);
  assert.ok((await page.locator(`[data-progress="${chapter}"] option`).allTextContents()).some(t=>t.includes(point.concept)));
 }
 assert.match(await page.locator('link[rel="stylesheet"]').getAttribute('href'),/calculus-acceptance-20261024/);
 const css=await (await context.request.get(base+'/static/styles.css')).text();assert.match(css,/has-network-course\{max-height:48dvh\}/);
 assert.deepEqual(errors,[]);await mkdir(out,{recursive:true});await page.screenshot({path:join(out,'08-production-courses.png'),fullPage:true});
 const v=await (await context.request.get(base+'/api/course-voice-status')).json(),voice=v.subjects.find(s=>s.id==='calculus');
 const result={passed:true,url:page.url(),checked_at:new Date().toISOString(),chapters:14,lessons:64,css_version:'calculus-acceptance-20261024',writes_blocked:true,voice_ready:voice.ready,voice_expected:voice.expected,generation:v.generation.status,errors};
 await writeFile(join(out,'production-result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
}finally{await context.close();await browser.close();}
