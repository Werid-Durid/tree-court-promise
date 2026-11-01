import {createRequire} from 'node:module';import {join} from 'node:path';import {mkdir,writeFile} from 'node:fs/promises';
const {chromium}=createRequire(join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/package.json'))('playwright');const browser=await chromium.launch({channel:'msedge',headless:true});const base='http://127.0.0.1:8765';const output='web/.runtime/elysia-review';await mkdir(output,{recursive:true});const results=[];
try{
 const request=await browser.newContext();const film=(await (await request.request.get(base+'/api/cinematics')).json()).films.find(f=>f.character==='phainon');if(!film.ready||!film.url.endsWith('?v=4'))throw Error('New Elysia film is not published');await request.close();
 for(const [index,cue] of film.interactions.entries())for(const choice of cue.choices){
  const context=await browser.newContext({viewport:{width:1440,height:960}}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/#companions');await page.waitForSelector('.char-phainon [data-film]');
  const answers=Object.fromEntries(film.interactions.slice(0,index).map(q=>[q.id,q.choices[0].id]));
  await page.evaluate(({film,answers})=>localStorage.setItem('treecourt.web.v1.cinema.'+film.id,JSON.stringify({revision:film.revision,time:0,answers})),{film,answers});
  await page.click('.char-phainon [data-film]');await page.waitForFunction(()=>document.querySelector('.cinematic-player')?.readyState>=2);
  await page.locator('[data-film-seek]').evaluate((el,at)=>{el.value=at;el.dispatchEvent(new Event('change'))},cue.at+.1);await page.locator(`[data-film-choice="${choice.id}"]`).click();
  await page.waitForFunction(url=>{const v=document.querySelector('.cinematic-player');return v?.getAttribute('src')===url&&v.readyState>=2&&!v.paused&&v.currentTime>.3},choice.clip_url);
  const state=await page.locator('.cinematic-player').evaluate(v=>({rate:v.playbackRate,width:v.videoWidth,height:v.videoHeight,currentTime:v.currentTime}));if(state.rate!==1||state.width!==1280)throw Error('Wrong video playback properties');
  await page.screenshot({path:join(output,`${cue.id}-${choice.id}.png`)});await page.locator('.cinematic-player').evaluate(v=>v.currentTime=v.duration-.25);
  await page.waitForFunction(url=>document.querySelector('.cinematic-player')?.getAttribute('src')===url,film.url,{timeout:20000});
  if(errors.length)throw Error(errors.join(';'));results.push({cue:cue.id,choice:choice.id,...state,returned_to_main:true,errors});await context.close();
 }
 await writeFile(join(output,'film-browser.json'),JSON.stringify({passed:true,media_revision:4,results},null,2));console.log('ELYSIA_FILM_BROWSER_VERIFIED');
}finally{await browser.close()}
