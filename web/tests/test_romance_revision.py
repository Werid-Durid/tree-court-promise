"""邀约新旧事件兼容、首次奖励、选择回响与双端重放一致性。"""
import copy
import json
import subprocess
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from web.backend.domain import initial_state, replay, update_affection
from web.backend.invitations import apply_outing

ROOT=Path(__file__).resolve().parents[2]
C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'))
P=json.loads((ROOT/'data/teaching-policy.json').read_text(encoding='utf-8'))
PATH=[('arrival','object'),('object','continue'),('task','first'),('first','stay'),('complication','continue'),('decision','quiet'),('quiet','continue'),('pause','goodbye')]

def payload(node,choice,cid='anaxa'):
 return dict(character=cid,node_id=node,choice_id=choice,story_revision=2)

class RomanceRevisionTests(unittest.TestCase):
 def test_independent_bonds_replay_and_learning_recalculation(self):
  s=initial_state(C)
  for node,choice in PATH:apply_outing(s,payload(node,choice),C)
  self.assertEqual(s['affection'],dict(anaxa=18,hyacine=0,castor=0,phainon=0))
  self.assertEqual(s['completed'],[])
  self.assertEqual(s['study_ms'],0)
  before=copy.deepcopy(s['bond_points'])
  for _ in range(3):
   apply_outing(s,dict(character='anaxa',restart=True),C)
   for node,choice in PATH:apply_outing(s,payload('second' if node=='first' else node,'second' if node=='task' else choice),C)
  self.assertEqual(s['bond_points'],before)
  update_affection(s,P)
  self.assertEqual(s['affection']['anaxa'],18)
  self.assertIn('first',s['outings']['anaxa']['memories'])
  self.assertIn('second',s['outings']['anaxa']['memories'])

 def test_rejected_choices_do_not_award_or_unlock_memories(self):
  s=initial_state(C);before=copy.deepcopy(s)
  with self.assertRaises(ValueError):apply_outing(s,payload('decision','quiet'),C)
  self.assertEqual(s,before)
  for node,choice in PATH[:-1]:apply_outing(s,payload(node,choice),C)
  before=copy.deepcopy(s)
  for choice in ['listen','closer']:
   with self.assertRaises(ValueError):apply_outing(s,payload('pause',choice),C)
   self.assertEqual(s,before)

 def test_heart_and_different_endings_do_not_duplicate_completion_reward(self):
  s=initial_state(C);s['affection']['anaxa']=85;s['relationships']['anaxa']='romance'
  for node,choice in PATH[:-1]:apply_outing(s,payload(node,choice),C)
  apply_outing(s,payload('pause','listen'),C);apply_outing(s,payload('deep','continue'),C)
  self.assertEqual(s['bond_points']['anaxa'],21)
  apply_outing(s,dict(character='anaxa',restart=True),C)
  for node,choice in PATH[:-1]:apply_outing(s,payload(node,choice),C)
  apply_outing(s,payload('pause','closer'),C)
  self.assertEqual(s['bond_points']['anaxa'],21)
  self.assertEqual(s['outings']['anaxa']['endings'],['end','romance'])
  self.assertEqual(s['affection']['anaxa'],100)

 def test_legacy_events_keep_zero_rewards(self):
  s=initial_state(C)
  for node,choice in PATH:
   p=payload(node,choice);p.pop('story_revision');apply_outing(s,p,C)
  self.assertEqual(s['affection']['anaxa'],0)

 def test_browser_and_server_rebuild_identical_state(self):
  events=[]
  for cid in ['anaxa','hyacine','castor','phainon']:
   for node,choice in PATH:
    events.append(dict(event_id=str(uuid4()),at=datetime.now(timezone.utc).isoformat(),type='outing_choice',payload=payload(node,choice,cid)))
  events.append(dict(event_id=str(uuid4()),at=datetime.now(timezone.utc).isoformat(),type='study_tick',payload=dict(seconds=30)))
  script="""import fs from 'node:fs';import {reduceEvents} from './web/frontend/state.js';
const c=JSON.parse(fs.readFileSync('data/curriculum/catalog.json')),p=JSON.parse(fs.readFileSync('data/teaching-policy.json'));
console.log(JSON.stringify(reduceEvents(JSON.parse(fs.readFileSync(0,'utf8')),c,p)));"""
  result=subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,input=json.dumps(events),capture_output=True,text=True,check=True,encoding='utf-8')
  self.assertEqual(json.loads(result.stdout),replay(events,C,P))

if __name__=='__main__':unittest.main()
