"""验证讲义课程映射、原进度兼容、迁移练习与服务端判题。"""
import copy,hashlib,json,sqlite3,tempfile,unittest
from pathlib import Path
from uuid import uuid4
from datetime import datetime,timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from web.backend.domain import initial_state,validate_and_apply,replay
from web.backend.course_exercises import evaluate
from web.backend.network_handout import install_network_handout
ROOT=Path(__file__).resolve().parents[2]
C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'));P=json.loads((ROOT/'data/teaching-policy.json').read_text(encoding='utf-8'))
NET=[p for p in C['points'] if p.get('module_id')=='net'];BY={p['id']:p for p in NET}
def event(pid,response):return {'event_id':str(uuid4()),'type':'course_attempt','at':datetime.now(timezone.utc).isoformat(),'payload':dict(policy_version=2,point_id=pid,exercise_id='transfer',response=response,response_ms=3000)}
# 新发布线代和六级有各自独立的目录/内容/兼容性测试；历史快照仅约束既有课程。
class NetworkCourseTests(unittest.TestCase):
 def test_old_ids_answers_and_unrelated_subjects_preserved(self):
  before=json.loads((ROOT/'knowledge/build/network-handout/before/catalog.json').read_text(encoding='utf-8'))
  def legacy(p):return {k:v for k,v in p.items() if k!='course' or p.get('module_id') not in {'co','os','ds'}}
  self.assertEqual([legacy(p) for p in C['points'] if p.get('module_id')!='net' and p.get('subject') not in {'calculus','linear','cet6','probability','postgrad'} and not p.get('vocabulary_lesson')],[legacy(p) for p in before['points'] if p.get('module_id')!='net'])
  old={p['id']:p for p in before['points'] if p.get('module_id')=='net'};self.assertEqual(set(old),set(BY))
  for p in NET:
   for key in ['test','clues','dialogue','feedback','micro_lesson']:self.assertEqual(p[key],old[p['id']][key])
  self.assertEqual([{k:c[k] for k in old} for c,old in zip(C['characters'],before['characters'])],before['characters'])
 def test_complete_lessons_and_honest_source_mapping(self):
  self.assertEqual(len(NET),56)
  for p in NET:
   c=p['course'];self.assertEqual(len(c['textbook']),3);self.assertEqual(len(c['worked_example']['steps']),3);self.assertEqual(len(c['exercises']),2)
   self.assertEqual([s['id'] for s in c['stages']],['textbook','worked','practice']);self.assertEqual(set(c['dialogue']),{'anaxa','hyacine','castor','phainon'})
   self.assertTrue(all(len(s['text'])>25 for s in c['textbook']))
   self.assertFalse(c['syllabus']['official_full_text_verified'])
   for lo,hi in c['source']['pages']:self.assertTrue(1<=lo<=hi<=1622)
  self.assertEqual(BY['cs408-net-network-13']['course']['source']['pages'],[])
  self.assertIn('RFC 6633',BY['cs408-net-network-09']['course']['textbook'][2]['text'])
 def test_source_hash_is_for_unchanged_original(self):
  m=json.loads((ROOT/'knowledge/network_handout_mapping.json').read_text(encoding='utf-8'))
  self.assertEqual(hashlib.sha256((ROOT/m['source']['file']).read_bytes()).hexdigest(),m['source']['sha256'])
 def test_all_canonical_answers_grade_and_invalid_choices_reject(self):
  for p in NET:
   for x in p['course']['exercises']:self.assertTrue(evaluate(x,x['answer']),p['id'])
  x=BY['cs408-net-physical-03']['course']['exercises'][0]
  self.assertTrue(evaluate(x,'１６０００'));self.assertTrue(evaluate(x,'16000 bit/s'));self.assertTrue(evaluate(x,'16000.0'));self.assertFalse(evaluate(x,'1.6e4'))
  with self.assertRaises(ValueError):evaluate(x,'')
  with self.assertRaises(ValueError):evaluate(NET[0]['course']['exercises'][1],True)
 def test_response_recomputed_no_client_correct_flag_no_penalty(self):
  s=initial_state(C);pid='cs408-net-physical-03'
  e=event(pid,'12000');e['payload']['correct']=True;validate_and_apply(s,e,C,P)
  self.assertFalse(s['course_attempts'][pid+':transfer'][-1]['correct']);self.assertNotIn(pid,s['attempts'])
  before=copy.deepcopy(s['affection']);validate_and_apply(s,event(pid,'16000'),C,P)
  self.assertTrue(s['course_attempts'][pid+':transfer'][-1]['correct']);self.assertTrue(all(s['affection'][k]>=v for k,v in before.items()))
  self.assertFalse(s['completed'])
 def test_computed_transfer_answers_match_models(self):
  answers={p['id'].removeprefix('cs408-net-'):p['course']['exercises'][0]['answer'] for p in NET}
  expected={'overview-01':(4+1)*2,'overview-02':30*8/20,'overview-03':(1000*8/8e6+200e3/2e8)*1000,'overview-04':40e6*.005,'physical-02':1000*4,'physical-03':4000*4,'link-04':2**4-1,'network-02':2**5-2,'network-07':1480/8,'transport-03':500+120,'transport-06':.875*100+.125*140,'transport-10':30000/.2}
  for key,value in expected.items():self.assertEqual(float(answers[key]),value,key)
 def test_handout_page_whitelist(self):
  app=FastAPI();install_network_handout(app,ROOT)
  with TestClient(app) as client:
   self.assertEqual(client.get('/api/network-handout/cs408-net-physical-03/page/239').status_code,200)
   self.assertEqual(client.get('/api/network-handout/cs408-net-physical-03/page/1').status_code,404)
   self.assertEqual(client.get('/api/network-handout/cs408-net-network-13/page/1').status_code,404)
if __name__=='__main__':unittest.main()
