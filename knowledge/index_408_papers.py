"""只读索引 408 真题与答案；原卷按页面展示，不用提取文本替换题目。"""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'web/.deps'))
import pymupdf
def build():
 source=ROOT/'408真题';papers=[]
 report_path=ROOT/'knowledge/build/408-upstream/comparison.json'
 report=json.loads(report_path.read_text(encoding='utf-8')) if report_path.is_file() else None
 verified={r['path']:r for r in report['files']} if report else {}
 for path in sorted((source/'papers-rebuild').glob('*.pdf'),reverse=True):
  if not re.fullmatch(r'20\d{2}',path.stem):continue
  year=int(path.stem);answer=source/'answers'/f'{year}-answer.pdf';assert answer.is_file(),f'{year} 缺配套答案'
  files=[];numbers=set()
  for p,kind in [(path,'paper'),(answer,'solution')]:
   with pymupdf.open(p) as doc:
    count=len(doc);assert count>0
    if kind=='paper':
     assert str(year) in doc[0].get_text(),(p.name,'封面年份不匹配')
     text='\n'.join(page.get_text() for page in doc);numbers={int(n) for n in re.findall(r'(?m)^\s*(\d{1,2})[.．、]',text)}
     assert set(range(1,48))<=numbers,(year,'未能确认完整题号',sorted(set(range(1,48))-numbers))
     assert not re.search(r'参考答案|答案解析|试题解析',text),(year,'试卷疑似混入答案，需人工检查')
   relative=p.relative_to(source).as_posix();files.append(dict(id=hashlib.sha256(('cs408/'+relative).encode()).hexdigest()[:20],name=f'{year}年408'+('真题试卷.pdf' if kind=='paper' else '参考答案.pdf'),path=relative,kind=kind,extension='.pdf',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,contains_answers=kind=='solution',pages=count,question_pages=count if kind=='paper' else 0,exam_safe=kind=='paper',pdf_path=p.relative_to(ROOT).as_posix()))
  paper=dict(id=f'cs408-{year}',level='cs408',year=year,month=0,form=1,title=f'{year}年 · 408计算机学科专业基础综合',files=files,paper_id=files[0]['id'],duration_minutes=180,max_score=150,answer_schema={'choice_first':1,'choice_last':40,'written_first':41,'written_last':47},reference_only=False,external_word=False,ready=True,exam_ready=True,source_note='使用本地 papers-rebuild 整理版试卷；原文件页面直接展示，配套答案独立隔离。')
  if report:
   for f in files:
    r=verified[f['path']];assert r['matches'] and r['upstream_sha256']==f['sha256'],('来源版本与原卷不一致',f['path'])
    f['source_url']=report['repository']+'/blob/'+report['commit']+'/'+f['path']
   paper['source']=dict(repository=report['repository'],commit=report['commit'],verified_on=report['verified_on'],verification='sha256_identical',edition='community_rebuild',note='社区重构排版版；仓库提示可能存在校对错误，疑义请对照原始材料。')
   paper['source_note']='已核对 neville-studio/408-exam-paper 固定版本；本地试卷与配套答案逐字节一致。'
  papers.append(paper)
 target=ROOT/'data/exams/cs408.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(dict(version=1,papers=papers,unclassified=[],resources=[]),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'papers':len(papers),'years':[p['year'] for p in papers],'files':sum(len(p['files']) for p in papers)},ensure_ascii=False))
if __name__=='__main__':build()
