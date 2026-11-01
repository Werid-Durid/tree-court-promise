// Blender/Eevee 三渲二陪学循环。计时由页面管理，切换角色不重置计时。
const NAMES={anaxa:'那刻夏',hyacine:'风堇',castor:'遐蝶',phainon:'白厄'};
let active=null;
export function destroyWallpaper(){active?.dispose();active=null;}
export async function mountWallpaper(container,{onStatus=()=>{},character='anaxa'}={}){
 destroyWallpaper();let disposed=false,generation=0,current=null;
 const api={
  async setCompanion(id){
   if(!Object.hasOwn(NAMES,id)||disposed)return false;const token=++generation;
   onStatus(`正在邀请${NAMES[id]}陪你学习…`);
   const response=await fetch('/api/study-companions');if(!response.ok)throw Error('无法读取自习室');
   const spec=(await response.json()).companions.find(c=>c.id===id);
   if(disposed||token!==generation)return false;
   if(!spec?.ready){onStatus(`${NAMES[id]}的自习动画尚未就绪`);return false;}
   const video=document.createElement('video');video.className='study-companion-video';video.muted=true;video.loop=true;video.playsInline=true;video.preload='auto';video.poster=spec.poster;video.src=spec.url;video.setAttribute('aria-label',`${NAMES[id]}与你安静自习的三渲二动画`);
   video.style.cssText='position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center 44%;';
   await new Promise((resolve,reject)=>{video.onloadeddata=resolve;video.onerror=()=>reject(Error('自习动画加载失败'));video.load();});
   if(disposed||token!==generation){video.removeAttribute('src');video.load();return false;}
   if(current){current.pause();current.removeAttribute('src');current.load();current.remove();}
   current=video;container.prepend(video);container.dataset.character=id;container.dataset.ready='true';
   video.addEventListener('ratechange',()=>{if(video.playbackRate!==1)video.playbackRate=1;});
   if(!document.hidden)await video.play().catch(()=>{});
   onStatus(`${NAMES[id]}在你对面 · 安静陪学`);return true;
  },
  dispose(){disposed=true;generation++;document.removeEventListener('visibilitychange',visibility);if(current){current.pause();current.removeAttribute('src');current.load();current.remove();current=null;}}
 };
 function visibility(){if(!current)return;if(document.hidden)current.pause();else current.play().catch(()=>{});}
 document.addEventListener('visibilitychange',visibility);active=api;
 try{await api.setCompanion(character);}catch(e){onStatus('自习动画暂时无法加载，计时仍可使用。');}
 return api;
}
