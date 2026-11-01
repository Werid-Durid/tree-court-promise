import {createRequire} from 'node:module';
import {join,resolve} from 'node:path';
import {writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const require=createRequire(join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/package.json'));
const {chromium}=require('playwright');
const base=process.env.TREECOURT_TEST_URL||'http://127.0.0.1:8768';
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1280,height:950}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>{
  const NativeAudio=window.Audio;window.__voicePlayed=[];
  window.Audio=function(url){const player=new NativeAudio(url);player.addEventListener('playing',()=>window.__voicePlayed.push(url));return player;};
 });
 await page.goto(base+'/#companions');
 const buttons=page.getByRole('button',{name:'▶ 试听角色开场'});await buttons.first().waitFor();assert.equal(await buttons.count(),4);
 const manifest=await(await page.request.get(base+'/api/voice-status')).json();
 const result=[];
 for(const [i,id]of ['anaxa','hyacine','castor','phainon'].entries()){
  const entry=manifest.clips.find(c=>c.id==='intro-'+id);assert.equal(entry.character,id);assert.equal(entry.synthetic,true);
  const audio=await page.request.get(base+entry.url);assert.equal(audio.status(),200);assert.match(audio.headers()['content-type'],/audio\/wav/);assert.ok((await audio.body()).length>20000);
  await buttons.nth(i).click();await page.waitForFunction(url=>window.__voicePlayed.includes(url),entry.url,{timeout:15000});
  const decoded=await page.evaluate(async url=>{const ctx=new AudioContext();try{const wav=await ctx.decodeAudioData(await(await fetch(url)).arrayBuffer());return {duration:wav.duration,channels:wav.numberOfChannels,rate:wav.sampleRate};}finally{await ctx.close();}},entry.url);
  assert.ok(decoded.duration>1&&decoded.duration<30);result.push({id,url:entry.url,...decoded});
 }
 assert.deepEqual(errors,[]);
 await page.screenshot({path:resolve('data/voice/research/companions-voice.png'),fullPage:true});
 await writeFile(resolve('data/voice/research/browser-verification.json'),JSON.stringify({passed:true,clips:result,page_errors:errors},null,2));
 console.log('FOUR_CHARACTER_PLAYBACK_VERIFIED');
}finally{await browser.close();}
