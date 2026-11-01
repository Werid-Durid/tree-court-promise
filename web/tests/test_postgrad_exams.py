"""近十年真题文件、按年制式、答卷保存和答案隔离集成验证。"""
import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI,Header,HTTPException
from fastapi.testclient import TestClient
from web.backend.exams import install_exams
ROOT=Path(__file__).resolve().parents[2]
class PostgradExamTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(dir=ROOT/'web/.runtime');app=FastAPI()
  def profile(authorization:str=Header(default='')):
   if not authorization.startswith('Bearer '):raise HTTPException(401)
   return authorization[7:]
  install_exams(app,ROOT,Path(cls.temp.name),profile);cls.app=app
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def setUp(self):self.client=TestClient(self.app);self.h={'Authorization':'Bearer '+str(uuid4())}
 def tearDown(self):self.client.close()
 def start(self,paper):
  r=self.client.post('/api/exams/sessions',headers=self.h,json=dict(paper_id=paper,mode='exam'));self.assertEqual(r.status_code,200,r.text);return r.json()
 def test_twenty_original_papers_and_both_year_ranges(self):
  papers=self.client.get('/api/exams').json()['papers'];new=[p for p in papers if p['level'] in ('math1','english1')];self.assertEqual(len(new),20)
  for level,score in [('math1',150),('english1',100)]:
   selected=[p for p in new if p['level']==level];self.assertEqual({p['year'] for p in selected},set(range(2017,2027)))
   for p in selected:self.assertTrue(p['exam_ready']);self.assertEqual(p['duration_minutes'],180);self.assertEqual(p['max_score'],score)
  self.assertEqual(len([p for p in papers if p['level']=='cs408']),18);self.assertTrue(any(p['level']=='cet4' for p in papers));self.assertTrue(any(p['level']=='cet6' for p in papers))
 def test_all_pdf_and_image_bytes_match_fixed_github_objects(self):
  build=ROOT/'knowledge/build/postgrad-exams';rows=json.loads((build/'downloads.json').read_text(encoding='utf-8'))+json.loads((build/'supplements.json').read_text(encoding='utf-8'))
  for r in rows:
   raw=(ROOT/r['local_path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256']);self.assertEqual(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),r['git_sha'])
  for year in [2023,2024,2025]:
   with zipfile.ZipFile(ROOT/f'assets/exams/postgrad/math1/{year}-question-images.zip') as z:
    self.assertEqual(len(z.namelist()),22)
    for i,name in enumerate(z.namelist(),1):self.assertTrue(name.startswith(f'Q{i:02}_'));self.assertEqual(z.read(name),(ROOT/f'assets/exams/postgrad/math1/{year}-images'/name).read_bytes())
 def test_old_and_new_math_structures_follow_original_year(self):
  papers={p['id']:p for p in self.client.get('/api/exams').json()['papers']}
  old=papers['math1-2020']['answer_schema'];new=papers['math1-2021']['answer_schema'];self.assertEqual((old['choice_last'],old['fill_first'],old['fill_last'],old['written_first'],old['written_last']),(8,9,14,15,23));self.assertEqual((new['choice_last'],new['fill_first'],new['fill_last'],new['written_first'],new['written_last']),(10,11,16,17,22))
 def test_math_numeric_proof_answers_and_limits(self):
  for year,last,proof in [(2020,23,15),(2026,22,17)]:
   s=self.start(f'math1-{year}');self.assertEqual(s['deadline']-s['started_at'],10800);url='/api/exams/sessions/'+s['id'];answers={'1':'C',str(last):'令 f(x)=x²\n分情况证明：x=0 时成立。',str(proof):'∫₀¹ x dx = 1/2'}
   r=self.client.put(url,headers=self.h,json=dict(answers=answers,revision=0));self.assertEqual(r.status_code,200);self.assertEqual(self.client.get(url,headers=self.h).json()['answers'],answers)
   for bad in ({str(last+1):'x'},{'writing':'x'},{'1':'AB'}):self.assertEqual(self.client.put(url,headers=self.h,json=dict(answers=bad,revision=1)).status_code,400)
 def test_english_has_separate_translation_and_two_essays(self):
  s=self.start('english1-2025');url='/api/exams/sessions/'+s['id'];answers={'1':'D','40':'A','41':'G','45':'F','46':'逐句译文','50':'保持否定范围','51':'Dear Sir,\nThank you.','52':'First paragraph.\nSecond paragraph.'}
  r=self.client.put(url,headers=self.h,json=dict(answers=answers,revision=0));self.assertEqual(r.status_code,200);self.assertEqual(self.client.get(url,headers=self.h).json()['answers'],answers)
  for bad in ({'53':'x'},{'41':'H'},{'translation':'x'},{'writing':'x'}):self.assertEqual(self.client.put(url,headers=self.h,json=dict(answers=bad,revision=1)).status_code,400)
 def test_original_image_page_zip_and_solution_gate(self):
  s=self.start('math1-2023');url='/api/exams/sessions/'+s['id'];paper=next(p for p in self.client.get('/api/exams').json()['papers'] if p['id']=='math1-2023');solution=next(f for f in paper['files'] if f['kind']=='solution')
  page=self.client.get(url+'/page?page=22',headers=self.h);self.assertEqual(page.status_code,200);self.assertTrue(page.content.startswith(b'\x89PNG'));self.assertEqual(self.client.get(url+'/page?page=23',headers=self.h).status_code,404)
  self.assertEqual(self.client.get(url+'/page?file_id='+solution['id'],headers=self.h).status_code,403);self.assertEqual(self.client.get(url+'/download',headers=self.h).status_code,403)
  self.client.put(url,headers=self.h,json=dict(answers={'1':'B'},revision=0,submit=True));self.assertEqual(self.client.get(url+'/page?file_id='+solution['id'],headers=self.h).status_code,200);self.assertTrue(self.client.get(url+'/download',headers=self.h).content.startswith(b'PK'))
 def test_pdf_gate_and_missing_solution_not_invented(self):
  s=self.start('english1-2024');url='/api/exams/sessions/'+s['id'];papers=self.client.get('/api/exams').json()['papers'];p=next(p for p in papers if p['id']=='english1-2024');fid=next(f['id'] for f in p['files'] if f['kind']=='solution');self.assertEqual(self.client.get(url+'/page?file_id='+fid,headers=self.h).status_code,403);self.assertTrue(self.client.get(url+'/page',headers=self.h).content.startswith(b'\xff\xd8'))
  newest=next(p for p in papers if p['id']=='english1-2026');self.assertFalse(newest['solution_available']);self.assertEqual(len(newest['files']),1);self.assertIn('尚未取得',newest['source_note'])
 def test_internal_image_paths_not_exposed_and_cross_profile_denied(self):
  papers=self.client.get('/api/exams').json()['papers']
  for p in papers:
   for f in p['files']:self.assertNotIn('image_pages',f);self.assertNotIn('pdf_path',f);self.assertNotIn('path',f)
  s=self.start('math1-2026');self.assertEqual(self.client.get('/api/exams/sessions/'+s['id'],headers={'Authorization':'Bearer other'}).status_code,404)
if __name__=='__main__':unittest.main()
