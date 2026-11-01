"""为原卷建立页级目录；题目页与答案页分开，不重写题干。"""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'web/.deps'))
import pymupdf
sys.stdout.reconfigure(encoding='utf-8')
path=ROOT/'data/exams/index.json';index=json.loads(path.read_text(encoding='utf-8'))
for paper in index['papers']:
 for f in paper['files']:
  source=ROOT/'四六级真题'/f['path'] if f['extension']=='.pdf' else ROOT/'data/exams/converted'/f"{f['id']}.pdf"
  if not source.is_file():continue
  with pymupdf.open(source) as doc:
   f['pages']=len(doc);boundary=None
   for n,page in enumerate(doc):
    text=re.sub(r'\s+','',page.get_text())
    # 仅匹配明确的答案标题；不把题干中的 answer / 听力 Directions 误判成答案页。
    if n and re.search(r'参考答案|真题答案|试题答案|答案解析|答案详解|答案及精析|真题解析|听力原文',text[:700]):boundary=n;break
   f['question_pages']=boundary if boundary is not None else len(doc)
   f.pop('question_last_clip',None)
   # 本卷第 13 页上方是 89—91 题，下方接答案；按原页坐标保留题目区域。
   if paper['id']=='cet4-2013-06-3' and f['kind']=='paper' and boundary==12:
    f['question_pages']=13;f['question_last_clip']=195
   f['answer_boundary']=boundary
   f['exam_safe']=not f['contains_answers'] or boundary is not None
   f['pdf_path']=str(source.relative_to(ROOT))
 primary=next((f for f in paper['files'] if f['id']==paper['paper_id'] and f['kind']=='paper'),None)
 paper['reference_only']=primary is None
 if primary is None and paper['files']:
  primary=sorted(paper['files'],key=lambda f:(f['extension']!='.pdf',f['name']))[0];paper['paper_id']=primary['id']
 paper['external_word']=bool(primary and not primary.get('pages'))
 paper['ready']=bool(primary)
 paper['exam_ready']=bool(paper['ready'] and not paper['reference_only'] and not paper.get('collection') and (primary.get('exam_safe') or paper['external_word']))
path.write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({s:{'papers':sum(p['level']==s and p['ready'] for p in index['papers']),'exam_ready':sum(p['level']==s and p['exam_ready'] for p in index['papers'])} for s in ['cet4','cet6']},ensure_ascii=False))
