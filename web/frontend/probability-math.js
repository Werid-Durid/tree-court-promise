// 演示只做概率计算，不产生作答、完成或好感事件。
export function alarmPosterior(prior,sensitivity,falsePositive){
 if([prior,sensitivity,falsePositive].some(p=>!Number.isFinite(p)||p<0||p>1))throw Error('概率必须在0与1之间');
 const trueAlarm=prior*sensitivity,falseAlarm=(1-prior)*falsePositive,total=trueAlarm+falseAlarm;
 return {trueAlarm,falseAlarm,total,posterior:total===0?null:trueAlarm/total};
}
