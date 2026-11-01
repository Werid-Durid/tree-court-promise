import {evaluateInteraction} from './story-engine.js';
import {evaluateCourseExercise} from './course-exercises.js';
import {gradeVocabulary} from './vocabulary-grade.js';
import {applyOuting} from './invitation-state.js';
// 与 domain.py 同源规则：保存原始作答，按测试、练习和时长重建好感。
export function initialState(catalog) {
 return {affection:Object.fromEntries(catalog.characters.map(c=>[c.id,0])),relationships:Object.fromEntries(catalog.characters.map(c=>[c.id,'partner'])),attempts:{},completed:[],academic_seen:[],study_ms:0,focus_sessions:[],assessments:{},practice_days:{},practice_count:0,time_days:{},course_attempts:{},vocabulary_attempts:{},affection_breakdown:{tests:0,practice:0,time:0},outings:{},bond_points:{},bond_moments:{}};
}
const day=at=>new Date(new Date(at).getTime()+8*3600000).toISOString().slice(0,10);
function addTime(s,e,ms){s.study_ms+=ms;const d=day(e.at);s.time_days[d]=(s.time_days[d]||0)+ms/1000;}
export function updateAffection(s,policy){
 const r=policy.affection;
 s.affection_breakdown={
  tests:Math.min(r.test_cap,Math.floor(Object.values(s.assessments).reduce((n,items)=>n+Math.max(...items.map(t=>t.score)),0)*r.test_points_per_chapter/100)),
  practice:Math.min(r.practice_cap,Math.floor(s.practice_count/r.attempts_per_point)),
  time:Math.min(r.time_cap,Math.floor(Object.values(s.time_days).reduce((n,v)=>n+Math.min(v,r.daily_credited_seconds),0)/(r.minutes_per_point*60)))
 };
 for(const id of Object.keys(s.affection))s.affection[id]=Math.min(policy.affection_max,Object.values(s.affection_breakdown).reduce((a,b)=>a+b,0)+(s.bond_points?.[id]||0));
}
export function reduceEvents(events,catalog,policy) {
 const s=initialState(catalog),points=new Map(catalog.points.map(p=>[p.id,p])),seen=new Set();
 for(const e of events){
  if(e.event_id&&seen.has(e.event_id))continue;if(e.event_id)seen.add(e.event_id);
  const p=e.payload;
  if(e.type==='attempt'){
   const point=points.get(p.point_id),clue=point?.clues.find(c=>c.id===p.clue_id);if(!clue)continue;
   if(['structure_order','template_match','revision_match'].includes(point.interaction?.type)){try{if(evaluateInteraction(point.interaction,p.interaction_response)!==clue.correct)continue;}catch{continue;}}
   const h=s.attempts[point.id]||=[];h.push({correct:clue.correct,clue_id:clue.id,response_ms:p.response_ms,at:e.at});
   const key=`${day(e.at)}:${point.vocabulary_lesson?.word_id||point.id}`,count=s.practice_days[key]||0;
   if(p.response_ms>=policy.affection.practice_min_response_ms&&count<policy.affection.practice_per_point_per_day){s.practice_days[key]=count+1;s.practice_count++;}
   addTime(s,e,p.study_ms??p.response_ms);updateAffection(s,policy);
  }else if(e.type==='vocabulary_attempt'){
   const entry=catalog.vocabulary_banks?.cet4?.entries.find(x=>x.id===p.word_id);if(!entry||!Number.isInteger(p.response_ms)||p.response_ms<0||p.response_ms>900000)continue;
   let correct;try{correct=gradeVocabulary(entry,p.mode,p.response);}catch{continue;}
   (s.vocabulary_attempts[p.word_id]||=[]).push({mode:p.mode,response:p.response,correct,at:e.at,response_ms:p.response_ms});
   const key=`${day(e.at)}:${entry.id}`,count=s.practice_days[key]||0;if(p.response_ms>=policy.affection.practice_min_response_ms&&count<policy.affection.practice_per_point_per_day){s.practice_days[key]=count+1;s.practice_count++;}updateAffection(s,policy);
  }else if(e.type==='course_attempt'){
   const point=points.get(p.point_id),exercise=point?.course?.exercises.find(x=>x.id===p.exercise_id);if(!exercise)continue;
   if(!Number.isInteger(p.response_ms)||p.response_ms<0||p.response_ms>900000)continue;
   let correct;try{correct=evaluateCourseExercise(exercise,p.response);}catch{continue;}
   (s.course_attempts[`${point.id}:${exercise.id}`]||=[]).push({response:p.response,correct,response_ms:p.response_ms,at:e.at});
   const key=`${day(e.at)}:${point.vocabulary_lesson?.word_id||point.id}`,count=s.practice_days[key]||0;
   if(p.response_ms>=policy.affection.practice_min_response_ms&&count<policy.affection.practice_per_point_per_day){s.practice_days[key]=count+1;s.practice_count++;}updateAffection(s,policy);
  }else if(e.type==='chapter_test'){
   const ch=catalog.subjects.flatMap(s=>s.chapters).find(c=>c.id===p.chapter_id),ids=ch?.test_points;
   if(!ids||!p.answers||Object.keys(p.answers).length!==ids.length||!ids.every(id=>Number.isInteger(p.answers[id])&&p.answers[id]>=0&&p.answers[id]<points.get(id).test.choices.length))continue;
   const correct=ids.filter(id=>p.answers[id]===points.get(id).test.answer).length,score=Math.round(correct*100/ids.length);
   (s.assessments[ch.id]||=[]).push({score,correct,total:ids.length,at:e.at});
   if(!s.completed.includes(ch.id))s.completed.push(ch.id);updateAffection(s,policy);
  }else if(e.type==='study_tick'){
   if(!Number.isInteger(p.seconds)||p.seconds<1||p.seconds>60)continue;addTime(s,e,p.seconds*1000);updateAffection(s,policy);
  }else if(e.type==='chapter_complete'){
   const ch=catalog.subjects.flatMap(s=>s.chapters).find(c=>c.id===p.chapter_id);
   if(ch?.points.every(id=>s.attempts[id]?.length)&&!s.completed.includes(ch.id))s.completed.push(ch.id);
  }else if(e.type==='relationship'){
   if(s.relationships[p.character]==='partner'&&['friend','romance'].includes(p.choice)&&((p.policy_version??1)<2||eligibleForRomance(s,p.character,policy)))s.relationships[p.character]=p.choice;
  }else if(e.type==='academic_seen'){
   const key=`${p.character}:${p.threshold}`;
   if(policy.academic_thresholds.includes(p.threshold)&&((p.policy_version??1)<2||s.affection[p.character]>=p.threshold)&&!s.academic_seen.includes(key))s.academic_seen.push(key);
  }else if(e.type==='outing_choice'){
   applyOuting(s,p,catalog);
  }else if(e.type==='focus_session'){
   s.focus_sessions.push({seconds:p.seconds,interruptions:p.interruptions,at:e.at});addTime(s,e,p.seconds*1000);updateAffection(s,policy);
  }
 }
 return s;
}
export function eligibleForRomance(s,id,policy){return s.affection[id]>=policy.romance_threshold&&s.completed.length>0&&s.relationships[id]==='partner';}
