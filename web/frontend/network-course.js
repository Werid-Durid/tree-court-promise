import {evaluateCourseExercise} from './course-exercises.js';
import {mountCalculusVisual} from './calculus-visuals.js';
import {mountWritingTask} from './course-writing.js';
// 课时步骤独立存储；阅读与切换步骤不会被记成一次答题。
export function createNetworkCourse({read,write,storageKey,state,record,show,redraw,notify,speak}){
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const isBook=p=>p.course.source.kind==='textbook';
 const isVideo=p=>p.course.source.kind==='video_course';
 const videoLabel=p=>p.subject==='postgrad'?'考研英语基础课堂':p.subject==='probability'?'概率论与数理统计课堂':p.subject==='cet6'?'六级英语课堂':p.subject==='linear'?'线性代数课堂':'高数课堂';
 const sourceNoun=p=>isBook(p)?'教材':'讲义';
 const sourceEndpoint=p=>isBook(p)?'textbook':'network-handout';
 const key=p=>`${storageKey}.networkStage.${p.id}`;
 const index=p=>{const n=read(key(p),0);return Number.isInteger(n)&&n>=0&&n<3?n:0;};
 const current=p=>p.course.stages[index(p)];
 const text=p=>current(p).dialogue;
 function characterText(p,id){return id==='anaxa'?text(p):(p.course.dialogue[id]||p.dialogue[id]);}
 function textbook(p){return `<p class="eyebrow">${isVideo(p)?'COURSE · '+videoLabel(p):isBook(p)?'408 TEXTBOOK · 教材课堂':'NETWORK TEXTBOOK · 讲义课程'}</p><h2 id="modal-title">${esc(p.concept)}</h2><ol class="network-objectives">${p.course.objectives.map(o=>`<li>${esc(o)}</li>`).join('')}</ol>${p.course.textbook.map(s=>`<section class="network-reading-section"><h3>${esc(s.heading)}</h3><p>${esc(s.text)}</p></section>`).join('')}<div class="network-board">${esc(p.course.board)}</div><p class="note">${esc(sourceLabel(p))}</p><p class="muted small">${isBook(p)||isVideo(p)?esc(p.course.syllabus.selection):'按 408 六章框架组织；2027 正式大纲全文未取得，年度新增删改仍待逐条核验。'}</p>`;}
 function sourceLabel(p){if(isVideo(p))return p.course.source.note||'参考公开视频目录；讲解、例题与记忆线索为项目原创。';return p.course.source.pages.length?`${isBook(p)?p.course.source.title+' · '+p.course.source.sections+' · ':''}${sourceNoun(p)} PDF 第 ${p.course.source.pages.map(r=>r.join('—')).join('、')} 页；正文为针对考点重新编写的教材讲解，页码是 PDF 页序。`:'本节为标准资料补充；未在此讲义找到独立章节，不冒称 PPT 原文。';}
 function openSource(p){
  if(isVideo(p)){
   const s=p.course.source;
   show(`<p class="eyebrow">COURSE · VIDEO REFERENCE</p><h2 id="modal-title">${esc(p.concept)} · 视频与内容来源</h2><p>${esc(s.note)}</p><p>对应视频：${esc(s.author)} · ${esc(s.title)}</p><p><a class="button light" href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">打开对应 B 站视频 ↗</a></p><p class="note">${s.lesson_origin==='original_prerequisite_supplement'?'本课是为同一主题增加的原创衔接课。':'已核对合集成员与标题，本课按对应主题原创编写。'} 未取得公开字幕，不标注虚构的时间戳，不把原创例题标成视频原题。</p><p class="muted small">记号：abs 表示绝对值，pi 或 π 表示圆周率；输入数值题可用精确分数。</p>`);return;
  }
  const ranges=p.course.source.pages;
  if(!ranges.length){show(`<h2 id="modal-title">${esc(p.concept)} · 补充资料</h2><p>这份讲义没有相应独立节，课程按基础考点作补充。</p>${p.course.source.supplement_urls.map(url=>`<p><a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(url)}</a></p>`).join('')}`);return;}
  let range=0,page=ranges[0][isBook(p)?0:1];
  show(`<p class="eyebrow">${isBook(p)?'SOURCE TEXTBOOK':'SOURCE SLIDES'}</p><h2 id="modal-title">${esc(p.concept)} · ${sourceNoun(p)}原页</h2><p class="muted small">${isBook(p)?esc(p.course.source.title)+'，对应分节 '+esc(p.course.source.sections)+'。从相关正文首段开始，可逐页对照。':'默认显示本节末尾汇总页；可向前翻看逐步演示。'}页码为 PDF 页序，不是书上印刷页码。</p><div class="notes-controls"><label>相关页段<select id="network-source-range">${ranges.map((r,i)=>`<option value="${i}">${r[0]}—${r[1]} 页</option>`).join('')}</select></label><button class="button light" id="network-source-prev">上一页</button><label>页码<input id="network-source-number" type="number" value="${page}"></label><button class="button light" id="network-source-next">下一页</button></div><p id="network-source-state" role="status"></p><img class="network-source-image" id="network-source-image" alt="${sourceNoun(p)}原页"><p class="muted small">原 PDF 保留不变。OCR 只辅助检索，图表与公式请对照原页。</p>`);
  const image=document.querySelector('#network-source-image'),number=document.querySelector('#network-source-number'),status=document.querySelector('#network-source-state');
  const draw=()=>{number.min=ranges[range][0];number.max=ranges[range][1];number.value=page;status.textContent=`第 ${page} 页`;image.src=`/api/${sourceEndpoint(p)}/${p.id}/page/${page}`;image.onload=()=>{status.textContent=`已显示${sourceNoun(p)}第 ${page} 页`;};image.onerror=()=>{status.textContent='本页暂时未载入，请重试翻页。';};};
  document.querySelector('#network-source-range').onchange=e=>{range=Number(e.target.value);page=ranges[range][isBook(p)?0:1];draw();};
  const turn=n=>{if(Number.isInteger(n)&&n>=ranges[range][0]&&n<=ranges[range][1]){page=n;draw();}};
  document.querySelector('#network-source-prev').onclick=()=>turn(page-1);document.querySelector('#network-source-next').onclick=()=>turn(page+1);number.onchange=e=>turn(Number(e.target.value));draw();
 }
 function mount(p){
  const course=p.course,n=index(p),stage=current(p),panel=document.querySelector('.dialogue-panel');panel.classList.add('has-network-course');
  const block=document.createElement('section');block.className='network-course';block.id='network-course';
  const transfer=course.exercises.find(x=>x.id==='transfer'),last=state().course_attempts?.[`${p.id}:transfer`]?.at(-1),draft=read(`${storageKey}.networkDraft.${p.id}`,'');
  block.innerHTML=`<nav class="network-stage-nav" aria-label="教材课时步骤">${course.stages.map((s,i)=>`<button class="${n===i?'active':''}" aria-current="${n===i?'step':'false'}" data-network-stage="${i}">${i+1}. ${esc(s.name)}</button>`).join('')}</nav><div class="network-lesson-tools"><button class="text-button" id="network-textbook">${isVideo(p)?'展开本课讲解':'打开完整教材'}</button><button class="text-button" id="network-source">${isVideo(p)?'对应视频 / 来源':course.source.pages.length?'对照'+sourceNoun(p)+'原页':'查看补充来源'}</button><span>${isVideo(p)?videoLabel(p):course.source.pages.length?(isBook(p)?'教材课堂':'讲义课程'):'补充考点'} · 建议 ${course.estimated_minutes} 分钟</span></div><div class="network-board">${esc(course.board)}</div>${(isBook(p)||isVideo(p))&&course.syllabus.items.length?`<p class="muted small">${isVideo(p)?'本课主题':'本节考纲细目'}：${course.syllabus.items.map(esc).join(' · ')}</p>`:''}${n===0?`<div class="network-textbook">${course.textbook.map(s=>`<section><h3>${esc(s.heading)}</h3><p>${esc(s.text)}</p></section>`).join('')}</div>`:n===1?`<section class="network-worked"><h3>老师的板书例题</h3><p>${esc(course.worked_example.question)}</p><ol>${course.worked_example.steps.map(s=>`<li><strong>${esc(s.label)}</strong><p>${esc(s.text)}</p></li>`).join('')}</ol><p class="note">这是重新编写的示例，条件与结果可逐步核对，并非原书习题逐字转写。</p></section>`:`<form id="network-transfer" class="network-transfer"><h3>迁移练习 · 换一组条件</h3><label>${esc(transfer.question)}<input id="network-response" maxlength="250" value="${esc(draft||last?.response||'')}" autocomplete="off" required placeholder="输入你的答案"></label><button class="button" type="submit">检验这一步</button><div id="network-exercise-feedback" role="status">${last?feedback(transfer,last.correct,last.response):''}</div></form><h3 class="network-review-heading">机制回顾 · 再解释一个情境</h3><p>${esc(p.test.question)}</p>`}${n<2?`<div class="button-row"><button class="button" id="network-next">${n===0?'随老师推演例题':'换一组条件练习'} →</button><button class="text-button" id="network-assistant">风堇助教 · 检查边界</button></div>`:''}<p class="muted small network-source-note">${esc(sourceLabel(p))}</p>`;
  document.querySelector('.word-line').after(block);
  if(n===0)mountCalculusVisual(p,block);
  if(n===2)mountWritingTask(p,block,{read,write,key:storageKey});
  document.querySelectorAll('.clue-label,.clues').forEach(el=>el.classList.toggle('network-hidden',n!==2));
  document.querySelectorAll('[data-network-stage]').forEach(b=>b.onclick=()=>{write(key(p),Number(b.dataset.networkStage));redraw();});
  document.querySelector('#network-next')?.addEventListener('click',()=>{write(key(p),n+1);redraw();});
  document.querySelector('#network-textbook').onclick=()=>show(textbook(p));document.querySelector('#network-source').onclick=()=>openSource(p);
  document.querySelector('#network-assistant')?.addEventListener('click',()=>speak('hyacine'));
  const form=document.querySelector('#network-transfer');
  if(form){const started=performance.now();document.querySelector('#network-response').oninput=e=>write(`${storageKey}.networkDraft.${p.id}`,e.target.value);
   form.onsubmit=e=>{e.preventDefault();const response=document.querySelector('#network-response').value;try{const correct=evaluateCourseExercise(transfer,response);record('course_attempt',{point_id:p.id,exercise_id:'transfer',response,response_ms:Math.min(900000,Math.round(performance.now()-started))});document.querySelector('#network-exercise-feedback').innerHTML=feedback(transfer,correct,response);write(`${storageKey}.networkDraft.${p.id}`,response);}catch(error){notify(error.message);}};
  }
 }
 function feedback(exercise,correct,response){return `<p><strong>${correct?'这一步推演成立':'再核对条件与单位'}</strong> · 你的答案：${esc(response)}</p><p>参考：${esc(exercise.answer)}。${esc(exercise.explanation)}</p><p class="muted small">可修改后重试；选错不扣好感。作答会保存到本地学习档案。</p>`;}
 return {text,speaker:p=>current(p).speaker,characterText,mount,openSource};
}
