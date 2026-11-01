import {studyChoice,saveStudyChoice,companionPicker,STUDY_PEOPLE} from './study-companions.js';
/* 树庭自习室 · 专注陪伴模式：计时环 + 3D 陪坐 + 环境声 + 今日统计 */
const $ = s => document.querySelector(s);
const KEY = 'treecourt-focus-v1';
const DURATION = 25 * 60;
const CIRC = 2 * Math.PI * 100;

let companion=studyChoice(),sceneApi=null;


const store = load();
let remaining = DURATION;
let running = false;
let timer = null;
let lastTick = 0;
let lineIndex = 0;
let audio = null;

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) || '{}');
    return { day: raw.day || '', today: raw.today || 0, sessions: raw.sessions || 0 };
  } catch {
    return { day: '', today: 0, sessions: 0 };
  }
}
function save() {
  try { localStorage.setItem(KEY, JSON.stringify(store)); } catch {}
}
function today() { const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; }
function ensureDay() {
  if (store.day !== today()) { store.day = today(); store.today = 0; store.sessions = 0; save(); }
}
function fmt(sec) {
  const s = Math.max(0, Math.ceil(sec));
  return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
}
function say(text, rotate = false) {
  const el = $('#fc-line');
  if (!el) return;
  el.textContent = text;
  
}
function render() {
  ensureDay();
  $('#fc-time').textContent = fmt(remaining);
  const progress = 1 - remaining / DURATION;
  $('#fc-bar').style.strokeDashoffset = String(CIRC * (1 - progress));
  $('#fc-start').textContent = running ? '暂停片刻' : (remaining >= DURATION ? '开始专注' : '继续专注');
  $('#fc-end').disabled = !running && remaining >= DURATION;
  $('#fc-hint').textContent = running
    ? '专注中 · 切出页面会自动暂停'
    : '25 分钟一轮 · 切出页面会自动暂停';
  $('#fc-stats').textContent = `今日专注 ${Math.floor(store.today)} 分钟 · 已完成 ${store.sessions} 轮`;
}

function start() {
  if (running) return;
  running = true;
  lastTick = performance.now();
  timer = setInterval(tick, 250);
  say(STUDY_PEOPLE[companion].name+'：'+STUDY_PEOPLE[companion].line);
  render();
}
function pause() {
  if (!running) return;
  running = false;
  clearInterval(timer);
  timer = null;
  say(STUDY_PEOPLE[companion].name+'：'+STUDY_PEOPLE[companion].pause);
  render();
}
function tick() {
  const now = performance.now();
  const dt = (now - lastTick) / 1000;
  lastTick = now;
  remaining = Math.max(0, remaining - dt);
  if (remaining <= 0) { complete(); return; }
  render();
}
function complete() {
  running = false;
  clearInterval(timer);
  timer = null;
  remaining = 0;
  store.sessions += 1;
  store.today += DURATION / 60;
  save();
  say(STUDY_PEOPLE[companion].name+'：这一轮结束了。做得很好，起来喝口水吧。');
  render();
}
function finish() {
  const used = remaining <= 0 ? 0 : Math.max(0, Math.round((DURATION - remaining) / 60));
  pause();
  if (used > 0) {
    store.today += used;
    store.sessions += 1;
    save();
  }
  remaining = DURATION;
  say(STUDY_PEOPLE[companion].name+'：这一段安静，已经留下了。');
  render();
}

function toggleSound() {
  const btn = $('#fc-sound');
  if (audio) {
    audio.context.close();
    audio = null;
    btn.textContent = '环境声 · 关';
    btn.setAttribute('aria-pressed', 'false');
    return;
  }
  try {
    const context = new AudioContext();
    const buffer = context.createBuffer(1, context.sampleRate * 3, context.sampleRate);
    const data = buffer.getChannelData(0);
    let last = 0;
    for (let i = 0; i < data.length; i++) {
      last = (last + 0.02 * (Math.random() * 2 - 1)) / 1.02;
      data[i] = last * 3.5;
    }
    const source = context.createBufferSource();
    const filter = context.createBiquadFilter();
    const gain = context.createGain();
    source.buffer = buffer;
    source.loop = true;
    filter.type = 'lowpass';
    filter.frequency.value = 400;
    gain.gain.value = 0.08;
    source.connect(filter).connect(gain).connect(context.destination);
    source.start();
    audio = { context };
    btn.textContent = '环境声 · 开';
    btn.setAttribute('aria-pressed', 'true');
  } catch {
    say(STUDY_PEOPLE[companion].name+'：浏览器这次没允许环境声，画面依旧陪你。');
  }
}

function setupUi() {
  $('#fc-picker').innerHTML=companionPicker(companion);
  say(STUDY_PEOPLE[companion].name+'：'+STUDY_PEOPLE[companion].line);
  document.querySelectorAll('[data-study-companion]').forEach(button=>button.onclick=async()=>{companion=button.dataset.studyCompanion;saveStudyChoice(companion);document.querySelectorAll('[data-study-companion]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));say(STUDY_PEOPLE[companion].name+'：'+STUDY_PEOPLE[companion].line);await sceneApi?.setCompanion(companion).catch(()=>say('自习动画暂时无法加载，计时仍可使用。'));});
  $('#fc-start').onclick = () => {
    if (running) { pause(); return; }
    if (remaining <= 0) remaining = DURATION;
    start();
  };
  $('#fc-end').onclick = finish;
  $('#fc-sound').onclick = toggleSound;
  $('#fc-full').onclick = () => {
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    else document.documentElement.requestFullscreen?.().catch(() => {});
  };
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && running) pause();
  });
  setInterval(() => {
    if (!running) return;
    say(STUDY_PEOPLE[companion].name+'：'+STUDY_PEOPLE[companion].line);
  }, 300000);
}

function setupScene() {
  import('/static/study-wallpaper.bundle.js')
    .then(mod => mod.mountWallpaper($('#focus-stage'), {
      character:companion,
      onStatus: text => {
        const el = $('#fc-status');
        if (el) el.textContent = text;
      },
    })).then(api=>{sceneApi=api;if(api&&document.querySelector('#focus-stage')?.dataset.character!==companion)api.setCompanion(companion).catch(()=>{});})
    .catch(() => {
      const el = $('#fc-status');
      if (el) el.textContent = '场景暂未载入，计时与陪伴仍可使用。';
    });
}

setupUi();
setupScene();
render();
