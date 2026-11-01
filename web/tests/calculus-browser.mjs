// 独立浏览器与独立验收数据库：不读取用户浏览器，不修改正式学习存档。
import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import assert from 'node:assert/strict';
const modules=process.env.TREECOURT_NODE_MODULES||join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const require=createRequire(join(modules,'package.json'));
const {chromium}=require('playwright');
const base=process.env.TREECOURT_URL||'http://127.0.0.1:8779';
assert.equal(new URL(base).hostname,'127.0.0.1','验收仅允许本地网站');
assert.notEqual(new URL(base).port,'8765','作答验收必须使用独立数据库');
const out=resolve('web/.runtime/calculus-browser');await mkdir(out,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
await context.addInitScript(()=>localStorage.setItem('treecourt.web.v1.settings',JSON.stringify({instant:true,voice:false})));
// 场景事件保留网页降级路径，防止测试对白控制正在使用的 UE 编辑器。
await context.route('**/api/stage/events',r=>r.fulfill({json:{accepted:true,executed:false,connected:false,reason:'独立验收：UE5 事件不外发'}}));
const page=await context.newPage(),errors=[],checks=[],screenshots=[];
page.setDefaultTimeout(30000);page.on('pageerror',e=>errors.push(e.message));
async function shot(name){await page.screenshot({path:join(out,name),fullPage:true});screenshots.push(name);}
async function openPoint(id){
 await page.goto(base+'/#home');await page.locator('[data-subject="calculus"]').click();
 const p=catalog.points.find(p=>p.id===id),ch=subject.chapters.find(c=>c.id===p.chapter);
 await page.locator(`[data-progress="${ch.id}"]`).selectOption(String(ch.points.indexOf(id)));
 await page.locator(`[data-enter="${ch.id}"]`).click();
 await page.locator('#network-course').waitFor();assert.equal(new URL(page.url()).hash,'#classroom');
 await page.locator('.word-line h3').filter({hasText:p.concept}).waitFor();
 await page.waitForFunction(()=>document.querySelector('.scene-host')?.dataset.ready==='true',{},{timeout:120000});
 assert.match(await page.locator('.stage-status').innerText(),/4\/4/);
 return p;
}
let catalog,subject;
try{
 const r=await context.request.get(base+'/api/catalog');assert.equal(r.status(),200);({catalog}=await r.json());subject=catalog.subjects.find(s=>s.id==='calculus');
 await page.goto(base+'/#home');await page.getByRole('heading',{name:'树庭课程表',exact:true}).waitFor();
 assert.equal(new URL(page.url()).origin,base);checks.push('local-url-confirmed');await shot('01-home-desktop.png');
 await page.locator('[data-subject="calculus"]').click();assert.equal(await page.locator('.course-card').count(),14);
 assert.equal(await page.locator('[data-progress] option').count(),64);checks.push('14-chapters-64-lessons-reachable');await shot('02-course-menu.png');
 await page.locator('[data-module="高数下"]').click();assert.equal(await page.locator('.course-card').count(),7);checks.push('lower-volume-free-selection');
 await page.locator('#modal-close').click();
 const p=await openPoint('calculus-upper-infinitesimal');
 await page.locator('#calc-sequence-mode').waitFor();
 await page.waitForFunction(()=>document.querySelector('.scene-host')?.dataset.ready==='true',{},{timeout:120000});
 assert.match(await page.locator('.stage-status').innerText(),/4\/4/);assert.equal(await page.locator('.scene-host').getAttribute('data-animated'),'4');checks.push('four-3d-characters-and-animation-loaded');
 const attemptCount=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('treecourt.web.v1')).events.filter(e=>e.type==='attempt'||e.type==='course_attempt').length);
 const before=await attemptCount();
 await page.locator('#calc-sequence-mode').selectOption('absolute');assert.match(await page.locator('#calc-sequence-note').innerText(),/既不趋/);
 await page.locator('#calc-sequence-n').fill('40');await page.locator('#calc-sequence-m').fill('20');
 assert.equal(await page.locator('#calc-sequence-plot circle').count(),40);
 await page.locator('#calc-sequence-mode').selectOption('small');assert.match(await page.locator('#calc-sequence-note').innerText(),/ε=0.05/);
 assert.equal(await attemptCount(),before);checks.push('sequence-controls-no-false-attempt');
 await page.locator('#calc-sequence-mode').selectOption('unbounded');await page.locator('#calc-sequence-plot').scrollIntoViewIfNeeded();await shot('03-sequence-desktop.png');
 await page.locator('#network-source').click();assert.equal(await page.locator('#modal-body a').first().getAttribute('href'),p.course.source.url);assert.match(await page.locator('#modal-body').innerText(),/未|无法|不/);await page.locator('#modal-close').click();checks.push('source-link-and-disclosure');
 await page.locator('#network-textbook').click();await page.locator('#modal-body').getByRole('heading',{name:p.concept,exact:true}).waitFor();await page.locator('#modal-close').click();checks.push('full-lesson-modal');
 await page.locator('[data-network-stage="1"]').click();assert.ok(await page.locator('.network-worked li').count()>=3);checks.push('worked-example-steps');
 await page.locator('[data-network-stage="2"]').click();await page.locator('#network-response').fill('故意输入的验收错答');await page.locator('#network-transfer button[type="submit"]').click();
 assert.ok((await page.locator('#network-exercise-feedback').innerText()).length>15);
 await page.locator('#network-response').fill(p.course.exercises.find(e=>e.id==='transfer').answer);await page.locator('#network-transfer button[type="submit"]').click();
 await page.waitForFunction(()=>{const s=JSON.parse(localStorage.getItem('treecourt.web.v1'));return s.events.length===s.synced.length;});
 const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('treecourt.web.v1')));
 const user=await (await context.request.get(base+'/api/user',{headers:{Authorization:'Bearer '+saved.profile}})).json();
 const attempts=user.state.course_attempts[p.id+':transfer'];assert.equal(attempts.at(-2).correct,false);assert.equal(attempts.at(-1).correct,true);assert.deepEqual(user.state.completed,[]);checks.push('real-wrong-and-correct-server-grading-no-false-completion');
 await page.reload();await page.locator('#network-response').waitFor();assert.equal(await page.locator('#network-response').inputValue(),p.course.exercises.find(e=>e.id==='transfer').answer);checks.push('refresh-keeps-exercise-draft');
 await openPoint('calculus-upper-taylor-errors');await page.locator('[data-network-stage="2"]').click();await page.locator('#network-response').fill('2/12');await page.locator('#network-transfer button[type="submit"]').click();assert.match(await page.locator('#network-exercise-feedback').innerText(),/相连|匹配|一致|成立|解释|推导|这一步/);checks.push('equivalent-fraction-real-form');
 await openPoint('calculus-lower-vectors');await page.locator('#calc-vector-x').waitFor();assert.match(await page.locator('#calc-vector-note').innerText(),/5.0000/);
 for(const a of ['x','y','z'])await page.locator('#calc-vector-'+a).fill('0');assert.match(await page.locator('#calc-vector-note').innerText(),/零向量没有/);checks.push('vector-length-and-zero-boundary');await page.locator('#calc-vector-note').scrollIntoViewIfNeeded();await shot('04-vector-desktop.png');
 // 全屏必须由真实点击触发，检查实际 Fullscreen API 和渲染画布的占高。
 await page.locator('#classroom-immersive').click();await page.waitForFunction(()=>!!document.fullscreenElement);
 assert.equal(await page.evaluate(()=>Math.abs(document.fullscreenElement.getBoundingClientRect().height-innerHeight)<2),true);
 await page.locator('#walk-mode').click();await page.waitForFunction(()=>document.querySelector('.classroom')?.classList.contains('walking'));
 assert.equal(await page.locator('.dialogue-panel').isVisible(),false);
 assert.equal(await page.evaluate(()=>{const r=document.querySelector('.scene-host canvas').getBoundingClientRect();return Math.abs(r.height-innerHeight)<2&&Math.abs(r.width-innerWidth)<2;}),true);
 await page.waitForTimeout(800);await shot('05-immersive.png');await page.evaluate(()=>document.exitFullscreen());checks.push('immersive-fullscreen-height');
 await page.setViewportSize({width:390,height:844});await page.goto(base+'/#home');await page.locator('[data-subject="calculus"]').waitFor();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);await shot('06-home-mobile.png');
 await openPoint('calculus-lower-vectors');assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);await page.locator('#calc-vector-note').scrollIntoViewIfNeeded();await shot('07-vector-mobile.png');checks.push('mobile-home-and-classroom-no-overflow');
 assert.deepEqual(errors,[],'无未处理的页面异常');checks.push('no-page-errors');
 await writeFile(join(out,'result.json'),JSON.stringify({passed:true,checked_at:new Date().toISOString(),browser:'Playwright '+require('playwright/package.json').version+' / isolated headless Edge',base,checks,screenshots,errors},null,2));console.log(JSON.stringify({passed:true,checks,screenshots,out},null,2));
}catch(e){await shot('failure.png').catch(()=>{});await writeFile(join(out,'result.json'),JSON.stringify({passed:false,error:e.stack,checks,screenshots,errors,url:page.url()},null,2));throw e;}
finally{await context.close();await browser.close();}
