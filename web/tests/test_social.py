"""重置防回灌、邀约分支越权及重玩不刷分。"""
import json,copy,unittest,sqlite3,tempfile
from pathlib import Path
from web.backend.invitations import apply_outing
from web.backend.domain import initial_state
from voice.dialogue import collect_lines
ROOT=Path(__file__).resolve().parents[2]
C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'))
class SocialTests(unittest.TestCase):
 def test_graph_and_boundaries(self):
  for story in C['invitations']['stories']:
   nodes={n['id']:n for n in story['nodes']};seen=set();todo=[story['start']]
   while todo:
    k=todo.pop()
    if k in seen:continue
    seen.add(k);n=nodes[k];self.assertEqual(n['speaker'],story['character']);self.assertGreaterEqual(len(n['text']),40)
    for c in n['choices']:self.assertIn(c['next'],nodes);todo.append(c['next'])
   self.assertEqual(seen,set(nodes));self.assertEqual(nodes['romance']['relationship'],'romance')
 def test_choices_gated_and_no_affection_reward(self):
  s=initial_state(C);cid='castor';base=copy.deepcopy(s['affection'])
  def go(n,c):apply_outing(s,dict(character=cid,node_id=n,choice_id=c),C)
  with self.assertRaises(ValueError):go('pause','closer')
  go('arrival','object');go('object','continue');go('task','first');go('first','continue')
  with self.assertRaises(ValueError):go('pause','listen')
  with self.assertRaises(ValueError):go('pause','closer')
  go('pause','goodbye');self.assertEqual(s['outings'][cid]['endings'],['end']);self.assertEqual(s['affection'],base)
  apply_outing(s,dict(character=cid,restart=True),C);self.assertEqual(s['outings'][cid]['endings'],['end']);self.assertEqual(s['outings'][cid]['node'],'arrival')
 def test_friend_cannot_use_romance_even_with_high_affection(self):
  s=initial_state(C);s['affection']['phainon']=100;s['relationships']['phainon']='friend';s['outings']['phainon']={'node':'pause','choices':[],'endings':[]}
  with self.assertRaises(ValueError):apply_outing(s,dict(character='phainon',node_id='pause',choice_id='closer'),C)
  s['relationships']['phainon']='romance';apply_outing(s,dict(character='phainon',node_id='pause',choice_id='closer'),C);self.assertEqual(s['outings']['phainon']['node'],'romance')
 def test_new_dialogue_voice_hashes_and_character_identity(self):
  lines={x['id']:x for x in collect_lines(C)}
  for story in C['invitations']['stories']:
   for n in story['nodes']:
    x=lines[f'outing-{story["character"]}-{n["id"]}'];self.assertEqual(x['text'],n['spoken']);self.assertEqual(x['character'],story['character'])
  for c in C['characters']:
   if c['id']=='anaxa':continue
   self.assertGreaterEqual(len(c['classroom_chat']),2);self.assertTrue(all(len(t['choices'])>=2 for t in c['classroom_chat']))
if __name__=='__main__':unittest.main()
