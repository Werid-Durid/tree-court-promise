"""可重复发布 408 四科。保留旧课程 ID、存档和角色档案，原创案例不冒充真题。"""
import json,sys,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'knowledge'))
import cs408_networks,cs408_architecture,cs408_operating_systems,cs408_data_structures
MODULES=[('net','计算机网络',cs408_networks.CHAPTERS,'https://space.bilibili.com/360996402/lists/6564646?type=season'),
 ('co','计算机组成原理',cs408_architecture.CHAPTERS,'https://space.bilibili.com/360996402/lists/2199556?type=season'),
 ('os','操作系统',cs408_operating_systems.CHAPTERS,'https://pages.cs.wisc.edu/~remzi/OSTEP/'),
 ('ds','数据结构',cs408_data_structures.CHAPTERS,'https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/')]
SYLLABUS_NOTE='2027 版大纲出版信息已核实；正文逐条映射尚待校对。当前为四科基础知识与原创微课框架，不是官方大纲逐字转写。'
SOURCES=[
 {'id':'cs408-outline-2027','title':'2027 全国硕士研究生招生考试计算机学科专业基础考试大纲 · 高等教育出版社','url':'https://www.hep.com.cn/book/show/2099763850751057921','status':'metadata_verified','note':'教育部教育考试院编，ISBN 978-7-04-068451-3，出版日期 2026-09-29。仅出版元数据可核实，未取得完整正文，不宣称逐条核验完成。'},
 {'id':'cs408-hep-analysis','title':'全国硕士研究生招生考试计算机学科专业基础考试大纲解析 · 高教社公开目录','url':'https://xuanshu.hep.com.cn/front/h5Mobile/bookDetails?bookId=68b8764ae119ac9729e8a8bc','status':'catalog_only','note':'2025-10-15 出版的解析书，公开目录作为基础知识组织参照，不冒充 2027 大纲正文。'},
 {'id':'cs408-co-season','title':'用户指定：计算机组成原理微课堂合集','url':MODULES[1][3],'status':'catalog_only','note':'合集页直读未成功；同作者公开课程页 BV1qG41197E4 的简介及部分目录可核对。借鉴短讲、形象过程推演；无字幕逐字转写，未核实合集全部成员。'},
 {'id':'cs408-net-season','title':'用户指定：计算机网络课程合集','url':MODULES[0][3],'status':'catalog_only','note':'合集页直读未成功；同作者 408 网络强化复习公开分集目录可检索。保留用户指定入口，不宣称完整观看或精确逐集映射。'},
 {'id':'cs408-co-public','title':'湖科大教书匠 · 计算机组成原理微课堂公开课程页','url':'https://www.bilibili.com/video/BV1qG41197E4/','status':'catalog_only','note':'核对公开简介和分集标题。课程例题与角色对白由本项目原创，不转载视频、讲义或配音。'},
 {'id':'cs408-net-public','title':'湖科大教书匠 · 408 计算机网络强化复习公开目录','url':'https://www.bilibili.com/video/BV1XHs3zPEuW/','status':'catalog_only','note':'公开检索目录包含性能、分层、物理、链路、路由、TCP 与应用层。具体板书、动画、逐句讲法未核实。'},
 {'id':'cs408-ostep','title':'OSTEP · 操作系统作者公开教材','url':MODULES[2][3],'status':'page_verified','note':'作者公开资源作为机制核对与后续深入阅读入口，不将其范围当作 408 官方考纲。'},
 {'id':'cs408-mit','title':'MIT 6.006 · 算法公开课程','url':MODULES[3][3],'status':'page_verified','note':'用于算法学习资源与概念复核入口，题目、案例和中文台词为原创。'},
 {'id':'cs408-rfc-tcp','title':'RFC 9293 · TCP 标准','url':'https://www.rfc-editor.org/rfc/rfc9293','status':'page_verified','note':'TCP 协议机制的原始规范；考场算法和计时模型仍以题干约定为准。'},
 {'id':'cs408-rfc-ip','title':'RFC 791 · IPv4 基础规范','url':'https://www.rfc-editor.org/rfc/rfc791','status':'page_verified','note':'IPv4 基础规范存在后续更新，课程不把历史文本视为全部现行实现。'}]

def build():
 path=ROOT/'data/curriculum/catalog.json';catalog=json.loads(path.read_text(encoding='utf-8'))
 old=[p for p in catalog['points'] if p['subject']!='cs408']
 backup=ROOT/'knowledge/build/cs408-before';backup.mkdir(parents=True,exist_ok=True)
 if not (backup/'catalog.json').exists():shutil.copy2(path,backup/'catalog.json')
 subject=next(s for s in catalog['subjects'] if s['id']=='cs408')
 subject.update(status='available',name='考研 408',description='计算机网络、计算机组成原理、操作系统、数据结构 · 四科自由选学',en='COMPUTER SCIENCE · 408',syllabus_note=SYLLABUS_NOTE,chapters=[],modules=[])
 points=[];coverage=[]
 for module_id,label,chapters,url in MODULES:
  module={'id':module_id,'name':label,'chapters':[],'source_url':url,'point_count':0}
  for slug,title,table in chapters:
   chid=f'cs408-{module_id}-{slug}';ids=[]
   rows=[line.strip().split('|') for line in table.strip().splitlines() if line.strip()]
   assert all(len(r)==6 for r in rows),(chid,'每条知识需要六个完整字段')
   chapter={'id':chid,'title':title,'module':label,'module_id':module_id,'subtitle':'短讲解 · 过程推演 · 易混辨析','status':'available','minutes':len(rows)*2,'opening':f'第一，称呼我阿那克萨戈拉斯。今天讨论{title}。我们不靠术语堆砌理解：先写清条件，再沿过程推演，最后检验结论。你可以从任意知识点开始。','points':ids,'reference_url':url}
   for index,(name,theory,case,clue,trap,hook) in enumerate(rows):
    pid=f'{chid}-{index+1:02d}';ids.append(pid)
    # 稳定、确定性轮换选项位置，避免记住“第一条总是匹配”。
    choices=[{'id':'evidence','text':clue,'correct':True,'type':'过程线索'},{'id':'boundary','text':trap,'correct':False,'type':'易混线索'}]
    if int(hashlib.sha256(pid.encode()).hexdigest()[-1],16)%2:choices.reverse()
    lead=['先把条件写清楚。','别让一个熟悉的名词代替推理。','我们只讨论能被过程检验的结论。','先问机制，再谈记忆。'][index%4]
    prompt=f'{lead}{theory} 现在，把它放进这个情境：{case}哪条线索保留了必要的条件？'
    hint=f'不用急着同时处理所有信息。先圈出这个情境的条件：{case} 再核对「{name}」的机制。{hook}'
    castor=f'请先保留条件。{theory.split("；")[0]}。' if '；' in theory else f'请留意这一点：{theory}'
    phainon=f'我把它记成这幅生活里的画面：{hook}不过，比喻只是帮忙记住，遇到具体数值还得按条件算。'
    peer='castor' if index%2==0 else 'phainon'
    refs=['cs408-outline-2027','cs408-hep-analysis']+({'net':['cs408-net-season','cs408-net-public','cs408-rfc-tcp','cs408-rfc-ip'],'co':['cs408-co-season','cs408-co-public'],'os':['cs408-ostep'],'ds':['cs408-mit']}[module_id])
    point={'id':pid,'subject':'cs408','chapter':chid,'module':label,'module_id':module_id,'concept':name,'summary':theory,'quick_meaning':theory,
     'character':'anaxa','speaker':'anaxa','prompt':prompt,'clues':choices,'difficulty':2,
     'feedback':{'matched':f'这次，依据比标签更可靠。{clue}。把机制再留住：{theory} 记忆钩子：{hook}',
                 'redirect':f'先别把一次试探当作定论。你选的线索是「{trap}」，它没有满足这里的条件。{clue}。{theory} 记忆钩子：{hook}'},
     'memoryHook':hook,'example':{'en':case,'zh':f'{clue}。{theory}'},'assistant_speaker':'hyacine','assistant_hint':hint,
     'classmate':{'character':peer,'text':castor if peer=='castor' else phainon},
     'dialogue':{'anaxa':prompt,'hyacine':hint,'castor':castor,'phainon':phainon},
     'micro_lesson':{'concept':theory,'scenario':case,'reasoning':clue,'common_traps':[trap],'memory_hook':hook,'steps':[{'label':'给定情境','text':case},{'label':'推演依据','text':clue},{'label':'机制回扣','text':theory}]},
     'test':{'question':case,'choices':[c['text'] for c in choices],'answer':next(i for i,c in enumerate(choices) if c['correct']),'explanation':f'{clue}。{theory}'},
     'source_refs':refs,'source':{'type':'original_micro_lesson','note':'原创教学案例，非历年真题；按基础知识框架组织，2027 大纲正文逐条校对待完成。','course_url':url},
     'syllabus':{'target_year':2027,'mapping_status':'full_text_pending','chapter':title,'module':label},'review_status':'original_content_checked'}
    points.append(point);coverage.append({'point_id':pid,'module_id':module_id,'chapter_id':chid,'topic':name,'syllabus_mapping':'2027_full_text_pending','has_lesson':True,'has_original_case':True,'characters':list(point['dialogue'])})
   chapter.update(test_points=list(ids),knowledgeCount=len(ids));subject['chapters'].append(chapter);module['chapters'].append(chid);module['point_count']+=len(ids)
  subject['modules'].append(module)
 subject['knowledgeCount']=len(points)
 catalog['points']=old+points;catalog['version']=4
 catalog['characters']=json.loads((ROOT/'characters/profiles.json').read_text(encoding='utf-8'))['characters']
 manifest={'target_exam_year':2027,'syllabus_publication_verified':True,'syllabus_full_text_verified':False,'latest_publication_date':'2026-09-29','note':SYLLABUS_NOTE,'course_learning_status':'public_catalog_and_description_only','modules':subject['modules'],'chapters':len(subject['chapters']),'knowledge_points':len(points),'coverage':coverage,'sources':SOURCES}
 (ROOT/'knowledge/cs408_coverage.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (ROOT/'knowledge/cs408_lessons.json').write_text(json.dumps({'subject':subject,'points':points},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 source_path=ROOT/'data/references/sources.json';sources=json.loads(source_path.read_text(encoding='utf-8'))
 sources['sources']=[s for s in sources['sources'] if not s['id'].startswith('cs408-')]+SOURCES;sources['checked_date']='2026-10-21'
 source_path.write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'points':len(points),'chapters':len(subject['chapters']),'modules':[{k:m[k] for k in ('id','name','point_count')} for m in subject['modules']]},ensure_ascii=False))

if __name__=='__main__':build()
