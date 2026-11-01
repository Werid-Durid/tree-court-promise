"""将指定词表接入运行时目录；旧课程及判题键只归档，不删除。"""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def build():
 path=ROOT/'data/curriculum/catalog.json';catalog=json.loads(path.read_text(encoding='utf-8'));backup=ROOT/'knowledge/build/cet4-core-vocabulary/before/catalog.json';backup.parent.mkdir(parents=True,exist_ok=True)
 if not backup.exists():shutil.copy2(path,backup)
 bank=json.loads((ROOT/'data/vocabulary/cet4-core.json').read_text(encoding='utf-8'))
 compact={'id':'cet4-core','title':bank['title'],'units':bank['units'],'source':{k:v for k,v in bank['source'].items() if k!='file'},'entries':[{k:e[k] for k in ('id','word','meaning','unit','page','review_status','accepted_spellings')}|{'continuation_pages':[r['page'] for r in e.get('continuations',[])]} for e in bank['entries']]}
 catalog.setdefault('vocabulary_banks',{})['cet4']=compact
 subject=next(s for s in catalog['subjects'] if s['id']=='cet4');subject['vocabulary_bank']='cet4-core'
 subject['description']='指定《英语四级核心词》词库 · 10个Unit；语法、听力、阅读、翻译、写作自由选学'
 for chapter in subject['chapters']:
  if chapter.get('module')=='词汇':chapter.update(archived=True,archive_note='旧版词汇剧情仅保留历史记录；四级词汇主入口改用用户指定PDF词库。')
 catalog['version']=max(catalog.get('version',1),6);write(path,catalog)
 refs_path=ROOT/'data/references/sources.json';refs=json.loads(refs_path.read_text(encoding='utf-8'))
 refs['sources']=[r for r in refs['sources'] if r['id']!='cet4-core-user-pdf']+[{'id':'cet4-core-user-pdf','title':'用户指定：英语四级核心词 · 38页PDF','status':'local_ocr_imported','note':f'导入{len(bank["entries"])}个词条，10个Unit；双栏定位与离线OCR，低置信度结果已对照原图修正，整本未逐词人工审定。'}]
 write(refs_path,refs)
 print(json.dumps({'entries':len(bank['entries']),'units':len(bank['units']),'legacy_chapters_retained':True},ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');build()
