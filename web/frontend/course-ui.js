// 课程导航、速记与检测各自独立；进入任一知识点不受章节完成状态限制。
export const allChapters=catalog=>catalog.subjects.flatMap(s=>(s.chapters||[]).filter(c=>c&&typeof c==='object'&&c.id&&Array.isArray(c.points)).map(c=>({...c,subject_id:s.id,subject_name:s.name})));
// 合并在同一课时内的考纲细目也可以搜索，如 Flash、条件变量、段页式虚存。
export const pointSearchText=p=>[p.concept,...(p.course?.syllabus.items||[])].join(' ');
export function createCourseUI({catalog,state,show,close,start,record,storageKey,write,read,speak=()=>{},openExams=()=>{},openVocabulary=()=>{}}){
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let selectedSubject=read(`${storageKey}.courseSubject`,'cet4');
 const available=()=>catalog().subjects.filter(s=>s.status==='available'&&s.chapters?.length);
 const subject=()=>catalog().subjects.find(s=>s.id===selectedSubject)||available()[0];
 const chapters=()=>subject().chapters;
 const point=id=>catalog().points.find(p=>p.id===id);
 const byId=id=>{const redirects=Object.assign({},...catalog().subjects.map(s=>s.chapter_redirects||{}));const ch=allChapters(catalog()).find(c=>c.id===(redirects[id]||id))||allChapters(catalog())[0];selectedSubject=ch.subject_id;return ch;};
 function menu(subjectId=selectedSubject,module='全部',query='',vocabUnit=1){
  if(available().some(s=>s.id===subjectId))selectedSubject=subjectId;
  write(`${storageKey}.courseSubject`,selectedSubject);
  const s=subject(),modules=[...new Set(chapters().filter(c=>!c.archived).map(c=>c.module))];
  if(s.id==='cet4'&&s.vocabulary_bank&&module==='词汇')module='核心词汇课堂';
  const filtered=chapters().filter(ch=>!ch.archived&&(module==='全部'||ch.module===module)&&(!(module==='核心词汇课堂'&&vocabUnit)||ch.vocabulary_unit===Number(vocabUnit))&&(!query||`${ch.title} ${ch.module} ${ch.points.map(id=>pointSearchText(point(id))).join(' ')}`.toLowerCase().includes(query.toLowerCase())));
  show(`<p class="eyebrow">CHOOSE YOUR OWN PATH</p><h2 id="modal-title">${esc(s.name)} · 板块与进度</h2><p class="muted">章节与知识点自由选择，分别记住进度，随时进入检测。</p><label class="course-subject-label">切换课程<select id="course-subject">${available().map(x=>`<option value="${x.id}" ${x.id===selectedSubject?'selected':''}>${esc(x.name)}</option>`).join('')}</select></label>${s.id==='cs408'?'<p class="note">教材课堂已接入：组成原理 52 课时、操作系统 54 课时、数据结构 54 课时。进入后可看教材讲解、例题、练习和原书页图；计算机网络沿用原讲义课程。</p>':''}${s.syllabus_note?`<p class="note">${esc(s.id==='cs408'?'三科教材依据本地2027版章首考纲组织；2027官方大纲全文未独立逐项核验。计算机网络仍使用原讲义课程。':s.syllabus_note)}</p>`:''}${s.modules?`<div class="module-grid">${s.modules.map(m=>`<button class="module-card ${module===m.name?'selected':''}" data-module="${esc(m.name)}"><strong>${esc(m.name)}</strong><span>${m.chapters.length} 章 · ${m.point_count} 个知识点</span></button>`).join('')}</div>`:''}<div class="course-filters"><label>板块<select id="course-module">${['全部',...modules].map(m=>`<option ${module===m?'selected':''}>${esc(m)}</option>`).join('')}</select></label><label>查找章节或知识点<input id="course-search" value="${esc(query)}" placeholder="如 TCP、页表、树"></label><button class="button light" id="course-search-submit">查找</button></div>${module==='核心词汇课堂'?`<label>词书单元<select id="course-vocab-unit"><option value="0">全部 Unit</option>${Array.from({length:10},(_,i)=>`<option value="${i+1}" ${Number(vocabUnit)===i+1?'selected':''}>Unit ${i+1}</option>`).join('')}</select></label>`:''}<p class="muted small">${filtered.length} 个章节</p><div class="course-grid">${filtered.map(ch=>{
   const studied=ch.points.filter(id=>state().attempts[id]?.length).length,tests=state().assessments[ch.id]||[];
   const checkpoint=read(`${storageKey}.lesson.${ch.id}`,null);
   const matched=query&&ch.points.find(id=>pointSearchText(point(id)).toLowerCase().includes(query.toLowerCase()));
   const current=matched||checkpoint?.ids?.[checkpoint.index]||ch.points.find(id=>!state().attempts[id])||ch.points[0];
   return `<section class="course-card"><small>${esc(ch.module)}</small><h3>${esc(ch.title)}</h3>${ch.course_format?`<p class="muted small">${esc(ch.subtitle)} · ${ch.points.length} 个课时</p>`:''}<p>${studied}/${ch.points.length} 已学 · ${tests.length?`检测最高 ${Math.max(...tests.map(t=>t.score))} 分`:'尚未检测'}</p><label>选择起点<select data-progress="${ch.id}">${ch.points.map((id,i)=>`<option value="${i}" ${id===current?'selected':''}>${i+1}. ${esc(point(id).concept)}${state().attempts[id]?' · 已学':''}</option>`).join('')}</select></label><div class="button-row"><button class="button" data-enter="${ch.id}">从这里学习</button><button class="text-button" data-test="${ch.id}">章节检测</button></div></section>`;
  }).join('')}</div>`);
  if(['cet4','cet6','cs408','postgrad','calculus','linear','probability'].includes(s.id)){const entry=document.createElement('button');entry.className='button light';entry.id='course-past-papers';const target=s.id==='postgrad'?'english1':['calculus','linear','probability'].includes(s.id)?'math1':s.id;entry.textContent=s.id==='cs408'?'408真题试炼 · 2009—2026':target==='math1'?'数学一真题试炼 · 2017—2026':target==='english1'?'英语一真题试炼 · 2017—2026':'历年真题 · 刷题与考试模式';entry.onclick=()=>{close();openExams(target);};document.querySelector('#course-subject').closest('label').before(entry);}
  if(s.id==='cet4'&&s.vocabulary_bank){const entry=document.createElement('button');entry.className='button';entry.id='course-vocabulary-bank';entry.textContent='核心词汇课堂 · 2327 词 · 3D 教室';entry.onclick=()=>menu('cet4','核心词汇课堂');document.querySelector('#course-subject').closest('label').before(entry);}
  document.querySelector('#course-vocab-unit')?.addEventListener('change',e=>menu(selectedSubject,module,document.querySelector('#course-search').value,Number(e.target.value)));
  document.querySelector('#course-subject').onchange=e=>menu(e.target.value);
  document.querySelectorAll('[data-module]').forEach(b=>b.onclick=()=>menu(selectedSubject,b.dataset.module));
  document.querySelector('#course-module').onchange=e=>menu(selectedSubject,e.target.value,document.querySelector('#course-search').value);
  document.querySelector('#course-search-submit').onclick=()=>menu(selectedSubject,document.querySelector('#course-module').value,document.querySelector('#course-search').value.trim(),document.querySelector('#course-vocab-unit')?.value??1);
  document.querySelector('#course-search').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();document.querySelector('#course-search-submit').click();}};
  document.querySelectorAll('[data-enter]').forEach(b=>b.onclick=()=>{const index=Number(document.querySelector(`[data-progress="${b.dataset.enter}"]`).value);close();start(b.dataset.enter,index);});
  document.querySelectorAll('[data-test]').forEach(b=>b.onclick=()=>assessment(b.dataset.test));
 }
 function notes(module=null){
  if(subject().id==='cet4'&&subject().vocabulary_bank&&(!module||module==='词汇'||module==='核心词汇课堂')){close();openVocabulary({mode:'quick'});return;}
  const modules=[...new Set(chapters().filter(c=>!c.archived).map(c=>c.module))];if(!modules.includes(module))module=modules[0];
  show(`<p class="eyebrow">QUICK RECALL</p><h2 id="modal-title">${esc(subject().name)} · 速记资料</h2><div class="notes-controls"><label>板块<select id="notes-module">${modules.map(m=>`<option ${module===m?'selected':''}>${esc(m)}</option>`).join('')}</select></label><label>查找<input id="notes-search" placeholder="输入知识点或关键词"></label><button class="button light" id="notes-download">下载速记 TXT</button></div><div id="quick-notes"></div>`);
  function selected(){
   const selectedModule=document.querySelector('#notes-module').value,query=document.querySelector('#notes-search').value.trim().toLowerCase();
   const ids=new Set(chapters().filter(ch=>ch.module===selectedModule).flatMap(ch=>ch.points));
   return catalog().points.filter(p=>ids.has(p.id)&&`${p.concept} ${p.quick_meaning||p.summary}`.toLowerCase().includes(query));
  }
  function draw(){const vocabulary=document.querySelector('#notes-module').value==='词汇';
   document.querySelector('#quick-notes').innerHTML=`<table class="quick-table"><thead><tr><th>${vocabulary?'单词':'知识点'}</th><th>${vocabulary?'中文':'要点'}</th></tr></thead><tbody>${selected().map(p=>`<tr><td>${esc(p.concept)}</td><td>${esc(p.quick_meaning||p.summary)}</td></tr>`).join('')}</tbody></table>${selected().length?'':'<p>没有匹配内容。</p>'}`;
  }
  document.querySelector('#notes-module').onchange=()=>{if(subject().id==='cet4'&&document.querySelector('#notes-module').value==='核心词汇课堂'&&subject().vocabulary_bank){close();openVocabulary({mode:'quick'});}else draw();};document.querySelector('#notes-search').oninput=draw;
  document.querySelector('#notes-download').onclick=()=>{const text=selected().map(p=>`${p.concept}\t${p.quick_meaning||p.summary}`).join('\n'),url=URL.createObjectURL(new Blob(['\ufeff'+text],{type:'text/plain;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='树庭速记.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};draw();
 }
 function assessment(id){
  const teacher=catalog().characters.find(c=>c.id==='anaxa');
  const ch=byId(id),key=`${storageKey}.test.${ch.id}`,draft=read(key,{}),answers=draft.answers||{};
  show(`<p class="eyebrow">CHAPTER CHECK · 原创练习</p><h2 id="modal-title">${esc(ch.title)} · 检测</h2><p class="muted">阿那克萨戈拉斯：${esc(teacher.system_lines.test_instruction)}</p><p class="note">本地基础检测，满分 100；不替代 408 综合题的完整推导、代码书写或英语主观题评分。答案自动暂存。</p><form id="chapter-test" class="chapter-test">${ch.test_points.map((pid,i)=>{const p=point(pid),t=p.test;return `<fieldset><legend>${i+1}. ${esc(t.question)}</legend>${t.choices.map((v,j)=>`<label><input type="radio" name="${pid}" value="${j}" ${answers[pid]===j?'checked':''} required>${esc(v)}</label>`).join('')}</fieldset>`;}).join('')}<button class="button" type="submit">交给老师，一起回顾</button></form>`);
  const form=document.querySelector('#chapter-test');
  const instruction=document.createElement('button');instruction.type='button';instruction.className='text-button';instruction.textContent='▶ 听老师的检测说明';instruction.onclick=()=>speak(teacher.system_lines.test_instruction,'anaxa');form.before(instruction);
  form.onchange=()=>{const answers=Object.fromEntries([...new FormData(form)].map(([k,v])=>[k,Number(v)]));write(key,{answers});};
  form.onsubmit=e=>{e.preventDefault();if(!form.reportValidity())return;const answers=Object.fromEntries([...new FormData(form)].map(([k,v])=>[k,Number(v)]));
   record('chapter_test',{chapter_id:ch.id,answers});write(key,null);
   const result=state().assessments[ch.id].at(-1),parts=state().affection_breakdown;
   show(`<p class="eyebrow">REVIEW WITH YOUR PARTNERS</p><h2 id="modal-title">${result.score} 分 · ${result.correct}/${result.total}</h2><p>阿那克萨戈拉斯：分数只是这一次的证据。把没有讲清的概念找出来，下一次再验证。</p><p class="note">当前好感贡献：测试 ${parts.tests} + 有效练习 ${parts.practice} + 学习时长 ${parts.time}。同章取最高分，低分不扣已有贡献。</p>${ch.test_points.map(pid=>{const p=point(pid),t=p.test,matched=answers[pid]===t.answer;return `<section class="test-review"><h3>${matched?'✧ 已掌握':'❧ 再照顾一下'} · ${esc(p.concept)}</h3><p>你的选择：${esc(t.choices[answers[pid]])}</p><p>参考：${esc(t.choices[t.answer])}</p><p>${esc(t.explanation)}</p><button class="text-button" data-return-point="${pid}">回到这个知识点</button></section>`;}).join('')}<button class="button" id="test-course-menu">选择其他板块</button>`);
   const reviewVoice=document.createElement('button');reviewVoice.className='text-button';reviewVoice.textContent='▶ 听老师的回顾';reviewVoice.onclick=()=>speak(teacher.system_lines.test_review,'anaxa');document.querySelector('#test-course-menu').before(reviewVoice);
   document.querySelectorAll('[data-return-point]').forEach(b=>b.onclick=()=>{close();start(ch.id,ch.points.indexOf(b.dataset.returnPoint));});document.querySelector('#test-course-menu').onclick=()=>menu();
  };
 }
 return {menu,notes,assessment,chapter:byId};
}
