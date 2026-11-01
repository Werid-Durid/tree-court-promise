export const normalizedSpelling=text=>String(text).normalize('NFKC').replace(/\s/g,'').toLowerCase().replace(/’/g,"'");
export function gradeVocabulary(entry,mode,response){
 if(mode==='self_review'){if(!['remembered','again'].includes(response))throw Error('未知自评选项');return null;}
 if(mode!=='spelling'||typeof response!=='string'||!response.trim()||response.length>120)throw Error('请填写有效的单词拼写');
 return (entry.accepted_spellings||[entry.word]).some(s=>normalizedSpelling(s)===normalizedSpelling(response));
}
