import {gradeVocabulary} from './vocabulary-grade.js';
// 本书词库独立于旧版词汇剧情；保留旧事件供历史记录重放。
export function createVocabularyUI({content,api=async()=>null,catalog,state,record,read,write,storageKey,show,notify,speak=()=>{},openClassroom=()=>{}}){
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let mode=read(`${storageKey}.vocabMode`,'study'),unit=read(`${storageKey}.vocabUnit`,1),query='',page=0,started=performance.now(),voiceTimer;
 const bank=()=>catalog().vocabulary_banks?.cet4;
 const entries=()=>bank().entries.filter(e=>(!unit||e.unit===Number(unit))&&(!query||`${e.word} ${e.meaning}`.toLowerCase().includes(query.toLowerCase())));
 const history=e=>state().vocabulary_attempts?.[e.id]||[];
 const label=e=>{const h=history(e),last=h.at(-1);return !last?'未复习':last.mode==='spelling'?(last.correct?'已拼对':'待复习'):last.response==='remembered'?'自评记住':'待复习';};
 function open(options={}){if(options.mode)mode=options.mode;write(`${storageKey}.vocabMode`,mode);location.hash='vocabulary';if(document.querySelector('#vocabulary-root'))render();}
 function source(e){
  const continuations=e.continuation_pages||[];
  show(`<p class="eyebrow">SOURCE WORD · PDF 第 ${e.page} 页</p><h2 id="modal-title">${esc(e.word)}</h2><p>${esc(e.meaning)}</p><p class="note">${e.review_status==='needs_review'?'此条识别结果待校对，请以原图为准。':'词条来自指定 PDF；自动识别仍可能有误，可在此核对。'}</p><button class="button light" id="vocab-source-full">查看整页</button><img class="network-source-image" id="vocab-source-image" src="/api/vocabulary/cet4/source/${e.id}" alt="单词与释义原图">${continuations.map((p,i)=>`<p>释义续页 · 第${p}页</p><img class="network-source-image" src="/api/vocabulary/cet4/source/${e.id}?part=${i+1}" alt="释义续页原图">`).join('')}`);
  document.querySelector('#vocab-source-full').onclick=()=>{document.querySelector('#vocab-source-image').src=`/api/vocabulary/cet4/source/${e.id}?full=true`;};
 }
 function render(){
  const b=bank();if(!b){content.innerHTML='<h1>四级词汇库</h1><p>词库暂未载入，请重启本地服务后刷新。</p>';return;}
  write(`${storageKey}.vocabMode`,mode);write(`${storageKey}.vocabUnit`,unit);
  const reviewed=b.entries.filter(e=>history(e).length).length,flagged=b.entries.filter(e=>e.review_status==='needs_review').length;
  content.innerHTML=`<section id="vocabulary-root"><p class="eyebrow">CET4 · YOUR SOURCE WORDBOOK</p><h1>四级词汇 · 英语四级核心词</h1><p class="muted">单词与释义以你提供的38页词表为来源，按原书 Unit 1–10 编排。</p><div class="button-row">${[['study','单词卡片'],['quick','单词＋中文速记'],['spelling','拼写练习']].map(([id,name])=>`<button class="button ${mode===id?'':'light'}" data-vocab-mode="${id}" aria-pressed="${mode===id}">${name}</button>`).join('')}<button class="button light" id="vocab-enter-classroom">在 3D 课堂中学习</button><a class="text-button" href="#home">返回课程表</a></div><div class="notes-controls"><label>单元<select id="vocab-unit"><option value="0" ${!unit?'selected':''}>全部单元</option>${b.units.map(u=>`<option value="${u.id}" ${Number(unit)===u.id?'selected':''}>${u.title} · ${u.count} 词条</option>`).join('')}</select></label><label>查找单词或中文<input id="vocab-query" value="${esc(query)}" placeholder="如 space、空间"></label><button class="button light" id="vocab-search">查找</button><button class="text-button" id="vocab-download">下载当前速记 TXT</button></div><p class="note">共 ${b.entries.length} 个词条 · 已留下复习记录 ${reviewed} 个。图片词表经离线识别，低置信度结果已对照原图修正；整本未逐词人工审定。点击词条可核对原图。${flagged?`${flagged}条待校对，不进入拼写练习。`:""}</p><p class="note" id="vocab-voice-state" role="status">正在核对本书录音进度…</p><div id="vocab-body"></div></section>`;
  clearTimeout(voiceTimer);const voiceLabel=document.querySelector('#vocab-voice-state');
  async function refreshVoice(){if(!voiceLabel.isConnected)return;try{const v=await api('/api/vocabulary-voice-status');if(v&&voiceLabel.isConnected)voiceLabel.textContent=`角色参考声线 AI 配音 · 单词发音 ${v.pronunciations.ready}/${v.pronunciations.expected} · 课堂台词 ${v.dialogue.ready}/${v.dialogue.expected} · ${{starting:'正在加载本机配音模型',running:'本机正在生成，完成后即可播放',complete:'本轮生成结束',failed:'生成已中断，可断点续跑',interrupted:'生成已中断，可断点续跑',partial:'部分录音需重试'}[v.generation.status]||'未运行生成任务'} · 非官方录音`;}catch{if(voiceLabel.isConnected)voiceLabel.textContent='录音进度暂时不可用，已生成录音仍可播放。';}if(voiceLabel.isConnected)voiceTimer=setTimeout(refreshVoice,15000);}
  refreshVoice();
  document.querySelector('#vocab-enter-classroom').onclick=()=>openClassroom();
  document.querySelectorAll('[data-vocab-mode]').forEach(el=>el.onclick=()=>{mode=el.dataset.vocabMode;page=0;render();});
  document.querySelector('#vocab-unit').onchange=e=>{unit=Number(e.target.value);page=0;render();};
  document.querySelector('#vocab-search').onclick=()=>{query=document.querySelector('#vocab-query').value.trim();page=0;draw();};
  document.querySelector('#vocab-query').onkeydown=e=>{if(e.key==='Enter')document.querySelector('#vocab-search').click();};
  document.querySelector('#vocab-download').onclick=()=>{const text=entries().map(e=>`${e.word}\t${e.meaning}`).join('\n'),url=URL.createObjectURL(new Blob(['\ufeff'+text],{type:'text/plain;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=`四级核心词-Unit${unit||'全部'}.txt`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};draw();
 }
 function draw(){
  let list=entries();if(mode==='spelling')list=list.filter(e=>e.review_status!=='needs_review');const target=document.querySelector('#vocab-body');
  if(!list.length){target.innerHTML='<p>当前筛选没有词条。可换一个单元或清空查找条件。</p>';return;}
  if(mode==='quick'){
   const size=80,last=Math.max(0,Math.ceil(list.length/size)-1);page=Math.min(page,last);
   target.innerHTML=`<p class="muted small">${list.length} 词条 · 第 ${page+1}/${last+1} 页。点击单词核对原图。</p><table class="quick-table"><thead><tr><th>单词</th><th>中文</th></tr></thead><tbody>${list.slice(page*size,(page+1)*size).map(e=>`<tr><td><button class="text-button" data-vocab-source="${e.id}">${esc(e.word)}</button></td><td>${esc(e.meaning)}</td></tr>`).join('')}</tbody></table><div class="button-row"><button class="button light" id="vocab-prev">上一页</button><button class="button light" id="vocab-next">下一页</button></div>`;
   document.querySelector('#vocab-prev').onclick=()=>{page=Math.max(0,page-1);draw();};document.querySelector('#vocab-next').onclick=()=>{page=Math.min(last,page+1);draw();};
  }else{
   const checkpointKey=`${storageKey}.vocabPosition.${unit}.${mode}`,position=read(checkpointKey,0),index=Math.max(0,Math.min(position,list.length-1)),e=list[index];started=performance.now();
   target.innerHTML=`<article class="vocabulary-card"><div class="heading-row"><span>Unit ${e.unit} · ${index+1}/${list.length} · 原书第${e.page}页</span><span id="vocab-progress-label">${label(e)}</span></div>${mode==='study'?`<h2 class="vocabulary-word">${esc(e.word)}</h2><button class="button light" data-vocab-pronounce="${e.id}">▶ 单词发音</button><button class="button light" id="vocab-flip">看中文释义</button><p id="vocab-meaning" class="vocabulary-meaning" hidden>${esc(e.meaning)}</p><div class="button-row"><button class="button" data-vocab-rating="remembered">自评 · 记住了</button><button class="button light" data-vocab-rating="again">还需复习</button></div>`:`<p class="vocabulary-meaning">${esc(e.meaning)}</p><form id="vocab-spelling"><label>写出这个单词<input id="vocab-spelling-input" maxlength="120" autocomplete="off" spellcheck="false" required value="${esc(read(`${storageKey}.vocabDraft.${e.id}`,''))}" placeholder="输入英文拼写"></label><button class="button" type="submit">核对拼写</button></form><p id="vocab-feedback" role="status"></p>`}<button class="text-button" data-vocab-source="${e.id}">${e.review_status==='needs_review'?'识别待校对 · 查看原图':'核对原书词条'}</button><div class="button-row vocabulary-navigation"><button class="button light" id="vocab-prev">上一个词</button><button class="button light" id="vocab-next">下一个词</button></div></article>`;
   const move=delta=>{write(checkpointKey,Math.max(0,Math.min(list.length-1,index+delta)));draw();};document.querySelector('#vocab-prev').onclick=()=>move(-1);document.querySelector('#vocab-next').onclick=()=>move(1);
   document.querySelector('#vocab-flip')?.addEventListener('click',()=>{document.querySelector('#vocab-meaning').hidden=false;});
   document.querySelectorAll('[data-vocab-rating]').forEach(el=>el.onclick=()=>{recordAttempt(e,'self_review',el.dataset.vocabRating);document.querySelector('#vocab-progress-label').textContent=label(e);notify('自评已保存；自评不计作客观正确率。');});
   const form=document.querySelector('#vocab-spelling');if(form){document.querySelector('#vocab-spelling-input').oninput=ev=>write(`${storageKey}.vocabDraft.${e.id}`,ev.target.value);form.onsubmit=ev=>{ev.preventDefault();try{const response=document.querySelector('#vocab-spelling-input').value,correct=gradeVocabulary(e,'spelling',response);recordAttempt(e,'spelling',response);document.querySelector('#vocab-feedback').textContent=correct?`拼写匹配：${e.word}。${e.meaning}`:`再看一遍：${e.word}。${e.meaning}。可以修改后重试，不扣好感。`;document.querySelector('#vocab-progress-label').textContent=label(e);}catch(err){notify(err.message);}};}
  }
  target.querySelectorAll('[data-vocab-pronounce]').forEach(el=>el.onclick=()=>{const e=bank().entries.find(e=>e.id===el.dataset.vocabPronounce),spoken=e.accepted_spellings.find(x=>!/[(/]/.test(x))||e.word;speak(spoken,'anaxa','pronounce-'+e.id);});
  target.querySelectorAll('[data-vocab-source]').forEach(el=>el.onclick=()=>source(bank().entries.find(e=>e.id===el.dataset.vocabSource)));
 }
 function recordAttempt(e,mode,response){record('vocabulary_attempt',{word_id:e.id,mode,response,response_ms:Math.min(900000,Math.round(performance.now()-started))});}
 return {open,render};
}
