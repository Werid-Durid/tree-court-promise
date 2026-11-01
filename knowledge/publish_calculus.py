"""按已保存的公开视频合集目录发布原创高数课堂，保持其他课程及旧事件合同不变。"""
import copy,hashlib,json,os,re,shutil,sys
from pathlib import Path
from fractions import Fraction
from calculus_upper import ROWS as UPPER
from calculus_lower import ROWS as LOWER
from calculus_supplements import EXTRA

ROOT=Path(__file__).resolve().parents[1]
ANCHORS={'upper':'BV1mCn36NEoN','lower':'BV15A4m1G7zG'}
LABELS={'upper':'高数上','lower':'高数下'}
SECTIONS={'upper':{'极限':'limits','导数与微分':'derivatives','中值定理泰勒公式':'mean-taylor','不定积分':'antiderivatives','定积分':'integrals','微分方程':'ode','期末大串讲':'ode-review','学习方法':'study-methods','刷题':'practice'},
 'lower':{'开学指南期末串讲':'overview','向量代数与几何':'geometry','多元函数微分学':'multivariable','重积分':'multiple-integrals','曲线积分':'line-integrals','无穷级数':'series','曲面积分':'surface-integrals','刷题课':'practice'}}
NOTE='参考「一高数」高数上下册公开合集目录组织主题；两条入口的公开接口未返回字幕。讲解、例题、记忆线索为项目原创，不冒称视频逐句复现或已核实原题。'
# 来源合集分区不直接决定课程分区；串讲回到知识主题，学习方法不作为数学课时发布。
EXCLUDED_SLUGS={'learning-review','learning-map'}
LESSON_SECTIONS={'upper':{'linear-ode':'微分方程'},'lower':{'lower-practice':'重积分','lower-map':'多元函数微分学'}}
CHAPTER_REDIRECTS={'calculus-upper-ode-review':'calculus-upper-ode','calculus-upper-study-methods':'calculus-upper-limits','calculus-lower-overview':'calculus-lower-multiple-integrals'}

def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp')
 tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,path)

def answer_variants(a):
 result=[a]
 for alt in [('pi','π'),('x²','x^2')]:
  if alt[0] in a:result.append(a.replace(*alt))
 if re.fullmatch(r'[+-]?\d+(?:/\d+)?',a):
  n=Fraction(a)
  if n.denominator in {1,2,4,5,8,10,20,25,50,100}:result.append(str(float(n)))
 return list(dict.fromkeys(result))

def build():
 catalog_path=ROOT/'data/curriculum/catalog.json';c=json.loads(catalog_path.read_text(encoding='utf-8'));before=copy.deepcopy(c)
 backup=ROOT/'knowledge/build/calculus/before/catalog.json';backup.parent.mkdir(parents=True,exist_ok=True)
 if not backup.exists():shutil.copy2(catalog_path,backup)
 subject=next(s for s in c['subjects'] if s['id']=='calculus');subject.update(status='available',description='高数上与高数下 · 按知识主题组织，串讲融入对应章节 · 原创讲解、例题与练习',chapters=[],modules=[],syllabus_note=NOTE,chapter_redirects=CHAPTER_REDIRECTS)
 points=[];videos=[];series=[];mapped={};allchapters={};rows=[]
 for volume,raw in [('upper',UPPER),('lower',LOWER)]:
  view=json.loads((ROOT/f'knowledge/build/calculus/{ANCHORS[volume]}-view.json').read_text(encoding='utf-8'))['data']
  assert view['owner']['mid']==1035929235
  season=view['ugc_season'];episodes=[]
  for section in season['sections']:
   assert section['title'] in SECTIONS[volume]
   slug=SECTIONS[volume][section['title']];chid=f'calculus-{volume}-{slug}'
   chapter=dict(id=chid,title=section['title'],module=LABELS[volume],module_id=volume,status='available',subtitle='概念拆解 · 反例辨析 · 例题推演 · 迁移练习',course_format='calculus_classroom',opening=f'今天讨论{section["title"]}。先说清对象，再检查条件。图像和比喻可以帮助你进入问题，但最后要让计算和定义给出证据。',points=[],test_points=[])
   allchapters[chid]=chapter;subject['chapters'].append(chapter)
   for episode in section['episodes']:
    entry=dict(bvid=episode['bvid'],title=episode['title'],section=section['title'],volume=volume,cid=episode.get('cid'),duration=episode.get('page',{}).get('duration',episode.get('arc',{}).get('duration')),url='https://www.bilibili.com/video/'+episode['bvid']+'/',lesson_ids=[],verification='public_catalog_metadata_verified',transcript_verified=False)
    assert episode['bvid'] not in mapped
    videos.append(entry);episodes.append(entry);mapped[episode['bvid']]=(entry,chid)
  assert len(episodes)==season['ep_count']
  series.append(dict(id=season['id'],volume=volume,title=season['title'],author=view['owner']['name'],author_mid=view['owner']['mid'],reported_count=season['ep_count'],returned_count=len(episodes),url=f'https://space.bilibili.com/1035929235/lists/{season["id"]}?type=season'))
  for row in raw.strip().splitlines():rows.append((volume,None,row,False))
 for volume,section,row in EXTRA:rows.append((volume,section,row,True))
 base_ids=set()
 for volume,section,row,supplement in rows:
  fields=row.split('|');assert len(fields)==13,(fields[:3],len(fields))
  bvid,slug,title,lecture,boundary,board,wq,reason,wa,question,answer,trap,hook=fields
  entry,base_chid=mapped[bvid]
  assert entry['volume']==volume
  if slug in EXCLUDED_SLUGS:
   entry['excluded_reason']='按用户要求移除学习方法课时'
   continue
  section=LESSON_SECTIONS.get(volume,{}).get(slug,section)
  chid=f'calculus-{volume}-{SECTIONS[volume][section]}' if section else base_chid
  ch=allchapters[chid];pid=f'calculus-{volume}-{slug}';assert pid not in {p['id'] for p in points}
  if not supplement:base_ids.add(bvid)
  entry['lesson_ids'].append(pid);ch['points'].append(pid);ch['test_points'].append(pid)
  source_id='calculus-bili-'+bvid
  # 两种线索分别对应公式机制和具体易混结论；次序由稳定哈希决定，不靠选项位置背答案。
  clues=[dict(id='evidence',type='公式与条件线索',text=f'{hook} 依此核对，本题得到「{answer}」。',correct=True),dict(id='boundary',type='易混联想',text=f'沿另一个猜想推下去：本题应得到「{trap}」。',correct=False)]
  if int(hashlib.sha256(pid.encode()).hexdigest()[-1],16)%2:clues.reverse()
  prompt=f'先把问题讲明白。{lecture} 现在看一个变式：{question}请沿线索推演，而不是只看符号像不像。'
  hint=f'先别急着把公式都搬上来。{boundary} 可以用这条原创记忆线索：{hook}'
  castor=f'请保留条件。{boundary}'
  phainon=f'我会这样记：{hook} 但我也得把式子算完，不能拿比喻顶替证明。'
  stages=[dict(id='textbook',name='概念与反例',speaker='anaxa',dialogue=f'今天讨论{title}。{lecture} 请先停在这个边界上：{boundary}'),dict(id='worked',name='例题推演',speaker='anaxa',dialogue=f'看这个原创例题：{wq} '+reason.replace(';',' ')+f' 结论是{wa}。'),dict(id='practice',name='迁移练习',speaker='anaxa',dialogue=f'现在换你检验：{question} 把对象、条件和使用的方法一起说明。需要核对边界时请风堇协助。')]
  transfer=dict(id='transfer',type='short_answer',question=question,answer=answer,accepted_answers=answer_variants(answer),unit='',explanation=f'{board}。结合本节条件，得到{answer}。{boundary}',origin='original_calculus_transfer')
  if re.fullmatch(r'[+-]?\d+(?:/\d+|\.\d+)?',answer):transfer['answer_format']='rational'
  test=dict(question=question,choices=[clue['text'] for clue in clues],answer=next(i for i,x in enumerate(clues) if x['correct']),explanation=f'{answer}。{board}。{boundary}')
  textbook=[dict(heading='从直觉到定义',text=lecture),dict(heading='反例与适用边界',text=boundary),dict(heading='原创记忆线索',text=hook+' 比喻只用于提取记忆，正式结论仍要检查定义、条件与推演。')]
  course=dict(version=1,format='calculus_classroom',title=title,estimated_minutes=15,objectives=[f'解释{title}的对象与条件','用反例区分相近概念','完成例题和独立变式'],textbook=textbook,board=board,
   worked_example=dict(question=wq,answer=wa,steps=[dict(label=f'推演{i+1}',text=t) for i,t in enumerate(reason.split(';'))],origin='original_not_video_question'),
   exercises=[transfer,dict(id='concept-check',type='choice',**test)],stages=stages,dialogue=dict(anaxa=stages[0]['dialogue'],hyacine=hint,castor=castor,phainon=phainon),
   source=dict(id=source_id,kind='video_course',title=entry['title'],author='一高数',bvid=bvid,url=entry['url'],pages=[],supplement_urls=[entry['url']],catalog_verified=True,transcript_verified=False,lesson_origin='original_prerequisite_supplement' if supplement else 'original_topic_lesson',note=NOTE),
   syllabus=dict(framework='用户指定高数上下册公开合集目录',items=[title],selection=NOTE,official_full_text_verified=False),
   teaching_style=dict(sequence=['直觉切入','定义辨析','适用边界','完整例题','变式检验'],evidence='合集简介与标题可核对；不声称获得全部视频正文或作者独有口诀'))
  if slug in {'infinitesimal','infinite-sign'}:course['visualization']={'type':'sequence-threshold'}
  if slug in {'vectors','unit-vector','projection'}:course['visualization']={'type':'vector-components'}
  feedback={k:f'{lead}{answer}。核对机制：{board}。{boundary} 记忆线索：{hook}' for k,lead in [('matched','这次，条件与结论接上了。'),('redirect','先把这个猜想放回定义里检验。参考结论是') ]}
  p=dict(id=pid,subject='calculus',chapter=chid,module=LABELS[volume],module_id='calculus-'+volume,concept=title,summary=lecture.split('。')[0]+'。',quick_meaning=board,character='anaxa',speaker='anaxa',prompt=prompt,clues=clues,difficulty=2,
   feedback=feedback,memoryHook=hook,example=dict(en=wq,zh=reason.replace(';',' ')+f' 结论：{wa}。'),assistant_speaker='hyacine',assistant_hint=hint,classmate=dict(character='castor',text=castor),dialogue=dict(anaxa=prompt,hyacine=hint,castor=castor,phainon=phainon),
   micro_lesson=dict(concept=lecture,scenario=wq,reasoning=reason,common_traps=[boundary],memory_hook=hook,steps=[dict(label='对象与定义',text=lecture),dict(label='例题推演',text=reason.replace(';',' ')),dict(label='边界回看',text=boundary)]),
   test=test,course=course,source_refs=[source_id],source=dict(type='original_calculus_course',note=NOTE,course_url=entry['url']),review_status='original_math_examples_reviewed')
  points.append(p)
 excluded={v['bvid'] for v in videos if v.get('excluded_reason')}
 assert base_ids|excluded==set(mapped),('unmapped_video',set(mapped)-base_ids-excluded)
 subject['chapters']=[ch for ch in subject['chapters'] if ch['points']]
 for ch in subject['chapters']:ch.update(minutes=15*len(ch['points']),knowledgeCount=len(ch['points']))
 for volume in LABELS:
  subject['modules'].append(dict(id=volume,name=LABELS[volume],chapters=[ch['id'] for ch in subject['chapters'] if ch['module_id']==volume],point_count=sum(p['module_id']=='calculus-'+volume for p in points)))
 subject['knowledgeCount']=len(points)
 c['points']=[p for p in c['points'] if p['subject']!='calculus']+points;c['version']=max(c.get('version',1),8)
 assert [p for p in c['points'] if p['subject']!='calculus']==[p for p in before['points'] if p['subject']!='calculus']
 assert [s for s in c['subjects'] if s['id']!='calculus']==[s for s in before['subjects'] if s['id']!='calculus']
 manifest=dict(version=2,checked_date='2026-10-24',series=series,video_count=len(videos),active_video_count=len(base_ids),excluded_video_count=len(excluded),lesson_count=len(points),chapter_count=len(subject['chapters']),supplement_count=len(EXTRA),note=NOTE,transcript_verified=False,videos=videos,unmapped_videos=[])
 write(ROOT/'knowledge/calculus_series_mapping.json',manifest);write(ROOT/'knowledge/calculus_lessons.json',dict(subject=subject,points=points));write(catalog_path,c)
 refs_path=ROOT/'data/references/sources.json';refs=json.loads(refs_path.read_text(encoding='utf-8'));refs['sources']=[r for r in refs['sources'] if not r['id'].startswith('calculus-bili-')]
 refs['sources'] += [dict(id='calculus-bili-'+v['bvid'],title='一高数 · '+v['title'],url=v['url'],status='public_catalog_verified_transcript_unavailable',note=NOTE) for v in videos];write(refs_path,refs)
 print(json.dumps(dict(videos=len(videos),lessons=len(points),chapters=len(subject['chapters']),modules=subject['modules'],unmapped_videos=[]),ensure_ascii=False))

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');build()
