// 结构化技巧交互：排序和匹配提交完整关系，不能只提交客户端自报“答对”。
export function evaluateInteraction(spec,response){
 if(spec.type==='structure_order'){
  const ids=spec.cards.map(c=>c.id);
  if(!Array.isArray(response)||response.length!==ids.length||new Set(response).size!==ids.length||response.some(x=>!ids.includes(x)))throw Error('请完整排列每张结构卡。');
  return response.every((x,n)=>x===spec.solution[n]);
 }
 const left=(spec.functions||spec.issues).map(c=>c.id),right=(spec.sentences||spec.revisions).map(c=>c.id);
 if(!response||Array.isArray(response)||typeof response!=='object'||Object.keys(response).length!==left.length||!left.every(k=>right.includes(response[k]))||new Set(Object.values(response)).size!==right.length)throw Error('请将各项一一匹配，避免重复。');
 return left.every(k=>response[k]===spec.solution[k]);
}

export function mountSkillInteraction({point,container,onSubmit,onError}){
 const spec=point.interaction;if(!spec)return;
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const material=document.createElement('section');material.className='skill-material';material.innerHTML=`<strong>一起观察的材料</strong><p>${esc(spec.material)}</p><p>${esc(spec.task)}</p>`;container.before(material);
 const label=container.previousElementSibling?.previousElementSibling;
 if(label?.classList.contains('clue-label'))label.textContent=spec.type==='reasoning_clues'?'沿哪条思路读出材料中的证据？':'把结构关系动手搭起来。';
 if(spec.type==='reasoning_clues')return;
 container.className='skill-workspace';
 if(spec.type==='structure_order'){
  const order=spec.cards.map(c=>c.id);
  const draw=()=>{
   container.innerHTML=`<ol class="structure-cards">${order.map((id,n)=>`<li><span>${esc(spec.cards.find(c=>c.id===id).text)}</span><button type="button" data-up="${n}" ${n===0?'disabled':''} aria-label="第${n+1}张上移">↑</button><button type="button" data-down="${n}" ${n===order.length-1?'disabled':''} aria-label="第${n+1}张下移">↓</button></li>`).join('')}</ol><button class="button" data-submit-structure>和老师一起看这组结构</button>`;
   container.querySelectorAll('[data-up],[data-down]').forEach(b=>b.onclick=()=>{const from=Number(b.dataset.up??b.dataset.down),to=from+(b.dataset.up===undefined?1:-1);[order[from],order[to]]=[order[to],order[from]];draw();});
   container.querySelector('[data-submit-structure]').onclick=()=>onSubmit([...order]);
  };draw();
 }else{
  const left=spec.functions||spec.issues,right=spec.sentences||spec.revisions;
  container.innerHTML=`<form class="template-match">${left.map(c=>`<label><span>${esc(c.text)}</span><select name="${c.id}" required><option value="">找到与它对应的表达</option>${right.map(r=>`<option value="${r.id}">${esc(r.text)}</option>`).join('')}</select></label>`).join('')}<button class="button">和老师一起核对搭配</button></form>`;
  container.querySelector('form').onsubmit=e=>{e.preventDefault();try{const response=Object.fromEntries(new FormData(e.target));evaluateInteraction(spec,response);onSubmit(response);}catch(err){onError(err.message);}};
 }
}
