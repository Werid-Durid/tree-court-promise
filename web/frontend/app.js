import {studyChoice,saveStudyChoice,companionPicker,STUDY_PEOPLE} from './study-companions.js';
import {createKnowledgeHub} from './knowledge-hub.js';
import {createInvitations} from './invitations.js';
import {bondStage} from './invitation-state.js';
import {createFilmPlayer} from './cinema-player.js';
import {createCharacterChat} from './character-chat.js';
import {resetProgressStorage} from './progress-reset.js';
import {saveCatalog,loadCatalog} from './catalog-cache.js';
import {reduceEvents,eligibleForRomance} from './state.js';
import {createCourseUI} from './course-ui.js';
import {createExamUI} from './exams.js?v=postgrad-exams-20261029';
import {createNetworkCourse} from './network-course.js?v=postgrad-20261025';
import {createVocabularyClassroom} from './vocabulary-classroom.js';
import {createVocabularyUI} from './vocabulary.js';
import {mountSkillInteraction,evaluateInteraction} from './story-engine.js';

const $=(s,root=document)=>root.querySelector(s);
const content=$('#content'),modal=$('#modal');
const KEY='treecourt.web.v1';
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dateLabel=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',month:'long',day:'numeric',weekday:'long'});
let persisted=true,resettingProgress=false;
let progressEpoch='initial';
function read(key,fallback){try{return JSON.parse(localStorage.getItem(key))??fallback;}catch{return fallback;}}
function write(key,value){try{localStorage.setItem(key,JSON.stringify(value));return true;}catch{persisted=false;$('#sync-status').textContent='设备存储不可用 · 请导出档案';return false;}}
let saved=read(KEY,null);
if(!saved||!Array.isArray(saved.events)||typeof saved.profile!=='string')saved={version:1,profile:crypto.randomUUID(),events:[],synced:[],quarantined:[]};
saved.synced??=[]; saved.quarantined??=[];
let settings=read(`${KEY}.settings`,{instant:matchMedia('(prefers-reduced-motion: reduce)').matches});
settings.voice??=true;
let catalog,policy,state,online=false,syncing=false,syncAgain=false,route='home',lesson=null,typeTimer,viewToken=0,questionAt=0;
let focus=null,focusTimer,focusPaused=false,audio=null;
let sceneHost=null,sceneApi=null,sceneModule=null,wallpaperModule=null,sceneGeneration=0,voiceAudio=null,voiceClips=new Map(),voiceRequest=0;
let currentSpeech=null;
const names={partner:'学术搭档',friend:'好友 · 学术搭档',romance:'亲密同行 · 学术搭档'};
const char=id=>catalog.characters.find(c=>c.id===id);
const point=id=>catalog.points.find(p=>p.id===id);
const portrait=(c,variant='head')=>`/art/portraits/${c.portrait}_${variant}.png`;
const minute=ms=>Math.floor(ms/60000);
const count=()=>Object.keys(state.attempts).length;
const weak=()=>catalog.points.filter(p=>state.attempts[p.id]?.length&&!state.attempts[p.id].at(-1).correct);
const event=(type,payload)=>({event_id:crypto.randomUUID(),type,payload:{...payload,policy_version:2},at:new Date().toISOString()});
const examUI=createExamUI({content,api,read,write,storageKey:KEY,notify});
const vocabularyUI=createVocabularyUI({content,api,catalog:()=>catalog,state:()=>state,record,read,write,storageKey:KEY,show:showDialog,notify,speak:(text,id,clip)=>playVoice(text,id,clip),openClassroom:()=>courseUI.menu('cet4','核心词汇课堂')});
const networkCourse=createNetworkCourse({read,write,storageKey:KEY,state:()=>state,record,show:showDialog,redraw:()=>classroom(),notify,speak:id=>talkCharacter(id)});
const wordClass=createVocabularyClassroom({read,write,storageKey:KEY,redraw:()=>classroom(),show:showDialog,talk:id=>talkCharacter(id)});
const courseUI=createCourseUI({catalog:()=>catalog,state:()=>state,show:showDialog,close:closeDialog,start:(id,index)=>startLesson('continue',id,index),record,storageKey:KEY,write,read,speak:(text,id)=>playVoice(text,id,null),openExams:id=>examUI.open(id),openVocabulary:options=>vocabularyUI.open(options)});
const knowledgeUI=createKnowledgeHub({content,catalog:()=>catalog,state:()=>state,read,write,key:KEY,record,start:(id,index)=>startLesson('continue',id,index),assessment:id=>courseUI.assessment(id),notify});
const invitationUI=createInvitations({content,catalog:()=>catalog,state:()=>state,record,read,write,key:KEY,speak:playVoice,stopVoice,notify,esc:escape,show:showDialog});
const filmPlayer=createFilmPlayer({root:modal,show:showDialog,read,write,key:KEY,esc:escape});
const activeChapter=()=>courseUI.chapter(lesson?.chapter_id||read(`${KEY}.lastChapter`,'cet4-01'));
let activeSeconds=0,lastActivity=0,lastTick=performance.now();
// 仅累计前台、近期有操作的课堂/检测时间，作答事件不再重复加上等待时间。
for(const name of ['pointerdown','keydown','wheel'])document.addEventListener(name,()=>{lastActivity=Date.now();},{passive:true});
function flushStudy(){if(activeSeconds>=1&&catalog){const seconds=Math.min(60,Math.floor(activeSeconds));activeSeconds-=seconds;record('study_tick',{seconds});}}
setInterval(()=>{const now=performance.now(),dt=Math.min(2,(now-lastTick)/1000);lastTick=now;if(catalog&&!document.hidden&&(['classroom','vocabulary'].includes(route)||document.querySelector('#chapter-test'))&&Date.now()-lastActivity<90000){activeSeconds+=dt;if(activeSeconds>=30)flushStudy();}},1000);
function rebuild(){state=reduceEvents(saved.events,catalog,policy);}
function persist(){if(!resettingProgress)write(KEY,saved);}
// 先写浏览器存档，再尝试同步；短暂断线不会丢失当前选择。
function record(type,payload){if(resettingProgress)return;const e=event(type,payload);saved.events.push(e);rebuild();persist();sync();return e;}
function notify(text){$('#toast').textContent=text;$('#toast').classList.add('show');clearTimeout(notify.timer);notify.timer=setTimeout(()=>$('#toast').classList.remove('show'),3800);}
async function api(path,options={}){const {rawBlob,...requestOptions}=options;const r=await fetch(path,{...requestOptions,headers:{Authorization:`Bearer ${saved.profile}`,'X-Treecourt-Epoch':progressEpoch,...options.headers},signal:AbortSignal.timeout(20000)});if(!r.ok){const j=await r.json().catch(()=>({}));if(j.detail==='progress_reset'){resettingProgress=true;location.reload();}throw new Error(j.detail||`请求失败 (${r.status})`);}return rawBlob?r.blob():r.json();}
// 以事件 ID 合并服务端记录和待提交事件；请求期间的新事件仍保留在队列中。
async function sync(){
  if(syncing){syncAgain=true;return;}syncing=true;
  $('#sync-status').textContent='正在同步档案…';
  try{
    const known=new Set(saved.synced),pending=saved.events.filter(e=>!known.has(e.event_id));
    if(pending.length){
      const result=await api('/api/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({events:pending.slice(0,500)})});
      const rejected=new Set(result.rejected.map(e=>e.event_id));
      saved.quarantined.push(...saved.events.filter(e=>rejected.has(e.event_id)));
      const merged=new Map(result.events.map(e=>[e.event_id,e]));
      for(const e of saved.events)if(!merged.has(e.event_id)&&!rejected.has(e.event_id))merged.set(e.event_id,e);
      saved.events=[...merged.values()];saved.synced=result.events.map(e=>e.event_id);
      if(result.rejected.length)notify('部分记录未通过校验，已保留在导出档案中。');
      if(pending.length>500)syncAgain=true;
    }else{
      const result=await api('/api/user');
      const merged=new Map(result.events.map(e=>[e.event_id,e]));
      for(const e of saved.events)if(!merged.has(e.event_id))merged.set(e.event_id,e);
      saved.events=[...merged.values()];saved.synced=result.events.map(e=>e.event_id);
    }
    online=true;rebuild();persist();$('#sync-status').textContent=persisted?'档案已保存 · 本地同步':'已同步 · 设备存储不可用';
  }catch{online=false;$('#sync-status').textContent=persisted?'已存于浏览器 · 等待本地服务':'暂存于内存 · 请导出档案';}
  finally{syncing=false;if(syncAgain){syncAgain=false;setTimeout(sync,250);}}
}
function showDialog(html){$('#modal-body').innerHTML=html;if(!modal.open)modal.showModal();}
function closeDialog(){stopVoice();modal.close();}
modal.addEventListener('close',()=>{filmPlayer.close();modal.querySelectorAll('video').forEach(video=>video.pause());});
$('#modal-close').onclick=closeDialog;
modal.addEventListener('cancel',stopVoice);
modal.addEventListener('click',e=>{if(e.target===modal)closeDialog();});
$('#settings-button').onclick=()=>{
  showDialog(`<p class="eyebrow">READING PREFERENCES</p><h2 id="modal-title">按你的节奏阅读</h2><p class="muted">文字可以缓缓出现，也可以一次展开。</p><label class="toggle-row"><span>直接显示全部对白</span><input id="instant-setting" type="checkbox" ${settings.instant?'checked':''}></label><p class="note">进度保存在浏览器与本地 SQLite。请勿在公共设备上共用同一个浏览器档案。</p><button class="button light" id="export-settings">导出学习档案 ↓</button>`);
  $('#instant-setting').onchange=e=>{settings.instant=e.target.checked;write(`${KEY}.settings`,settings);};$('#export-settings').onclick=exportData;
};
function exportData(){const a=document.createElement('a');const url=URL.createObjectURL(new Blob([JSON.stringify({...saved,exported_at:new Date().toISOString()},null,2)],{type:'application/json'}));a.href=url;a.download='树庭学习档案.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function progressDots(){return `<div class="lesson-dots" aria-label="本章知识点进度">${activeChapter().points.map(point).map((p,i)=>`<span class="${state.attempts[p.id]?'done':''} ${lesson&&lesson.ids[lesson.index]===p.id?'current':''}" title="${i+1}. ${p.concept}"></span>`).join('')}</div>`;}
function statCard(value,label,detail){return `<div class="stat"><strong>${value}</strong><span>${label}</span><small>${detail}</small></div>`;}
function home(){
 const complete=state.completed.includes(activeChapter().id),started=count()>0;
 content.innerHTML=`<div class="heading-row"><div><p class="eyebrow">THE GROVE OF KNOWLEDGE</p><h1>欢迎回到，神悟树庭<span class="heading-star">✧</span></h1><p class="muted">不必急着抵达。今天，也和知识靠近一点。</p></div><div class="date-label">${dateLabel.format(new Date())}<small>适合开启一段新的修习</small></div></div>
 <section class="hero"><div class="hero-grain"></div><div class="hero-copy"><span class="pill">自由选学 <span>·</span> 英语 · 高数 · 线代 · 概率统计 · 考研 408</span><h2>在树庭，<br>让每一次理解都有回响。</h2><p>英语、高数上下册、线代、概率统计与 408 四科，四位学术搭档。<br>从你需要的知识点开始，让线索留在记忆里。</p><button class="button gold" id="hero-start">选择板块与进度<span>↗</span></button><small>${count()} / ${catalog.points.length} 个知识点 · 自由选择</small></div><img class="hero-character" src="${portrait(char('anaxa'),'full')}" alt="那刻夏在树庭等候开课"><div class="hero-quote"><span>「</span>不必记住我的结论。<br>记住你如何抵达它。<small>— 阿那克萨戈拉斯</small></div><span class="hero-number">01 <i>/ 约定从这里开始</i></span></section>
 <section class="stats-row" aria-label="修习概况">${statCard(`${count()}<em>/${catalog.points.length}</em>`,'已相识的知识点','每一步，都算数')}${statCard(`${minute(state.study_ms)}<em>分钟</em>`,'累计修习时间','按自己的节奏前行')}${statCard(`${state.completed.length}<em>章</em>`,'已完成的篇章','理解，终将连成风景')}<div class="stat companion-stat"><div class="avatar-stack">${catalog.characters.map(c=>`<img src="${portrait(c)}" alt="${c.name}">`).join('')}</div><span>四位学术搭档</span><small>在求知路上，彼此照应</small></div></section>
 <section><div class="section-heading"><div><p class="eyebrow">YOUR CURRICULUM</p><h2>树庭课程表</h2></div><span class="muted small">选择一门课，让好奇心带路</span></div><div class="subject-grid">${catalog.subjects.map((s,i)=>`<button class="subject-card ${s.status==='available'?'available':''}" data-subject="${s.id}"><div class="subject-top"><span class="subject-icon">${escape(s.icon)}</span><span class="tag ${s.status==='available'?'green':''}">${s.id==='cet6'&&s.status!=='available'?'真题已开放':s.status==='available'?'可修习':'筹备中'}</span></div><small>${s.en}</small><h3>${s.name}</h3><p>${s.description}</p><div class="subject-bottom">${s.id==='cet6'&&s.status!=='available'?'历年真题 · 刷题与考试模式':s.id==='cet4'&&s.vocabulary_bank?`${catalog.vocabulary_banks.cet4.entries.length} 词条 · 10个Unit`:s.status==='available'?`${s.chapters.length} 个可选小章 · 随时切换`:'首章教案正在整理'}<span>${s.status==='available'?'↗':'＋'}</span></div></button>`).join('')}</div></section>
 <section class="garden-note"><a class="button light" id="home-cet4-papers" href="#library-exams">智库 · 英语 / 408 真题计时模拟 ↗</a></section><section class="garden-note"><span>❧</span><div><h3>学习不是一场独行。</h3><p>遇到不熟悉的知识，可以再听一遍，也可以先去自习室坐坐。</p></div><a href="#focus">去树荫下歇一会儿 ↗</a></section>`;
 $('#hero-start').onclick=()=>courseUI.menu();
 document.querySelectorAll('[data-subject]').forEach(b=>b.onclick=()=>showSubject(b.dataset.subject));
}
function showSubject(id){
 const subject=catalog.subjects.find(s=>s.id===id);
 if(id==='cet6'&&catalog.subjects.find(s=>s.id===id)?.status!=='available'){examUI.open(id);return;}
 if(subject?.status==='available'&&subject.chapters?.length){courseUI.menu(id);return;}
 showDialog(`<h2 id="modal-title">${escape(subject.name)}</h2><p>本课程教案仍在整理。可先选择四级英语、高等数学或考研 408。</p>`);
}
// 各章节分别记住起点；显式选择知识点优先于自动继续。
function startLesson(mode='continue',chapterId=null,selectedIndex=null){
 const ch=courseUI.chapter(chapterId||read(`${KEY}.lastChapter`,'cet4-01'));
 if(ch.archived&&mode==='continue'&&selectedIndex===null){courseUI.menu('cet4','核心词汇课堂');return;}
 let ids=[...ch.points],index=0,phase='intro';
 if(mode==='weak')ids=ids.filter(id=>state.attempts[id]?.length&&!state.attempts[id].at(-1).correct);
 if(!ids.length){notify('本章暂时没有待巩固的知识点。');courseUI.menu();return;}
 const checkpoint=read(`${KEY}.lesson.${ch.id}`,null)||read(`${KEY}.lesson`,null);
 if(Number.isInteger(selectedIndex)){index=Math.max(0,Math.min(selectedIndex,ids.length-1));phase='prompt';}
 else if(mode==='continue'&&checkpoint&&checkpoint.ids?.every(id=>ch.points.includes(id))&&Number.isInteger(checkpoint.index)&&checkpoint.index>=0&&checkpoint.index<checkpoint.ids.length&&['intro','prompt','feedback'].includes(checkpoint.phase)){
  ids=checkpoint.ids;index=checkpoint.index;phase=checkpoint.phase;
 }else if(mode==='continue'){const next=ids.findIndex(id=>!state.attempts[id]);index=next<0?0:next;phase=index?'prompt':'intro';}
 else if(mode==='weak')phase='prompt';
 lesson={chapter_id:ch.id,ids,index,phase,mode};write(`${KEY}.lastChapter`,ch.id);saveLesson();location.hash='classroom';if(route==='classroom')render();
}
function saveLesson(){write(`${KEY}.lesson`,lesson);write(`${KEY}.lesson.${lesson.chapter_id||activeChapter().id}`,lesson);}
function stage(type,payload){api('/api/stage/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({protocol_version:1,event_id:crypto.randomUUID(),sequence:saved.events.length,type,payload})}).then(result=>{const status=$('#ue-stage-status');if(status&&(!payload.point_id||lesson?.ids[lesson.index]===payload.point_id)){status.textContent=result.executed?'UE5 黑板已同步':result.reason||'UE5 未连接';status.dataset.executed=String(!!result.executed);}}).catch(()=>{const status=$('#ue-stage-status');if(status)status.textContent='UE5 联动暂不可用';});}
function typeText(text){
 clearInterval(typeTimer);const target=$('#dialogue-text');if(!target)return;
 if(settings.instant){target.textContent=text;return;}
 let index=0;target.textContent='';typeTimer=setInterval(()=>{if(!target.isConnected){clearInterval(typeTimer);return;}target.textContent=text.slice(0,index+=2);if(index>=text.length)clearInterval(typeTimer);},26);
 const skip=$('#skip-typing');if(skip)skip.onclick=()=>{clearInterval(typeTimer);target.textContent=text;};
}
function classroom(){
 stopVoice();
 if(!lesson){startLesson();return;}
 if(sceneHost)sceneHost.remove();
 const p=point(lesson.ids[lesson.index]),c=char(lesson.phase==='prompt'?(p.vocabulary_lesson?wordClass.speaker(p):p.course?networkCourse.speaker(p):(p.speaker||p.character)):(p.speaker||p.character)),history=state.attempts[p.id]||[],last=history.at(-1),feedback=lesson.phase==='feedback';
 if(feedback&&!last)lesson.phase='prompt';
 const intro=lesson.phase==='intro';
 const text=intro?activeChapter().opening:feedback?(last.correct?p.feedback.matched:p.feedback.redirect):p.vocabulary_lesson?wordClass.text(p):p.course?networkCourse.text(p):p.prompt;
 questionAt=performance.now();
 content.innerHTML=`<section class="classroom"><div class="class-top"><a href="#home" class="text-button">← 回到课程表</a><span>${escape(activeChapter().subject_name)} / ${escape(activeChapter().title)}</span><a href="#focus" class="text-button">☾ 进入自习室</a></div><div class="class-stage"><div class="stage-vignette"></div><div class="stage-title"><p class="eyebrow">TREE COURT · CLASSROOM</p><h2>神悟树庭课堂</h2><span class="stage-status">◇ 平面立绘陪伴 · UE5 待接入</span></div><img class="class-character" src="${portrait(c,'full')}" alt="${c.name}的课堂立绘"><div class="character-plaque"><span>${c.role}</span><h2>${c.address}</h2><small>${names[state.relationships[c.id]]}</small></div><div class="class-roster">${catalog.characters.map(t=>`<span class="roster-item ${c.id===t.id?'active':''}"><img src="${portrait(t)}" alt=""><span>${t.name}<small>${state.affection[t.id]} / 100</small></span></span>`).join('')}</div></div><div class="dialogue-panel"><div class="dialogue-header"><span class="speaker">${c.address}<small>${c.role}</small></span><span class="affection-label">好感 · ${state.affection[c.id]}<span class="affection-track"><i class="affection-fill" data-value="${state.affection[c.id]}"></i></span></span><button class="text-button" id="skip-typing">展开对白</button></div><p id="dialogue-text" class="dialogue-text" aria-live="off"></p>${!intro?`<div class="word-line"><h3 lang="en">${p.concept}</h3><span>${p.summary}</span><span class="tag">${lesson.index+1} / ${lesson.ids.length}</span></div>`:''}${feedback?`<div class="memory-hook"><span>✧ 留一条记忆的线索</span><p>${p.memoryHook}</p><blockquote lang="en">${p.example.en}<small>${p.example.zh}</small></blockquote></div><div class="dialogue-actions"><span class="muted small">${last.correct?'这条线索，已与你的记忆相连。':'再见到它时，就多了一条能认出的路。'} 选错不扣好感。</span><button class="button" id="next-point">${lesson.index===lesson.ids.length-1?'翻到本章回顾':'沿着线索，继续'} →</button></div>`:intro?`<div class="intro-actions"><span class="muted">每次选择后，都会留下一条记忆钩子。</span><button class="button" id="begin-question">翻开第一张知识手札 →</button></div>`:`<p class="clue-label">沿哪条线索推演，能解释这个情境？</p><div class="clues">${p.clues.map((clue,i)=>`<button class="clue" data-clue="${clue.id}"><span class="clue-symbol">${['❧','◇','✧'][i]}</span>${clue.text}</button>`).join('')}</div>`}${progressDots()}</div></section>`;
 document.querySelectorAll('.affection-fill').forEach(e=>e.style.width=`${e.dataset.value}%`);
 typeText(text);stage(feedback?'feedback':'dialogue',{character:c.id,emotion:feedback?'encouraging':'neutral',point_id:p.id,lesson_step:p.vocabulary_lesson?wordClass.step(p):undefined});
 if(p.vocabulary_lesson&&!intro&&!feedback)wordClass.mount(p);
 if(p.course&&!intro&&!feedback)networkCourse.mount(p);
 if(p.micro_lesson&&!p.course&&!intro&&!feedback){
  // 微课卡展开机制、情境与推演，帮助回看；不改变选题或检测计分规则。
  const sheet=document.createElement('details');sheet.className='micro-lesson';
  sheet.innerHTML=`<summary>展开微课手札 · 条件与推演</summary><ol>${p.micro_lesson.steps.map(s=>`<li><strong>${escape(s.label)}</strong><p>${escape(s.text)}</p></li>`).join('')}</ol><p>易混边界：${escape(p.micro_lesson.common_traps[0])}</p><p>记忆钩子：${escape(p.memoryHook)}</p>`;
  $('.word-line').after(sheet);
 }
 setupGameScene(p,text,intro,feedback);
 if(intro)$('#begin-question').onclick=()=>{lesson.phase='prompt';saveLesson();classroom();};
 if(!intro&&!feedback&&p.interaction)mountSkillInteraction({point:p,container:$('.clues'),onError:notify,onSubmit:response=>{
  if(lesson.phase!=='prompt')return;
  const correct=evaluateInteraction(p.interaction,response);
  record('attempt',{point_id:p.id,clue_id:correct?'structured-match':'structured-retry',interaction_response:response,response_ms:Math.min(900000,Math.round(performance.now()-questionAt)),study_ms:0});
  lesson.phase='feedback';saveLesson();classroom();
 }});
 document.querySelectorAll('[data-clue]').forEach(b=>b.onclick=()=>{
   if(lesson.phase!=='prompt')return;
   const response=Math.min(900000,Math.round(performance.now()-questionAt));
   record('attempt',{point_id:p.id,clue_id:b.dataset.clue,response_ms:response,study_ms:0});
   lesson.phase='feedback';saveLesson();classroom();stage('feedback',{character:c.id,emotion:'encouraging',point_id:p.id});
 });
 if(feedback)$('#next-point').onclick=()=>{
   if(lesson.index<lesson.ids.length-1){lesson.index++;lesson.phase='prompt';saveLesson();classroom();}
   else{if(activeChapter().points.every(id=>state.attempts[id])&&!state.completed.includes(activeChapter().id))record('chapter_complete',{chapter_id:activeChapter().id});write(`${KEY}.lesson`,null);location.hash='summary';}
 };
}
function summary(){
 const chapter=activeChapter(),all=chapter.points.map(point).filter(p=>state.attempts[p.id]),fresh=all.filter(p=>state.attempts[p.id].at(-1).correct),needs=weak().filter(p=>p.chapter===chapter.id);
 content.innerHTML=`<section class="summary-page"><span class="summary-seal">❧</span><p class="eyebrow">A CHAPTER TO REMEMBER</p><h1>今天的理解，已在树庭生根。</h1><p class="muted">${state.completed.includes(chapter.id)?`${chapter.title}已完成。可以检测，也可以切换板块。`:'这一轮回顾结束。随时回来，继续理解余下的知识点。'}</p><div class="summary-stats">${statCard(all.length,'已相识的知识点','每个知识点都有自己的线索')}${statCard(fresh.length,'已连接的线索','按最近一次回顾记录')}${statCard(needs.length,'可以再照顾的知识点','不急，我们还会相遇')}</div><div class="summary-voices">${catalog.characters.map(c=>`<div><img src="${portrait(c)}" alt=""><p><strong>${c.name}</strong>${c.hook}</p><span>好感 ${state.affection[c.id]}</span></div>`).join('')}</div><div class="button-row"><button class="button" id="summary-review">${needs.length?'再照顾一下不熟悉的知识点':'重温本章知识点'} →</button><a class="button light" href="#companions">看看同行之人的手札</a><a class="text-button" href="#home">回到课程表</a></div><p class="note">所有板块均可自由进入，检测分数不限制选课。</p></section>`;
 $('#summary-review').onclick=()=>startLesson(needs.length?'weak':'replay');
 const check=document.createElement('button');check.className='button light';check.textContent='章节测试';check.onclick=()=>courseUI.assessment(chapter.id);$('#summary-review').after(check);
 const choose=document.createElement('button');choose.className='button light';choose.textContent='选择板块与进度';choose.onclick=()=>courseUI.menu();check.after(choose);
}
function companions(){
 const parts=state.affection_breakdown;
 content.innerHTML=`<section class="companions-page" aria-labelledby="companions-title">
  <div class="heading-row"><div><p class="eyebrow">THOSE WHO WALK BESIDE YOU</p><h1 id="companions-title">同行之人</h1><p class="muted">选一位同行之人，赴约，或留下今天的回忆。</p></div><span class="companions-count">四位同行 · 各自相知</span></div>
  <section class="companions-progress" aria-label="共同修习贡献"><div class="companions-progress-title"><span class="eyebrow">一起走过的时间</span><strong>共同修习</strong></div><div class="companions-progress-values"><span>章节测试 <b>${parts.tests}<small> / 60</small></b></span><span>有效练习 <b>${parts.practice}<small> / 20</small></b></span><span>学习时长 <b>${parts.time}<small> / 20</small></b></span></div><details class="affection-explainer"><summary>好感如何积累</summary><p>各章最高分每 10 分贡献 1 点；每 5 次有效练习贡献 1 点，同题每天最多计 3 次；每 15 分钟有效学习贡献 1 点。课堂仅计算前台且 90 秒内有操作的时间，专注模式按计时器记录。答错不扣好感。邀约关键相处为对应角色额外贡献最多 ${catalog.invitations.bond_cap} 点，同一节点仅记一次；总好感上限 100。</p></details></section>
  <div class="companion-grid">${catalog.characters.map(c=>{
   const story=catalog.invitations.stories.find(s=>s.character===c.id);
   return `<article class="companion-card char-${c.id}" aria-labelledby="companion-name-${c.id}"><div class="companion-art"><img src="${portrait(c,'full')}" alt="${escape(c.name)}" loading="lazy"></div><div class="companion-info">
    <header class="companion-identity"><span class="eyebrow">${escape(c.role)}</span><h2 id="companion-name-${c.id}">${escape(c.name)}</h2><span class="tag">${names[state.relationships[c.id]]}</span></header>
    <section class="companion-bond" aria-label="${escape(c.name)}的好感进度"><div class="bond-row"><span>${bondStage(state.affection[c.id])}</span><strong>${state.affection[c.id]}<small> / 100</small></strong></div><progress max="100" value="${state.affection[c.id]}" aria-label="${escape(c.name)}好感"></progress><div class="milestones">${policy.academic_thresholds.map(t=>`<span class="${state.affection[c.id]>=t?'unlocked':''}">${t} · ${t===30?'心事':t===60?'默契':'信赖'}</span>`).join('')}</div><p class="companion-bond-note">专属相处 <b>${state.bond_points?.[c.id]||0}</b> / ${catalog.invitations.bond_cap}</p></section>
    <section class="companion-invitation"><span class="eyebrow">与你的邀约</span><h3>${escape(story.title)}</h3><p>${escape(story.synopsis||'')}</p><div class="companion-main-actions"><button class="button light" data-invite="${c.id}">${state.outings[c.id]?'继续文字邀约 · 查看回忆':'开启文字邀约'}</button></div></section>
    <div class="companion-utilities"><button class="text-button" data-bond="${c.id}">▷ 鼓励语音</button><button class="text-button" data-memories="${c.id}">回忆手札</button><button class="text-button" data-relationship="${c.id}">关系选择</button></div>
   </div></article>`;
  }).join('')}</div>
  <div class="garden-note"><span>♧</span><div><h3>按你的心意，慢慢靠近。</h3><p>好感达到 ${policy.romance_threshold} 且完成章节后开放关系邀请。你可以选择恋爱，也可以继续做好友与学术搭档。拒绝不扣好感，不影响课程与帮助，也不会重复邀请。</p></div></div><div class="companion-extras"><a class="text-button" href="/static/walk-preview.html">查看四人行走动作 ↗</a></div>
 </section>`;
 for(const c of catalog.characters){
  document.querySelector(`[data-bond="${c.id}"]`).onclick=()=>encouragementDialog(c.id);
  document.querySelector(`[data-invite="${c.id}"]`).onclick=()=>invitationUI.open(c.id);
  document.querySelector(`[data-memories="${c.id}"]`).onclick=()=>invitationUI.memories(c.id);
  document.querySelector(`[data-relationship="${c.id}"]`).onclick=()=>relationshipDialog(c.id);
 }
 const filmView=viewToken;
 api('/api/cinematics').then(({films})=>{
  if(route!=='companions'||viewToken!==filmView)return;
  for(const film of films.filter(f=>f.ready)){
   const anchor=document.querySelector(`[data-invite="${film.character}"]`);if(!anchor||document.querySelector(`[data-film="${film.id}"]`))continue;
   const button=document.createElement('button');button.className='button companion-film';button.dataset.film=film.id;button.innerHTML=`<span>▶ 动画邀约</span><small>${escape(film.title)}</small>`;
   button.onclick=()=>{stopVoice();filmPlayer.open(film);};anchor.before(button);
  }
 }).catch(()=>{});
}
function encouragementDialog(id){
 const c=char(id),lines=c.encouragement||[];
 showDialog(`<p class="eyebrow">A VOICE FOR YOUR NEXT STEP</p><h2 id="modal-title">${escape(c.name)} · 专属鼓励语音</h2><p class="muted">选一句此刻想听的话。</p><div class="encouragement-list">${lines.map((line,i)=>`<section><h3>${escape(line.title)}</h3><p>${escape(line.text)}</p><button class="button" data-encourage="${i}">▶ 听${escape(c.name)}说</button></section>`).join('')}</div><p class="muted small">角色音色参考的 AI 原创鼓励语，非官方录音。</p><button class="text-button" id="encourage-stop">停止播放</button>`);
 document.querySelectorAll('[data-encourage]').forEach(b=>b.onclick=()=>{const line=lines[Number(b.dataset.encourage)];playVoice(line.text,id,line.clip);});$('#encourage-stop').onclick=stopVoice;
}
function relationshipDialog(id){
 const c=char(id),eligible=eligibleForRomance(state,id,policy),relationship=state.relationships[id];
 showDialog(`<h2 id="modal-title">${escape(c.name)} · 关系选择</h2><p class="muted">${names[relationship]} · 好感 ${state.affection[id]} / 100</p>${eligible?`<p>${escape(c.invitation)}</p><div class="button-row"><button class="button" id="choose-romance">我愿意，试着更进一步</button><button class="button light" id="choose-friend">继续做好朋友与学术搭档</button></div>`:relationship==='partner'?`<p>好感 ${policy.romance_threshold} 且完成至少一章后，可以主动选择恋爱路线。好友和学术搭档路线始终保留。</p>`:`<p>${escape(relationship==='friend'?c.friendship:c.romance)}</p>`}`);
 for(const choice of ['friend','romance']){const b=$(`#choose-${choice}`);if(b)b.onclick=()=>{record('relationship',{character:id,choice});companions();relationshipDialog(id);};}
}
function notebook(){knowledgeUI.render();}
async function materials(){
 const token=viewToken;
 content.innerHTML=`<div class="heading-row"><div><p class="eyebrow">YOUR OWN LIBRARY</p><h1>我的资料</h1><p class="muted">把自己的书页带进树庭。知识点草稿将在审核后，才能进入课堂。</p></div></div><section class="upload-card"><span class="upload-symbol">▱</span><div><h2>添一页，你的学习资料</h2><p>PDF、TXT 或 Markdown · 最大 10 MB · 文本使用 UTF-8</p><form id="upload-form"><label class="file-label">选择资料<input type="file" id="material-file" accept=".pdf,.txt,.md" required></label><button class="button" type="submit">放入待编译队列 ↑</button></form><p id="upload-status" role="status" class="muted small">本阶段提供文本提取与队列保存；知识点编译和审核界面将在后续阶段实现。</p></div></section><div class="section-heading"><h2>资料编译队列</h2><span class="muted small">待编译 → 草稿 → 人工审核 → 发布</span></div><div id="material-list" class="material-list"><p class="muted">正在翻阅资料…</p></div>`;
 $('#upload-form').onsubmit=async e=>{e.preventDefault();const file=$('#material-file').files[0];if(!file)return;if(file.size>policy.max_upload_bytes){notify('资料不能超过 10 MB');return;}const form=new FormData();form.append('file',file);const b=$('button[type=submit]',e.target);b.disabled=true;$('#upload-status').textContent='正在保存并提取文本…';try{const result=await api('/api/materials',{method:'POST',body:form});if(route==='materials'){await materials();notify(result.detail);}}catch(err){if(route==='materials'){$('#upload-status').textContent=err.message;b.disabled=false;}}};
 try{const result=await api('/api/materials');if(token!==viewToken||route!=='materials')return;
 const statuses={queued:'待编译',needs_ocr:'待 OCR',parse_failed:'解析失败',needs_split:'请拆分'};
 $('#material-list').innerHTML=result.materials.length?result.materials.map(m=>`<article class="material-row"><span class="document-icon">▤</span><div><h3>${escape(m.name)}</h3><p>${escape(m.detail)}</p><small>${new Date(m.created_at).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai'})}</small></div><span class="tag">${statuses[m.status]||escape(m.status)}</span>${m.status==='queued'?`<button class="text-button" data-preview="${m.id}">查看文本 ↗</button>`:''}</article>`).join(''):'<div class="empty-state compact"><h3>书架上还没有你的资料。</h3><p>先上传一份文本，或直接去体验现有四级课堂。</p></div>';
 document.querySelectorAll('[data-preview]').forEach(b=>b.onclick=async()=>{try{const result=await api(`/api/materials/${b.dataset.preview}/text`);showDialog(`<p class="eyebrow">EXTRACTED TEXT · 待人工审核</p><h2 id="modal-title">${escape(result.material.name)}</h2><pre class="text-preview">${escape(result.text.slice(0,30000))}</pre><p class="note">仅预览前 30,000 字符；完整文本保存在本地资料目录。</p>`);}catch(err){notify(err.message);}});
 }catch{if(token===viewToken)$('#material-list').innerHTML='<p class="muted">资料上传需要本地服务在线。请启动网站后重试。</p>';}
}
function focusPage(){
 sceneGeneration++;sceneModule?.destroyScene();wallpaperModule?.destroyWallpaper();sceneHost=null;sceneApi=null;stopVoice();
 content.innerHTML=`<section class="focus-page"><a class="text-button focus-exit" href="#home">← 紧急退出 / 返回树庭</a><a class="text-button focus-wallpaper" href="/wallpaper" target="_blank" rel="noopener">☾ 专注陪伴模式 · 自习室 ↗</a><p class="eyebrow">A QUIET MOMENT IN THE GROVE</p><h1>此刻，只做一件事。</h1><p>风穿过树叶。这里不提问，也不催促。</p><label class="focus-goal">这一刻想完成什么？<input id="focus-goal" maxlength="100" placeholder="例如：复习构词与易混词" value="${escape(read(`${KEY}.goal`,'按自己的进度完成一次复习'))}"></label><div class="focus-mode"><button data-mode="forward" class="${!focus||focus.mode==='forward'?'selected':''}" ${focus?'disabled':''}>正向计时</button><button data-mode="pomodoro" class="${focus?.mode==='pomodoro'?'selected':''}" ${focus?'disabled':''}>25 分钟番茄钟</button></div><div id="focus-clock" class="focus-clock">${focus?'00:00':'00:00'}</div><span id="focus-hint">${STUDY_PEOPLE[studyChoice()].name}会安静陪伴，不打断你的专注。</span>${companionPicker(studyChoice())}<div class="button-row"><button class="button gold" id="focus-start">${focus?(focusPaused?'继续专注':'暂停片刻'):'开始专注'}</button><button class="button ghost" id="focus-end" ${focus?'':'disabled'}>结束并保存</button><button class="button ghost" id="focus-sound" aria-pressed="false">环境声 · 关</button></div><div id="quiet-room" class="quiet-room"><span class="quiet-status">正在准备自习室…</span></div><label class="focus-journal"><span class="focus-journal-label">写给此刻的自己 · 目标与鼓励（自动保存）</span><textarea id="focus-note" rows="3" maxlength="600" placeholder="写下今天的目标，或一句给自己的鼓励…">${escape(read(`${KEY}.focusNote`,''))}</textarea></label><p class="focus-note">循环自习室 · 安静陪伴 · 切出页面自动暂停计时</p></section>`;
 setupQuietScene();
 $('#focus-note').oninput=e=>{write(`${KEY}.focusNote`,e.target.value);};
 document.querySelectorAll('[data-study-companion]').forEach(button=>button.onclick=async()=>{const id=button.dataset.studyCompanion;saveStudyChoice(id);document.querySelectorAll('[data-study-companion]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));if($('#focus-hint'))$('#focus-hint').textContent=STUDY_PEOPLE[id].name+'在你对面，按自己的节奏就好。';await sceneApi?.setCompanion(id).catch(()=>notify('这段自习动画暂时无法读取，计时仍可使用。'));});
 let mode=focus?.mode||'forward';document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(t=>t.classList.toggle('selected',t===b));$('#focus-clock').textContent=mode==='pomodoro'?'25:00':'00:00';});
 $('#focus-start').onclick=()=>{
  if(!focus){focus={mode,started:Date.now(),elapsed:0,interruptions:0};focusPaused=false;write(`${KEY}.goal`,$('#focus-goal').value);stage('focus',{mode:'quiet',scene:'dusk'});focusPage();document.documentElement.requestFullscreen?.().catch(()=>{});}
  else{if(!focusPaused){focus.elapsed+=Date.now()-focus.started;focus.interruptions++;focusPaused=true;}else{focus.started=Date.now();focusPaused=false;}$('#focus-start').textContent=focusPaused?'继续专注':'暂停片刻';}
  saveFocus();updateClock();
 };
 $('#focus-end').onclick=()=>finishFocus(true);
 $('#focus-sound').onclick=toggleSound;
 clearInterval(focusTimer);focusTimer=setInterval(updateClock,1000);updateClock();
}
async function setupQuietScene(){
 const generation=sceneGeneration,host=$('#quiet-room');
 try{wallpaperModule??=await import('./study-wallpaper.bundle.js');if(route!=='focus'||generation!==sceneGeneration)return;
  const result=await wallpaperModule.mountWallpaper(host,{character:studyChoice(),onStatus:text=>{const target=host.querySelector('.quiet-status');if(target)target.textContent=text;}});
  if(route==='focus'&&generation===sceneGeneration){sceneApi=result;if(result&&host.dataset.character!==studyChoice())await result.setCompanion(studyChoice());}
 }catch{const target=host.querySelector('.quiet-status');if(target)target.textContent='场景暂未载入，计时仍可使用。';}
}
function elapsed(){return focus?focus.elapsed+(focusPaused?0:Date.now()-focus.started):0;}
// 只保存实际已计时片段，意外关闭后的离线时间不补入专注时长。
function saveFocus(){if(focus)write(`${KEY}.focus`,{elapsed:Math.floor(elapsed()),mode:focus.mode,interruptions:focus.interruptions,at:new Date().toISOString()});}
function updateClock(){if(!focus)return;const seconds=Math.min(14400,Math.floor(elapsed()/1000)),remaining=focus.mode==='pomodoro'?Math.max(0,1500-seconds):seconds;const target=$('#focus-clock');if(target)target.textContent=`${String(Math.floor(remaining/60)).padStart(2,'0')}:${String(remaining%60).padStart(2,'0')}`;if($('#focus-hint'))$('#focus-hint').textContent=focusPaused?'暂停中，照顾好自己再回来。':`已安静修习 ${Math.floor(seconds/60)} 分钟 · 中断 ${focus.interruptions} 次`;saveFocus();if(seconds>=14400||(focus.mode==='pomodoro'&&seconds>=1500))finishFocus(true);}
// 报告先取历史均值再追加本次记录，避免本次数据影响自己的比较基线。
function finishFocus(report){
 if(!focus)return;const seconds=Math.min(14400,Math.floor(elapsed()/1000)),interruptions=focus.interruptions;
 const recent=state.focus_sessions.filter(s=>Date.now()-new Date(s.at).getTime()<7*86400000),average=recent.length?Math.round(recent.reduce((a,s)=>a+s.seconds,0)/recent.length):null;
 if(seconds>0)record('focus_session',{seconds,interruptions});focus=null;focusPaused=false;clearInterval(focusTimer);write(`${KEY}.focus`,null);stopSound();if(document.fullscreenElement)document.exitFullscreen().catch(()=>{});stage('classroom',{scene:'day'});
 if(report){focusPage();showDialog(`<p class="eyebrow">A MOMENT WELL SPENT</p><h2 id="modal-title">这一段安静，已留下。</h2><div class="summary-stats">${statCard(`${Math.floor(seconds/60)}分${seconds%60}秒`,'专注时间','按实际计时保存')}${statCard(interruptions,'中断次数','暂停与切出页面')}</div><p class="muted">${average===null?'这是你的第一次专注记录，之后会与过去七天的平均单次时长比较。':`过去七天平均单次专注 ${Math.floor(average/60)} 分 ${average%60} 秒；本次${seconds>=average?'多':'少'} ${Math.abs(seconds-average)} 秒。`}</p><p class="note">自习期间不考核知识点；有效时长计入学习时长贡献。</p>`);}
}
function stopSound(){if(audio){audio.context.close();audio=null;}if($('#focus-sound')){$('#focus-sound').textContent='环境声 · 关';$('#focus-sound').setAttribute('aria-pressed','false');}}
async function toggleSound(){if(audio){stopSound();return;}try{const context=new AudioContext(),buffer=context.createBuffer(1,context.sampleRate*3,context.sampleRate),samples=buffer.getChannelData(0);let last=0;for(let i=0;i<samples.length;i++){last=(last+0.02*(Math.random()*2-1))/1.02;samples[i]=last*3.5;}const source=context.createBufferSource(),filter=context.createBiquadFilter(),gain=context.createGain();source.buffer=buffer;source.loop=true;filter.type='lowpass';filter.frequency.value=400;gain.gain.value=0.08;source.connect(filter).connect(gain).connect(context.destination);source.start();audio={context};$('#focus-sound').textContent='环境声 · 开';$('#focus-sound').setAttribute('aria-pressed','true');}catch{notify('浏览器暂时无法播放环境声。');}}
function render(){
 if(!catalog)return;flushStudy();viewToken++;clearInterval(typeTimer);const next=location.hash.slice(1)||'home';
 if(next==='cs408-trials'){examUI.open('cs408');return;}
 if(next==='math1-trials'){examUI.open('math1');return;}
 if(next==='english1-trials'){examUI.open('english1');return;}
 if(next!==route)stopVoice();
 if(['exams','library-exams'].includes(route)&&!['exams','library-exams'].includes(next))examUI.leave();
 if(route==='outing'&&next!=='outing')invitationUI.leave();
 if(route==='focus'&&next!=='focus'){finishFocus(false);stopSound();clearInterval(focusTimer);}
 if(['classroom','focus'].includes(route)&&next!==route){sceneGeneration++;sceneModule?.destroyScene();wallpaperModule?.destroyWallpaper();sceneHost=null;sceneApi=null;stopVoice();if(document.fullscreenElement===content)document.exitFullscreen().catch(()=>{});}
 route=next;const labels={home:'课程表',classroom:'课堂',companions:'同行之人',notebook:'智库',library:'智库', 'library-exams':'智库 / 考试区',materials:'我的资料',focus:'自习室',summary:'章节回顾',exams:'智库 / 考试区',outing:'同行邀约',vocabulary:'四级词汇库'};
 $('#breadcrumb').textContent=`神悟树庭 / ${labels[route]||'课程表'}`;
 document.querySelectorAll('[data-nav]').forEach(a=>a.classList.toggle('active',a.dataset.nav===(['library','notebook','library-exams','exams'].includes(route)?'library':['classroom','summary','vocabulary'].includes(route)?'home':route)));
 document.body.classList.toggle('in-class',route==='classroom');document.body.classList.toggle('in-focus',route==='focus');document.body.classList.toggle('in-outing',route==='outing');
 ({home,classroom,summary,companions,notebook,library:()=>knowledgeUI.render(),'library-exams':()=>examUI.render(),materials,outing:()=>invitationUI.render().catch(e=>notify(e.message)),focus:focusPage,exams:()=>examUI.render(),vocabulary:()=>vocabularyUI.render()}[route]||home)();window.scrollTo(0,0);
}
window.addEventListener('hashchange',render);
window.addEventListener('online',sync);
window.addEventListener('storage',e=>{if(e.key===KEY+'.epoch'&&e.newValue!==JSON.stringify(progressEpoch)){resettingProgress=true;location.reload();}});
document.addEventListener('visibilitychange',()=>{if(document.hidden)flushStudy();if(focus&&document.hidden&&!focusPaused){focus.elapsed+=Date.now()-focus.started;focus.interruptions++;focusPaused=true;saveFocus();if($('#focus-start'))$('#focus-start').textContent='继续专注';}else if(!document.hidden)sync();});
window.addEventListener('pagehide',()=>{flushStudy();saveFocus();persist();});
async function init(){
 try{const e=await fetch('/api/progress-epoch',{cache:'no-store',signal:AbortSignal.timeout(20000)});if(!e.ok)throw Error('纪元读取失败');progressEpoch=(await e.json()).epoch;if(resetProgressStorage(localStorage,progressEpoch,KEY)){saved={version:1,profile:crypto.randomUUID(),events:[],synced:[],quarantined:[]};settings={instant:matchMedia('(prefers-reduced-motion: reduce)').matches,voice:true};activeSeconds=0;lastActivity=0;}}catch{progressEpoch=read(`${KEY}.epoch`,'initial');}
 try{const result=await api('/api/catalog');catalog=result.catalog;policy=result.policy;if(await saveCatalog(result)){try{localStorage.removeItem(`${KEY}.curriculum`);}catch{}}}
 catch{const cache=await loadCatalog()||read(`${KEY}.curriculum`,null);if(cache){catalog=cache.catalog;policy=cache.policy;}else{content.innerHTML='<div class="empty-state"><h1>还没有连上树庭。</h1><p>请用“启动树庭网站.bat”启动本地服务，再刷新这个页面。</p><button class="button" id="retry">重新连接</button></div>';$('#retry').onclick=()=>location.reload();return;}}
 rebuild();persist();const nav=document.createElement('div');nav.className='study-shortcuts';nav.innerHTML='<button id="open-courses">板块与进度</button><button id="open-quick">速记资料</button><button id="open-voice-progress">配音进度</button>';$('#settings-button').before(nav);$('#open-voice-progress').onclick=showVoiceProgress;$('#open-courses').onclick=()=>courseUI.menu();$('#open-quick').onclick=()=>route==='vocabulary'?vocabularyUI.open({mode:'quick'}):courseUI.notes();render();await sync();if(!['classroom','focus','materials','outing'].includes(route))render();
 const interrupted=read(`${KEY}.focus`,null);if(interrupted?.elapsed>0){showDialog(`<p class="eyebrow">UNFINISHED MOMENT</p><h2 id="modal-title">上次的专注，被轻轻打断了。</h2><p>已保留 ${Math.floor(interrupted.elapsed/60000)} 分钟。离线后的时间没有计入。</p><button class="button" id="recover-focus">保存已计时的片段</button><button class="button light" id="discard-focus">不保留这次</button>`);$('#recover-focus').onclick=()=>{record('focus_session',{seconds:Math.max(1,Math.min(14400,Math.floor(interrupted.elapsed/1000))),interruptions:Math.min(1000,interrupted.interruptions+1)});write(`${KEY}.focus`,null);closeDialog();render();};$('#discard-focus').onclick=()=>{write(`${KEY}.focus`,null);closeDialog();};}
 setInterval(sync,30000);
}
init();

document.addEventListener('pointerdown',event=>{document.querySelectorAll('.class-tool-menu[open]').forEach(menu=>{if(!menu.contains(event.target))menu.open=false;});});

// 课堂每次选择只更新对白与黑板，不重新下载四个人物或重建 WebGL 上下文。
async function setupGameScene(p,text,intro,feedback){
 const speaker=!intro&&!feedback?(p.vocabulary_lesson?wordClass.speaker(p):p.course?networkCourse.speaker(p):(p.speaker||'anaxa')):(p.speaker||'anaxa');
 currentSpeech={text,id:speaker,clip:intro?'chapter-'+activeChapter().id:feedback?null:p.id};
 const stageElement=$('.class-stage');
 if(p.vocabulary_lesson)$('.dialogue-panel').classList.add('has-word-class');
 const toolbar=document.createElement('div');toolbar.className='game-tools';
 toolbar.setAttribute('aria-label','课堂操作');
 toolbar.innerHTML=`<div class="class-view-tools" role="group" aria-label="行走与角色视角"><span class="class-tools-label">视角</span><button id="walk-mode" aria-pressed="false">自由行走</button><button data-talk="anaxa">老师</button><button data-talk="hyacine">风堇</button><button data-talk="castor">遐蝶</button><button data-talk="phainon">白厄</button></div><div class="class-action-tools"><button id="voice-play">▶ 朗读</button><details class="class-tool-menu"><summary>语音设置 <span aria-hidden="true">⌄</span></summary><div class="class-tool-panel class-voice-panel"><span class="class-tools-label">语音与表情</span><label><input id="auto-voice" type="checkbox">自动配音</label><button id="mood-cycle">情绪 · 平静</button></div></details><details class="class-tool-menu"><summary>学习工具 <span aria-hidden="true">⌄</span></summary><div class="class-tool-panel class-learning-panel"><span class="class-tools-label">课堂工具</span></div></details></div>`;
 const voiceTools=toolbar.querySelector('.class-voice-panel'),learningTools=toolbar.querySelector('.class-learning-panel'),actionTools=toolbar.querySelector('.class-action-tools');
 toolbar.addEventListener('toggle',event=>{if(event.target.matches('.class-tool-menu[open]'))toolbar.querySelectorAll('.class-tool-menu').forEach(menu=>{if(menu!==event.target)menu.open=false;});},true);
 toolbar.addEventListener('keydown',event=>{if(event.key==='Escape'){const opened=toolbar.querySelector('.class-tool-menu[open]');if(opened){opened.open=false;opened.querySelector('summary').focus();}}});
 toolbar.addEventListener('click',event=>{if(event.target.closest('.class-learning-panel button'))toolbar.querySelectorAll('.class-tool-menu').forEach(menu=>menu.open=false);});
 stageElement.append(toolbar);
 toolbar.querySelectorAll('[data-talk]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.talk===speaker)));
 const progressButton=document.createElement('button');progressButton.textContent='配音进度';progressButton.onclick=showVoiceProgress;voiceTools.append(progressButton);
 if(p.course||p.micro_lesson){const materialsButton=document.createElement('button');materialsButton.id='course-material-voice';materialsButton.textContent='教材配音';materialsButton.onclick=()=>showMaterialAudio(p);voiceTools.append(materialsButton);}
 const ueStatus=document.createElement('span');ueStatus.id='ue-stage-status';ueStatus.className='ue-stage-status';ueStatus.textContent='正在连接 UE5 场景…';
 if(p.vocabulary_lesson)stage(feedback?'feedback':'dialogue',{character:speaker,point_id:p.id,lesson_step:wordClass.step(p)});
 for(const [label,fn] of [['板块 / 进度',()=>courseUI.menu()],['速记资料',()=>courseUI.notes(activeChapter().module)],['章节测试',()=>courseUI.assessment(activeChapter().id)]]){const b=document.createElement('button');b.textContent=label;b.onclick=()=>{sceneApi?.focus('anaxa');stopVoice();fn();};learningTools.append(b);}
 if(p.vocabulary_lesson){const entry=catalog.vocabulary_banks.cet4.entries.find(e=>e.id===p.vocabulary_lesson.word_id),spoken=entry.accepted_spellings.find(x=>!/[(/]/.test(x))||entry.word;const b=document.createElement('button');b.id='word-pronunciation';b.textContent='▶ 单词发音';b.onclick=()=>playVoice(spoken,'anaxa','pronounce-'+entry.id);voiceTools.append(b);}
 if(p.listen_text){const b=document.createElement('button');b.textContent='听老师读材料';b.onclick=()=>playVoice(p.listen_text,p.speaker||'anaxa',`listen-${p.id}`);voiceTools.append(b);}
 $('#auto-voice').checked=!!settings.voice;
 $('#auto-voice').onchange=e=>{settings.voice=e.target.checked;write(`${KEY}.settings`,settings);if(settings.voice&&currentSpeech)playVoice(currentSpeech.text,currentSpeech.id,currentSpeech.clip);else stopVoice();};
 $('#voice-play').onclick=()=>{if(currentSpeech)playVoice(currentSpeech.text,currentSpeech.id,currentSpeech.clip);};
 toolbar.querySelectorAll('[data-talk]').forEach(b=>b.onclick=()=>talkCharacter(b.dataset.talk));
 $('#walk-mode').onclick=()=>{stopVoice();sceneApi?.walk();};
 const moodOrder=['neutral','warm','sad'],moodLabel={neutral:'平静',warm:'微笑',sad:'难过'};let moodAt=0;
 $('#mood-cycle').onclick=()=>{moodAt=(moodAt+1)%moodOrder.length;const mood=moodOrder[moodAt];$('#mood-cycle').textContent='情绪·'+moodLabel[mood];sceneApi?.speech(currentSpeech?.id||'anaxa',false,null,mood);};
 const guide=document.createElement('div');guide.className='player-guide';guide.innerHTML='<span class="crosshair">＋</span><span class="walk-instructions">W A S D 移动 · 鼠标观察 · E 附近交谈 · Esc 释放鼠标</span><div class="touch-pad"><button data-move="KeyW" aria-label="前进">↑</button><button data-move="KeyA" aria-label="向左">←</button><button data-move="KeyS" aria-label="后退">↓</button><button data-move="KeyD" aria-label="向右">→</button></div>';stageElement.append(guide);
 guide.querySelectorAll('[data-move]').forEach(b=>{b.onpointerdown=e=>{e.preventDefault();b.setPointerCapture(e.pointerId);sceneApi?.moveInput(b.dataset.move,true);};b.onpointerup=b.onpointercancel=()=>sceneApi?.moveInput(b.dataset.move,false);});
 const sourcesButton=document.createElement('button');sourcesButton.textContent='资料出处';sourcesButton.onclick=showReferences;learningTools.append(sourcesButton);learningTools.append(ueStatus);
 const immerse=document.createElement('button');immerse.id='classroom-immersive';immerse.textContent='⛶ 沉浸';immerse.onclick=()=>{if(document.fullscreenElement)document.exitFullscreen().catch(()=>{});else content.requestFullscreen?.().catch(()=>notify('浏览器暂不支持全屏，可使用窗口模式。'));};actionTools.append(immerse);
 const note=document.createElement('div');note.className='class-participation';
 note.innerHTML=`<button id="assistant-hint" class="text-button">风堇助教 · 给我一条提示</button><span>${escape(char(p.classmate?.character||'castor').name)}同学：${escape(p.vocabulary_lesson&&!feedback&&wordClass.step(p)===2?'先独立回忆，需要时再请同学提示。':p.classmate?.text||'请留意概念的边界。')}</span><small id="voice-disclosure">角色配音加载中 · 本题协作搭档：${char(p.character).name}</small>`;
 api('/api/voice-status?include_clips=false').then(v=>{const label=$('#voice-disclosure');if(label)label.textContent=`角色参考声线 AI 配音 · ${v.coverage?.generated||0}/${v.coverage?.expected||0} 句就绪${v.generation?.status==='running'?` · ${v.generation.scope==='all_courses'?'全课程补全':'词汇补全'} ${v.generation.completed_jobs}/${v.generation.total_jobs}`:''} · 非官方录音`;}).catch(()=>{const label=$('#voice-disclosure');if(label)label.textContent='角色录音状态暂不可用';});
 $('.word-line')?.after(note);
 $('#assistant-hint')?.addEventListener('click',()=>talkCharacter('hyacine'));
 if(p.classmate){const peerButton=document.createElement('button');peerButton.className='text-button';peerButton.textContent='▶ 听同学回应';peerButton.onclick=()=>playVoice(p.classmate.text,p.classmate.character,`peer-${p.id}`);note.append(peerButton);}
 if(!sceneHost){sceneHost=document.createElement('div');sceneHost.className='scene-host';}
 stageElement.prepend(sceneHost);stageElement.classList.add('is-3d');
 if(sceneHost.dataset.status)$('.stage-status').textContent=sceneHost.dataset.status;
 const generation=sceneGeneration;
 if(!sceneApi){try{
   sceneModule??=await import('./scene.bundle.js');
   if(route!=='classroom'||generation!==sceneGeneration)return;
   if(!sceneApi)sceneApi=await sceneModule.mountScene(sceneHost,{onInteract:id=>id?talkCharacter(id):notify('靠近角色后按 E，也可以点击右上角角色名字交谈。'),onMode:walking=>{$('.classroom')?.classList.toggle('walking',walking);$('#walk-mode')?.setAttribute('aria-pressed',String(walking));document.querySelectorAll('[data-talk]').forEach(button=>button.setAttribute('aria-pressed',String(!walking&&button.dataset.talk===(currentSpeech?.id||speaker))));},onStatus:message=>{const status=$('.stage-status');if(status)status.textContent=message;if(sceneHost)sceneHost.dataset.status=message;}});
 }catch(error){stageElement.classList.remove('is-3d');$('.stage-status').textContent='3D 渲染不可用 · 已保留立绘与学习流程';console.warn(error.message);}}
 if(route==='classroom'){
   const current=point(lesson.ids[lesson.index]);sceneApi?.update({word:current.concept,line:current.vocabulary_lesson?wordClass.board(current,feedback):['textbook','video_course'].includes(current.course?.source.kind)?current.course.board:current.memoryHook,character:speaker});
 }
 if(settings.voice)playVoice(text,speaker,currentSpeech.clip);
}
function talkCharacter(id){
 if(route!=='classroom'||!lesson)return;stopVoice();
 const p=point(lesson.ids[lesson.index]),c=char(id),text=id==='anaxa'?(lesson.phase==='intro'?activeChapter().opening:p.vocabulary_lesson?p.dialogue.anaxa:p.course?networkCourse.text(p):p.prompt):(p.course?networkCourse.characterText(p,id):p.dialogue?.[id])||(id==='hyacine'?(p.assistant_hint||p.memoryHook):p.classmate?.character===id?p.classmate.text:c.intro);
 currentSpeech={text,id,clip:null};
 stage('dialogue',{character:id,emotion:'neutral',point_id:p.id,lesson_step:p.vocabulary_lesson?wordClass.step(p):undefined});
 sceneApi?.focus(id);$('.classroom')?.classList.remove('walking');const panel=$('.dialogue-panel');panel.classList.add('is-aside');$('.speaker').innerHTML=`${escape(c.address)}<small>${escape(c.role)}</small>`;typeText(text);
 $('.affection-label').textContent=`好感 · ${state.affection[id]}`;
 let back=$('.aside-return');if(!back){back=document.createElement('button');back.className='button aside-return';back.textContent='回到课堂话题 →';panel.append(back);}back.onclick=()=>classroom();
 $('#voice-play').onclick=()=>playVoice(text,id,null);
 if(c.classroom_chat?.length){back.remove();createCharacterChat({character:c,point:p,panel,esc:escape,back:()=>classroom(),say:(line,spoken=true)=>{stopVoice();currentSpeech={text:line,id,clip:null};typeText(line);sceneApi?.focus(id);$('#voice-play').onclick=()=>playVoice(line,id,null);if(spoken&&settings.voice)playVoice(line,id,null);}});}else if(settings.voice)playVoice(text,id,null);
}
let voiceContext=null,voiceMeterCleanup=null;
function stopVoice(){voiceRequest++;voiceAudio?.pause();voiceAudio?.remove();voiceAudio=null;voiceMeterCleanup?.();voiceMeterCleanup=null;window.speechSynthesis?.cancel();sceneApi?.speech?.('anaxa',false);invitationUI.speech(false);}
async function playVoice(text,id,clip){
 stopVoice();
 const request=voiceRequest;
 let resolved;
 try{const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)),hash=[...new Uint8Array(bytes)].map(x=>x.toString(16).padStart(2,'0')).join('');resolved=await api(`/api/voice/resolve?character=${encodeURIComponent(id)}&text_sha256=${hash}`);}catch{if(request===voiceRequest)notify('本地角色录音暂时无法读取。');return;}
 if(request!==voiceRequest)return;
 const entry=resolved.ready?resolved.clip:null;
 // 角色与完整台词必须匹配；缺失时不会回退为另一角色的旧录音。
 if(entry){const url=entry.url||`/voice/${encodeURIComponent(entry.id)}.mp3`;
  if(/^\/voice\/[A-Za-z0-9_-]+\.(wav|mp3)$/.test(url)){
   if(!entry.synthetic){notify('这句角色录音尚未就绪。');return;}
   voiceAudio=new Audio(url);const clipAudio=voiceAudio;clipAudio.id='character-audio';clipAudio.hidden=true;document.body.append(clipAudio);
   clipAudio.onplay=()=>{if(request!==voiceRequest)return;let meter=null;
    try{voiceContext??=new AudioContext();voiceContext.resume();const source=voiceContext.createMediaElementSource(clipAudio),analyser=voiceContext.createAnalyser();analyser.fftSize=256;source.connect(analyser);analyser.connect(voiceContext.destination);voiceMeterCleanup=()=>{source.disconnect();analyser.disconnect();};const buffer=new Uint8Array(256);meter=()=>{analyser.getByteTimeDomainData(buffer);return Math.sqrt(buffer.reduce((sum,v)=>sum+((v-128)/128)**2,0)/buffer.length)*2.8;};}catch{}
    sceneApi?.speech?.(id,true,meter,id==='hyacine'?'warm':'neutral');if(route==='outing')invitationUI.speech(true);};
   clipAudio.onended=clipAudio.onerror=()=>{if(request===voiceRequest){sceneApi?.speech?.(id,false);invitationUI.speech(false);voiceMeterCleanup?.();voiceMeterCleanup=null;}};
   clipAudio.play().catch(()=>{if(request===voiceRequest)notify('点击朗读按钮后再播放音频。');});return;
  }
 }
 notify(resolved?.generating?`${char(id).name}的这句录音正在批量补全，请稍后重试。`:`${char(id).name}的这句角色录音尚未就绪。`);
}
async function showReferences(){
 try{const result=await api('/api/references');
 showDialog(`<p class="eyebrow">TEACHING REFERENCES · ${escape(result.checked_date||'')}</p><h2 id="modal-title">课堂资料与检索记录</h2><p class="muted small">课堂对白为原创。可获取的公开资料已留存；检索到视频入口不等于已经看完视频。最新与最高播放量无法完全核实时，不宣称全站排名。</p>${result.sources.map(s=>`<section class="bond-story"><h3>${s.url&&s.url.startsWith('https://')?`<a href="${escape(s.url)}" target="_blank" rel="noopener noreferrer">${escape(s.title)} ↗</a>`:escape(s.title)}</h3><p class="muted small">${escape(s.note||s.license||'')} · ${escape({downloaded:'已下载公开原件',unavailable:'未取得正文',search_index_only:'仅检索候选',sample_verified:'已抽查页面及片段',page_verified:'已读取公开页面',original:'原创教学脚本'}[s.status]||s.status)}</p></section>`).join('')}`);
 }catch{notify('资料索引暂时无法读取。');}
}

// 全课程显示真实累计覆盖；不把排队任务当作已经完成。
let voiceProgressTimer;
async function showVoiceProgress(){
 clearTimeout(voiceProgressTimer);stopVoice();
 showDialog('<p class="eyebrow">ALL COURSES · CHARACTER VOICE</p><h2 id="modal-title">全课程角色配音</h2><div id="course-voice-progress">正在核对录音…</div>');
 const target=$('#course-voice-progress');
 async function refresh(){if(!target.isConnected||!modal.open)return;try{
  const result=await api('/api/course-voice-status');if(!target.isConnected)return;
  target.innerHTML=`<p><strong>${result.ready} / ${result.expected}</strong> 条录音已就绪 · ${result.complete?'全部就绪':result.generation.status==='running'?'本机正在批量生成':'尚未全部完成'}</p><p class="note">讲课、助教提示、同学回应、反馈和教材段落按对应角色配音；已生成部分立即可用。角色参考声线 AI 合成，非官方录音。</p><div class="voice-course-grid">${result.subjects.filter(s=>s.expected).map(s=>`<section class="test-review"><h3>${escape(s.name)}</h3><p>${s.ready} / ${s.expected} 条就绪</p><ul>${Object.entries(s.modules).map(([name,m])=>`<li>${escape(name==='词汇'?'词汇（历史教案）':name)}：${m.ready} / ${m.expected}</li>`).join('')}</ul></section>`).join('')}</div><p class="muted small">尚无教案可配音：${result.subjects.filter(s=>!s.expected).map(s=>escape(s.name)).join('、')}。筹备课程不计作已完成。</p>`;
 }catch{if(target.isConnected)target.textContent='配音进度暂时无法读取。';}if(target.isConnected&&modal.open)voiceProgressTimer=setTimeout(refresh,15000);}
 refresh();
}
async function showMaterialAudio(p){
 stopVoice();try{const result=await api('/api/course-audio/'+encodeURIComponent(p.id));
 showDialog(`<p class="eyebrow">LESSON MATERIAL · 老师朗读</p><h2 id="modal-title">${escape(p.concept)} · 教材配音</h2><p class="note">学习模式的教材与例题讲解，可按段朗读；生成中的录音会提示稍后重试。</p>${result.segments.map((s,i)=>`<section class="test-review"><h3>${escape(s.title)}</h3><p>${escape(s.text)}</p><button class="text-button" data-material-audio="${i}">▶ 听老师讲这一段</button></section>`).join('')||'<p>此知识点直接使用课堂朗读按钮。</p>'}`);
 document.querySelectorAll('[data-material-audio]').forEach(b=>b.onclick=()=>{const s=result.segments[Number(b.dataset.materialAudio)];playVoice(s.text,s.character,s.id);});
 }catch{notify('教材配音目录暂时不可用。');}
}
