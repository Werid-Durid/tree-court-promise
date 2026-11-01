"""408 原卷来源、答题卡制式、限时保存及答案隔离；全部使用临时数据库。"""
import hashlib,json,sqlite3,tempfile,time,unittest
from contextlib import closing
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI,Header,HTTPException
from fastapi.testclient import TestClient
from web.backend.exams import install_exams
ROOT=Path(__file__).resolve().parents[2]
class CS408ExamTests(unittest.TestCase):
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
 def start(self,**changes):
  body=dict(paper_id='cs408-2026',mode='exam');body.update(changes);r=self.client.post('/api/exams/sessions',json=body,headers=self.h);self.assertEqual(r.status_code,200,r.text);return r.json()
 def test_every_local_pdf_indexed_with_exact_hash_and_year(self):
  index=json.loads((ROOT/'data/exams/cs408.json').read_text(encoding='utf-8'));self.assertEqual({p['year'] for p in index['papers']},set(range(2009,2027)));seen=set()
  for p in index['papers']:
   self.assertTrue(p['exam_ready']);self.assertEqual(p['answer_schema'],dict(choice_first=1,choice_last=40,written_first=41,written_last=47))
   for f in p['files']:
    source=ROOT/'408真题'/f['path'];seen.add(source.resolve());self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),f['sha256']);self.assertEqual((ROOT/f['pdf_path']).resolve(),source.resolve())
  self.assertEqual(seen,{p.resolve() for p in (ROOT/'408真题').rglob('*.pdf')})
 def test_listing_merges_english_and_408_without_path_leak(self):
  p=self.client.get('/api/exams').json()['papers'];self.assertEqual(len([x for x in p if x['level']=='cs408']),18);self.assertTrue(any(x['level']=='cet4' for x in p));self.assertTrue(any(x['level']=='cet6' for x in p));self.assertNotIn('pdf_path',p[-1]['files'][0]);self.assertNotIn('path',p[-1]['files'][0])
 def test_all_upstream_pdfs_match_fixed_commit_without_changing_ids(self):
  audit=json.loads((ROOT/'knowledge/build/408-upstream/comparison.json').read_text(encoding='utf-8'));self.assertEqual(len(audit['files']),36);self.assertTrue(all(f['matches'] and f['upstream_sha256']==f['local_sha256'] for f in audit['files']))
  upstream={f['path']:f for f in audit['files']}
  for p in self.client.get('/api/exams').json()['papers']:
   if p['level']!='cs408':continue
   self.assertEqual(p['id'],f'cs408-{p["year"]}');self.assertEqual(p['source']['repository'],'https://github.com/neville-studio/408-exam-paper');self.assertEqual(p['source']['commit'],audit['commit']);self.assertEqual(p['source']['verification'],'sha256_identical')
   for f in p['files']:
    relative=('papers-rebuild/'+str(p['year'])+'.pdf') if f['kind']=='paper' else 'answers/'+str(p['year'])+'-answer.pdf'
    self.assertEqual(f['id'],hashlib.sha256(('cs408/'+relative).encode()).hexdigest()[:20]);self.assertEqual(f['sha256'],upstream[relative]['upstream_sha256'])
 def test_default_three_hour_deadline_and_exact_response_resume(self):
  s=self.start();self.assertAlmostEqual(s['deadline']-s['started_at'],10800);url='/api/exams/sessions/'+s['id'];answers={'1':'B','40':'D','41':'for (int i=0; i<n; ++i) { count++; }\n时间复杂度 O(n)','47':'RTT = 5ms','notes':'检查边界'}
  r=self.client.put(url,json={'answers':answers,'revision':0},headers=self.h);self.assertEqual(r.status_code,200);self.assertEqual(self.client.get(url,headers=self.h).json()['answers'],answers);self.assertEqual(self.client.get(url,headers={'Authorization':'Bearer other'}).status_code,404)
 def test_invalid_english_fields_and_multiple_choice_rejected(self):
  s=self.start();url='/api/exams/sessions/'+s['id']
  for answers in ({'48':'x'},{'writing':'essay'},{'translation':'text'},{'1':'AB'},{'2':'<script>'}):self.assertEqual(self.client.put(url,json={'answers':answers,'revision':0},headers=self.h).status_code,400)
 def test_solution_gate_page_boundaries_and_original_download(self):
  s=self.start();url='/api/exams/sessions/'+s['id'];p=next(p for p in self.client.get('/api/exams').json()['papers'] if p['id']==s['paper_id']);solution=next(f for f in p['files'] if f['kind']=='solution');original=next(f for f in p['files'] if f['kind']=='paper')
  self.assertEqual(self.client.get(url+'/page',headers=self.h).content[:2],b'\xff\xd8');self.assertEqual(self.client.get(url+f'/page?page={original["pages"]+1}',headers=self.h).status_code,404);self.assertEqual(self.client.get(url+'/page?file_id='+solution['id'],headers=self.h).status_code,403);self.assertEqual(self.client.get(url+'/download?file_id='+solution['id'],headers=self.h).status_code,403)
  self.client.put(url,json={'answers':{'1':'A'},'revision':0,'submit':True},headers=self.h);self.assertEqual(self.client.get(url+'/page?file_id='+solution['id'],headers=self.h).status_code,200)
  for f in (solution,original):self.assertEqual(hashlib.sha256(self.client.get(url+'/download?file_id='+f['id'],headers=self.h).content).hexdigest(),f['sha256'])
 def test_timeout_keeps_saved_work_and_rejects_late_edits(self):
  s=self.start(minutes=1);s.update(deadline=time.time()-1,answers={'41':'已保存的算法'})
  with closing(sqlite3.connect(Path(self.temp.name)/'exams.sqlite3')) as db:
   db.execute('UPDATE sessions SET body=? WHERE id=?',(json.dumps(s),s['id']));db.commit()
  r=self.client.put('/api/exams/sessions/'+s['id'],json={'answers':{'41':'超时修改'},'revision':0},headers=self.h).json();self.assertTrue(r['timed_out']);self.assertEqual(r['status'],'submitted');self.assertEqual(r['answers'],s['answers'])
if __name__=='__main__':unittest.main()
