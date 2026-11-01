"""只读扫描本地原卷；按文件名归档，保留原文件哈希与配套资料。"""
import hashlib,json,re,sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'四六级真题'
def metadata(name):
    level='cet4' if '四级' in name else 'cet6' if '六级' in name else None
    date=re.search(r'(20\d{2})[年.](\d{1,2})',name)
    if not level or not date:return None
    year,month=map(int,date.groups())
    match=re.search(r'第?([一二三123])套',name) or re.search(r'卷([一二三123])',name) or re.search(r'[（(]([一二三123])[）)]',name)
    form={'一':1,'二':2,'三':3}.get(match[1],int(match[1]) if match and match[1].isdigit() else 1) if match else 1
    return level,year,month,form
def build():
    groups={};excluded=[];resources=[]
    for path in sorted(SOURCE.rglob('*')):
        if not path.is_file():continue
        meta=metadata(path.name)
        if not meta:
            if '历年真题大全' in path.name and path.suffix=='.pdf':
                meta=('cet6',1990,0,0)
            else:
                excluded.append(path.name);resources.append(dict(id=hashlib.sha256(str(path.relative_to(SOURCE)).encode()).hexdigest()[:20],name=path.name,path=str(path.relative_to(SOURCE))));continue
        level,year,month,form=meta;key=f'{level}-{year}-{month:02d}-{form}'
        group=groups.setdefault(key,dict(id=key,level=level,year=year,month=month,form=form,title=f'{year}年{month}月 · 第{form}套',files=[]))
        if month==0:group.update(title='1990—2007年 · 六级历年真题合集（37套原稿）',collection=True)
        kind='solution' if re.search('解析|精析|答案|听力原文',path.name) and not re.search('真题.*[及与+以].*(答案|精析)|真题.*以及答案',path.name) else 'paper'
        group['files'].append(dict(id=hashlib.sha256(str(path.relative_to(SOURCE)).encode()).hexdigest()[:20],name=path.name,path=str(path.relative_to(SOURCE)),kind=kind,extension=path.suffix.lower(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size,contains_answers=bool(re.search('答案|精析|解析',path.name))))
    for g in groups.values():
        candidates=[f for f in g['files'] if f['kind']=='paper']
        candidates.sort(key=lambda f:(f['extension']!='.pdf',f['contains_answers'],f['extension']!='.docx',f['name']))
        g['paper_id']=candidates[0]['id'] if candidates else None
        g['duration_minutes']=125 if g['level']=='cet4' else 130
    result=dict(version=1,source_directory='四六级真题',papers=sorted(groups.values(),key=lambda g:(-g['year'],-g['month'],g['form'],g['level'])),unclassified=excluded,resources=resources)
    out=ROOT/'data/exams';out.mkdir(exist_ok=True)
    (out/'index.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'groups':len(groups),'playable':{s:sum(g['level']==s and bool(g['paper_id']) for g in groups.values()) for s in ['cet4','cet6']},'unclassified':excluded,'non_pdf_papers':[(g['id'],next(f['name'] for f in g['files'] if f['id']==g['paper_id'])) for g in groups.values() if g['paper_id'] and next(f for f in g['files'] if f['id']==g['paper_id'])['extension']!='.pdf']},ensure_ascii=False,indent=2))
if __name__=='__main__':build()
