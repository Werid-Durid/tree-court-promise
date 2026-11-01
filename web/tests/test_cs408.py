"""验证四科连接、旧进度兼容与原创微课的交互合同。"""
import json,unittest
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
from web.backend.domain import replay
from voice.dialogue import collect_lines
ROOT=Path(__file__).resolve().parents[2]
C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'))
P=json.loads((ROOT/'data/teaching-policy.json').read_text(encoding='utf-8'))
S=next(s for s in C['subjects'] if s['id']=='cs408')
def event(kind,payload):return {'event_id':str(uuid4()),'type':kind,'at':datetime.now(timezone.utc).isoformat(),'payload':dict(payload,policy_version=2)}
# 新发布线代和六级有各自独立的目录/内容/兼容性测试；历史快照仅约束既有课程。
class CS408Tests(unittest.TestCase):
 def test_four_modules_have_complete_reachable_lessons(self):
  self.assertEqual([m['name'] for m in S['modules']],['计算机网络','计算机组成原理','操作系统','数据结构'])
  points={p['id']:p for p in C['points']};self.assertEqual(len(points),len(C['points']))
  ids=[pid for ch in S['chapters'] for pid in ch['points']]
  self.assertEqual(len(ids),216);self.assertEqual(len(set(ids)),216)
  self.assertEqual(set(ids),{p['id'] for p in C['points'] if p['subject']=='cs408'})
  for ch in S['chapters']:
   self.assertEqual(ch['points'],ch['test_points'])
   for pid in ch['points']:
    p=points[pid];self.assertEqual(p['chapter'],ch['id']);self.assertEqual(set(p['dialogue']),{'anaxa','hyacine','castor','phainon'})
    self.assertEqual(sum(c['correct'] for c in p['clues']),1)
    self.assertTrue(p['clues'][p['test']['answer']]['correct'])
    self.assertEqual(len({c['text'] for c in p['clues']}),2)
    self.assertIn(p['memoryHook'],p['feedback']['matched']);self.assertIn(p['memoryHook'],p['feedback']['redirect'])
    self.assertEqual(len(p['micro_lesson']['steps']),3)
 def test_previous_english_points_and_progress_contract_unchanged(self):
  before=json.loads((ROOT/'knowledge/build/cs408-before/catalog.json').read_text(encoding='utf-8'))
  self.assertEqual([p for p in C['points'] if p['subject'] not in {'cs408','calculus','linear','cet6','probability','postgrad'} and not p.get('vocabulary_lesson')],[p for p in before['points'] if p['subject']!='cs408'])
  self.assertEqual([{k:c[k] for k in old} for c,old in zip(C['characters'],before['characters'])],before['characters'])
 def test_cross_subject_chapter_grading_and_wrong_attempt(self):
  points={p['id']:p for p in C['points']};events=[]
  for m in S['modules']:
   ch=next(c for c in S['chapters'] if c['id']==m['chapters'][0])
   events.append(event('chapter_test',{'chapter_id':ch['id'],'answers':{pid:points[pid]['test']['answer'] for pid in ch['test_points']}}))
  s=replay(events,C,P);self.assertEqual(len(s['completed']),4)
  for tests in s['assessments'].values():self.assertEqual(tests[-1]['score'],100)
  p=points[S['chapters'][0]['points'][0]]
  after=replay(events+[event('attempt',{'point_id':p['id'],'clue_id':'boundary','response_ms':2000,'study_ms':0})],C,P)
  self.assertEqual(after['affection'],s['affection']);self.assertFalse(after['attempts'][p['id']][-1]['correct'])
 def test_sources_are_honest_and_resolve(self):
  refs=json.loads((ROOT/'data/references/sources.json').read_text(encoding='utf-8'))
  ids={r['id'] for r in refs['sources']}
  coverage=json.loads((ROOT/'knowledge/cs408_coverage.json').read_text(encoding='utf-8'))
  self.assertFalse(coverage['syllabus_full_text_verified'])
  for p in C['points']:
   if p['subject']=='cs408':self.assertTrue(set(p['source_refs'])<=ids)
 def test_all_four_dialogue_routes_are_collected_for_dubbing(self):
  lines=collect_lines(C);mapped={(r['character'],r['text']) for r in lines}
  self.assertEqual(len(lines),len({r['id'] for r in lines}))
  for p in C['points']:
   if p['subject']=='cs408':
    for cid,text in p['dialogue'].items():self.assertIn((cid,text),mapped)
 def test_computational_examples_keep_explicit_assumptions(self):
  points={p['concept']:p for p in C['points'] if p['subject']=='cs408'}
  for name,token in [('Cache 映射与地址分解','18 位'),('发送、传播、处理与排队时延','8ms'),('拥塞控制与窗口约束','2KB'),('流水线时空图与吞吐量','14 拍')]:
   p=points[name];correct=next(c['text'] for c in p['clues'] if c['correct']);self.assertIn(token,correct)
if __name__=='__main__':unittest.main()
