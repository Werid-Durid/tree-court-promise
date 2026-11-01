"""全词库课堂覆盖、同词贡献上限、章节检测与 UE5 黑板契约。"""
import json,unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from datetime import datetime,timezone
from web.backend.domain import initial_state,validate_and_apply
from web.backend.stage import send_event
ROOT=Path(__file__).resolve().parents[2]
C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'))
P=json.loads((ROOT/'data/teaching-policy.json').read_text(encoding='utf-8'))
WORDS=C['vocabulary_banks']['cet4']['entries']
POINTS=[p for p in C['points'] if p.get('vocabulary_lesson')]
CHAPTERS=[c for s in C['subjects'] for c in s['chapters'] if c.get('vocabulary_unit')]
def event(kind,payload):return dict(event_id=str(uuid4()),type=kind,at=datetime.now(timezone.utc).isoformat(),payload=payload)
class VocabularyClassroomTests(unittest.TestCase):
 def test_every_word_is_reachable_exactly_once_with_original_meaning(self):
  self.assertEqual(len(CHAPTERS),150);self.assertEqual(len(POINTS),2327)
  self.assertEqual({p['vocabulary_lesson']['word_id'] for p in POINTS},{e['id'] for e in WORDS})
  self.assertEqual(len({p['id'] for p in POINTS}),2327)
  by={e['id']:e for e in WORDS};lookup={p['id']:p for p in POINTS}
  for ch in CHAPTERS:
   self.assertTrue(1<=len(ch['points'])<=16)
   for pid in ch['points']:
    p=lookup[pid];e=by[p['vocabulary_lesson']['word_id']]
    self.assertEqual((p['concept'],p['quick_meaning']),(e['word'],e['meaning']))
    self.assertEqual(set(p['dialogue']),{'anaxa','hyacine','castor','phainon'})
    self.assertEqual(sum(c['correct'] for c in p['clues']),1)
    self.assertEqual(p['test']['choices'][p['test']['answer']],e['meaning'])
    self.assertIn(p['memoryHook'],p['feedback']['redirect'])
 def test_classroom_and_word_card_share_daily_practice_bucket(self):
  s=initial_state(C);p=POINTS[0];wid=p['vocabulary_lesson']['word_id']
  for _ in range(P['affection']['practice_per_point_per_day']):
   validate_and_apply(s,event('vocabulary_attempt',dict(word_id=wid,mode='self_review',response='again',response_ms=3000)),C,P)
  before=s['practice_count']
  validate_and_apply(s,event('attempt',dict(point_id=p['id'],clue_id=p['clues'][0]['id'],response_ms=3000,study_ms=0)),C,P)
  self.assertEqual(s['practice_count'],before);self.assertIn(p['id'],s['attempts'])
  self.assertFalse(s['completed'])
 def test_chapter_test_uses_server_answers(self):
  s=initial_state(C);ch=CHAPTERS[-1];by={p['id']:p for p in POINTS}
  validate_and_apply(s,event('chapter_test',dict(chapter_id=ch['id'],answers={pid:by[pid]['test']['answer'] for pid in ch['test_points']})),C,P)
  self.assertEqual(s['assessments'][ch['id']][-1]['score'],100)
 def test_ue_recall_does_not_leak_meaning_and_feedback_restores_it(self):
  calls=[]
  class Response:
   def raise_for_status(self):pass
  class Client:
   def __init__(self,**kwargs):pass
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def get(self,*args,**kwargs):return Response()
   def put(self,url,json):calls.append(json);return Response()
  p=POINTS[0]
  with patch('web.backend.stage.httpx.Client',Client):
   result=send_event(dict(type='dialogue',payload=dict(point_id=p['id'],lesson_step=2)),C)
   self.assertTrue(result['executed']);self.assertNotIn(p['quick_meaning'],calls[-1]['parameters']['Value'])
   send_event(dict(type='feedback',payload=dict(point_id=p['id'],lesson_step=2)),C)
   self.assertIn(p['quick_meaning'],calls[-1]['parameters']['Value'])
