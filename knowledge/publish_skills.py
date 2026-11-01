"""把已确认的技巧组织为独立专项章节，旧题 ID、答案与存档解释保持稳定。"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def publish():
    kp=ROOT/'knowledge/cet4_skills.json';skills=json.loads(kp.read_text(encoding='utf-8'))
    path=ROOT/'data/curriculum/catalog.json';catalog=json.loads(path.read_text(encoding='utf-8'))
    profiles=json.loads((ROOT/'characters/profiles.json').read_text(encoding='utf-8'))
    catalog['characters']=profiles['characters']
    catalog['points']=[p for p in catalog['points'] if not p['id'].startswith('cet4-skills-')]
    subject=next(s for s in catalog['subjects'] if s['id']=='cet4')
    subject['chapters']=[c for c in subject['chapters'] if not c['id'].startswith('cet4-skills-')]
    labels={'reading':'阅读','listening':'听力','writing':'写作'}
    hooks={
      'reading_skimming_topic':'先看整棵树，再认枝叶；标题要罩住中心，也要守住范围。',
      'reading_detail_evidence':'定位是书签，核对才是证据；谁、做什么、何时，都要对齐。',
      'reading_inference_boundary':'推断只跨有支点的一步，不把可能写成保证。',
      'reading_word_context':'陌生词先问邻居，再把释义放回句子试一遍。',
      'reading_author_attitude':'态度要认说话人，也要认程度；一句转折，两边都留下。',
      'listening_preview_options':'预读先找选项的不同，耳朵才知道该追哪条线索。',
      'listening_signal_relations':'信号词是路标，答案在它连接的意思里。',
      'listening_paraphrase':'换了词也要是同一件事，主体、方向和程度不能换。',
      'listening_number_revision':'数字带标签：原定、现在、时长，别装进同一个口袋。',
      'listening_intention_evidence':'先听建议，再听回应；答应去做，不等于已经做过。',
      'writing_three_part_structure':'先立观点，再给支撑，最后收束；先服从题目，再选结构。',
      'writing_template_function':'模板像工具，先看要做什么，再决定拿哪一件。',
      'writing_lexical_precision':'词语升级先求准确；自然的句子，可以原样留下。',
      'writing_revision_errors':'先查任务和逻辑，再查句子骨架，最后修拼写标点。',
      'writing_reason_example_link':'原因搭桥，例子落地，解释把它们接回观点。'}
    for module,items in skills['modules'].items():
        chapter_id='cet4-skills-'+module;label=labels[module]
        opening=f'今天做{label}专项。先认清任务，再看证据。你可以任选一节，完成后也可以直接换板块。'
        chapter={'id':chapter_id,'title':label+' · 技巧实战','module':label,'subtitle':'辨析思路 · 排序结构 · 匹配表达','opening':opening,'points':[],'status':'available','minutes':15}
        for index,s in enumerate(items):
            pid=f'{chapter_id}-{index+1:02d}';i=s['interaction'];hook=hooks[s['skill_id']]
            peer='castor' if index%2==0 else 'phainon'
            prompt=f'{s["skill_name"]}。'+('先别急着选词。' if module=='writing' else '别让熟悉的字面替你作判断。')+' '.join(s['action_steps'])+' '+i['task']
            if i['type']=='reasoning_clues':
                clues=[{'id':c['id'],'text':c['text'],'correct':c['id']==i['solution'],'type':'思路线索'} for c in i['clues']]
                answer=next(n for n,c in enumerate(i['clues']) if c['id']==i['solution'])
                test={'question':i['task'],'choices':[c['text'] for c in i['clues']],'answer':answer,'explanation':i['feedback_basis']}
            else:
                clues=[{'id':'structured-match','text':'结构与语义相符','correct':True,'type':i['type']},{'id':'structured-retry','text':'回看结构关系','correct':False,'type':i['type']}]
                test={'question':f'运用「{s["skill_name"]}」时，应优先检查什么？','choices':[s['action_steps'][0],s['common_traps'][0]],'answer':0,'explanation':hook}
            p={'id':pid,'subject':'cet4','chapter':chapter_id,'concept':s['skill_name'],'summary':s['action_steps'][0],
              'character':'anaxa','speaker':'anaxa','skill_id':s['skill_id'],'prompt':prompt,'interaction':i,
              'clues':clues,'feedback':{'matched':f'这次，结论有证据支撑。{i["feedback_basis"]} {hook}',
                                      'redirect':f'把这条线索放回材料，看看它越过了哪条边界。{i["feedback_basis"]} {hook}'},
              'memoryHook':hook,'example':{'en':i['material'],'zh':i['feedback_basis']},'difficulty':2,
              'assistant_speaker':'hyacine','assistant_hint':f'我们先把任务拆小。{s["action_steps"][0]} {hook}',
              'classmate':{'character':peer,'text':f'请保留条件。{hook}' if peer=='castor' else f'我记成一个能做的小动作：{hook}'},
              'test':test,'source':{'type':'original_adaptation','note':'按用户确认的技巧规格创作，不是课程逐字转写或真题。'},
              'source_refs':['bili-course-2026','original-cet4-v2'],'review_status':'approved_by_user'}
            if module=='listening':p['listen_text']=i['material'].split('Playback: ')[-1]
            catalog['points'].append(p);chapter['points'].append(pid)
            s['implementation_point_id']=pid;s['project_memory_hook']=hook
        chapter['test_points']=list(chapter['points']);chapter['knowledgeCount']=len(chapter['points']);subject['chapters'].append(chapter)
    skills.update(review_status='user_authorized_implementation',publish_enabled=True)
    skills['provenance']['course_attribution_note']='用户取消讲义/时间戳作为接入前置条件；这不把未核实讲法变成教师原话。'
    skills['integration_contract'].update(status='connected',character_source='characters/profiles.json')
    catalog['version']=max(3,catalog.get('version',3))
    path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    kp.write_text(json.dumps(skills,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Published',len(catalog['points']),'points;',len(subject['chapters']),'chapters')

if __name__=='__main__':publish()
