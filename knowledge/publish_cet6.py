"""发布用户指定六级课程的原创题型课堂，其他科目与进度数据保持不变。"""
import copy,hashlib,json,os,shutil,sys
from pathlib import Path
from cet6_rows import ROWS
ROOT=Path(__file__).resolve().parents[1]
NOTE='已核对用户提供的BV1PPbL6oE5f视频93个分P标题，上传者为四六级冲鸭。未取得字幕正文和Unit原词表；本课讲解、英语材料、例题、练习及记忆钩子均为原创补充，不冒称刘晓燕原话、原题或原词表。'
CHAPTERS={'vocabulary':'词汇与语境','listening':'听力理解','careful':'仔细阅读','matching':'长篇阅读匹配','cloze':'选词填空','writing':'写作表达','translation':'汉译英'}
LISTENING={
 'preview':"I considered taking the bus, but the last service leaves too early. I'll cycle instead.",
 'paraphrase':'The seminar has been put off until Friday.',
 'correction':'The meeting is at three. Sorry, at four.',
 'conversation':"Shall we print the forms? The online version is easier to update. Let's use that.",
 'lecture':'Students who slept longer scored higher, but the study did not establish causation.'}
ESSAY='''University students can make a meaningful contribution to their communities through regular volunteering. Although academic work requires considerable time, a small and realistic commitment can benefit both students and local residents.

One important benefit is the opportunity to develop responsibility. For example, a student who promises to help children with reading every Saturday must prepare carefully and arrive on time. Such repeated actions turn an abstract value into a practical habit. Working with people of different ages can also help students understand needs that are not always visible on campus.

However, enthusiasm alone is not enough. Before joining a project, students should ask what support is actually needed and choose a schedule they can maintain. Universities can help by providing reliable information and basic training. Starting with one manageable task is often more useful than making a large promise that cannot be kept.

In this way, volunteering becomes a sustainable part of university life. Its value lies not only in the hours recorded, but also in the care and consistency behind them.'''
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,path)
def build():
 path=ROOT/'data/curriculum/catalog.json';c=json.loads(path.read_text(encoding='utf-8'));before=copy.deepcopy(c);backup=ROOT/'knowledge/build/cet6/before/catalog.json';backup.parent.mkdir(parents=True,exist_ok=True)
 if not backup.exists():shutil.copy2(path,backup)
 view=json.loads((ROOT/'knowledge/build/cet6/BV1PPbL6oE5f-view.json').read_text(encoding='utf-8'))['data'];assert view['bvid']=='BV1PPbL6oE5f'
 videos=[dict(bvid=view['bvid'],page=p['page'],title=p['part'],url=f'https://www.bilibili.com/video/{view["bvid"]}/?p={p["page"]}',cid=p['cid'],lesson_ids=[],catalog_verified=True,transcript_verified=False) for p in view['pages']];assert len(videos)==93;mapped={str(v['page']):v for v in videos}
 subject=next(s for s in c['subjects'] if s['id']=='cet6');subject.update(status='available',description='六级七板块 · 词汇、听力、阅读、写作与翻译 · 原创材料与练习',chapters=[],modules=[],syllabus_note=NOTE)
 chapters={};points=[]
 for key,title in CHAPTERS.items():
  ch=dict(id='cet6-course-'+key,title=title,module=title,module_id=key,status='available',subtitle='直觉与定义 · 反例边界 · 板书例题 · 迁移练习',course_format='cet6_classroom',opening=f'今天练习{title}。先看题目要我们找什么，再把词和句子放回语境。每个判断都应有证据，不要只凭一个眼熟的单词下结论。',points=[],test_points=[]);chapters[key]=ch;subject['chapters'].append(ch)
 for row in ROWS.strip().splitlines():
  fields=row.split('|');assert len(fields)==14,(len(fields),fields[:4]);key,page,slug,title,lecture,boundary,board,wq,reason,wa,question,answer,trap,hook=fields;entry=mapped[page];bvid=view['bvid'];pid='cet6-'+slug;ch=chapters[key];ch['points'].append(pid);ch['test_points'].append(pid);entry['lesson_ids'].append(pid)
  clues=[dict(id='evidence',type='定义与推演线索',text=f'{hook} 核对本题得到「{answer}」。',correct=True),dict(id='boundary',type='易混猜想',text=f'如果暂不检查条件，可能猜成「{trap}」。',correct=False)]
  if int(hashlib.sha256(pid.encode()).hexdigest()[-1],16)%2:clues.reverse()
  prompt=f'{lecture} 现在把这一步交给你：{question} 请选一条能由条件支持的线索。';hint=f'先把这道题拆成一小步，好吗？{boundary} 我们可以再核对一遍。';castor=f'请留意：{boundary}';phainon=f'这让我想到一个日常办法：{hook} 不过比喻要落到式子上，咱们再验算一次。'
  stages=[dict(id='textbook',name='概念与反例',speaker='anaxa',dialogue=f'今天讨论{title}。{lecture} 别把条件丢在门外：{boundary}'),dict(id='worked',name='例题推演',speaker='anaxa',dialogue=f'看这个例子。{wq} '+reason.replace(';','。')+f' 因此，结果是{wa}。现在，指出决定结论的那一步。'),dict(id='practice',name='迁移练习',speaker='anaxa',dialogue=f'换一个条件，再检验：{question} 不要借我的结论，写下你自己的推演。')]
  test=dict(question=question,choices=[x['text'] for x in clues],answer=next(i for i,x in enumerate(clues) if x['correct']),explanation=f'{board}。由条件得{answer}。{boundary}')
  transfer=dict(id='transfer',type='short_answer',question=question,answer=answer,accepted_answers=[answer],unit='',explanation=test['explanation'],origin='original_cet6_transfer')
  if answer.lstrip('-').isdigit():transfer['answer_format']='rational'
  textbook=[dict(heading='题型、语境与方法',text=lecture),dict(heading='易错点与证据边界',text=boundary),dict(heading='原创记忆线索',text=hook+' 比喻帮助回忆，判断仍须依据定义与推演。')]
  course=dict(version=1,format='cet6_classroom',title=title,estimated_minutes=15,objectives=[f'解释{title}的含义与适用条件','用具体反例检查容易混淆的结论','独立完成一次变式计算或判断'],textbook=textbook,board=board,worked_example=dict(question=wq,answer=wa,steps=[dict(label=f'推演{i+1}',text=t) for i,t in enumerate(reason.split(';'))],origin='original_not_video_question'),exercises=[transfer,dict(id='concept-check',type='choice',**test)],stages=stages,dialogue=dict(anaxa=stages[0]['dialogue'],hyacine=hint,castor=castor,phainon=phainon),source=dict(id='cet6-bili-'+bvid+'-p'+page,kind='video_course',page=int(page),course_title=view['title'],title=entry['title'],author=view['owner']['name'],bvid=bvid,url=entry['url'],pages=[],supplement_urls=[entry['url']],catalog_verified=True,transcript_verified=False,lesson_origin='original_topic_lesson',note=NOTE),syllabus=dict(framework='用户指定六级课程公开分P主题',items=[title],selection=NOTE,official_full_text_verified=False),teaching_style=dict(sequence=['语境与任务','题型方法','证据与易错点','完整例题','同题型迁移'],evidence='依据公开主题组织原创教学，不宣称取得视频全文或复述作者独有口诀'))

  feedback={k:f'{lead}{answer}。核对：{board}。{boundary} 记忆线索：{hook}' for k,lead in [('matched','这次推演有据可查。参考结论为'),('redirect','先把猜想放回条件里检验。参考结论为')]}
  if key=='vocabulary':course['source']['lesson_origin']='original_vocabulary_strategy_supplement';course['source']['mapping_note']='只核对Unit标题，未取得该Unit原词表；本课词汇与策略为原创补充。'
  if key in ('writing','translation'):
   essay=key=='writing'
   course['writing_task']=dict(kind='essay' if essay else 'translation',prompt='原创写作练习：就大学生如何持续参与社区志愿服务提出建议。可讨论价值、现实困难和可执行的安排。' if essay else '原创翻译小段：近年来，这座城市改善了公共交通，并建成了几个新公园。由学生发起的志愿活动吸引了许多居民。为了让更多人参与，社区提供了基本培训。参与者可以根据自己的时间选择合适的任务。',min_words=150 if essay else None,max_words=200 if essay else None,reference=ESSAY if essay else 'In recent years, the city has improved public transport and built several new parks. Volunteer activities initiated by students have attracted many residents. To encourage wider participation, the community provides basic training. Participants can choose suitable tasks according to their schedules.',rubric=['是否完整回应任务并保留主要信息','是否能说明本课要点：'+title,'主谓、时态、修饰关系和搭配是否准确','例子和事实是否可靠，是否存在无根据的绝对化'],origin='original_practice_not_video_or_past_paper',grading='self_review_only')
  points.append(dict(id=pid,subject='cet6',chapter=ch['id'],module=CHAPTERS[key],module_id='cet6-'+key,concept=title,summary=lecture.split('。')[0]+'。',quick_meaning=board,character='anaxa',speaker='anaxa',prompt=prompt,clues=clues,difficulty=2,feedback=feedback,memoryHook=hook,example=dict(en=wq,zh=reason.replace(';','。')+f' 结论：{wa}。'),assistant_speaker='hyacine',assistant_hint=hint,classmate=dict(character='castor',text=castor),dialogue=dict(anaxa=prompt,hyacine=hint,castor=castor,phainon=phainon),test=test,course=course,source_refs=['cet6-bili-'+bvid+'-p'+page],source=dict(type='original_cet6_course',note=NOTE,course_url=entry['url']),review_status='original_english_examples_reviewed'))
  if key=='listening':points[-1]['listen_text']=LISTENING[slug];course['listening_origin']='原创角色朗读材料，非原课录音或真题听力音轨'
 for key,ch in chapters.items():ch.update(minutes=15*len(ch['points']),knowledgeCount=len(ch['points']));subject['modules'].append(dict(id=key,name=CHAPTERS[key],chapters=[ch['id']],point_count=len(ch['points'])))
 for v in videos:
  title=v['title']
  if '导学' in title or '前言' in title:keys=['vocabulary'];v['coverage']='orientation_reference'
  elif 'Unit' in title:keys=['vocabulary'];v['coverage']='unit_title_only_wordlist_unavailable'
  elif '写作' in title and '翻译' in title:keys=['writing','translation'];v['coverage']='topic_reference'
  elif '写作' in title:keys=['writing'];v['coverage']='topic_reference'
  elif '翻译' in title:keys=['translation'];v['coverage']='topic_reference'
  elif '听力' in title or '长对话' in title or '讲话' in title:keys=['listening'];v['coverage']='topic_reference'
  elif '仔细阅读' in title:keys=['careful'];v['coverage']='topic_reference'
  elif '长篇阅读' in title:keys=['matching'];v['coverage']='topic_reference'
  elif '词汇理解' in title:keys=['cloze'];v['coverage']='topic_reference'
  elif '阅读' in title:keys=['careful','matching','cloze'];v['coverage']='topic_reference'
  else:raise ValueError('未分类分P：'+title)
  v['topic_modules']=keys;v['lesson_ids']=sorted(set(v['lesson_ids']+[pid for k in keys for pid in chapters[k]['points']]))
 subject['knowledgeCount']=len(points);c['points']=[p for p in c['points'] if p['subject']!='cet6']+points;c['version']=max(c.get('version',1),10)
 assert [p for p in c['points'] if p['subject']!='cet6']==[p for p in before['points'] if p['subject']!='cet6'];assert [s for s in c['subjects'] if s['id']!='cet6']==[s for s in before['subjects'] if s['id']!='cet6']
 write(path,c);write(ROOT/'knowledge/cet6_lessons.json',dict(note=NOTE,chapters=subject['chapters'],points=points));write(ROOT/'knowledge/cet6_series_mapping.json',dict(anchor=view['bvid'],title=view['title'],uploader=view['owner']['name'],uploader_mid=view['owner']['mid'],reported_count=len(view['pages']),returned_count=len(videos),pages=videos,unclassified_pages=[],note=NOTE))
 p=ROOT/'data/references/sources.json';refs=json.loads(p.read_text(encoding='utf-8'));refs['sources']=[s for s in refs['sources'] if not s['id'].startswith('cet6-bili-')]+[dict(id='cet6-bili-'+v['bvid']+'-p'+str(v['page']),title=view['owner']['name']+' · '+v['title'],url=v['url'],status='public_catalog_verified_transcript_unavailable',note=NOTE) for v in videos];write(p,refs)
 print(json.dumps({'chapters':len(chapters),'lessons':len(points),'videos':len(videos),'unmapped':[]},ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');build()
