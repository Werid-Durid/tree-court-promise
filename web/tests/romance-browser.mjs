// 独立 QA 服务与匿名档案，验证邀约、回忆、专属好感与窄屏布局。
import {createRequire} from 'node:module';
import {join,resolve} from 'node:path';
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const require=createRequire(join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/package.json'));
const {chromium}=require('playwright'),out=resolve('characters/reports/romance-v2');await mkdir(out,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true}),ctx=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
const page=await ctx.newPage(),errors=[],checks=[];page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(30000);
const base=process.env.TREECOURT_QA_URL||'http://127.0.0.1:8783';
const choose=id=>page.locator(`[data-outing-choice="${id}"]`).click();
const path=['object','continue','first','stay','continue','quiet','continue','goodbye'];
async function play(){for(const id of path)await choose(id);await page.locator('.outing-keepsake').waitFor();}
try{
 await page.goto(base+'/#companions');await page.locator('[data-invite]').first().waitFor();assert.equal(await page.locator('[data-invite]').count(),4);
 await page.screenshot({path:join(out,'companions.png'),fullPage:true});
 for(const id of ['anaxa','hyacine','castor','phainon']){
  await page.locator(`[data-invite="${id}"]`).click();await page.waitForFunction(()=>document.querySelector('.outing-canvas')?.dataset.ready==='true',null,{timeout:120000});
  assert.ok(await page.locator('.outing-narration').count());assert.ok(await page.locator('.outing-spoken').count());
  await page.screenshot({path:join(out,id+'.png')});
  for(const choice of path.slice(0,-1))await choose(choice);
  assert.equal(await page.locator('[data-outing-choice="listen"]').isDisabled(),true);
  assert.equal(await page.locator('[data-outing-choice="closer"]').isDisabled(),true);
  assert.equal(await page.locator('#outing-text .outing-echo').count(),1);
  await choose('goodbye');await page.locator('.outing-keepsake').waitFor();
  await page.reload();await page.locator('.outing-keepsake').waitFor();
  await page.getByRole('button',{name:'回忆手札',exact:true}).click();assert.equal(await page.locator('.outing-memory').count(),9);
  await page.locator('.outing-memory summary').first().click();assert.ok((await page.locator('.outing-memory[open]').innerText()).length>60);
  await page.locator('#modal-close').click();await page.locator('#outing-restart').click();await play();
  await page.locator('a[href="#companions"]').last().click();await page.locator('[data-invite]').first().waitFor();
  checks.push(id+': scene, branching echo, gates, ending, reload, memories, replay');
 }
 await page.waitForFunction(()=>{const x=JSON.parse(localStorage.getItem('treecourt.web.v1'));return x.events.length===x.synced.length;});
 const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('treecourt.web.v1')));
 const user=await(await ctx.request.get(base+'/api/user',{headers:{Authorization:'Bearer '+saved.profile}})).json();
 assert.deepEqual(Object.values(user.state.affection),[18,18,18,18]);assert.deepEqual(user.state.completed,[]);assert.equal(user.state.study_ms,0);
 checks.push('server persists first-time bonds, no replay reward or academic side effects');
 await page.setViewportSize({width:390,height:844});await page.locator('[data-invite="hyacine"]').click();await page.locator('.outing-keepsake').waitFor();
 await page.waitForFunction(()=>document.querySelector('.outing-canvas')?.dataset.ready==='true',null,{timeout:120000});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
 await page.screenshot({path:join(out,'mobile.png')});
 await page.getByRole('button',{name:'回忆手札',exact:true}).click();await page.locator('.outing-memory summary').first().click();
 assert.equal(await page.evaluate(()=>document.querySelector('#modal').scrollWidth>document.querySelector('#modal').clientWidth+1),false);
 checks.push('390px dialogue and memory modal fit viewport');assert.deepEqual(errors,[]);
 await writeFile(join(out,'result.json'),JSON.stringify({passed:true,checks,errors,checked_at:new Date().toISOString()},null,2));console.log(JSON.stringify({passed:true,checks}));
}catch(error){await page.screenshot({path:join(out,'failure.png')}).catch(()=>{});await writeFile(join(out,'result.json'),JSON.stringify({passed:false,checks,errors,error:error.stack},null,2));throw error;}
finally{await ctx.close();await browser.close();}
