// 与服务端同一分支规则；入口不因重置好感而锁死，心事/恋爱分支分别检查。
export const outingAllowed=(item,state,id)=>state.affection[id]>=(item.min_affection||0)&&(!item.relationship||state.relationships[id]===item.relationship);
export function applyOuting(state,p,catalog){
 const story=catalog.invitations?.stories.find(s=>s.character===p.character);if(!story)return;
 const session=state.outings[p.character]||{node:story.start,choices:[],endings:[]};
 if(p.restart===true){state.outings[p.character]={...session,node:story.start,choices:[]};return;}
 const node=story.nodes.find(n=>n.id===session.node),choice=node?.choices.find(c=>c.id===p.choice_id),target=story.nodes.find(n=>n.id===choice?.next);
 if(!choice||!target||p.node_id!==node.id||![node,choice,target].every(n=>outingAllowed(n,state,p.character)))return;
 if(p.story_revision===2){
  const moments=((state.bond_moments??={})[p.character]??=[]);
  for(const key of [node.id,...(target.ending?['ending']:[])]){
   const moment=story.bond_moments?.[key];if(moment&&!moments.includes(key)){
   const points=state.bond_points??={},before=points[p.character]||0;
   points[p.character]=Math.min(catalog.invitations.bond_cap??21,before+moment.points);moments.push(key);
   state.affection[p.character]=Math.min(100,state.affection[p.character]+points[p.character]-before);
   }
  }
 }
 const endings=[...session.endings];if(target.ending&&!endings.includes(target.id))endings.push(target.id);
 const choices=[...session.choices,choice.id],memories={...session.memories,[node.id]:session.choices,[target.id]:choices};
 state.outings[p.character]={...session,node:target.id,choices,endings,memories};
}

export function bondStage(value){return value>=85?'深深信赖':value>=60?'默契渐深':value>=30?'愿诉心事':value>=12?'渐渐熟悉':'初次相识';}
export function outingEchoes(node,choices=[]){return (node.echoes||[]).filter(e=>choices.includes(e.choice)).map(e=>e.text);}
