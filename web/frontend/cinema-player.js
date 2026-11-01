import {pendingCue,normalizeFilmProgress,filmLineAt} from './cinema-state.js';

export function createFilmPlayer({root,show,read,write,key,esc}){
 let active=null;
 function close(){
  if(!active)return;
  const {video,film,progress,mode}=active;video.pause();
  if(mode==='main')progress.time=video.currentTime;
  write(`${key}.cinema.${film.id}`,progress);active=null;
 }
 function open(film){
  close();const person=film.character_name||'白厄';const saveKey=`${key}.cinema.${film.id}`,progress=normalizeFilmProgress(film,read(saveKey,null));
  show(`<h2 id="modal-title">${esc(film.title)}</h2><section class="interactive-film" aria-label="${esc(person)}第一人称互动邀约">
   <div class="film-stage"><video class="cinematic-player" playsinline preload="metadata" poster="${esc(film.poster)}" aria-label="${esc(person)}互动演出"></video><button class="film-start button" data-film-start>开始赴约${progress.time>0?' · 继续上次':''}</button></div>
   <section class="film-dialogue" aria-live="polite"><small data-film-speaker>${esc(person)} · 与你独处的时光</small><p data-film-line>准备好了，就来听听对方想对你说的话。</p><div class="film-options" data-film-options></div></section>
   <div class="film-controls"><button class="text-button" data-film-toggle>播放</button><label class="film-seek-label">剧情进度<input data-film-seek type="range" min="0" max="${film.duration_seconds}" step="0.1" value="${progress.time}" aria-label="剧情进度"></label><span data-film-time></span><button class="text-button" data-film-fullscreen>全屏</button><button class="text-button" data-film-reset>重新赴约</button></div>
   <p class="muted small">${esc(film.disclosure)} 选项会暂停演出，回应播放后继续。进度保存在此浏览器。</p><a class="text-button" href="${esc(film.download_url)}" target="_blank" rel="noopener">打开连续观看版 ↗</a>
  </section>`);
  const video=root.querySelector('video'),stage=root.querySelector('.interactive-film'),line=root.querySelector('[data-film-line]'),speaker=root.querySelector('[data-film-speaker]'),options=root.querySelector('[data-film-options]'),start=root.querySelector('[data-film-start]'),toggle=root.querySelector('[data-film-toggle]'),seek=root.querySelector('[data-film-seek]'),clock=root.querySelector('[data-film-time]');
  const s={video,film,progress,mode:'main',cue:null,choice:null};active=s;
  const persist=()=>write(saveKey,progress);
  const playing=()=>{start.hidden=true;video.playbackRate=1;toggle.textContent='暂停';video.play().catch(()=>{start.hidden=false;start.textContent='点击继续演出';toggle.textContent='播放';});};
  function loadMain(at,play=false){
   s.mode='main';seek.disabled=false;options.replaceChildren();video.src=film.url;video.onloadedmetadata=()=>{if(active!==s)return;video.currentTime=at;if(play)playing();};video.load();
  }
  function showCue(cue){
   s.mode='choice';s.cue=cue;video.pause();video.currentTime=cue.at;progress.time=cue.at;persist();start.hidden=true;toggle.disabled=true;seek.disabled=true;speaker.textContent='你的回应';line.textContent=cue.prompt;
   options.innerHTML=cue.choices.map(choice=>`<button class="button light" data-film-choice="${esc(choice.id)}">${esc(choice.label)}</button>`).join('');
   for(const button of options.querySelectorAll('button'))button.onclick=()=>{
    const choice=cue.choices.find(c=>c.id===button.dataset.filmChoice);s.mode='response';s.choice=choice;options.replaceChildren();speaker.textContent=person;line.textContent=choice.reply;toggle.disabled=false;
    video.src=choice.clip_url;video.onloadedmetadata=()=>{if(active===s)playing();};video.load();
   };
  }
  video.addEventListener('timeupdate',()=>{
   if(active!==s||s.mode!=='main')return;
   const at=video.currentTime,cue=pendingCue(film,at,progress.answers);
   if(cue){showCue(cue);return;}
   const caption=filmLineAt(film,at);speaker.textContent=caption?person:(film.quiet_label||'麦田里的晚风');line.textContent=caption?.text||film.silence||'风轻轻吹过，你们仍坐在彼此看得见的地方。';
   seek.value=at;clock.textContent=`${Math.floor(at)} / ${film.duration_seconds} 秒`;progress.time=at;
   if(Math.floor(at)%2===0)persist();
  });
  video.addEventListener('ended',()=>{
   if(active!==s)return;
   if(s.mode==='response'){
    progress.answers[s.cue.id]=s.choice.id;progress.time=s.cue.at+.08;persist();toggle.disabled=false;loadMain(progress.time,true);
   }else if(s.mode==='main'){
    progress.time=film.duration_seconds;persist();speaker.textContent='已留在回忆里';line.textContent='下次见面的地方，留给你们慢慢决定。';toggle.textContent='已结束';
   }
  });
  video.addEventListener('ratechange',()=>{if(video.playbackRate!==1)video.playbackRate=1;});
  start.onclick=()=>{
   if(s.mode==='main'){const cue=pendingCue(film,video.currentTime,progress.answers);if(cue){showCue(cue);return;}}
   playing();
  };
  toggle.onclick=()=>{if(video.paused)start.onclick();else{video.pause();toggle.textContent='继续';persist();}};
  seek.onchange=()=>{
   if(s.mode!=='main')return;
   const target=Number(seek.value),cue=pendingCue(film,target,progress.answers);video.currentTime=cue?cue.at:target;
   if(cue)showCue(cue);
  };
  root.querySelector('[data-film-reset]').onclick=()=>{close();write(saveKey,{revision:film.revision,time:0,answers:{}});open(film);};
  video.addEventListener('error',()=>{if(active===s){speaker.textContent='演出暂未加载';line.textContent='这段画面暂时无法读取。可以重新赴约，或打开下方连续观看版。';}});
  root.querySelector('[data-film-fullscreen]').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else stage.requestFullscreen?.();};
  loadMain(progress.time);clock.textContent=`${Math.floor(progress.time)} / ${film.duration_seconds} 秒`;
 }
 return {open,close};
}
