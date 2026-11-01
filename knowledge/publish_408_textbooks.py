"""仅升级组成、操作系统和数据结构；保持题目 ID、旧答案和事件重放合同。"""
import copy,hashlib,json,os,re,shutil,sys
from pathlib import Path
from textbook_syllabus import ITEMS
from textbook_examples import EXAMPLES
from textbook_deepening import DEEPEN

ROOT=Path(__file__).resolve().parents[1]
BOOKS={'co':('计算机组成原理',351,[14,33,91,165,213,295,313]),'os':('操作系统',384,[14,50,194,271,327]),'ds':('数据结构',415,[14,26,77,124,140,212,285,353])}
NOTE='按用户提供的2027版教材章首「考纲内容」及正文分节组织。2027官方大纲全文尚未独立逐项核验，不将本地教材目录冒称官方年度全文。'

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,path)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def build():
    path=ROOT/'data/curriculum/catalog.json';catalog=json.loads(path.read_text(encoding='utf-8'))
    before=ROOT/'knowledge/build/408-textbooks/before/catalog.json';before.parent.mkdir(parents=True,exist_ok=True)
    if not before.exists():shutil.copy2(path,before)
    old=copy.deepcopy(catalog);by={p['id']:p for p in catalog['points']};lessons=[];books=[];atoms=[]
    for mod,(title,count,outline_pages) in BOOKS.items():
        matches=list((ROOT/'408教材').glob(f'*{title}*.pdf'))
        if len(matches)!=1:raise ValueError(f'{title}教材必须唯一')
        source=matches[0];sha=digest(source);book_id=f'wangdao2027-{mod}'
        # 已提取的正文用于定位和复现；不把 OCR 识别错误的公式直接发布为讲解。
        extracted=json.loads((ROOT/f'knowledge/build/408-textbooks/{mod}-pages.json').read_text(encoding='utf-8'))
        assert len(extracted)==count
        book=dict(id=book_id,module_id=mod,title=f'2027 王道《{title}》',file=source.relative_to(ROOT).as_posix(),sha256=sha,pages=count,outline_pages=outline_pages,
            method='正文文本分节定位，章首考纲映射，选定原页图像核对；讲解重新编写，不直接发布OCR数学公式。原书未改动。',official_full_text_verified=False)
        books.append(book)
        local_atoms={}
        for line in ITEMS[mod].strip().splitlines():
            key,topics=line.split('|');pid=f'cs408-{mod}-{key}'
            if pid not in by:raise ValueError(pid)
            local_atoms.setdefault(pid,[]).extend(topics.split(';'))
        rows=__import__('textbook_'+mod).ROWS.strip().splitlines()
        expected={p['id'] for p in catalog['points'] if p.get('module_id')==mod}
        seen=set()
        for row in rows:
            key,ranges,section,mechanism,boundary,board,question,answer,explanation=row.split('|')
            pid=f'cs408-{mod}-{key}';p=by[pid];assert pid not in seen;seen.add(pid)
            pages=[list(map(int,r.split('-'))) for r in ranges.split(';')]
            assert all(1<=lo<=hi<=count for lo,hi in pages)
            topics=local_atoms.get(pid,[])
            textbook=[dict(heading='概念与问题',text=p['summary']),dict(heading='教材机制 · '+section,text=mechanism)]
            if f'{mod}-{key}' in DEEPEN:
                heading,text=DEEPEN[f'{mod}-{key}'];textbook.append(dict(heading=heading,text=text))
            textbook.append(dict(heading='适用条件与易错边界',text=boundary))
            example=EXAMPLES.get(f'{mod}-{key}')
            if example:wq,wa,steps=example
            else:
                wq=p['example']['en'];wa=p['test']['choices'][p['test']['answer']]
                steps=[f'本题讨论「{p["concept"]}」。{p["summary"]}',mechanism,f'因此保留的依据是：{wa}。检查边界：{boundary}']
            worked=dict(question=wq,answer=wa,steps=[dict(label=f'推演 {i+1}',text=t) for i,t in enumerate(steps)],origin='original_teaching_example')
            aliases={'PC':['程序计数器'],'IR':['指令寄存器'],'PCB':['进程控制块'],'VMM':['虚拟机监控器'],'SPOOLing':['假脱机','假脱机技术'],'栈帧':['活动记录'],'DRAM':['动态随机存储器'],'DMA':['直接存储器访问'],'DMA控制器':['DMA 控制器'],'脏位':['修改位'],'CF':['进位标志'],'中断嵌套':['多重中断'],'缺页异常':['缺页中断'],'静态链表':['游标链表'],'同一集合':['同一个集合']}
            accepted=[answer]+aliases.get(answer,[])
            if re.fullmatch('[01]{4,}',answer):accepted += [answer+'B',answer+'₂']
            transfer=dict(id='transfer',type='short_answer',question=question,answer=answer,accepted_answers=accepted,unit='',explanation=explanation,origin='original_textbook_transfer')
            check=dict(id='concept-check',type='choice',question=p['test']['question'],choices=p['test']['choices'],answer=p['test']['answer'],explanation=p['test']['explanation'],origin='preserved_original_review')
            teacher=f'今天讨论{p["concept"]}。{p["summary"]} {mechanism}'
            assistant=f'我把边界条件写在这里：{boundary} 记忆时可以借助这条线索：{p["memoryHook"]}'
            castor=f'请留意。{boundary}'
            phainon=f'我用这个情境试一遍：{wq} 推到最后是：{wa}。生活里的比喻可以帮助记忆，计算还是要按条件来。'
            course=dict(version=2,title=p['concept'],estimated_minutes=18,format='textbook_classroom',
                objectives=[f'说明{p["concept"]}的定义及机制','追踪一个完整情境的中间状态','区分适用条件，独立完成迁移练习'],
                textbook=textbook,board=board,worked_example=worked,exercises=[transfer,check],
                stages=[dict(id='textbook',name='教材讲解',speaker='anaxa',dialogue=teacher),dict(id='worked',name='例题推演',speaker='anaxa',dialogue=f'看这一题：{wq} '+ ' '.join(steps)+f' 结论是{wa}。'),dict(id='practice',name='随堂练习',speaker='anaxa',dialogue=f'现在请你独立推演：{question} 不必猜我想听什么，按定义和条件给出依据。')],
                dialogue=dict(anaxa=teacher,hyacine=assistant,castor=castor,phainon=phainon),
                source=dict(id=book_id,kind='textbook',book_id=book_id,title=book['title'],sha256=sha,pages=pages,sections=section,review_status='section_mapping_and_selected_page_images_checked',supplement_urls=[],page_numbering='pdf_1_based'),
                syllabus=dict(framework='本地2027教材章首考纲',target_year=2027,official_full_text_verified=False,selection=NOTE,items=topics,role='core' if topics else 'prerequisite_or_deepening'))
            p['course']=course
            lesson=dict(point_id=pid,module_id=mod,concept=p['concept'],book_id=book_id,pages=pages,sections=section,syllabus_items=topics,source_text_sha256=digest_text(extracted,pages))
            lessons.append(lesson)
            for topic in topics:atoms.append(dict(id=f'{mod}-{len(atoms)+1:03}',module_id=mod,topic=topic,point_id=pid,book_id=book_id,pages=pages,status='mapped_with_textbook_explanation'))
        assert seen==expected,(seen^expected)
    # 不改章 ID 和检测题目，避免旧测试记录因扩充教材正文而被重新计分。
    subject=next(s for s in catalog['subjects'] if s['id']=='cs408')
    for ch in subject['chapters']:
        if ch.get('module_id') in BOOKS:
            ch.update(subtitle='教材讲解 · 例题推演 · 随堂练习 · 原书对照',course_format='textbook_classroom',minutes=18*len(ch['points']),textbook_source=f'wangdao2027-{ch["module_id"]}')
    catalog['version']=max(catalog.get('version',1),7)
    assert len(catalog['points'])==len(old['points'])
    for original,new in zip(old['points'],catalog['points']):
        if original.get('module_id') not in BOOKS:assert original==new
        else:assert {k:v for k,v in new.items() if k!='course'}=={k:v for k,v in original.items() if k!='course'}
    coverage=dict(version=1,basis=NOTE,official_full_text_verified=False,network_read=False,books=books,lesson_count=len(lessons),mapped_syllabus_items=len(atoms),items=atoms,unmapped_items=[],
        audit_note='细项由本地教材章首考纲人工拆分并映射；自动检查每条有课时、讲解、原书页段。该检查不等价于独立官方年度逐字比对。',
        supplementary_lessons=[l['point_id'] for l in lessons if not l['syllabus_items']])
    write(ROOT/'knowledge/408_textbook_mapping.json',dict(version=1,books=books,lessons=lessons,syllabus_note=NOTE))
    write(ROOT/'knowledge/408_textbook_coverage.json',coverage)
    write(path,catalog)
    write(ROOT/'knowledge/cs408_lessons.json',dict(subject=subject,points=[p for p in catalog['points'] if p.get('subject')=='cs408']))
    coverage_path=ROOT/'knowledge/cs408_coverage.json';current=json.loads(coverage_path.read_text(encoding='utf-8'))
    current['textbook_courses']={k:dict(lessons=sum(l['module_id']==k for l in lessons),mapped_syllabus_items=sum(a['module_id']==k for a in atoms)) for k in BOOKS}
    current['textbook_mapping']='knowledge/408_textbook_mapping.json';current['textbook_syllabus_basis']=NOTE;write(coverage_path,current)
    print(json.dumps(dict(lessons=len(lessons),syllabus_items=len(atoms),exercises=len(lessons)*2,network_unchanged=True,legacy_ids_and_answers_unchanged=True),ensure_ascii=False))

def digest_text(extracted,ranges):
    text='\n'.join(extracted[n-1]['text'] for lo,hi in ranges for n in range(lo,hi+1))
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');build()
