export const STUDY_KEY='treecourt.study.companion';
export const STUDY_PEOPLE={
 anaxa:{name:'那刻夏',line:'把这一段时间，交给眼前这件事。',pause:'先把思路停在这里。休息好了，再继续。'},
 hyacine:{name:'风堇',line:'我也带了手札。我们一人写一页，慢慢来。',pause:'先松松肩膀吧。我会在这里等你。'},
 castor:{name:'遐蝶',line:'我会把书翻得轻一些。你按自己的节奏就好。',pause:'书签替我们记着。歇一会儿也没有关系。'},
 phainon:{name:'白厄',line:'今天这一段路，我们一起走。我先从这道题开始。',pause:'累了吗？先喝点水，我替你看着这一页。'}
};
export function studyChoice(){try{const id=localStorage.getItem(STUDY_KEY);return Object.hasOwn(STUDY_PEOPLE,id)?id:'anaxa';}catch{return 'anaxa';}}
export function saveStudyChoice(id){if(!Object.hasOwn(STUDY_PEOPLE,id))return;try{localStorage.setItem(STUDY_KEY,id);}catch{}}
export function companionPicker(selected){return `<div class="study-picker" role="group" aria-label="选择一位陪学搭档">${Object.entries(STUDY_PEOPLE).map(([id,p])=>`<button type="button" data-study-companion="${id}" aria-pressed="${id===selected}"><img src="/art/portraits/${id}_head.png" alt=""><span>${p.name}</span></button>`).join('')}</div>`;}
