"""合集完整性、数学反例、旧档案兼容和有理数判题。"""
import json,math,sqlite3,unittest
from datetime import datetime,timezone
from fractions import Fraction
from pathlib import Path
from uuid import uuid4
from web.backend.course_exercises import evaluate
from web.backend.domain import replay
from voice.dialogue import collect_lines

ROOT=Path(__file__).resolve().parents[2]
C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'))
B=json.loads((ROOT/'knowledge/build/calculus/before/catalog.json').read_text(encoding='utf-8'))
P=json.loads((ROOT/'data/teaching-policy.json').read_text(encoding='utf-8'))
M=json.loads((ROOT/'knowledge/calculus_series_mapping.json').read_text(encoding='utf-8'))
POINTS=[p for p in C['points'] if p['subject']=='calculus'];BY={p['id']:p for p in POINTS}

# 新发布线代和六级有各自独立的目录/内容/兼容性测试；历史快照仅约束既有课程。
class CalculusTests(unittest.TestCase):
 def test_series_complete_and_original_course_not_false_transcript(self):
  self.assertEqual([s['returned_count'] for s in M['series']],[26,32]);self.assertEqual(len(M['videos']),58)
  self.assertEqual(M['unmapped_videos'],[]);self.assertEqual(len(POINTS),64)
  subject=next(s for s in C['subjects'] if s['id']=='calculus')
  self.assertEqual(subject['status'],'available');self.assertEqual(len(subject['chapters']),14)
  self.assertEqual({pid for ch in subject['chapters'] for pid in ch['points']},set(BY))
  for v in M['videos']:
   self.assertTrue(v['lesson_ids'] or v.get('excluded_reason'));self.assertFalse(v['transcript_verified'])
   for pid in v['lesson_ids']:self.assertEqual(BY[pid]['course']['source']['bvid'],v['bvid'])
  self.assertEqual(M['excluded_video_count'],2)
  self.assertFalse(any('学习方法' in ch['title'] or '串讲' in ch['title'] for ch in subject['chapters']))
  self.assertNotIn('calculus-upper-learning-review',BY);self.assertNotIn('calculus-upper-learning-map',BY)
  for slug,target in [('upper-linear-ode','upper-ode'),('lower-lower-practice','lower-multiple-integrals'),('lower-lower-map','lower-multivariable')]:
   self.assertEqual(BY['calculus-'+slug]['chapter'],'calculus-'+target)
  for p in POINTS:
   co=p['course'];self.assertEqual(len(co['stages']),3);self.assertGreaterEqual(len(co['worked_example']['steps']),3)
   self.assertTrue(all(s['speaker']=='anaxa' for s in co['stages']));self.assertFalse(co['source']['transcript_verified'])
   self.assertGreater(len(co['textbook'][0]['text']),65)
   self.assertTrue(all(evaluate(x,x['answer']) for x in co['exercises']),p['id'])
   self.assertTrue(p['clues'][p['test']['answer']]['correct'])

 def test_other_subjects_and_characters_unchanged(self):
  self.assertEqual([p for p in C['points'] if p['subject'] not in {'calculus','linear','cet6','probability','postgrad'}],[p for p in B['points'] if p['subject'] not in {'calculus','linear','cet6','probability','postgrad'}])
  self.assertEqual([s for s in C['subjects'] if s['id'] not in {'calculus','linear','cet6','probability','postgrad'}],[s for s in B['subjects'] if s['id'] not in {'calculus','linear','cet6','probability','postgrad'}])
  # 新邀约给人设添加了原作约束与课堂分支，既有人物字段仍保持原值。
  self.assertEqual([{k:c[k] for k in old} for c,old in zip(C['characters'],B['characters'])],B['characters'])

 def test_counterexamples_and_numeric_results(self):
  # 无界不推出最终逃离；两条路径不同否定二元极限。
  self.assertTrue(any((n if n%2 else 0)>100 for n in range(101,110)))
  self.assertTrue(all((n if n%2 else 0)==0 for n in range(102,110,2)))
  self.assertNotEqual(0,1/2)
  answers={k:p['course']['exercises'][0]['answer'] for k,p in BY.items()}
  for key,expected in {'upper-floor':-2,'upper-derivative-definition':4,'upper-taylor-errors':Fraction(1,6),'upper-integral-geometry':Fraction(1,3),'lower-vectors':5,'lower-vector-products':5,'lower-gradient':2,'lower-double-integral':4,'lower-gauss':3,'lower-stokes':2}.items():
   self.assertEqual(Fraction(answers['calculus-'+key]),expected,key)
  self.assertEqual(math.hypot(0,3,4),5)
  self.assertEqual(3/5*2+4/5*4,22/5)
  # 通过部分和复核望远镜级数，避免把“单项趋零”当成充分条件。
  n=20;s=sum(Fraction(1,k*(k+1)) for k in range(1,n+1));self.assertEqual(s,1-Fraction(1,n+1))

 def test_rational_answers_are_exact_and_never_evaluated(self):
  e=BY['calculus-upper-taylor-errors']['course']['exercises'][0]
  for response in ['1/6','2/12','１６／９６']:self.assertTrue(evaluate(e,response))
  for response in ['1/0','0/0','0.1667','1e-1','__import__("os")','1/600']:self.assertFalse(evaluate(e,response))
  half=BY['calculus-upper-taylor']['course']['exercises'][0]
  self.assertTrue(evaluate(half,'0.5000'));self.assertTrue(evaluate(half,'2/4'))

 def test_progress_and_role_audio_contract(self):
  p=POINTS[0];e={'event_id':str(uuid4()),'type':'course_attempt','at':datetime.now(timezone.utc).isoformat(),'payload':dict(policy_version=2,point_id=p['id'],exercise_id='transfer',response='999',response_ms=3000,correct=True)}
  s=replay([e],C,P);self.assertFalse(s['course_attempts'][p['id']+':transfer'][-1]['correct']);self.assertFalse(s['completed'])
  lines={r['id']:r for r in collect_lines(C)}
  for p in POINTS:
   self.assertEqual(lines[p['id']]['character'],'anaxa');self.assertEqual(lines['hint-'+p['id']]['character'],'hyacine')
   self.assertEqual(lines['peer-'+p['id']]['character'],'castor');self.assertEqual(lines['side-phainon-'+p['id']]['character'],'phainon')
   for stage in p['course']['stages']:self.assertEqual(lines[f'course-{p["id"]}-{stage["id"]}']['text'],stage['dialogue'])

if __name__=='__main__':unittest.main()
