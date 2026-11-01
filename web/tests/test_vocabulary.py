"""指定词库、来源图、变体拼写、旧事件兼容与新复习事件验证。"""
import copy,hashlib,json,unittest
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient
from web.backend.domain import initial_state,validate_and_apply,replay
from web.backend.vocabulary import grade,install_vocabulary
ROOT=Path(__file__).resolve().parents[2];C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'));P=json.loads((ROOT/'data/teaching-policy.json').read_text(encoding='utf-8'));B=C['vocabulary_banks']['cet4'];BY={e['word']:e for e in B['entries']}
def event(word,mode,response):return dict(event_id=str(uuid4()),type='vocabulary_attempt',at=datetime.now(timezone.utc).isoformat(),payload=dict(word_id=BY[word]['id'],mode=mode,response=response,response_ms=3000,policy_version=2))
# 新发布线代和六级有各自独立的目录/内容/兼容性测试；历史快照仅约束既有课程。
class VocabularyTests(unittest.TestCase):
 def test_bank_integrity_units_source_and_corrections(self):
  self.assertEqual(len(B['entries']),2327);self.assertEqual(len({e['id'] for e in B['entries']}),2327);self.assertEqual(len(B['units']),10)
  self.assertEqual(sum(u['count'] for u in B['units']),2327)
  self.assertEqual(len({e['word'] for e in B['entries']}),2327)
  self.assertTrue(all(e['meaning'] and 1<=e['page']<=38 for e in B['entries']))
  self.assertEqual(BY['space']['meaning'],'外层空间；太空；空间');self.assertIn('改进',BY['progress']['meaning'])
  for w in ['inquire/enquire','air conditioning','centimetre/-ter','kilometre/-ter','marvel(l)ous']:self.assertIn(w,BY)
  raw=json.loads((ROOT/'data/vocabulary/cet4-core.json').read_text(encoding='utf-8'));self.assertEqual(hashlib.sha256((ROOT/raw['source']['file']).read_bytes()).hexdigest(),raw['source']['sha256'])
 def test_old_points_keys_and_other_courses_preserved(self):
  before=json.loads((ROOT/'knowledge/build/cet4-core-vocabulary/before/catalog.json').read_text(encoding='utf-8'))
  def legacy(p):return {k:v for k,v in p.items() if k!='course' or p.get('module_id') not in {'co','os','ds'}}
  self.assertEqual([legacy(p) for p in C['points'] if p.get('subject') not in {'calculus','linear','cet6','probability','postgrad'} and not p.get('vocabulary_lesson')],[legacy(p) for p in before['points']]);self.assertEqual([{k:c[k] for k in old} for c,old in zip(C['characters'],before['characters'])],before['characters'])
  def subject(c):
   s=copy.deepcopy(next(s for s in c['subjects'] if s['id']=='cs408'))
   for ch in s['chapters']:
    if ch.get('module_id') in {'co','os','ds'}:
     for key in ['subtitle','minutes','course_format','textbook_source']:ch.pop(key,None)
   return s
  self.assertEqual(subject(C),subject(before))
  subject=next(s for s in C['subjects'] if s['id']=='cet4');self.assertTrue(all(ch['archived'] for ch in subject['chapters'] if ch['module']=='词汇'))
 def test_source_variants_and_self_review_are_not_fake_accuracy(self):
  for word,variants in [('program(me)',['program','programme']),('recognise/-ize',['recognise','recognize']),('licence/-se',['licence','license']),('centimetre/-ter',['centimetre','centimeter'])]:
   for v in variants:self.assertTrue(grade(BY[word],'spelling',v))
  self.assertTrue(grade(BY['space'],'spelling',' SPACE '));self.assertFalse(grade(BY['space'],'spelling','spaces'))
  self.assertIsNone(grade(BY['space'],'self_review','remembered'))
  with self.assertRaises(ValueError):grade(BY['space'],'self_review','correct')
 def test_server_recomputes_input_preserves_attempts_and_no_completion(self):
  s=initial_state(C);e=event('space','spelling','spaces');e['payload']['correct']=True;validate_and_apply(s,e,C,P)
  h=s['vocabulary_attempts'][BY['space']['id']];self.assertFalse(h[-1]['correct'])
  validate_and_apply(s,event('space','spelling','space'),C,P);validate_and_apply(s,event('space','self_review','remembered'),C,P)
  self.assertIsNone(s['vocabulary_attempts'][BY['space']['id']][-1]['correct']);self.assertFalse(s['completed']);self.assertFalse(s['attempts'])
 def test_original_crop_and_continuation_are_whitelisted(self):
  app=FastAPI();install_vocabulary(app,ROOT)
  with TestClient(app) as client:
   r=client.get('/api/vocabulary/cet4/source/'+BY['space']['id']);self.assertEqual(r.status_code,200);self.assertEqual(r.content[:2],b'\xff\xd8')
   self.assertEqual(client.get('/api/vocabulary/cet4/source/'+BY['progress']['id']+'?part=1').status_code,200)
   self.assertEqual(client.get('/api/vocabulary/cet4/source/'+BY['space']['id']+'?page=38').status_code,404)
   self.assertEqual(client.get('/api/vocabulary/cet4/source/'+BY['space']['id']+'?part=-1').status_code,404)
   self.assertEqual(client.get('/api/vocabulary/cet4/source/missing').status_code,404)
if __name__=='__main__':unittest.main()
