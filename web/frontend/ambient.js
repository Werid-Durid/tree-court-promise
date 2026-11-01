// 程序化环境音乐引擎：全部声音由 Web Audio 实时合成（原创，不采样他人作品）。
const midi = n => 440 * Math.pow(2, (n - 69) / 12);

// 三种氛围预设：warm-pad / rain-paper / night-drone
const PRESETS = {
  'warm-pad': {
    chords: [
      [60, 64, 67, 71], // Cmaj7
      [57, 60, 64, 67], // Am7
      [53, 57, 60, 64], // Fmaj7
      [55, 59, 62, 64], // G6
    ],
    chord_seconds: 8,
    pad_gain: 0.10,
    pluck: { scale: [60, 62, 64, 67, 69, 71, 72], interval: [2.2, 5.5], gain: 0.05 },
    noise: 'crackle',
  },
  'rain-paper': {
    chords: [
      [57, 60, 63],       // Am
      [53, 57, 60],       // F
      [55, 59, 62],       // G
      [57, 60, 64],       // Am7
    ],
    chord_seconds: 10,
    pad_gain: 0.06,
    pluck: null,
    noise: 'rain',
  },
  'night-drone': {
    chords: [
      [48, 55, 60],
      [50, 57, 62],
    ],
    chord_seconds: 12,
    pad_gain: 0.08,
    pluck: { scale: [72, 76, 79, 81], interval: [4, 9], gain: 0.025 },
    noise: 'crackle',
  },
};

export class AmbientEngine {
  constructor() {
    this.ctx = null;
    this.master = null;
    this.live = [];        // 当前活跃节点，停止时断开
    this.timers = [];
    this.preset = null;
    this.running = false;
  }

  async ensure() {
    if (this.ctx) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.0;
    this.master.connect(this.ctx.destination);
  }

  _noiseBuffer(seconds = 2) {
    const len = Math.floor(this.ctx.sampleRate * seconds);
    const buf = this.ctx.createBuffer(1, len, this.ctx.sampleRate);
    const d = buf.getChannelData(0);
    let last = 0;
    for (let i = 0; i < len; i++) { last = (last + 0.02 * (Math.random() * 2 - 1)) / 1.02; d[i] = last * 3.0; }
    return buf;
  }

  _osc(type, freq, gain) {
    const o = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    o.type = type; o.frequency.value = freq;
    g.gain.value = gain; o.connect(g); g.connect(this.master);
    o.start();
    this.live.push(o, g);
    return { o, g };
  }

  _noise(mode) {
    const src = this.ctx.createBufferSource();
    src.buffer = this._noiseBuffer(); src.loop = true;
    const g = this.ctx.createGain();
    const f = this.ctx.createBiquadFilter();
    if (mode === 'rain') {
      f.type = 'bandpass'; f.frequency.value = 1800; f.Q.value = 0.4;
      g.gain.value = 0.12;
      // 雨声起伏
      const lfo = this.ctx.createOscillator(), lg = this.ctx.createGain();
      lfo.frequency.value = 0.08; lg.gain.value = 0.04;
      lfo.connect(lg); lg.connect(g.gain); lfo.start();
      this.live.push(lfo, lg);
    } else { // crackle
      f.type = 'highpass'; f.frequency.value = 2600;
      g.gain.value = 0.018;
    }
    src.connect(f); f.connect(g); g.connect(this.master); src.start();
    this.live.push(src, f, g);
  }

  _pad(preset) {
    let ci = 0;
    const chordGains = [];
    const chord = () => preset.chords[ci % preset.chords.length];
    const build = () => {
      for (const n of chord()) {
        for (const det of [-3, 0, 3]) {
          const { o, g } = this._osc('triangle', midi(n) + det * 0.06, preset.pad_gain / 3);
          g.gain.setValueAtTime(0.0001, this.ctx.currentTime);
          g.gain.linearRampToValueAtTime(preset.pad_gain / 3, this.ctx.currentTime + 2.5);
          chordGains.push(g);
        }
      }
    };
    const sweep = () => {
      const t = this.ctx.currentTime;
      for (const g of chordGains) {
        g.gain.cancelScheduledValues(t);
        g.gain.setValueAtTime(g.gain.value, t);
        g.gain.linearRampToValueAtTime(0.0001, t + 2.2);
      }
      chordGains.length = 0;
      ci++;
      build();
    };
    build();
    const timer = setInterval(sweep, preset.chord_seconds * 1000);
    this.timers.push(timer);
  }

  _pluck(preset) {
    if (!preset.pluck) return;
    const play = () => {
      const scale = preset.pluck.scale;
      const n = scale[Math.floor(Math.random() * scale.length)];
      const { o, g } = this._osc('sine', midi(n), preset.pluck.gain);
      const t = this.ctx.currentTime;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(preset.pluck.gain, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 1.6);
      o.stop(t + 1.8);
      const [a, b] = preset.pluck.interval;
      const next = a + Math.random() * (b - a);
      this.timers.push(setTimeout(play, next * 1000));
    };
    play();
  }

  _paper() {
    // 旧书页轻响：随机短促带通噪声。
    const tick = () => {
      const dur = 0.08 + Math.random() * 0.12;
      const src = this.ctx.createBufferSource();
      src.buffer = this._noiseBuffer(0.4);
      const f = this.ctx.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = 1200 + Math.random() * 1800; f.Q.value = 1.4;
      const g = this.ctx.createGain(); const t = this.ctx.currentTime;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.06, t + 0.015);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      src.connect(f); f.connect(g); g.connect(this.master); src.start(t); src.stop(t + dur + 0.05);
      this.timers.push(setTimeout(tick, (1.6 + Math.random() * 3.4) * 1000));
    };
    tick();
  }

  async play(mood) {
    await this.ensure();
    this.stop();
    if (this.ctx.state === 'suspended') await this.ctx.resume();
    this.preset = PRESETS[mood] || PRESETS['warm-pad'];
    this.running = true;
    this._pad(this.preset);
    if (this.preset.pluck) this._pluck(this.preset);
    this._noise(this.preset.noise);
    if (mood === 'rain-paper') this._paper();
    this.master.gain.cancelScheduledValues(this.ctx.currentTime);
    this.master.gain.setValueAtTime(this.master.gain.value, this.ctx.currentTime);
    this.master.gain.linearRampToValueAtTime(0.8, this.ctx.currentTime + 1.5);
  }

  stop() {
    this.timers.forEach(t => { clearTimeout(t); clearInterval(t); });
    this.timers = [];
    for (const n of this.live) { try { n.stop?.(); n.disconnect?.(); } catch {} }
    this.live = [];
    this.running = false;
  }

  dispose() {
    this.stop();
    this.ctx?.close().catch(() => {});
    this.ctx = null;
  }
}
