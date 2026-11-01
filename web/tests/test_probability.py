"""九章概率统计、来源覆盖、独立概率计算及原有档案合同检查。"""
import json,math,unittest
from fractions import Fraction as F
from pathlib import Path
from web.backend.course_exercises import evaluate
from voice.dialogue import collect_lines
ROOT=Path(__file__).resolve().parents[2];C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'));POINTS={p['id']:p for p in C['points'] if p['subject']=='probability'}
class ProbabilityTests(unittest.TestCase):
 def test_all_teaching_pages_mapped_to_nine_free_chapters(self):
  s=next(s for s in C['subjects'] if s['id']=='probability');m=json.loads((ROOT/'knowledge/probability_series_mapping.json').read_text(encoding='utf-8'));self.assertEqual(s['status'],'available');self.assertEqual(len(s['chapters']),9);self.assertEqual(len(POINTS),48);self.assertEqual({pid for ch in s['chapters'] for pid in ch['points']},set(POINTS));self.assertEqual(m['returned_count'],73);self.assertEqual(m['unmapped_pages'],[]);self.assertEqual({v['page'] for v in m['pages']},set(range(1,74)))
  for v in m['pages']:
   self.assertTrue(v['catalog_verified']);self.assertFalse(v['transcript_verified']);self.assertTrue(v['lesson_ids'] or v.get('excluded_reason'))
  self.assertFalse(any('学习指南' in p['concept'] for p in POINTS.values()))
 def test_other_courses_and_all_character_profiles_unchanged(self):
  old=json.loads((ROOT/'knowledge/build/probability/before/catalog.json').read_text(encoding='utf-8'));self.assertEqual([p for p in C['points'] if p['subject'] not in {'probability','postgrad'}],[p for p in old['points'] if p['subject'] not in {'probability','postgrad'}]);self.assertEqual([s for s in C['subjects'] if s['id'] not in {'probability','postgrad'}],[s for s in old['subjects'] if s['id'] not in {'probability','postgrad'}]);self.assertEqual(C['characters'],old['characters'])
 def test_numeric_and_concept_answers_from_independent_formulas(self):
  expected={'sample-space':6,'event-rules':F(7,10),'classical':F(2,5),'geometric':F(1,4),'conditional':F(2,5)*F(1,2),'independent-events':'不能','bayes':F(1,2)*F(1,10)+F(1,2)*F(3,10),'cdf':1,'discrete':F(3,4),'binomial':F(math.comb(2,1),4),'geometric-wait':4,'poisson':3,'hypergeometric':F(math.comb(2,2)*math.comb(3,0),math.comb(5,2)),'density':0,'uniform':F(1,4),'exponential':F(1,4),'normal':1-F(8413,10000),'transform':1,'joint-cdf':'正无穷','joint-table':F(1,2),'marginal':2*(1-F(1,2)),'conditional-density':F(1,4),'independent-variables':'不足以','bivariate-normal':'不必然','sum-distribution':F(1,2),'extremes':1-(1-F(1,2))**2,'expectation':3*2+1,'function-expectation':3*F(2,3),'variance':4*F(1,2)*F(1,2),'chebyshev':F(4,16),'covariance':F(2,4),'uncorrelated':0,'large-numbers':F(100,400),'central-limit':F(2,20),'sample-edf':F(1,4),'sample-statistics':F(2+4,2),'sampling-laws':9,'normal-sampling':'(4,6)','moments-estimator':3,'likelihood':max([1,3,2]),'estimator-quality':'无偏','mean-interval':F(1,2),'variance-interval':F(20,5),'sample-size':4,'hypothesis':'不拒绝','mean-test':'双侧','variance-test':6-1,'two-sample':'(4,6)'}
  self.assertEqual(len(expected),48)
  for slug,result in expected.items():
   with self.subTest(slug=slug):self.assertTrue(evaluate(POINTS['probability-'+slug]['course']['exercises'][0],str(result)))
 def test_bayes_counterexample_and_statistical_boundaries(self):
  true=F(1,100)*F(9,10);false=F(99,100)*F(5,100);self.assertEqual(true/(true+false),F(2,13));self.assertEqual(F(4,100),F(1,25));self.assertEqual(F(196,100)*F(2,10),F(392,1000));self.assertEqual((5+7-2),10)
  self.assertIn('长期比例',POINTS['probability-mean-interval']['course']['textbook'][0]['text']);self.assertIn('不是H0为真的概率',POINTS['probability-hypothesis']['course']['textbook'][0]['text']);self.assertIn('联合正态',POINTS['probability-bivariate-normal']['course']['textbook'][0]['text']);self.assertIn('一般不等于1-α',POINTS['probability-hypothesis']['course']['textbook'][1]['text'])
 def test_complete_four_character_lessons_and_unambiguous_tests(self):
  for p in POINTS.values():
   self.assertEqual(set(p['course']['dialogue']),{'anaxa','hyacine','castor','phainon'});self.assertEqual(len(p['course']['stages']),3);self.assertGreaterEqual(len(p['course']['worked_example']['steps']),3);self.assertTrue(p['memoryHook']);self.assertEqual(sum(x['correct'] for x in p['clues']),1)
   for ex in p['course']['exercises']:self.assertTrue(evaluate(ex,ex['answer']))
   self.assertFalse(evaluate(p['course']['exercises'][0],'未知答案'))
 def test_voice_index_has_every_stage_with_matching_characters(self):
  lines={l['id']:l for l in collect_lines(C)}
  for p in POINTS.values():
   for step in p['course']['stages']:self.assertEqual(lines[f'course-{p["id"]}-{step["id"]}']['character'],step['speaker'])
if __name__=='__main__':unittest.main()
