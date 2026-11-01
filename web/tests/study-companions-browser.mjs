import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
const modules=process.env.TREECOURT_NODE_MODULES||join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const {chromium}=createRequire(join(modules,'package.json'))('playwright');
const base=process.env.TREECOURT_URL||'http://127.0.0.1:8876';
const output=join(process.cwd(),'web/.runtime/companion-review');await mkdir(output,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:1440,height:960}});const page=await context.newPage();const errors=[];const results=[];
page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(base+'/wallpaper',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>document.querySelector('#focus-stage')?.dataset.ready==='true',null,{timeout:60000});
 if(await page.locator('[data-study-companion]').count()!==4)throw Error('Expected exactly four choices');
 await page.locator('#fc-start').click();await page.waitForTimeout(1300);
 for(const id of ['phainon','hyacine','castor','anaxa']){
  const before=await page.locator('#fc-time').textContent();await page.locator(`[data-study-companion="${id}"]`).click();
  await page.waitForFunction(id=>document.querySelector('#focus-stage')?.dataset.character===id,id,{timeout:45000});
  const videos=await page.locator('#focus-stage video').count();if(videos!==1)throw Error('Expected one companion video, got '+videos);
  const playback=await page.locator('#focus-stage video').evaluate(video=>({loop:video.loop,rate:video.playbackRate}));
  if(!playback.loop||playback.rate!==1)throw Error('Companion must loop at normal speed');
  await page.locator('#focus-stage video').evaluate(video=>{video.currentTime=18.8;});
  await page.waitForFunction(()=>{const video=document.querySelector('#focus-stage video');return video&&!video.paused&&video.currentTime<3;},null,{timeout:15000});
  const after=await page.locator('#fc-time').textContent();if(after==='25:00')throw Error('Switch reset timer');
  if(await page.locator(`[data-study-companion="${id}"]`).getAttribute('aria-pressed')!=='true')throw Error('Selection state mismatch');
  await page.screenshot({path:join(output,`study-${id}.png`)});results.push({id,before,after,videos,looped:true});
 }
 await page.reload({waitUntil:'domcontentloaded'});await page.waitForFunction(()=>document.querySelector('#focus-stage')?.dataset.character==='anaxa');
 await page.goto(base+'/#focus',{waitUntil:'domcontentloaded'});await page.locator('#focus-note').waitFor();await page.waitForFunction(()=>document.querySelector('#quiet-room')?.dataset.ready==='true',null,{timeout:60000});
 await page.locator('[data-study-companion="castor"]').click();await page.waitForFunction(()=>document.querySelector('#quiet-room')?.dataset.character==='castor',null,{timeout:45000});
 if(await page.locator('#quiet-room video').count()!==1)throw Error('Embedded focus scene missing video');
 await page.screenshot({path:join(output,'embedded-study.png'),fullPage:true});
 if(!process.argv.includes('--study-only')){
 const films=(await (await context.request.get(base+'/api/cinematics')).json()).films;
 if(films.length!==4||films.some(f=>!f.ready))throw Error('Four complete invitation films are required');
 await page.goto(base+'/#companions',{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>document.querySelectorAll('[data-film]').length===4,null,{timeout:30000});
 for(const [id,name]of [['anaxa','那刻夏'],['hyacine','风堇'],['castor','遐蝶'],['phainon','白厄']]){
  const button=page.locator(`.companion-card.char-${id} [data-film]`);await button.click();
  const speaker=await page.locator('[data-film-speaker]').textContent();if(!speaker.includes(name))throw Error('Wrong cinema speaker: '+speaker);
  await page.waitForFunction(()=>document.querySelector('.cinematic-player')?.readyState>=2);
  await page.screenshot({path:join(output,`invitation-${id}.png`)});
  const film=films.find(f=>f.character===id),cue=film.interactions[0];
  await page.locator('[data-film-seek]').evaluate((el,at)=>{el.value=String(at);el.dispatchEvent(new Event('change'));},cue.at+.2);
  await page.locator('[data-film-choice]').first().waitFor();
  if(!await page.locator('.cinematic-player').evaluate(el=>el.paused))throw Error('Choice failed to pause film');
  await page.locator('[data-film-choice]').first().click();
  await page.waitForFunction(()=>{const v=document.querySelector('.cinematic-player');return v?.readyState>=2&&!v.paused&&v.currentTime>.1;});
  if(await page.locator('.cinematic-player').evaluate(el=>el.playbackRate)!==1)throw Error('Unexpected playback speed');
  await page.waitForFunction(url=>document.querySelector('.cinematic-player')?.getAttribute('src')===url,film.url,{timeout:25000});
  await page.waitForFunction(at=>document.querySelector('.cinematic-player')?.currentTime>at,cue.at,{timeout:15000});
  await page.keyboard.press('Escape');
 }
 }
 if(errors.length)throw Error(errors.join('\n'));
 await writeFile(join(output,'verification.json'),JSON.stringify({passed:true,results,errors},null,2));console.log('FOUR_COMPANIONS_BROWSER_VERIFIED',JSON.stringify(results));
}catch(error){
 await page.screenshot({path:join(output,'failure.png'),fullPage:true});
 const state=await page.evaluate(()=>({url:location.href,films:document.querySelectorAll('[data-film]').length,text:document.body.innerText.slice(-3000)}));
 await writeFile(join(output,'failure.json'),JSON.stringify({error:String(error),errors,state},null,2));
 console.error(JSON.stringify({errors,state}));throw error;
}finally{await context.close();await browser.close();}
