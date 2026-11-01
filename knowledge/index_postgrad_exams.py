"""近十年数学一、英语一原卷索引；与四六级、408及用户答卷独立。"""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'web/.deps'));import pymupdf
BUILD=ROOT/'knowledge/build/postgrad-exams';BASE=ROOT/'assets/exams/postgrad'
def build():
 rows=json.loads((BUILD/'downloads.json').read_text(encoding='utf-8'))+json.loads((BUILD/'supplements.json').read_text(encoding='utf-8'));papers=[]
 def file(row,kind,label):
  p=ROOT/row['local_path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_sha']
  with pymupdf.open(p) as doc:pages=len(doc);assert pages>0
  path=p.relative_to(BASE).as_posix()
  return dict(id=hashlib.sha256(('postgrad/'+path).encode()).hexdigest()[:20],name=label,path=path,pdf_path=p.relative_to(ROOT).as_posix(),kind=kind,extension='.pdf',sha256=row['sha256'],bytes=len(raw),pages=pages,question_pages=pages if kind=='paper' else 0,exam_safe=kind=='paper',contains_answers=kind!='paper',source_url=row['source_url'],repository=row['repository'],source_commit=row['commit'])
 for level,name,score in [('math1','数学一',150),('english1','英语一',100)]:
  for year in range(2026,2016,-1):
   selected=[r for r in rows if r['year']==year and r['level']==level];files=[]
   if level=='math1' and year in [2023,2024,2025]:
    images=sorted([r for r in selected if r['kind']=='question_image'],key=lambda r:r['local_path']);assert len(images)==22
    image_pages=[]
    for i,r in enumerate(images,1):
     assert Path(r['local_path']).name.startswith(f'Q{i:02}_');assert hashlib.sha256((ROOT/r['local_path']).read_bytes()).hexdigest()==r['sha256'];image_pages.append(dict(path=r['local_path'],sha256=r['sha256'],question_number=i))
    path=f'math1/{year}-question-images.zip';p=BASE/path;raw=p.read_bytes();files.append(dict(id=hashlib.sha256(('postgrad/'+path).encode()).hexdigest()[:20],name=f'{year}年数学一真题（逐题原图）.zip',path=path,kind='paper',extension='.zip',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),pages=22,question_pages=22,exam_safe=True,contains_answers=False,image_pages=image_pages,source_url=images[0]['repository']+'/tree/'+images[0]['commit']+'/kaoyan_math_images/',repository=images[0]['repository'],source_commit=images[0]['commit']))
    files.append(file(next(r for r in selected if r['kind']=='combined'),'solution',f'{year}年数学一试题与解析.pdf'));form='question_images'
   else:
    original=next(r for r in selected if r['kind']=='paper');f=file(original,'paper',f'{year}年{name}真题试卷.pdf')
    if level=='english1':
     with pymupdf.open(ROOT/original['local_path']) as doc:
      text='\n'.join(p.get_text() for p in doc);assert 'Use' in text and 'English' in text and 'Writing' in text and '52' in text,(year,'英语一部分缺失');assert not any(w in text for w in ['参考答案','试题解析','答案解析']),(year,'原卷混入答案')
    files.append(f);solution=next((r for r in selected if r['kind']=='solution'),None)
    if solution:files.append(file(solution,'solution',f'{year}年{name}参考解析.pdf'))
    form='pdf'
   schema=dict(choice_first=1,choice_last=10 if year>=2021 else 8,fill_first=11 if year>=2021 else 9,fill_last=16 if year>=2021 else 14,written_first=17 if year>=2021 else 15,written_last=22 if year>=2021 else 23) if level=='math1' else dict(choice_first=1,choice_last=40,matching_first=41,matching_last=45,translation_first=46,translation_last=50,writing_first=51,writing_last=52)
   papers.append(dict(id=f'{level}-{year}',level=level,year=year,month=0,form=1,title=f'{year}年 · 考研{name}',files=files,paper_id=files[0]['id'],duration_minutes=180,max_score=score,answer_schema=schema,reference_only=False,external_word=False,ready=True,exam_ready=True,paper_format=form,solution_available=len(files)>1,source=dict(repository=files[0]['repository'],commit=files[0]['source_commit'],verified_on='2026-10-29',verification='git_blob_sha1_and_local_sha256'),source_note='原题图文按文件展示，不经OCR重写。'+('本卷按第1—22题原图分页；下载为原图ZIP，配套PDF解析交卷后开放。' if form=='question_images' else '')+('尚未取得完整配套解析。' if len(files)==1 else '')))
 target=ROOT/'data/exams/postgrad.json';tmp=target.with_suffix('.json.tmp');tmp.write_text(json.dumps(dict(version=1,years=list(range(2017,2027)),papers=papers),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(target);print(json.dumps(dict(papers=len(papers),math1=10,english1=10,math_image_papers=3,english_missing_solution=[p['year'] for p in papers if p['level']=='english1' and not p['solution_available']])))
if __name__=='__main__':build()
