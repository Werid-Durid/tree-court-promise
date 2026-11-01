// 互动片只记录观看与选项，不写入课程或好感事件。
export function pendingCue(film,time,answers={}){
 return (film.interactions||[]).find(cue=>cue.at<=time+.04&&!answers[cue.id]);
}
export function normalizeFilmProgress(film,saved){
 const answers={};
 if(saved?.revision===film.revision)for(const cue of film.interactions||[]){
  if(cue.choices.some(choice=>choice.id===saved.answers?.[cue.id]))answers[cue.id]=saved.answers[cue.id];
 }
 let time=saved?.revision===film.revision&&Number.isFinite(saved.time)?Math.max(0,Math.min(film.duration_seconds,saved.time)):0;
 const cue=pendingCue(film,time,answers);if(cue)time=cue.at;
 return {revision:film.revision,time,answers};
}
export function filmLineAt(film,time){return (film.lines||[]).find(line=>line.start<=time&&time<=line.end);}
