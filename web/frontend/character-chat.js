// 同学/助教对话使用人设档案中的分支模板；只插入当前知识点，不修改题目答案。
export function chatText(template,point){
 const context={topic:point.concept,boundary:point.course?.textbook?.[1]?.text||point.summary,hook:point.memoryHook};
 return String(template).replace(/\{(topic|boundary|hook)\}/g,(_,k)=>context[k]||'');
}
export function createCharacterChat({character,point,panel,say,back,esc}){
 const topics=character.classroom_chat||[];if(!topics.length)return false;
 panel.querySelector('.aside-conversation')?.remove();
 const box=document.createElement('div');box.className='aside-conversation';panel.append(box);
 function buttons(items){box.innerHTML=items.map((x,i)=>`<button class="button light" data-chat="${i}">${esc(x.label)}</button>`).join('');box.querySelectorAll('[data-chat]').forEach(b=>b.onclick=items[Number(b.dataset.chat)].run);}
 function menu(){say(`你想和${character.name}聊哪一件事？`,false);buttons([...topics.map(t=>({label:t.label,run:()=>open(t)})),{label:'回到课堂话题',run:back}]);}
 function open(t){say(chatText(t.opening,point));buttons(t.choices.map(c=>({label:c.label,run:()=>{say(chatText(c.reply,point));buttons([{label:c.followup_label,run:()=>{say(chatText(c.followup,point));buttons([{label:'再聊一个话题',run:menu},{label:'回到课堂话题',run:back}]);}},{label:'我想聊另一个话题',run:menu},{label:'回到课堂话题',run:back}]);}})));}
 menu();return true;
}
