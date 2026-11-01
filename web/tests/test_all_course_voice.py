"""全课程教材索引、角色路由、覆盖报告及真实缺口。"""
import json,tempfile,unittest
from pathlib import Path
from voice.dialogue import collect_lines,text_hash
from voice.course_audio import material_segments
from web.backend.voice_index import all_course_coverage,generation
ROOT=Path(__file__).resolve().parents[2]
C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'))

class AllCourseVoiceTests(unittest.TestCase):
 def test_every_published_point_and_material_has_matching_character_and_text(self):
  lines=collect_lines(C);by={x['id']:x for x in lines}
  self.assertEqual(len(by),len(lines))
  for p in C['points']:
   entry=by[p['id']]
   self.assertEqual((entry['character'],entry['text']),(p.get('speaker',p['character']),p['prompt']))
   self.assertEqual(entry['subject_id'],p['subject'])
   self.assertEqual(by['hint-'+p['id']]['character'],'hyacine')
   for stage in p.get('course',{}).get('stages',[]):
    entry=by[f'course-{p["id"]}-{stage["id"]}']
    self.assertEqual((entry['character'],entry['text']),(stage['speaker'],stage['dialogue']))
   for segment in material_segments(p):
    self.assertEqual(by[segment['id']]['text'],segment['text'])
    self.assertEqual(by[segment['id']]['character'],'anaxa')
 def test_materials_include_textbook_worked_example_and_transfer_review(self):
  p=next(p for p in C['points'] if p.get('course'))
  texts={x['text'] for x in material_segments(p)}
  for row in p['course']['textbook']:self.assertIn(row['heading']+'。'+row['text'],texts)
  self.assertIn(p['course']['worked_example']['question'],texts)
  for row in p['course']['exercises']:self.assertIn(row['explanation'],texts)
 def test_report_never_counts_plan_or_wrong_character_as_ready(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'web/.runtime') as folder:
   root=Path(folder);out=root/'data/voice/generated';out.mkdir(parents=True)
   entry=next(x for x in collect_lines(C) if x.get('subject_id')=='cs408')
   wrong={**entry,'character':'hyacine' if entry['character']!='hyacine' else 'anaxa','synthetic':True,'status':'generated','file':'data/voice/generated/test.wav'}
   (out/'test.wav').write_bytes(b'RIFF')
   (root/'data/voice/manifest.json').write_text(json.dumps({'clips':[wrong]}),encoding='utf-8')
   report=all_course_coverage(root,C)
   self.assertFalse(report['complete']);self.assertEqual(report['ready'],0)
   self.assertTrue(all(s['expected']==0 for s in report['subjects'] if s['status']=='planned'))
   net=next(s for s in report['subjects'] if s['id']=='cs408')
   self.assertEqual(set(net['modules']),{'计算机网络','计算机组成原理','操作系统','数据结构'})
 def test_global_progress_is_exposed_as_all_courses(self):
  with tempfile.TemporaryDirectory(dir=ROOT/'web/.runtime') as folder:
   root=Path(folder);out=root/'data/voice/research';out.mkdir(parents=True)
   (out/'all-course-progress.json').write_text(json.dumps(dict(status='complete',scope='all_courses',total_jobs=100,completed_jobs=100,updated_at='2026-10-22T00:00:00+00:00')),encoding='utf-8')
   self.assertEqual(generation(root)['scope'],'all_courses')
