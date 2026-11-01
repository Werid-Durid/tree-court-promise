"""局部升级网络课程，保留知识点 ID、原有判题键及其他学科全部内容。"""
import hashlib,json,shutil,sys
from pathlib import Path
from network_course_content import rows,DEEPEN
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('D:/啥都有/xwechat_files/wxid_yatdtzqtl4cf22_4b5e/msg/file/2026-10/计算机网络讲义全-湖工.pdf')
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def build():
 path=ROOT/'data/curriculum/catalog.json';catalog=json.loads(path.read_text(encoding='utf-8'))
 backup=ROOT/'knowledge/build/network-handout/before/catalog.json';backup.parent.mkdir(parents=True,exist_ok=True)
 if not backup.exists():shutil.copy2(path,backup)
 asset=ROOT/'data/lectures/network/handout.pdf';asset.parent.mkdir(parents=True,exist_ok=True)
 digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
 if not asset.exists() or hashlib.sha256(asset.read_bytes()).hexdigest()!=digest:shutil.copy2(SOURCE,asset)
 data=rows();selected=[]
 for p in catalog['points']:
  if p.get('module_id')!='net':continue
  key=p['id'].removeprefix('cs408-net-')
  ranges,mechanism,boundary,formula,wq,wa,we,q,a,ex=data[key]
  if key in DEEPEN:mechanism+=' '+DEEPEN[key]
  page_ranges=[list(map(int,r.split('-'))) for r in ranges.split(';')] if ranges!='-' else []
  supplements=[]
  if key=='network-13':supplements=['https://www.rfc-editor.org/rfc/rfc8200']
  if key=='network-14':supplements=['https://datatracker.ietf.org/doc/html/rfc9776','https://datatracker.ietf.org/doc/html/rfc5944']
  if key=='network-15':supplements=['https://opennetworking.org/sdn-definition/']
  if key=='network-09':supplements=['https://datatracker.ietf.org/doc/html/rfc6633']
  if key=='transport-06':supplements=['https://www.rfc-editor.org/rfc/rfc6298']
  units=['bit/s','B/s','MSS','KB','bit','ms','B','s','%']
  unit=next((u for u in units if u in q),'') if a.lstrip('-').isdigit() else ''
  transfer=dict(id='transfer',type='short_answer',question=q,answer=a,accepted_answers=[a]+([a+unit] if unit else []),unit=unit,explanation=ex,origin='original_transfer_exercise')
  check=dict(id='concept-check',type='choice',question=p['test']['question'],choices=p['test']['choices'],answer=p['test']['answer'],explanation=p['test']['explanation'],origin='existing_original_review')
  teacher=f'今天把「{p["concept"]}」讲清楚。先确认定义：{p["summary"]} 接着追踪机制：{mechanism}'
  assistant=f'我把容易混淆的边界写在旁边：{boundary} 做题前先检查这一条，慢一点也没关系。'
  castor=f'请保留适用条件。{boundary}'
  phainon=f'我试着从例子走一遍：{wq} {we} 换一组条件再算，才知道自己有没有跟上。'
  course=dict(version=1,title=p['concept'],estimated_minutes=12,objectives=[f'解释{p["concept"]}的机制',f'明确条件：{boundary.split("。")[0]}','完成例题推演与迁移练习'],
   textbook=[{'heading':'概念与问题','text':p['summary']},{'heading':'机制如何工作','text':mechanism},{'heading':'适用条件与易错边界','text':boundary}],board=formula,
   worked_example=dict(question=wq,answer=wa,steps=[{'label':'明确条件','text':wq},{'label':'沿机制推演','text':we},{'label':'核对结果','text':wa+'；'+boundary.split('。')[0]+'。'}]),
   exercises=[transfer,check],
   stages=[dict(id='textbook',name='教材讲解',speaker='anaxa',dialogue=teacher),dict(id='worked',name='例题推演',speaker='anaxa',dialogue=f'看这个例子：{wq} {we} 结论是{wa}。把适用条件带进计算，结论才有依据。'),dict(id='practice',name='随堂练习',speaker='anaxa',dialogue=f'现在换一组条件。{q} 先独立推演，再检验结果；需要提示时请风堇协助。')],
   dialogue=dict(anaxa=teacher,hyacine=assistant,castor=castor,phainon=phainon),
   source=dict(id='network-handout-hugong',sha256=digest,pages=page_ranges,review_status='toc_and_selected_slides_reviewed' if page_ranges else 'supplement_not_in_handout',supplement_urls=supplements),
   syllabus=dict(framework='408 网络六章考查框架',target_year=2027,official_full_text_verified=False,selection='讲义相关章节筛选；年度条目以教育部教育考试院正式大纲为准'))
  p['course']=course
  selected.append(dict(point_id=p['id'],concept=p['concept'],pages=page_ranges,source_status=course['source']['review_status'],supplement_urls=supplements))
 subject=next(s for s in catalog['subjects'] if s['id']=='cs408')
 for ch in subject['chapters']:
  if ch.get('module_id')=='net':
   ch['subtitle']='教材讲解 · 例题推演 · 随堂练习';ch['minutes']=len(ch['points'])*12;ch['course_format']='textbook_classroom';ch['handout_source']='network-handout-hugong'
 catalog['version']=max(catalog.get('version',1),5)
 write(path,catalog)
 manifest=dict(version=1,source=dict(id='network-handout-hugong',title='用户提供：计算机网络讲义全-湖工',file='data/lectures/network/handout.pdf',original_path=str(SOURCE),sha256=digest,pages=1622,extraction='图片型 PPT，目录索引及选定汇总/过程页离线 OCR 与图像核对，未声称逐字识别全部页'),
  syllabus_note='参照408六章知识框架与出版社公开复习目录筛选，2027正式大纲全文未取得，年度变动未逐条核验。',
  framework_source='https://phei.com.cn/module/goods/wssd_content.jsp?bookid=68922',
  lessons=selected,lesson_count=len(selected),exercise_count=len(selected)*2,
  supplementary_topics=['IPv6','IP组播、IGMP与移动IP','SDN（路由器本体部分可参照讲义）','ALOHA、海明码等边界补充'],
  lower_priority=['因特网历史与标准化过程：保留查阅，不作为独立必修课时','STP、VPN的配置细节及动画重复页：按主题辅助理解，不增设独立检测','HTML/CSS/JavaScript页面制作细节：不代替HTTP协议课'],
  corrections=[dict(topic='ICMP源点抑制',page=1107,note='讲义列出历史报文类型；课程提示 RFC 6633 已弃用，不把它作为现行拥塞控制机制。',reference='https://datatracker.ietf.org/doc/html/rfc6633')])
 write(ROOT/'knowledge/network_handout_mapping.json',manifest)
 write(ROOT/'knowledge/network_course.json',{'lessons':[p for p in catalog['points'] if p.get('module_id')=='net'],'mapping':manifest})
 write(ROOT/'knowledge/cs408_lessons.json',{'subject':subject,'points':[p for p in catalog['points'] if p.get('subject')=='cs408']})
 coverage_path=ROOT/'knowledge/cs408_coverage.json';coverage=json.loads(coverage_path.read_text(encoding='utf-8'))
 coverage['network_course']={'lessons':56,'exercises':112,'handout_mapping':'knowledge/network_handout_mapping.json','official_2027_full_text_verified':False};write(coverage_path,coverage)
 sys.path.insert(0,str(ROOT))
 from voice.dialogue import collect_lines
 write(ROOT/'knowledge/network_course_voice_queue.json',{'status':'pending_audio_generation','note':'教材课堂台词按角色及全文哈希索引；尚未合成音频，不复用错词旧录音。','lines':[r for r in collect_lines(catalog) if r['id'].startswith('course-')]})
 refs_path=ROOT/'data/references/sources.json';refs=json.loads(refs_path.read_text(encoding='utf-8'))
 refs['sources']=[r for r in refs['sources'] if r['id']!='network-handout-hugong']+[{'id':'network-handout-hugong','title':manifest['source']['title'],'url':'/api/network-handout/info','status':'local_slides_reviewed','note':manifest['source']['extraction']}]
 write(refs_path,refs)
 print(json.dumps({'lessons':len(selected),'exercises':len(selected)*2,'pages':1622,'network_ids_preserved':True},ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');build()
