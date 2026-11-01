"""六级题型课堂、来源透明、答案与原有课程保留。"""
import json,re,unittest
from pathlib import Path
from web.backend.course_exercises import evaluate
from voice.dialogue import collect_lines
ROOT=Path(__file__).resolve().parents[2];C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'));POINTS={p['id']:p for p in C['points'] if p['subject']=='cet6'}
class CET6CourseTests(unittest.TestCase):
 def test_seven_modules_and_all_public_page_titles_classified(self):
  s=next(s for s in C['subjects'] if s['id']=='cet6');self.assertEqual(s['status'],'available');self.assertEqual(len(s['chapters']),7);self.assertEqual(len(POINTS),28);self.assertEqual({pid for ch in s['chapters'] for pid in ch['points']},set(POINTS));m=json.loads((ROOT/'knowledge/cet6_series_mapping.json').read_text(encoding='utf-8'));self.assertEqual(m['returned_count'],93);self.assertEqual({p['page'] for p in m['pages']},set(range(1,94)));self.assertEqual(m['unclassified_pages'],[])
  for p in m['pages']:
   self.assertFalse(p['transcript_verified']);self.assertTrue(p['catalog_verified']);self.assertTrue(p['lesson_ids'])
   if 'Unit' in p['title']:self.assertEqual(p['coverage'],'unit_title_only_wordlist_unavailable')
 def test_existing_courses_characters_and_exam_ids_not_replaced(self):
  old=json.loads((ROOT/'knowledge/build/cet6/before/catalog.json').read_text(encoding='utf-8'));self.assertEqual([p for p in C['points'] if p['subject'] not in {'cet6','probability','postgrad'}],[p for p in old['points'] if p['subject'] not in {'cet6','probability','postgrad'}]);self.assertEqual([s for s in C['subjects'] if s['id'] not in {'cet6','probability','postgrad'}],[s for s in old['subjects'] if s['id'] not in {'cet6','probability','postgrad'}]);self.assertEqual(C['characters'],old['characters'])
 def test_each_lesson_has_explanation_worked_steps_and_exercises(self):
  for p in POINTS.values():
   self.assertEqual(set(p['course']['dialogue']),{'anaxa','hyacine','castor','phainon'});self.assertEqual(len(p['course']['stages']),3);self.assertGreater(len(p['course']['textbook'][0]['text']),70);self.assertGreaterEqual(len(p['course']['worked_example']['steps']),3);self.assertEqual(sum(c['correct'] for c in p['clues']),1)
   for exercise in p['course']['exercises']:self.assertTrue(evaluate(exercise,exercise['answer']))
 def test_distinct_wrong_answers_are_rejected(self):
  for p in POINTS.values():
   e=p['course']['exercises'][0];wrong=next(c['text'] for c in p['clues'] if not c['correct']);self.assertFalse(evaluate(e,'未作答'));self.assertFalse(evaluate(e,wrong))
  self.assertEqual(POINTS['cet6-correction']['course']['exercises'][0]['answer'],'15');self.assertEqual(POINTS['cet6-inference']['course']['exercises'][0]['answer'],'不能');self.assertEqual(POINTS['cet6-sentence-control']['course']['exercises'][0]['answer'],'gain');self.assertEqual(POINTS['cet6-revision']['course']['exercises'][0]['answer'],'spelling')
 def test_open_writing_is_self_review_with_original_reference(self):
  tasks=[p['course']['writing_task'] for p in POINTS.values() if p['course'].get('writing_task')];self.assertEqual(len(tasks),9)
  for t in tasks:
   self.assertEqual(t['grading'],'self_review_only');self.assertEqual(t['origin'],'original_practice_not_video_or_past_paper');self.assertTrue(t['reference']);self.assertEqual(len(t['rubric']),4)
   if t['kind']=='essay':self.assertTrue(150<=len(re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*",t['reference']))<=200)
 def test_listening_is_original_english_and_all_roles_enter_voice_index(self):
  lines=collect_lines(C);ids={l['id']:l for l in lines}
  for p in POINTS.values():
   for step in ('textbook','worked','practice'):self.assertIn('course-'+p['id']+'-'+step,ids)
   if p.get('listen_text'):self.assertEqual(ids['listen-'+p['id']]['language'],'English');self.assertIn('原创',p['course']['listening_origin'])
if __name__=='__main__':unittest.main()
