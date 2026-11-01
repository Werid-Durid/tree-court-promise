import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createFilmPlayer} from '../frontend/cinema-player.js';
const spec=JSON.parse(fs.readFileSync(new URL('../../data/cinematics/phainon-wheat.json',import.meta.url)));
const film={...spec,duration_seconds:spec.duration,url:'/main.mp4',poster:'/poster.jpg',download_url:'/continuous.mp4',interactions:spec.interactions.map(q=>({...q,choices:q.choices.map(c=>({...c,clip_url:`/${q.id}-${c.id}.mp4`}))}))};

// 媒体事件由测试驱动，覆盖加载、选择完成和中途关闭的状态转换。
// 此处不模拟浏览器解码或画面布局，后者由媒体完整解码报告与审看帧检查。
function harness(){
 let nodes;const saved=new Map();
 function show(){
  nodes=new Map();for(const selector of ['.interactive-film','[data-film-line]','[data-film-speaker]','[data-film-options]','[data-film-start]','[data-film-toggle]','[data-film-seek]','[data-film-time]','[data-film-reset]','[data-film-fullscreen]'])nodes.set(selector,{hidden:false,disabled:false,textContent:'',value:0});
  const options=nodes.get('[data-film-options]');options.replaceChildren=()=>{options.buttons=[];};options.querySelectorAll=()=>options.buttons||[];
  Object.defineProperty(options,'innerHTML',{set(html){options.buttons=[...html.matchAll(/data-film-choice="([^"]+)"/g)].map(m=>({dataset:{filmChoice:m[1]}}));}});
  const handlers={};nodes.set('video',{paused:true,currentTime:0,playbackRate:1,src:'',addEventListener(name,fn){(handlers[name]??=[]).push(fn);},emit(name){for(const fn of handlers[name]||[])fn();},load(){},play(){this.paused=false;return Promise.resolve();},pause(){this.paused=true;}});
 }
 const root={querySelector:selector=>nodes.get(selector)};
 const player=createFilmPlayer({root,show,read:(key,fallback)=>saved.has(key)?structuredClone(saved.get(key)):fallback,write:(key,value)=>saved.set(key,structuredClone(value)),key:'qa',esc:String});
 const el=selector=>nodes.get(selector);const video=()=>el('video');
 const metadata=()=>video().onloadedmetadata();
 const seek=at=>{el('[data-film-seek]').value=at;el('[data-film-seek]').onchange();};
 const choose=id=>el('[data-film-options]').buttons.find(b=>b.dataset.filmChoice===id).onclick();
 return{player,el,video,metadata,seek,choose,saved};
}

test('四个选项各加载自己的回应，播放完成才提交并继续主片',()=>{
 for(const first of film.interactions[0].choices)for(const second of film.interactions[1].choices){
  const h=harness();h.player.open(film);h.metadata();h.seek(74);
  assert.equal(h.video().currentTime,22);assert.equal(h.video().paused,true);assert.equal(h.el('[data-film-seek]').disabled,true);
  h.choose(first.id);assert.equal(h.video().src,first.clip_url);h.metadata();assert.equal(h.video().paused,false);
  h.video().emit('ended');assert.equal(h.video().src,film.url);h.metadata();assert.ok(h.video().currentTime>22);
  h.seek(74);assert.equal(h.video().currentTime,58.4);h.choose(second.id);assert.equal(h.video().src,second.clip_url);h.metadata();h.video().emit('ended');h.metadata();
  h.seek(74);assert.equal(h.video().currentTime,74);h.player.close();
  const saved=[...h.saved.values()][0];assert.deepEqual(saved.answers,{waymark:first.id,name:second.id});
 }
});

test('回应中关闭会暂停；重新打开保留选择节点而不误记完成',()=>{
 const h=harness();h.player.open(film);h.metadata();h.seek(60);h.choose('blank');h.metadata();const old=h.video();h.player.close();assert.equal(old.paused,true);
 h.player.open(film);h.metadata();assert.equal(h.video().currentTime,22);h.el('[data-film-start]').onclick();assert.equal(h.el('[data-film-speaker]').textContent,'你的回应');assert.equal(h.el('[data-film-options]').buttons.length,2);
});

test('重新赴约清空已选回应；异常倍速恢复正常',()=>{
 const h=harness();h.player.open(film);h.metadata();h.seek(70);h.choose('next_place');h.metadata();h.video().emit('ended');h.metadata();h.el('[data-film-reset]').onclick();h.metadata();assert.equal(h.video().currentTime,0);h.seek(70);assert.equal(h.video().currentTime,22);
 h.video().playbackRate=1.45;h.video().emit('ratechange');assert.equal(h.video().playbackRate,1);
});

test('不同角色的回应和静默段使用各自姓名与场景文案',()=>{
 for(const character_name of ['那刻夏','风堇','遐蝶']){
  const other={...film,id:character_name,character_name,quiet_label:'专属场景',silence:'与你独处的安静时刻。'};
  const h=harness();h.player.open(other);h.metadata();h.video().currentTime=0;h.video().emit('timeupdate');
  assert.equal(h.el('[data-film-speaker]').textContent,'专属场景');assert.equal(h.el('[data-film-line]').textContent,other.silence);
  h.seek(70);h.choose('blank');assert.equal(h.el('[data-film-speaker]').textContent,character_name);
 }
});
