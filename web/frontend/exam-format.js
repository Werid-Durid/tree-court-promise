// 试卷制式与默认时长独立维护，避免 408 沿用英语作文/翻译答题卡。
export function examFormat(level,year=2026){
 if(level==='math1')return {label:'考研数学一',minutes:180,choiceFirst:1,choiceLast:year>=2021?10:8,fillFirst:year>=2021?11:9,fillLast:year>=2021?16:14,writtenFirst:year>=2021?17:15,writtenLast:year>=2021?22:23,totalScore:150};
 if(level==='english1')return {label:'考研英语一',minutes:180,choiceFirst:1,choiceLast:40,matchingFirst:41,matchingLast:45,translationFirst:46,translationLast:50,writingFirst:51,writingLast:52,totalScore:100};
 if(level==='cs408')return {label:'408计算机综合',minutes:180,choiceFirst:1,choiceLast:40,writtenFirst:41,writtenLast:47,totalScore:150};
 return {label:level==='cet4'?'英语四级':level==='cet6'?'英语六级':'全部真题',minutes:level==='cet6'?130:125};
}
