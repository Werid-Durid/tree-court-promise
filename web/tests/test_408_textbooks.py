"""检查教材覆盖、源页白名单、旧记录兼容和可复算题目，而非只数生成字段。"""
import copy,json,sys,unittest
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient
from web.backend.textbook_sources import install_textbook_sources
from web.backend.course_exercises import evaluate
from web.backend.domain import replay
from voice.course_audio import material_segments

ROOT=Path(__file__).resolve().parents[2]
C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'))
B=json.loads((ROOT/'knowledge/build/408-textbooks/before/catalog.json').read_text(encoding='utf-8'))
M=json.loads((ROOT/'knowledge/408_textbook_mapping.json').read_text(encoding='utf-8'))
V=json.loads((ROOT/'knowledge/408_textbook_coverage.json').read_text(encoding='utf-8'))
P=json.loads((ROOT/'data/teaching-policy.json').read_text(encoding='utf-8'))
TARGET=[p for p in C['points'] if p.get('module_id') in {'co','os','ds'}]
BY={p['id']:p for p in TARGET}

# 新发布线代和六级有各自独立的目录/内容/兼容性测试；历史快照仅约束既有课程。
class TextbookTests(unittest.TestCase):
 def test_network_and_all_legacy_contracts_preserved(self):
  self.assertEqual([p for p in C['points'] if p.get('subject') not in {'calculus','linear','cet6','probability','postgrad'} and p.get('module_id') not in {'co','os','ds'}],[p for p in B['points'] if p.get('module_id') not in {'co','os','ds'}])
  old={p['id']:p for p in B['points']}
  for p in TARGET:
   self.assertEqual({k:v for k,v in p.items() if k!='course'},{k:v for k,v in old[p['id']].items() if k!='course'})
  self.assertEqual([{k:c[k] for k in old} for c,old in zip(C['characters'],B['characters'])],B['characters'])
  cs=lambda c:next(s for s in c['subjects'] if s['id']=='cs408')
  for new,old in zip(cs(C)['chapters'],cs(B)['chapters']):
   self.assertEqual(new['id'],old['id']);self.assertEqual(new['points'],old['points']);self.assertEqual(new['test_points'],old['test_points'])

 def test_all_textbook_modules_reachable_and_syllabus_atoms_taught(self):
  self.assertEqual(len(TARGET),160);self.assertEqual(len(M['lessons']),160)
  self.assertEqual(len({i['id'] for i in V['items']}),280);self.assertEqual(V['unmapped_items'],[])
  self.assertFalse(V['official_full_text_verified']);self.assertFalse(V['network_read'])
  for atom in V['items']:
   p=BY[atom['point_id']];self.assertIn(atom['topic'],p['course']['syllabus']['items'])
  for p in TARGET:
   c=p['course'];self.assertGreater(sum(len(s['text']) for s in c['textbook']),140)
   self.assertNotEqual(c['textbook'][1]['text'],p['summary'])
   self.assertGreaterEqual(len(c['worked_example']['steps']),3)
   self.assertEqual([s['id'] for s in c['stages']],['textbook','worked','practice'])
   self.assertEqual(set(c['dialogue']),{'anaxa','hyacine','castor','phainon'})
   self.assertTrue(all(s['speaker']=='anaxa' for s in c['stages']))
   self.assertTrue(all(len(s['dialogue'])>20 for s in c['stages']))
   self.assertTrue(all(evaluate(x,x['answer']) for x in c['exercises']))
   self.assertNotEqual(c['exercises'][0]['question'],c['worked_example']['question'])
   self.assertTrue(any(seg['text'].endswith(c['textbook'][1]['text']) for seg in material_segments(p)))

 def test_topic_gaps_are_explanations_not_only_index_labels(self):
  expected={'co-memory-08':['段表','段内页号'],'co-memory-09':['旋转','块擦除'],'co-arithmetic-05':['Q0','01','10'],'os-process-01':['代码区','堆','栈'],'os-io-01':['socket','非阻塞'],'ds-trees-01':['孩子兄弟','森林中序'],'ds-search-06':['借','合并','叶层'],'ds-sort-09':['败者树','置换选择','虚段']}
  for key,terms in expected.items():
   text=''.join(r['text'] for r in BY['cs408-'+key]['course']['textbook'])
   for term in terms:self.assertIn(term,text,key)

 def test_numeric_transfer_answers_recompute(self):
  expected={'co-overview-04':10**9*2/(2*10**9),'co-memory-03':4*2,'co-memory-05':4096/(64*2),'co-memory-07':2+.05*80,'co-pipeline-01':5+12-1,'os-memory-01':10000+320,'os-files-03':1024/4,'os-files-06':8192/8,'os-virtual-05':100+.001*1000000,'ds-graphs-01':18/2,'ds-trees-06':5+10,'ds-sort-09':2}
  for key,value in expected.items():self.assertEqual(float(BY['cs408-'+key]['course']['exercises'][0]['answer']),value)
  self.assertFalse(evaluate(BY['cs408-co-memory-03']['course']['exercises'][0],'4'))
  self.assertTrue(evaluate(BY['cs408-co-overview-01']['course']['exercises'][0],'程序计数器'))

 def test_source_bounds_and_network_exclusion(self):
  self.assertEqual({b['module_id'] for b in M['books']},{'co','os','ds'})
  app=FastAPI();install_textbook_sources(app,ROOT)
  with TestClient(app) as client:
   self.assertTrue(all('path' not in b for b in client.get('/api/textbooks/info').json()['books']))
   for pid,page in [('cs408-co-overview-01',15),('cs408-os-overview-01',14),('cs408-ds-basics-01',14)]:
    r=client.get(f'/api/textbook/{pid}/page/{page}');self.assertEqual(r.status_code,200);self.assertEqual(r.headers['content-type'],'image/jpeg');self.assertTrue(r.content.startswith(b'\xff\xd8'))
   for pid,page in [('cs408-co-overview-01',1),('cs408-co-overview-01',351),('cs408-net-overview-01',14),('unknown',14)]:
    self.assertEqual(client.get(f'/api/textbook/{pid}/page/{page}').status_code,404)
   self.assertEqual(client.get('/api/textbooks/coverage').json()['mapped_syllabus_items'],280)

 def test_old_events_replay_same_state_and_new_transfer_server_grades(self):
  pid=TARGET[0]['id'];old=next(p for p in B['points'] if p['id']==pid)
  event=lambda kind,payload:{'event_id':str(uuid4()),'type':kind,'at':datetime.now(timezone.utc).isoformat(),'payload':dict(policy_version=2,**payload)}
  events=[event('attempt',dict(point_id=pid,clue_id=next(x['id'] for x in old['clues'] if x['correct']),response_ms=3000,study_ms=0))]
  self.assertEqual(replay(events,B,P),replay(events,C,P))
  events.append(event('course_attempt',dict(point_id=pid,exercise_id='transfer',response='not a PC',response_ms=3000,correct=True)))
  s=replay(events,C,P);self.assertFalse(s['course_attempts'][pid+':transfer'][-1]['correct'])

if __name__=='__main__':unittest.main()
