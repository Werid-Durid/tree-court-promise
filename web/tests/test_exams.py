"""原卷内容、持久化、考试时限和解析权限的集成验证。"""
import hashlib,json,sqlite3,tempfile,time,unittest
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI,Header,HTTPException
from fastapi.testclient import TestClient
from web.backend.exams import install_exams
ROOT=Path(__file__).resolve().parents[2]
class ExamTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'web/.runtime');cls.app=FastAPI()
  def profile(authorization:str=Header(default='')):
   if not authorization.startswith('Bearer '):raise HTTPException(401)
   return authorization[7:]
  install_exams(cls.app,ROOT,Path(cls.temp.name),profile)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def setUp(self):self.client=TestClient(self.app);self.h={'Authorization':'Bearer '+str(uuid4())}
 def tearDown(self):self.client.close()
 def start(self,mode='exam',paper='cet6-2024-06-1'):
  r=self.client.post('/api/exams/sessions',json={'paper_id':paper,'mode':mode,'minutes':1},headers=self.h);self.assertEqual(r.status_code,200,r.text);return r.json()
 def test_manifest_covers_every_original_and_preserves_hash(self):
  i=json.loads((ROOT/'data/exams/index.json').read_text(encoding='utf-8'));seen=set()
  for p in i['papers']:
   for f in p['files']:
    source=ROOT/'四六级真题'/f['path'];seen.add(source.resolve());self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),f['sha256'])
  seen.update((ROOT/'四六级真题'/r['path']).resolve() for r in i['resources'])
  self.assertEqual(seen,{p.resolve() for p in (ROOT/'四六级真题').rglob('*') if p.is_file()})
 def test_chinese_volume_number_matches_question_form(self):
  from knowledge.index_exam_papers import metadata
  self.assertEqual(metadata('2014年12月英语四级真题答案及解析（卷三）.pdf'),('cet4',2014,12,3))
  i=json.loads((ROOT/'data/exams/index.json').read_text(encoding='utf-8'))
  for p in i['papers']:
   for f in p['files']:
    meta=metadata(f['name'])
    if meta:self.assertEqual(meta,(p['level'],p['year'],p['month'],p['form']))
 def test_save_resume_conflict_and_profile_isolation(self):
  s=self.start();url='/api/exams/sessions/'+s['id'];body={'answers':{'1':'B','writing':'My exact essay'},'revision':0}
  saved=self.client.put(url,json=body,headers=self.h).json();self.assertEqual(saved['revision'],1)
  self.assertEqual(self.client.get(url,headers=self.h).json()['answers'],body['answers'])
  self.assertEqual(self.client.put(url,json=body,headers=self.h).status_code,409)
  self.assertEqual(self.client.get(url,headers={'Authorization':'Bearer someone-else'}).status_code,404)
  self.assertEqual(self.client.get(url+'/page',headers={'Authorization':'Bearer someone-else'}).status_code,404)
 def test_original_page_and_review_gate(self):
  s=self.start();url='/api/exams/sessions/'+s['id'];i=self.client.get('/api/exams').json();p=next(p for p in i['papers'] if p['id']==s['paper_id']);solution=next(f for f in p['files'] if f['kind']=='solution' and f.get('pages'))
  r=self.client.get(url+'/page',headers=self.h);self.assertEqual(r.status_code,200);self.assertEqual(r.content[:2],b'\xff\xd8')
  self.assertEqual(self.client.get(url+'/page?file_id='+solution['id'],headers=self.h).status_code,403)
  self.assertEqual(self.client.get(url+'/download',headers=self.h).status_code,403)
  self.client.put(url,json={'answers':{'1':'A'},'revision':0,'submit':True},headers=self.h)
  self.assertEqual(self.client.get(url+'/page?file_id='+solution['id'],headers=self.h).status_code,200)
  source=self.client.get(url+'/download',headers=self.h)
  self.assertEqual(hashlib.sha256(source.content).hexdigest(),next(f for f in p['files'] if f['id']==p['paper_id'])['sha256'])
 def test_deadline_enforced_after_refresh_and_does_not_accept_late_changes(self):
  s=self.start();url='/api/exams/sessions/'+s['id']
  with sqlite3.connect(Path(self.temp.name)/'exams.sqlite3') as db:
   s.update(deadline=time.time()-1,answers={'1':'B'});db.execute('UPDATE sessions SET body=? WHERE id=?',(json.dumps(s),s['id']))
  r=self.client.put(url,json={'answers':{'1':'D'},'revision':0},headers=self.h).json()
  self.assertEqual(r['status'],'submitted');self.assertTrue(r['timed_out']);self.assertEqual(r['answers'],{'1':'B'})
 def test_invalid_answer_and_unknown_asset_rejected(self):
  s=self.start();url='/api/exams/sessions/'+s['id']
  self.assertEqual(self.client.put(url,json={'answers':{'101':'A'},'revision':0},headers=self.h).status_code,400)
  self.assertEqual(self.client.get(url+'/page?file_id=../../characters/profiles.json',headers=self.h).status_code,404)
  self.assertEqual(self.client.get('/api/exams/resources/unknown',headers=self.h).status_code,404)
 def test_word_original_is_available_without_fabricated_pages(self):
  s=self.start('practice','cet4-2007-06-1');url='/api/exams/sessions/'+s['id']
  self.assertEqual(self.client.get(url+'/download',headers=self.h).status_code,200)
  self.assertEqual(self.client.get(url+'/page',headers=self.h).status_code,404)
 def test_mixed_answer_page_is_clipped_and_collection_is_not_a_single_exam(self):
  s=self.start('exam','cet4-2013-06-3');url='/api/exams/sessions/'+s['id']
  r=self.client.get(url+'/page?page=13',headers=self.h);self.assertEqual(r.status_code,200)
  import pymupdf
  pix=pymupdf.Pixmap(r.content);self.assertLess(pix.height,400)
  self.assertEqual(self.client.get(url+'/page?page=14',headers=self.h).status_code,404)
  r=self.client.post('/api/exams/sessions',json={'paper_id':'cet6-1990-00-0','mode':'exam','minutes':125},headers=self.h)
  self.assertEqual(r.status_code,400)
if __name__=='__main__':unittest.main()
