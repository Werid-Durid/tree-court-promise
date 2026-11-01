import {alarmPosterior} from './probability-math.js';
// 课堂演示只改变图示参数，不生成作答、好感或完成记录。
export function mountCalculusVisual(point,host){
 const type=point.course?.visualization?.type;if(!type)return;
 const panel=document.createElement('section');panel.className='calculus-visual';host.querySelector('.network-board').after(panel);
 if(type==='probability-bayes'){
  panel.innerHTML='<h3>报警之后，为什么还要看故障原本多常见？</h3>'+[['prior','故障率',1],['sensitivity','故障时报警率',90],['false','正常时误报率',5]].map(([id,title,value])=>`<label>${title}<input data-probability="${id}" type="range" min="0" max="100" step="1" value="${value}"><output data-probability-value="${id}"></output></label>`).join('')+'<div id="probability-bayes-bars"></div><p id="probability-bayes-result" role="status"></p><p class="muted small">原创机器报警模型。绿色为故障且报警，棕色为正常却报警；没有报警时，给定报警的后验无定义。改变滑块不计作答。</p>';
  const percent=x=>(100*x).toFixed(2)+'%';const draw=()=>{const values=['prior','sensitivity','false'].map(id=>{const x=Number(panel.querySelector(`[data-probability="${id}"]`).value)/100;panel.querySelector(`[data-probability-value="${id}"]`).textContent=percent(x);return x;}),r=alarmPosterior(...values);
   panel.querySelector('#probability-bayes-bars').innerHTML=r.posterior===null?'':`<svg viewBox="0 0 500 85" role="img" aria-label="所有报警中的真实故障与误报占比"><rect x="0" y="10" width="${500*r.posterior}" height="30" fill="#39745c"/><rect x="${500*r.posterior}" y="10" width="${500*(1-r.posterior)}" height="30" fill="#b38a62"/><text x="0" y="70" fill="#294739">报警中真故障 ${percent(r.posterior)}；误报 ${percent(1-r.posterior)}</text></svg>`;
   panel.querySelector('#probability-bayes-result').textContent=r.posterior===null?'报警概率为0：条件事件没有正概率，不能计算该后验。':`故障且报警 ${percent(r.trueAlarm)}；正常且报警 ${percent(r.falseAlarm)}；总报警 ${percent(r.total)}。报警后故障概率 = ${percent(r.posterior)}。`;};panel.querySelectorAll('input').forEach(input=>input.oninput=draw);draw();return;
 }
 if(type==='linear-determinant'){
  panel.innerHTML='<h3>两根向量围出的有向面积</h3><div class="linear-matrix-inputs">'+['a','b','c','d'].map((name,i)=>`<label>${name}<input data-linear-entry="${name}" type="number" min="-3" max="3" step="1" value="${[2,1,1,2][i]}"></label>`).join('')+'</div><div id="linear-area-diagram"></div><p id="linear-area-result" role="status"></p><p class="muted small">列向量为 (a,c) 与 (b,d)。正负表示方向，几何面积取绝对值；修改图示不计作答或学习完成。</p>';
  const draw=()=>{const values=[...panel.querySelectorAll('[data-linear-entry]')].map(input=>Math.max(-3,Math.min(3,Number(input.value)||0))),[a,b,c,d]=values,det=a*d-b*c;const point=(x,y)=>`${180+x*22},${180-y*22}`;
   panel.querySelector('#linear-area-diagram').innerHTML=`<svg viewBox="0 0 360 360" role="img" aria-label="列向量形成的平行四边形"><path d="M15 180H345M180 15V345" stroke="#a8ad9a" fill="none"/><polygon points="${point(0,0)} ${point(a,c)} ${point(a+b,c+d)} ${point(b,d)}" fill="${det>=0?'#61987c':'#c18d64'}" fill-opacity=".28" stroke="#59715d"/><path d="M${point(0,0)}L${point(a,c)} M${point(0,0)}L${point(b,d)}" stroke="#244e3d" stroke-width="3"/><text x="15" y="24" fill="#244e3d">det = ${det}</text></svg>`;
   panel.querySelector('#linear-area-result').textContent=`ad − bc = ${a}×${d} − ${b}×${c} = ${det}；面积 = ${Math.abs(det)}。${det===0?'两列相关，面积塌缩为零。':det>0?'方向保持为正。':'方向翻转为负。'}`;
  };panel.querySelectorAll('input').forEach(input=>input.oninput=draw);draw();return;
 }
 if(type==='sequence-threshold'){
  panel.innerHTML='<h3>把定义画出来 · 数列与阈值</h3><label>观察对象<select id="calc-sequence-mode"><option value="unbounded">奇数项为 n，偶数项为 0</option><option value="infinite">aₙ=n</option><option value="absolute">aₙ=(-1)ⁿ n</option><option value="small">aₙ=1/n</option></select></label><label>显示前 N 项<input id="calc-sequence-n" type="range" min="4" max="40" value="20"></label><label><span id="calc-threshold-label">阈值 M</span><input id="calc-sequence-m" type="range" min="1" max="20" value="8"></label><div class="calculus-diagram" id="calc-sequence-plot"></div><p id="calc-sequence-note" role="status"></p><p class="muted small">图示只有有限项，不能靠有限采样证明极限；下面的判断依据是给定公式。切换图示不计为作答。</p>';
  const mode=panel.querySelector('#calc-sequence-mode'),nInput=panel.querySelector('#calc-sequence-n'),mInput=panel.querySelector('#calc-sequence-m');
  const draw=()=>{
   const count=Math.max(4,Math.min(40,Number(nInput.value))),m=Math.max(1,Math.min(20,Number(mInput.value))),small=mode.value==='small',infinite=mode.value==='infinite',absolute=mode.value==='absolute';
   const scale=small?190:2.8,baseline=small?250:150,threshold=small?1/m:m;
   const points=Array.from({length:count},(_,i)=>{const n=i+1,v=small?1/n:infinite?n:absolute?(n%2?-n:n):n%2?n:0;return `<circle cx="${36+7*n}" cy="${baseline-scale*v}" r="3" fill="${(small?v<threshold:Math.abs(v)>threshold)?'#315c49':'#a5753d'}"><title>n=${n}，aₙ=${Number(v.toFixed(4))}</title></circle>`;}).join('');
   panel.querySelector('#calc-threshold-label').textContent=small?'精度分母 M（ε=1/M）':'阈值 M';
   panel.querySelector('#calc-sequence-plot').innerHTML=`<svg viewBox="0 0 360 285" role="img" aria-label="数列前${count}项示意图"><path d="M36 20V265M36 ${baseline}H340" fill="none" stroke="#7c887a"/><path d="M36 ${baseline-scale*threshold}H340" stroke="#b7763b" stroke-dasharray="5 4"/><text x="42" y="18">${small?'纵轴 0～1.2':'纵轴 -40～40'}</text><text x="270" y="275">n（0～40）</text>${absolute?`<path d="M36 ${baseline+scale*threshold}H340" stroke="#b7763b" stroke-dasharray="5 4"/>`:''}${points}</svg>`;
   panel.querySelector('#calc-sequence-note').textContent=`当前 N=${count}，${small?'ε='+Number(threshold.toFixed(4)): 'M='+m}。`+(small?'当 n>M 时 1/n<1/M，所以 1/n→0。':infinite?'当 n>M 后全部项超过 M，这是最终全部超过。':absolute?'绝对值等于 n，最终全部超过 M；但奇数项为负、偶数项为正，因此既不趋 +∞ 也不趋 -∞。':'总能选奇数 n>M 使取值超过 M，但任意远处仍有值为 0 的偶数项，所以无界而非无穷大。');
  };
  for(const input of [mode,nInput,mInput])input.addEventListener('input',draw);draw();
 }else if(type==='vector-components'){
  panel.innerHTML='<h3>把位移拆成三个分量</h3><div class="calculus-vector-inputs">'+['x','y','z'].map((a,i)=>`<label>${a} 分量<input id="calc-vector-${a}" type="range" min="-5" max="5" step="1" value="${[0,3,4][i]}"></label>`).join('')+'</div><div class="calculus-diagram" id="calc-vector-plot"></div><p id="calc-vector-note" role="status"></p><p class="muted small">这是三维向量的二维投影示意，屏幕线长不代表真实模长；模长按三个分量计算。零向量不作单位化。</p>';
  const inputs=['x','y','z'].map(a=>panel.querySelector('#calc-vector-'+a));
  const draw=()=>{const [x,y,z]=inputs.map(i=>Math.max(-5,Math.min(5,Number(i.value)))),len=Math.hypot(x,y,z),sx=180+11*x-11*y,sy=180+6*x+6*y-13*z;
   panel.querySelector('#calc-vector-plot').innerHTML=`<svg viewBox="0 0 360 330" role="img" aria-label="向量(${x},${y},${z})分量示意"><defs><marker id="calc-vector-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0L7 3.5L0 7Z" fill="#315c49"/></marker></defs><path d="M180 180L246 216M180 180L114 216M180 180V102" fill="none" stroke="#9b9f8e"/><text x="250" y="220">x</text><text x="100" y="220">y</text><text x="180" y="95">z</text><text x="164" y="196">O</text><path d="M180 180L${sx} ${sy}" stroke="#315c49" stroke-width="3" marker-end="url(#calc-vector-arrow)"/><circle cx="${sx}" cy="${sy}" r="4" fill="#b7763b"/></svg>`;
   panel.querySelector('#calc-vector-note').textContent=`v=(${x},${y},${z})，模长=√(${x*x+y*y+z*z})≈${len.toFixed(4)}。`+(len===0?'零向量没有唯一的同向单位向量。':`同向单位向量≈(${[x,y,z].map(v=>(v/len).toFixed(4)).join(',')})。`);
  };inputs.forEach(i=>i.addEventListener('input',draw));draw();
 }
}
