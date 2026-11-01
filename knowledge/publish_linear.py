"""发布用户指定线代系列的原创课堂，其他科目与进度数据保持不变。"""
import copy,hashlib,json,os,shutil,sys
from pathlib import Path
from linear_rows import ROWS
ROOT=Path(__file__).resolve().parents[1]
NOTE='已核对一高数「线性代数｜同济7版」公开合集13个视频的标题和所属关系。未取得视频字幕正文；本课讲解、例题、练习与记忆钩子均为项目原创，不冒称视频逐字复现或作者原题。'
CHAPTERS={'det':'行列式','matrix':'矩阵与初等变换','systems':'线性方程组','vectors':'向量组与线性空间','eigen':'特征值与相似对角化','quadratic':'二次型'}
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,path)
def build():
 path=ROOT/'data/curriculum/catalog.json';c=json.loads(path.read_text(encoding='utf-8'));before=copy.deepcopy(c);backup=ROOT/'knowledge/build/linear/before/catalog.json';backup.parent.mkdir(parents=True,exist_ok=True)
 if not backup.exists():shutil.copy2(path,backup)
 view=json.loads((ROOT/'knowledge/build/linear/BV1LK421b7xs-view.json').read_text(encoding='utf-8'))['data'];season=view['ugc_season'];assert view['owner']['mid']==1035929235
 videos=[dict(bvid=e['bvid'],title=e['title'],url=f'https://www.bilibili.com/video/{e["bvid"]}/',cid=e['cid'],lesson_ids=[],catalog_verified=True,transcript_verified=False) for section in season['sections'] for e in section['episodes']];assert len(videos)==season['ep_count'];mapped={v['bvid']:v for v in videos}
 subject=next(s for s in c['subjects'] if s['id']=='linear');subject.update(status='available',description='六章线代课堂 · 几何直觉、定义与反例、例题推演、独立练习',chapters=[],modules=[],syllabus_note=NOTE)
 chapters={};points=[]
 for key,title in CHAPTERS.items():
  ch=dict(id='linear-'+key,title=title,module=title,module_id=key,status='available',subtitle='直觉与定义 · 反例边界 · 板书例题 · 迁移练习',course_format='linear_classroom',opening=f'今天讨论{title}。别急着背一串符号。先说清我们研究的对象，再用一个能算到底的例子检验你的判断。',points=[],test_points=[]);chapters[key]=ch;subject['chapters'].append(ch)
 for row in ROWS.strip().splitlines():
  fields=row.split('|');assert len(fields)==14,(len(fields),fields[:4]);key,bvid,slug,title,lecture,boundary,board,wq,reason,wa,question,answer,trap,hook=fields;entry=mapped[bvid];pid='linear-'+slug;ch=chapters[key];ch['points'].append(pid);ch['test_points'].append(pid);entry['lesson_ids'].append(pid)
  clues=[dict(id='evidence',type='定义与推演线索',text=f'{hook} 核对本题得到「{answer}」。',correct=True),dict(id='boundary',type='易混猜想',text=f'如果暂不检查条件，可能猜成「{trap}」。',correct=False)]
  if int(hashlib.sha256(pid.encode()).hexdigest()[-1],16)%2:clues.reverse()
  prompt=f'{lecture} 现在把这一步交给你：{question} 请选一条能由条件支持的线索。';hint=f'先把这道题拆成一小步，好吗？{boundary} 我们可以再核对一遍。';castor=f'请留意：{boundary}';phainon=f'这让我想到一个日常办法：{hook} 不过比喻要落到式子上，咱们再验算一次。'
  stages=[dict(id='textbook',name='概念与反例',speaker='anaxa',dialogue=f'今天讨论{title}。{lecture} 别把条件丢在门外：{boundary}'),dict(id='worked',name='例题推演',speaker='anaxa',dialogue=f'看这个例子。{wq} '+reason.replace(';','。')+f' 因此，结果是{wa}。现在，指出决定结论的那一步。'),dict(id='practice',name='迁移练习',speaker='anaxa',dialogue=f'换一个条件，再检验：{question} 不要借我的结论，写下你自己的推演。')]
  test=dict(question=question,choices=[x['text'] for x in clues],answer=next(i for i,x in enumerate(clues) if x['correct']),explanation=f'{board}。由条件得{answer}。{boundary}')
  transfer=dict(id='transfer',type='short_answer',question=question,answer=answer,accepted_answers=[answer],unit='',explanation=test['explanation'],origin='original_linear_transfer')
  if answer.lstrip('-').isdigit():transfer['answer_format']='rational'
  textbook=[dict(heading='对象、直觉与定义',text=lecture),dict(heading='适用条件与常见误区',text=boundary),dict(heading='原创记忆线索',text=hook+' 比喻帮助回忆，判断仍须依据定义与推演。')]
  course=dict(version=1,format='linear_classroom',title=title,estimated_minutes=15,objectives=[f'解释{title}的含义与适用条件','用具体反例检查容易混淆的结论','独立完成一次变式计算或判断'],textbook=textbook,board=board,worked_example=dict(question=wq,answer=wa,steps=[dict(label=f'推演{i+1}',text=t) for i,t in enumerate(reason.split(';'))],origin='original_not_video_question'),exercises=[transfer,dict(id='concept-check',type='choice',**test)],stages=stages,dialogue=dict(anaxa=stages[0]['dialogue'],hyacine=hint,castor=castor,phainon=phainon),source=dict(id='linear-bili-'+bvid,kind='video_course',title=entry['title'],author=view['owner']['name'],bvid=bvid,url=entry['url'],pages=[],supplement_urls=[entry['url']],catalog_verified=True,transcript_verified=False,lesson_origin='original_topic_lesson',note=NOTE),syllabus=dict(framework='用户指定线性代数公开合集主题',items=[title],selection=NOTE,official_full_text_verified=False),teaching_style=dict(sequence=['几何或生活直觉','精确定义','反例与条件','完整例题','独立变式'],evidence='依据公开主题组织原创教学，不宣称取得视频全文或复述作者独有口诀'))
  if slug=='det2':course['visualization']={'type':'linear-determinant'}
  feedback={k:f'{lead}{answer}。核对：{board}。{boundary} 记忆线索：{hook}' for k,lead in [('matched','这次推演有据可查。参考结论为'),('redirect','先把猜想放回条件里检验。参考结论为')]}
  points.append(dict(id=pid,subject='linear',chapter=ch['id'],module=CHAPTERS[key],module_id=key,concept=title,summary=lecture.split('。')[0]+'。',quick_meaning=board,character='anaxa',speaker='anaxa',prompt=prompt,clues=clues,difficulty=2,feedback=feedback,memoryHook=hook,example=dict(en=wq,zh=reason.replace(';','。')+f' 结论：{wa}。'),assistant_speaker='hyacine',assistant_hint=hint,classmate=dict(character='castor',text=castor),dialogue=dict(anaxa=prompt,hyacine=hint,castor=castor,phainon=phainon),test=test,course=course,source_refs=['linear-bili-'+bvid],source=dict(type='original_linear_course',note=NOTE,course_url=entry['url']),review_status='original_math_examples_reviewed'))
 for key,ch in chapters.items():ch.update(minutes=15*len(ch['points']),knowledgeCount=len(ch['points']));subject['modules'].append(dict(id=key,name=CHAPTERS[key],chapters=[ch['id']],point_count=len(ch['points'])))
 assert all(v['lesson_ids'] for v in videos);subject['knowledgeCount']=len(points);c['points']=[p for p in c['points'] if p['subject']!='linear']+points;c['version']=max(c.get('version',1),9)
 assert [p for p in c['points'] if p['subject']!='linear']==[p for p in before['points'] if p['subject']!='linear'];assert [s for s in c['subjects'] if s['id']!='linear']==[s for s in before['subjects'] if s['id']!='linear']
 write(path,c);write(ROOT/'knowledge/linear_lessons.json',dict(note=NOTE,chapters=subject['chapters'],points=points));write(ROOT/'knowledge/linear_series_mapping.json',dict(anchor='BV1LK421b7xs',series_id=season['id'],series_title=season['title'],author=view['owner']['name'],author_mid=view['owner']['mid'],reported_count=season['ep_count'],returned_count=len(videos),videos=videos,unmapped_videos=[],note=NOTE))
 p=ROOT/'data/references/sources.json';refs=json.loads(p.read_text(encoding='utf-8'));refs['sources']=[s for s in refs['sources'] if not s['id'].startswith('linear-bili-')]+[dict(id='linear-bili-'+v['bvid'],title='一高数 · '+v['title'],url=v['url'],status='public_catalog_verified_transcript_unavailable',note=NOTE) for v in videos];write(p,refs)
 print(json.dumps({'chapters':len(chapters),'lessons':len(points),'videos':len(videos),'unmapped':[]},ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');build()
