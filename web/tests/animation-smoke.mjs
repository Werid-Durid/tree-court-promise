// 使用独立测试服务；仅预览动画，不提交学习事件。
import {createRequire} from 'node:module';
import {join,resolve} from 'node:path';
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const require=createRequire(join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/package.json'));
const {chromium}=require('playwright');
const out=resolve('blender/animation-reports/previews');await mkdir(out,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.TREECOURT_TEST_URL||'http://127.0.0.1:8768/');await page.locator('#hero-start').click();
 await page.locator('.scene-host[data-animated="4"]').waitFor({timeout:120000});
 await page.screenshot({path:join(out,'classroom-browser.png'),fullPage:true});
 await page.locator('[data-view="teacher"]').click();
 await page.screenshot({path:join(out,'teacher-browser.png'),fullPage:true});
 const bytes=await page.locator('.scene-host canvas').evaluate(async canvas=>{
  const stream=canvas.captureStream(24),chunks=[];const recorder=new MediaRecorder(stream,{mimeType:'video/webm;codecs=vp9',videoBitsPerSecond:2500000});
  return await new Promise(resolve=>{recorder.ondataavailable=e=>chunks.push(e.data);recorder.onstop=async()=>{stream.getTracks().forEach(t=>t.stop());resolve(Array.from(new Uint8Array(await new Blob(chunks).arrayBuffer())));};recorder.start();setTimeout(()=>recorder.stop(),25000);});
 });await writeFile(join(out,'teacher-classroom.webm'),Buffer.from(bytes));
 await page.locator('[data-view="classmates"]').click();await page.screenshot({path:join(out,'students-browser.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 const status=await(await page.request.get(new URL('/api/animation-status',page.url()).href)).json();
 assert.equal(Object.values(status.characters).filter(c=>c.available).length,4);assert.deepEqual(errors,[]);
 const result={passed:true,animated_characters:4,mobile_overflow:false,errors};await writeFile(join(out,'browser-result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{await browser.close();}
