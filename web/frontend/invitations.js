import {outingAllowed,bondStage,outingEchoes} from './invitation-state.js';
export function createInvitations({content,catalog,state,record,read,write,key,speak,stopVoice,notify,esc,show}){
 let host,sceneApi,sceneModule,activeId,generation=0,loading=false;
 function open(id){write(key+'.outingCharacter',id);location.hash='outing';}
 function leave(){generation++;sceneApi?.dispose();sceneApi=null;host=null;activeId=null;loading=false;stopVoice();}
 function prose(node,choices){return node.text.split('\n').map(line=>`<p class="${line.startsWith('「')?'outing-spoken':'outing-narration'}">${esc(line)}</p>`).join('')+outingEchoes(node,choices).map(text=>`<p class="outing-echo">${esc(text)}</p>`).join('');}
 function memories(id){
  const story=catalog().invitations.stories.find(s=>s.character===id),session=state().outings[id];
  const entries=story.nodes.filter(n=>session?.memories?.[n.id]||session?.endings?.includes(n.id));
  show(`<h2 id="modal-title">${esc(story.title)} · 回忆手札</h2><p class="muted">${entries.length} 段已读片段 · 专属相处 ${state().bond_points?.[id]||0} / ${catalog().invitations.bond_cap}。回看不会改变当前进度。</p>${entries.length?entries.map((n,i)=>`<details class="outing-memory"><summary>${i+1}. ${esc(n.ending?(n.ending==='romance'?'恋人结尾':'同行结尾'):n.text.split('\n')[0].slice(0,24)+'…')}</summary>${prose(n,session.memories?.[n.id]||[])}${n.afterword?`<blockquote>${esc(n.afterword)}</blockquote>`:''}</details>`).join(''):'<p>赴约后，读过的片段会留在这里。</p>'}`);
 }
 async function render(){
  const id=read(key+'.outingCharacter','anaxa'),c=catalog().characters.find(c=>c.id===id),story=catalog().invitations?.stories.find(s=>s.character===id);if(!story){location.hash='companions';return;}
  if(activeId&&activeId!==id)leave();activeId=id;
  const session=state().outings[id]||{node:story.start,choices:[],endings:[]},node=story.nodes.find(n=>n.id===session.node)||story.nodes[0];
  if(host)host.remove();
  content.innerHTML=`<section class="outing-world" data-character="${id}"><div id="outing-scene" class="outing-scene"></div><header class="outing-header"><a class="button light" href="#companions">← 返回同行之人</a><div><small>树庭日常邀约 · 原创</small><h1>${esc(story.title)}</h1><p>${esc(story.place)}</p></div><button class="button light" id="outing-walk">看看周围</button></header><span class="outing-status" id="outing-status">正在准备场景…</span><section class="outing-dialogue"><div class="dialogue-header"><strong class="speaker">${esc(c.address)}</strong><span class="tag">${state().relationships[id]==='romance'?'亲密同行':'好友与学术搭档'} · 好感 ${state().affection[id]}</span><button class="text-button" id="outing-voice">▶ 朗读</button></div><div id="outing-text" aria-live="polite">${esc(node.text)}</div><div class="outing-choices">${node.choices.map(choice=>{const ok=outingAllowed(choice,state(),id);return `<button class="button light" data-outing-choice="${esc(choice.id)}" ${ok?'':'disabled'}>${esc(choice.label)}${ok?'':choice.relationship?' · 恋爱关系后开放':` · 好感 ${choice.min_affection} 后开放`}</button>`;}).join('')}</div>${node.ending?`<div class="outing-keepsake"><strong>已收入回忆 · ${esc(node.keepsake)}</strong><p>这段回忆不会增加学习分数或好感。可以保留不同选择的结局。</p><button class="button" id="outing-restart">再赴一次约</button><a class="button light" href="#companions">回到同行之人</a></div>`:''}<p class="muted small">30 好感可谈更多心事。亲密分支需先在同行之人的「关系选择」中主动选择恋爱；好友路线始终保留。</p></section></section>`;
  const text=content.querySelector('#outing-text');text.innerHTML=prose(node,session.choices);
  content.querySelector('.outing-dialogue .tag').textContent=`${bondStage(state().affection[id])} · ${state().relationships[id]==='romance'?'恋人':state().relationships[id]==='friend'?'好友':'同行'} · 好感 ${state().affection[id]}`;
  const note=content.querySelector('.outing-dialogue>p.small');note.textContent='首次关键相处只增加这一位角色的好感；同一节点的不同回答等额，重玩不重复增加。30 好感开放心事，恋人结尾需先确认关系。';
  const collected=content.querySelector('.outing-keepsake p');if(collected)collected.textContent=node.afterword;
  const memoryButton=document.createElement('button');memoryButton.className='text-button';memoryButton.textContent='回忆手札';memoryButton.onclick=()=>memories(id);content.querySelector('.dialogue-header').append(memoryButton);
  content.querySelectorAll('[data-outing-choice]').forEach(b=>b.onclick=()=>{stopVoice();const before=state().bond_points?.[id]||0;record('outing_choice',{character:id,node_id:node.id,choice_id:b.dataset.outingChoice,story_revision:2});const gain=(state().bond_points?.[id]||0)-before;if(gain)notify(`这段相处已被记住 · ${c.name}好感 +${gain}`);render();});
  content.querySelector('#outing-restart')?.addEventListener('click',()=>{record('outing_choice',{character:id,restart:true});render();});
  content.querySelector('#outing-voice').onclick=()=>speak(node.spoken||node.text,id,'outing-'+id+'-'+node.id);
  content.querySelector('#outing-walk').onclick=()=>{content.querySelector('.outing-world').classList.toggle('exploring');const exploring=content.querySelector('.outing-world').classList.contains('exploring');if(exploring)sceneApi?.walk();else sceneApi?.focus();content.querySelector('#outing-walk').textContent=exploring?'回到谈话':'看看周围';};
  if(!host){host=document.createElement('div');host.className='outing-canvas';}content.querySelector('#outing-scene').append(host);
  if(sceneApi){content.querySelector('#outing-status').textContent=host.dataset.status||'场景已就绪';sceneApi.focus();return;}
  if(loading)return;loading=true;
  const token=++generation;sceneModule??=await import('./outing-scene.bundle.js');
  const api=await sceneModule.mountOuting(host,{character:id,scene:story.scene,onStatus:message=>{if(token!==generation)return;host.dataset.status=message;const el=content.querySelector('#outing-status');if(el)el.textContent=message;}});
  if(token!==generation){api.dispose();return;}sceneApi=api;loading=false;
 }
 return {open,render,leave,memories,speech:value=>sceneApi?.speech(value)};
}
