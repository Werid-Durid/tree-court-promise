export const normalizeAnswer=value=>String(value).normalize('NFKC').toLowerCase().replace(/\s/g,'').replace(/[。.!！]+$/,'');
// 仅解析数值字面量，用整数交叉相乘比较，不执行用户输入的表达式。
function rational(value){
 const fraction=/^([+-]?\d{1,12})\/(\d{1,12})$/.exec(value);
 if(fraction){const d=BigInt(fraction[2]);return d===0n?null:[BigInt(fraction[1]),d];}
 const decimal=/^([+-]?\d{1,12})(?:\.(\d{1,12}))?$/.exec(value);
 return decimal?[BigInt(decimal[1]+(decimal[2]||'')),10n**BigInt((decimal[2]||'').length)]:null;
}
export function evaluateCourseExercise(exercise,response){
 if(exercise.type==='choice'){if(!Number.isInteger(response)||response<0||response>=exercise.choices.length)throw Error('请选择有效选项');return response===exercise.answer;}
 if(typeof response!=='string'||!response.trim()||response.length>250)throw Error('请填写不超过250字的答案');
 const value=normalizeAnswer(response);if((exercise.accepted_answers||[exercise.answer]).some(a=>normalizeAnswer(a)===value))return true;
 if(exercise.answer_format==='rational'){const a=rational(value),b=rational(String(exercise.answer));if(a&&b)return a[0]*b[1]===b[0]*a[1];}
 const numeric=/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/;
 return numeric.test(value)&&numeric.test(String(exercise.answer))&&Number(value)===Number(exercise.answer);
}
