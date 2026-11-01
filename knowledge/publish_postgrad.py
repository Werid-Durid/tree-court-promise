"""发布考研英语基础课，原课程、人物与进度数据不变。"""
import copy,hashlib,json,os,shutil,sys
from pathlib import Path
from postgrad_rows import ROWS
ROOT=Path(__file__).resolve().parents[1]
NOTE='已核对BV1f1nW6HEyA的41个分P标题；多数仅有lesson编号，未取得字幕、讲义和完整词表。11个词汇标题可确认主题，相关讲解仍为项目原创；语法、长难句是依据课程标题增加的原创衔接课，不冒称已确认某分P正文。'
CHAPTERS={'vocabulary':'词汇与语境','skeleton':'句子骨架与结构','clauses':'从句分层','nonfinite':'非谓语与逻辑主语','tense':'时态、情态与虚拟','long':'长难句理解与翻译'}
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,path)
def build():
 path=ROOT/'data/curriculum/catalog.json';c=json.loads(path.read_text(encoding='utf-8'));before=copy.deepcopy(c);backup=ROOT/'knowledge/build/postgrad/before/catalog.json';backup.parent.mkdir(parents=True,exist_ok=True)
 if not backup.exists():shutil.copy2(path,backup)
 d=json.loads((ROOT/'knowledge/build/postgrad/BV1f1nW6HEyA-view.json').read_text(encoding='utf-8'))['data'];assert d['bvid']=='BV1f1nW6HEyA' and len(d['pages'])==41
 videos=[dict(page=p['page'],title=p['part'],cid=p['cid'],url=f'https://www.bilibili.com/video/{d["bvid"]}/?p={p["page"]}',lesson_ids=[],catalog_verified=True,transcript_verified=False,coverage='lesson_content_unconfirmed') for p in d['pages']];mapped={v['page']:v for v in videos};mapped[1]['coverage']='orientation_reference'
 subject=next(s for s in c['subjects'] if s['id']=='postgrad');subject.update(status='available',description='考研英语基础 · 词汇、语法与长难句 · 六板块自由选学',chapters=[],modules=[],syllabus_note=NOTE)
 chapters={};points=[]
 for key,title in CHAPTERS.items():
  ch=dict(id='postgrad-'+key,title=title,module=title,module_id='postgrad-'+key,status='available',subtitle='语境讲解 · 结构拆解 · 迁移练习',course_format='postgrad_classroom',opening=f'今天讨论{title}。第一，别用眼熟代替理解。找出句子的证据，再告诉我你的判断从何而来。',points=[],test_points=[]);chapters[key]=ch;subject['chapters'].append(ch)
 for row in ROWS.strip().splitlines():
  fields=row.split('|');assert len(fields)==14,fields[:3]
  key,page,slug,title,lecture,boundary,board,wq,reason,wa,question,answer,trap,hook=fields;page=int(page);pid='postgrad-'+slug;ch=chapters[key];ch['points'].append(pid);ch['test_points'].append(pid)
  if page:mapped[page]['lesson_ids'].append(pid);mapped[page]['coverage']='keyword_title_verified_original_lesson'
  url=mapped[page]['url'] if page else f'https://www.bilibili.com/video/{d["bvid"]}/';origin='original_topic_lesson' if page else 'original_prerequisite_supplement'
  anaxa=f'今天讨论{title}。{lecture} 条件不能省略：{boundary}'
  hint=f'我们先放慢一点。{hook} 再检查一句：{boundary}'
  castor=f'请留意：{boundary}'
  phainon=f'我会用这个办法记：{hook} 记住之后，咱们拿原句再试一次。'
  clues=[dict(id='evidence',type='语境与结构线索',text=f'{hook} 按证据应为「{answer}」。',correct=True),dict(id='trap',type='易混联想',text=f'只凭眼熟，可能先猜「{trap}」。',correct=False)]
  if int(hashlib.sha256(pid.encode()).hexdigest()[-1],16)%2:clues.reverse()
  stages=[dict(id='textbook',name='语境与结构',speaker='anaxa',dialogue=anaxa),dict(id='worked',name='例句拆解',speaker='anaxa',dialogue=f'看这个例子：{wq} '+reason.replace(';','。')+f' 结论是{wa}。依据在句子里，而不在猜测里。'),dict(id='practice',name='独立迁移',speaker='anaxa',dialogue=f'换一句，再检验：{question} 给出能由结构与语境支持的答案。')]
  test=dict(question=question,choices=[x['text'] for x in clues],answer=next(i for i,x in enumerate(clues) if x['correct']),explanation=f'{board}。本题为{answer}。{boundary}')
  transfer=dict(id='transfer',type='short_answer',question=question,answer=answer,accepted_answers=[answer],explanation=test['explanation'],origin='original_postgrad_transfer')
  course=dict(version=1,format='postgrad_classroom',title=title,estimated_minutes=15,objectives=[f'理解{title}在语境中的作用','找出结构和适用边界','独立完成新例句的分析'],textbook=[dict(heading='语境、定义与拆解方法',text=lecture),dict(heading='易错点与适用边界',text=boundary),dict(heading='原创记忆线索',text=hook+' 联想不是词源证明，判断仍回到原句。')],board=board,worked_example=dict(question=wq,answer=wa,steps=[dict(label=f'分析{i+1}',text=t) for i,t in enumerate(reason.split(';'))],origin='original_not_video_question'),exercises=[transfer,dict(id='concept-check',type='choice',**test)],stages=stages,dialogue=dict(anaxa=anaxa,hyacine=hint,castor=castor,phainon=phainon),source=dict(id='postgrad-bili-'+d['bvid']+(f'-p{page}' if page else ''),kind='video_course',title=mapped[page]['title'] if page else d['title']+' · 原创主题衔接',author=d['owner']['name'],bvid=d['bvid'],url=url,pages=[],video_pages=[page] if page else [],catalog_verified=True,transcript_verified=False,lesson_origin=origin,note=NOTE),syllabus=dict(framework='用户指定考研英语词汇、语法与长难句课程主题',items=[title],selection=NOTE,official_full_text_verified=False))
  feedback={kind:f'{lead}参考为{answer}。{board}。{boundary} 记忆线索：{hook}' for kind,lead in [('matched','这次判断有证据。'),('redirect','回到原句，再看一遍。')]}
  points.append(dict(id=pid,subject='postgrad',chapter=ch['id'],module=CHAPTERS[key],module_id=ch['module_id'],concept=title,summary=lecture.split('。')[0]+'。',quick_meaning=board,character='anaxa',speaker='anaxa',prompt=f'{lecture} 现在试一句：{question}',clues=clues,difficulty=2,feedback=feedback,memoryHook=hook,example=dict(en=wq,zh=reason.replace(';','。')+f' 结论：{wa}。'),assistant_speaker='hyacine',assistant_hint=hint,classmate=dict(character='castor',text=castor),dialogue=dict(anaxa=anaxa,hyacine=hint,castor=castor,phainon=phainon),test=test,course=course,source_refs=[course['source']['id']],source=dict(type='original_postgrad_course',note=NOTE,course_url=url),review_status='original_english_examples_reviewed'))
 for key,ch in chapters.items():ch.update(minutes=15*len(ch['points']),knowledgeCount=len(ch['points']));subject['modules'].append(dict(id=ch['module_id'],name=CHAPTERS[key],chapters=[ch['id']],point_count=len(ch['points'])))
 subject['knowledgeCount']=len(points);c['points']=[p for p in c['points'] if p['subject']!='postgrad']+points;c['version']=max(c.get('version',1),12)
 assert [p for p in c['points'] if p['subject']!='postgrad']==[p for p in before['points'] if p['subject']!='postgrad'];assert [s for s in c['subjects'] if s['id']!='postgrad']==[s for s in before['subjects'] if s['id']!='postgrad'];assert c['characters']==before['characters']
 write(path,c);write(ROOT/'knowledge/postgrad_lessons.json',dict(note=NOTE,chapters=subject['chapters'],points=points));write(ROOT/'knowledge/postgrad_series_mapping.json',dict(anchor=d['bvid'],title=d['title'],uploader=d['owner']['name'],uploader_mid=d['owner']['mid'],returned_count=len(videos),pages=videos,unconfirmed_content_pages=[v['page'] for v in videos if v['coverage']=='lesson_content_unconfirmed'],note=NOTE))
 p=ROOT/'data/references/sources.json';refs=json.loads(p.read_text(encoding='utf-8'));refs['sources']=[s for s in refs['sources'] if not s['id'].startswith('postgrad-bili-')]+[dict(id='postgrad-bili-'+d['bvid']+(f'-p{v["page"]}' if v else ''),title=v['title'] if v else d['title'],url=v['url'] if v else f'https://www.bilibili.com/video/{d["bvid"]}/',status='public_catalog_verified_transcript_unavailable',note=NOTE) for v in [None,*videos]];write(p,refs)
 print(json.dumps(dict(chapters=len(chapters),lessons=len(points),public_pages=len(videos),confirmed_keyword_pages=sum(v['coverage']=='keyword_title_verified_original_lesson' for v in videos)),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');build()
