// 真实 UI 验收只访问独立服务，不触碰正式档案或当前用户浏览器。
import {createRequire} from 'node:module';import {join,resolve} from 'node:path';import {mkdir,writeFile} from 'node:fs/promises';import assert from 'node:assert/strict';
const require=createRequire(join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/package.json'));
const {chromium}=require('playwright');const out=resolve('web/.runtime/social-browser');await mkdir(out,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});const ctx=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
await ctx.route('**/api/stage/events',r=>r.fulfill({json:{accepted:true,executed:false,reason:'验收不控制 UE 编辑器'}}));
const page=await ctx.newPage(),errors=[],checks=[],shots=[];page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(30000);
async function shot(n){await page.screenshot({path:join(out,n),fullPage:true});shots.push(n);}
async function clickChoice(id){await page.locator(`[data-outing-choice="${id}"]`).click();}
try{
 await page.goto('http://127.0.0.1:8779/#companions');await page.locator('[data-invite]').first().waitFor();assert.equal(await page.locator('[data-invite]').count(),4);await shot('01-companions.png');checks.push('four-invitation-entries');
 for(const id of ['anaxa','hyacine','castor','phainon']){
  await page.locator(`[data-invite="${id}"]`).click();await page.waitForFunction(()=>document.querySelector('.outing-canvas')?.dataset.ready==='true',{},{timeout:120000});assert.equal(new URL(page.url()).hash,'#outing');
  assert.ok((await page.locator('#outing-text').innerText()).length>50);await shot('outing-'+id+'.png');
  await clickChoice('object');await clickChoice('continue');await clickChoice('first');await clickChoice('continue');
  assert.equal(await page.locator('[data-outing-choice="listen"]').isDisabled(),true);assert.equal(await page.locator('[data-outing-choice="closer"]').isDisabled(),true);await clickChoice('goodbye');await page.locator('.outing-keepsake').waitFor();
  await page.reload();await page.locator('.outing-keepsake').waitFor();checks.push(id+'-scene-branch-ending-refresh');await page.locator('a[href="#companions"]').last().click();await page.locator('[data-invite]').first().waitFor();
 }
 const save=await page.evaluate(()=>JSON.parse(localStorage.getItem('treecourt.web.v1')));const user=await (await ctx.request.get('http://127.0.0.1:8779/api/user',{headers:{Authorization:'Bearer '+save.profile}})).json();assert.deepEqual(Object.values(user.state.affection),[15,15,15,15]);assert.equal(Object.keys(user.state.outings).length,4);checks.push('endings-persist-first-bonds-no-learning-score');
 await page.goto('http://127.0.0.1:8779/#home');await page.locator('[data-subject="calculus"]').click();await page.locator('[data-enter="calculus-upper-limits"]').click();await page.locator('#network-course').waitFor();
 await page.waitForFunction(()=>document.querySelector('.scene-host')?.dataset.ready==='true',{},{timeout:120000});
 for(const id of ['hyacine','castor','phainon']){
  await page.locator(`[data-talk="${id}"]`).click();const menu=page.locator('.aside-conversation');await menu.locator('[data-chat="0"]').click();const first=await page.locator('#dialogue-text').innerText();assert.ok(first.length>25);
  await menu.locator('[data-chat="0"]').click();const reply=await page.locator('#dialogue-text').innerText();assert.notEqual(reply,first);await menu.locator('[data-chat="0"]').click();assert.notEqual(await page.locator('#dialogue-text').innerText(),reply);await shot('class-chat-'+id+'.png');await menu.getByRole('button',{name:'回到课堂话题',exact:true}).click();checks.push(id+'-multi-turn-classroom');
 }
 await page.setViewportSize({width:390,height:844});await page.goto('http://127.0.0.1:8779/#companions');await page.locator('[data-invite="hyacine"]').click();await page.waitForFunction(()=>document.querySelector('.outing-canvas')?.dataset.ready==='true',{},{timeout:120000});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);await shot('outing-mobile.png');checks.push('mobile-no-overflow');
 assert.deepEqual(errors,[]);await writeFile(join(out,'result.json'),JSON.stringify({passed:true,checks,shots,errors,checked_at:new Date().toISOString()},null,2));console.log(JSON.stringify({passed:true,checks,shots}));
}catch(e){await shot('failure.png').catch(()=>{});await writeFile(join(out,'result.json'),JSON.stringify({passed:false,error:e.stack,errors,checks,shots},null,2));throw e;}finally{await ctx.close();await browser.close();}
