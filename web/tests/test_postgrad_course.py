"""考研英语：来源边界、独立语法答案、四人课堂与原课程保留。"""
import json,unittest
from pathlib import Path
from web.backend.course_exercises import evaluate
from voice.dialogue import collect_lines
ROOT=Path(__file__).resolve().parents[2];C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'));POINTS={p['id']:p for p in C['points'] if p['subject']=='postgrad'}
class PostgradTests(unittest.TestCase):
 def test_six_modules_thirty_two_lessons(self):
  s=next(s for s in C['subjects'] if s['id']=='postgrad');self.assertEqual(s['status'],'available');self.assertEqual(len(s['chapters']),6);self.assertEqual(len(POINTS),32);self.assertEqual({i for ch in s['chapters'] for i in ch['points']},set(POINTS))
 def test_source_metadata_does_not_invent_generic_lesson_topics(self):
  m=json.loads((ROOT/'knowledge/postgrad_series_mapping.json').read_text(encoding='utf-8'));self.assertEqual(m['returned_count'],41);self.assertEqual(len(m['unconfirmed_content_pages']),29)
  keywords=[v for v in m['pages'] if v['coverage']=='keyword_title_verified_original_lesson'];self.assertEqual(len(keywords),11)
  for v in m['pages']:
   self.assertTrue(v['catalog_verified']);self.assertFalse(v['transcript_verified'])
   if v['page'] in m['unconfirmed_content_pages']:self.assertEqual(v['lesson_ids'],[])
  for p in POINTS.values():
   source=p['course']['source'];self.assertFalse(source['transcript_verified'])
   if source['video_pages']:self.assertEqual(len(source['video_pages']),1)
   else:self.assertEqual(source['lesson_origin'],'original_prerequisite_supplement')
 def test_all_other_courses_and_profiles_unchanged(self):
  old=json.loads((ROOT/'knowledge/build/postgrad/before/catalog.json').read_text(encoding='utf-8'));self.assertEqual([p for p in C['points'] if p['subject']!='postgrad'],[p for p in old['points'] if p['subject']!='postgrad']);self.assertEqual([s for s in C['subjects'] if s['id']!='postgrad'],[s for s in old['subjects'] if s['id']!='postgrad']);self.assertEqual(C['characters'],old['characters'])
 def test_independent_grammar_and_vocabulary_oracles(self):
  answers={'scare':'scared','previous':'previous','advance':'advanced','desirable':'desirable','expand':'expand','tense':'tense','relate':'related','fantasy':'fantasy','cognitive':'cognitive','confirm':'confirmation','appearance':'appearance','word-context':'生效','predicate':'belongs','agreement':'has','voice':'are','coordination':'不是','relative':'主语','noun-clause':'what','adverbial':'下雨','appositive':'宾语','infinitive':'seeing','participles':'broken','gerund':'helping','attachment':'不能','past-present':'有','past-perfect':'had','modality':'可能有帮助','subjunctive':'过去','bracketing':'is','negation':'不一定为真','reference':'books','translation':'可能性'}
  self.assertEqual(len(answers),32)
  for slug,answer in answers.items():
   with self.subTest(slug=slug):self.assertTrue(evaluate(POINTS['postgrad-'+slug]['course']['exercises'][0],answer));self.assertFalse(evaluate(POINTS['postgrad-'+slug]['course']['exercises'][0],'未知答案'))
 def test_complete_explanations_four_roles_and_voice_index(self):
  lines={x['id']:x for x in collect_lines(C)}
  for p in POINTS.values():
   self.assertEqual(set(p['course']['dialogue']),{'anaxa','hyacine','castor','phainon'});self.assertGreater(len(p['course']['textbook'][0]['text']),70);self.assertEqual(len(p['course']['worked_example']['steps']),3);self.assertEqual(len(p['course']['stages']),3);self.assertEqual(sum(x['correct'] for x in p['clues']),1)
   for ex in p['course']['exercises']:self.assertTrue(evaluate(ex,ex['answer']))
   for stage in p['course']['stages']:self.assertEqual(lines[f'course-{p["id"]}-{stage["id"]}']['character'],'anaxa')
 def test_important_logical_boundaries(self):
  self.assertIn('不能',POINTS['postgrad-negation']['course']['worked_example']['steps'][-1]['text']);self.assertIn('导致',POINTS['postgrad-relate']['course']['textbook'][1]['text']);self.assertIn('与现在事实相反',POINTS['postgrad-subjunctive']['course']['textbook'][0]['text']);self.assertEqual(POINTS['postgrad-translation']['course']['exercises'][0]['answer'],'可能性')
if __name__=='__main__':unittest.main()
