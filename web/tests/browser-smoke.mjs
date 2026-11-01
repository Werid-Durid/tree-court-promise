// 使用已安装的 Playwright 与 Edge 验证真实浏览器，不向发行包添加浏览器运行库。
import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import assert from 'node:assert/strict';
const modules=process.env.TREECOURT_NODE_MODULES||join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const require=createRequire(join(modules,'package.json'));
const {chromium}=require('playwright');
const root=resolve('web/.runtime/browser');await mkdir(root,{recursive:true});
const base=process.env.TREECOURT_URL||'http://127.0.0.1:8765';
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1050},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('net::ERR_FAILED'))errors.push(m.text());});
try{
 await page.goto(base);await page.getByRole('heading',{name:'树庭课程表',exact:true}).waitFor();
 await page.screenshot({path:join(root,'home-desktop.png'),fullPage:true});
 assert.equal(await page.locator('.subject-card').count(),7);
 assert.equal(await page.locator('.subject-card.available').count(),2);
 await page.locator('[data-subject="calculus"]').click();await page.getByText('函数极限与连续入门',{exact:true}).waitFor();assert.equal(await page.locator('#chapter-enter').count(),0);await page.locator('#modal-close').click();
 await page.locator('#hero-start').click();await page.locator('#begin-question').click();
 const {catalog}=await (await context.request.get(`${base}/api/catalog`)).json();
 for(let i=0;i<12;i++){
   const p=catalog.points[i],clue=p.clues.find(c=>c.correct===(i!==0));
   await page.locator(`[data-clue="${clue.id}"]`).click();await page.locator('.memory-hook').waitFor();
   if(i===0){
     await page.reload();await page.locator('.memory-hook').waitFor();assert.equal(await page.locator('.word-line h3').textContent(),'abandon');
     await page.screenshot({path:join(root,'classroom-desktop.png'),fullPage:true});
   }
   await page.locator('#next-point').click();
 }
 await page.getByRole('heading',{name:'今天的理解，已在树庭生根。'}).waitFor();
 await page.waitForFunction(()=>{const s=JSON.parse(localStorage.getItem('treecourt.web.v1'));return s.synced.length===s.events.length;});
 let saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('treecourt.web.v1')));
 let server=await (await context.request.get(`${base}/api/user`,{headers:{Authorization:`Bearer ${saved.profile}`}})).json();
 assert.equal(server.events.length,13);assert.equal(server.state.affection.anaxa,8);assert.equal(server.state.affection.hyacine,12);assert.deepEqual(server.state.completed,['cet4-01']);
 await page.locator('a[href="#notebook"]').first().click();assert.equal(await page.locator('.note-card').count(),12);assert.equal(await page.locator('.review-banner').count(),1);
 await page.locator('#review-weak').click();await page.locator('[data-clue="clue-0"]').click();await page.locator('#next-point').click();
 await page.getByRole('heading',{name:'今天的理解，已在树庭生根。'}).waitFor();
 await page.locator('a[href="#companions"]').first().click();await page.locator('[data-bond="anaxa"]').click();assert.match(await page.locator('#modal-body').innerText(),/尚未|共同修习|85/);assert.equal(await page.locator('#choose-romance').count(),0);await page.locator('#modal-close').click();
 await page.locator('a[href="#materials"]').first().click();await page.locator('#material-file').setInputFiles({name:'browser-lesson.md',mimeType:'text/markdown',buffer:Buffer.from('# 本地测试资料\n极限与连续，待编译审核。')});
 await page.getByRole('button',{name:'放入待编译队列'}).click();await page.locator('[data-preview]').first().waitFor();await page.locator('[data-preview]').first().click();await page.getByText(/极限与连续，待编译审核/).waitFor();await page.locator('#modal-close').click();
 // 模拟本地服务短暂不可达；缓存课程仍能运行，恢复后同步待提交事件。
 await page.route('**/api/**',r=>r.abort());await page.goto(`${base}/#home`);await page.locator('#hero-start').waitFor();await page.locator('#hero-start').click();await page.locator('#begin-question').click();await page.locator('[data-clue="clue-0"]').click();await page.locator('.memory-hook').waitFor();
 const offlineCount=await page.evaluate(()=>JSON.parse(localStorage.getItem('treecourt.web.v1')).events.length);
 await page.unroute('**/api/**');await page.reload();await page.locator('.memory-hook').waitFor();await page.waitForFunction(()=>{const s=JSON.parse(localStorage.getItem('treecourt.web.v1'));return s.synced.length===s.events.length;});
 saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('treecourt.web.v1')));assert.equal(saved.events.length,offlineCount);
 server=await (await context.request.get(`${base}/api/user`,{headers:{Authorization:`Bearer ${saved.profile}`}})).json();assert.equal(server.state.affection.anaxa,8);
 await page.goto(`${base}/#focus`);await page.locator('#focus-start').click();await page.waitForTimeout(1250);await page.locator('#focus-start').click();await page.locator('#focus-end').click();await page.getByRole('heading',{name:'这一段安静，已留下。'}).waitFor();await page.locator('#modal-close').click();
 await page.setViewportSize({width:390,height:844});await page.goto(`${base}/#home`);await page.locator('#hero-start').waitFor();
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'mobile home must not overflow');
 await page.screenshot({path:join(root,'home-mobile.png'),fullPage:true});
 await page.locator('#hero-start').click();await page.locator('#begin-question').click();await page.locator('.clue').first().waitFor();
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'mobile classroom must not overflow');
 await page.screenshot({path:join(root,'classroom-mobile.png'),fullPage:true});
 assert.deepEqual(errors,[],'no browser errors');
 await writeFile(join(root,'result.json'),JSON.stringify({passed:true,checks:['seven-subjects-one-playable','complete-12-points','refresh-feedback','wrong-no-penalty','review-no-farming','relationship-locked','upload-preview','offline-sync','focus-report','mobile-no-overflow'],screenshots:['home-desktop.png','classroom-desktop.png','home-mobile.png','classroom-mobile.png']},null,2));
 console.log('Browser acceptance passed. Evidence: '+root);
}finally{await context.close();await browser.close();}
