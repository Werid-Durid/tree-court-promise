// 词库课堂沿用真实课堂、角色镜头与学习事件；切换讲解步骤不计作答。
export function createVocabularyClassroom({read,write,storageKey,redraw,show,talk}){
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const key=p=>`${storageKey}.wordClassStage.${p.id}`;
 const step=p=>{const n=read(key(p),0);return Number.isInteger(n)&&n>=0&&n<3?n:0;};
 const speaker=p=>step(p)===1?'hyacine':'anaxa';
 const text=p=>step(p)===2?p.prompt:p.dialogue[speaker(p)];
 const board=(p,feedback=false)=>feedback||step(p)!==2?`${p.vocabulary_lesson.meaning}\n原书 Unit ${p.vocabulary_lesson.unit} · 第${p.vocabulary_lesson.page}页`:'遮住中文：回忆释义 → 选择联想锚点 → 核对原书';
 function source(p){const v=p.vocabulary_lesson;show(`<p class="eyebrow">YOUR WORDBOOK · Unit ${v.unit}</p><h2 id="modal-title">${esc(p.concept)} · 原书第${v.page}页</h2><p>${esc(v.meaning)}</p><img class="network-source-image" src="/api/vocabulary/cet4/source/${v.word_id}" alt="本词原图">${(v.continuation_pages||[]).map((page,i)=>`<p>释义续行 · 第${page}页</p><img class="network-source-image" src="/api/vocabulary/cet4/source/${v.word_id}?part=${i+1}" alt="本词释义续行">`).join('')}<p class="note">词义来自指定扫描词表，OCR 仍可能有误，请以原页为准；联想练习为本项目原创，不冒称词源分析。</p>`);}
 function mount(p){
  const n=step(p),block=document.createElement('section');block.className='vocabulary-lesson';
  block.innerHTML=`<nav class="network-stage-nav" aria-label="词汇课堂步骤">${['老师讲词','助教联想','遮义回忆'].map((name,i)=>`<button data-word-stage="${i}" aria-current="${i===n?'step':'false'}" class="${i===n?'active':''}">${i+1}. ${name}</button>`).join('')}</nav><div class="network-lesson-tools"><button class="text-button" id="word-source">核对词书原页</button><span>Unit ${p.vocabulary_lesson.unit} · 原书第${p.vocabulary_lesson.page}页</span></div>${n<2?`<div class="network-board">${esc(p.concept)} — ${esc(p.vocabulary_lesson.meaning)}</div><p>${n===0?'听老师辨认词形与释义，再用自己的话复述。':'记忆钩子是回忆练习，不把形似拼写误当成真实词根。'}</p><div class="button-row"><button class="button" id="word-stage-next">${n===0?'请助教建立联想':'遮住释义，试着回忆'} →</button><button class="text-button" id="word-peer">${p.classmate.character==='castor'?'听遐蝶精炼释义':'和白厄互相抽查'}</button></div>`:'<p class="note">先自己回忆，再选释义锚点；每次作答后都保留记忆钩子，选错不扣好感。</p>'}`;
  document.querySelector('.word-line').after(block);
  document.querySelectorAll('.clue-label,.clues').forEach(x=>x.classList.toggle('network-hidden',n!==2));
  block.querySelectorAll('[data-word-stage]').forEach(b=>b.onclick=()=>{write(key(p),Number(b.dataset.wordStage));redraw();});
  block.querySelector('#word-stage-next')?.addEventListener('click',()=>{write(key(p),n+1);redraw();});
  block.querySelector('#word-peer')?.addEventListener('click',()=>talk(p.classmate.character));
  block.querySelector('#word-source').onclick=()=>source(p);
 }
 return {step,speaker,text,board,mount,source};
}
