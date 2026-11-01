"""线代目录、独立小矩阵计算、判题与其他课程保留检查。"""
import copy,json,unittest
from fractions import Fraction as F
from pathlib import Path
from web.backend.course_exercises import evaluate
from voice.dialogue import collect_lines
ROOT=Path(__file__).resolve().parents[2];C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'));POINTS={p['id']:p for p in C['points'] if p['subject']=='linear'}
def det(a):
 if len(a)==1:return F(a[0][0])
 return sum(((-1)**j)*F(a[0][j])*det([row[:j]+row[j+1:] for row in a[1:]]) for j in range(len(a)))
def rank(a):
 a=[[F(v) for v in row] for row in a];r=0
 for j in range(len(a[0])):
  pivot=next((i for i in range(r,len(a)) if a[i][j]),None)
  if pivot is None:continue
  a[r],a[pivot]=a[pivot],a[r];value=a[r][j];a[r]=[x/value for x in a[r]]
  for i in range(len(a)):
   if i!=r:
    value=a[i][j];a[i]=[x-value*y for x,y in zip(a[i],a[r])]
  r+=1
  if r==len(a):break
 return r
class LinearTests(unittest.TestCase):
 def test_series_all_thirteen_videos_reachable_in_six_chapters(self):
  s=next(s for s in C['subjects'] if s['id']=='linear');m=json.loads((ROOT/'knowledge/linear_series_mapping.json').read_text(encoding='utf-8'));self.assertEqual(s['status'],'available');self.assertEqual(len(s['chapters']),6);self.assertEqual(len(POINTS),30);self.assertEqual(m['returned_count'],13);self.assertEqual(m['reported_count'],13);self.assertEqual(m['unmapped_videos'],[]);self.assertEqual({pid for ch in s['chapters'] for pid in ch['points']},set(POINTS))
  for v in m['videos']:self.assertTrue(v['lesson_ids']);self.assertFalse(v['transcript_verified'])
 def test_other_courses_and_character_profiles_unchanged(self):
  old=json.loads((ROOT/'knowledge/build/linear/before/catalog.json').read_text(encoding='utf-8'));self.assertEqual([p for p in C['points'] if p['subject'] not in {'linear','cet6','probability','postgrad'}],[p for p in old['points'] if p['subject'] not in {'linear','cet6','probability','postgrad'}]);self.assertEqual(C['characters'],old['characters']);self.assertEqual([s for s in C['subjects'] if s['id'] not in {'linear','cet6','probability','postgrad'}],[s for s in old['subjects'] if s['id'] not in {'linear','cet6','probability','postgrad'}])
 def test_exercise_answers_match_independent_small_matrix_calculations(self):
  expected={'det2':det([[1,2],[3,4]]),'permutation':sum(a>b for i,a in enumerate([2,3,1]) for b in [2,3,1][i+1:]),'row-rules':det([[1,0],[2,5]]),'cofactor':det([[3,4],[0,6]]),'triangular':det([[1,2,3],[0,4,5],[0,0,2]]),'scale-trap':4*3,'matrix-product':1*1+2*3,'inverse':-2,'elementary':-1,'rank':rank([[1,2],[2,4]]),'transpose-product':'不能','gauss':F(5+1,2),'consistency':'无穷多解','nullity':4-2,'parameter-system':1,'span':2,'independence':'相关','basis':rank([[1,0,1],[0,1,1],[0,0,0]]),'coordinates':5-2,'orthogonal':1*1+1*(-1),'eigenvalue':3,'trace-det':det([[2,0,0],[0,3,0],[0,0,4]]),'diagonalize':'能','repeated-root':2-rank([[0,1],[0,0]]),'symmetric':2+2,'quadratic-matrix':F(4,2),'complete-square':(1-1)**2+(-1)**2,'positive':det([[2,1],[1,2]]),'inertia':1,'dimension-check':6-4}
  self.assertEqual(len(expected),30)
  for slug,result in expected.items():
   e=POINTS['linear-'+slug]['course']['exercises'][0]
   with self.subTest(point=slug):self.assertTrue(evaluate(e,str(result)))
 def test_worked_examples_can_be_verified_exactly(self):
  self.assertEqual(det([[2,1],[3,4]]),5);self.assertEqual(det([[0,4],[5,6]])*(-1),20);self.assertEqual(det([[2,1,0],[0,3,4],[0,0,-1]]),-6);self.assertEqual(rank([[1,2,3],[2,4,6],[0,1,1]]),2);self.assertEqual(det([[2,1],[1,2]]),3);self.assertEqual(det([[1,2],[0,1]]),1)
 def test_each_lesson_has_four_roles_complete_stages_and_memory_hook(self):
  for p in POINTS.values():
   self.assertEqual(set(p['course']['dialogue']),{'anaxa','hyacine','castor','phainon'});self.assertEqual(len(p['course']['stages']),3);self.assertTrue(p['memoryHook']);self.assertFalse(p['course']['source']['transcript_verified']);self.assertEqual(sum(x['correct'] for x in p['clues']),1);self.assertFalse(evaluate(p['course']['exercises'][0],'这不是答案'))
 def test_all_linear_lines_enter_role_voice_index(self):
  lines=collect_lines(C);ids={line['id'] for line in lines};self.assertIn('chapter-linear-det',ids)
  for pid in POINTS:
   for step in ('textbook','worked','practice'):self.assertIn(f'course-{pid}-{step}',ids)
if __name__=='__main__':unittest.main()
