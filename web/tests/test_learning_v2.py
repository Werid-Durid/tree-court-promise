"""不依赖生产存档的规则验证，包括前后端重放一致性。"""
import json, subprocess, unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from web.backend.domain import initial_state, validate_and_apply, replay
ROOT=Path(__file__).resolve().parents[2]
C=json.loads((ROOT/'data/curriculum/catalog.json').read_text(encoding='utf-8'))
P=json.loads((ROOT/'data/teaching-policy.json').read_text(encoding='utf-8'))
def event(kind,p):
    return dict(event_id=str(uuid4()),at=datetime.now(timezone.utc).isoformat(),type=kind,payload={**p,'policy_version':2})
def assessment(ch,correct=True):
    points={p['id']:p for p in C['points']}
    return event('chapter_test',{'chapter_id':ch['id'],'answers':{pid:points[pid]['test']['answer'] if correct else 1-points[pid]['test']['answer'] for pid in ch['test_points']}})
class LearningTests(unittest.TestCase):
    def test_free_chapter_server_grades_and_best_score(self):
        ch=C['subjects'][0]['chapters'][-1]
        events=[assessment(ch),assessment(ch,False),assessment(ch)]
        s=replay(events,C,P)
        self.assertEqual(s['completed'],[ch['id']])
        self.assertEqual(s['affection_breakdown'],dict(tests=10,practice=0,time=0))
        self.assertEqual([x['score'] for x in s['assessments'][ch['id']]],[100,0,100])
        invalid=assessment(ch);invalid['payload']['answers'].pop(ch['test_points'][0])
        with self.assertRaises(ValueError): validate_and_apply(s,invalid,C,P)
        invalid=assessment(ch);invalid['payload']['answers'][ch['test_points'][0]]=True
        with self.assertRaises(ValueError): validate_and_apply(s,invalid,C,P)
    def test_practice_speed_daily_cap_and_no_wrong_penalty(self):
        p=C['points'][0]
        def a(ms): return event('attempt',{'point_id':p['id'],'clue_id':next(c['id'] for c in p['clues'] if not c['correct']),'response_ms':ms,'study_ms':0})
        s=replay([a(100) for _ in range(8)]+[a(2000) for _ in range(8)],C,P)
        self.assertEqual(s['practice_count'],3)
        self.assertEqual(s['study_ms'],0)
        self.assertEqual(s['affection']['anaxa'],0)
    def test_time_and_legacy_relationship_preserved(self):
        e=event('relationship',{'character':'anaxa','choice':'friend'});del e['payload']['policy_version']
        s=replay([e,event('focus_session',{'seconds':900,'interruptions':1})],C,P)
        self.assertEqual(s['relationships']['anaxa'],'friend')
        self.assertEqual(s['affection_breakdown']['time'],1)
        with self.assertRaises(ValueError):validate_and_apply(initial_state(C),e,C,P)
    def test_browser_server_replay_match(self):
        events=[assessment(ch) for ch in C['subjects'][0]['chapters']]
        events += [event('focus_session',{'seconds':14400,'interruptions':2}),event('study_tick',{'seconds':60})]
        for p in C['points'][:15]:
            events.append(event('attempt',{'point_id':p['id'],'clue_id':p['clues'][0]['id'],'response_ms':2000,'study_ms':0}))
        expected=replay(events,C,P)
        script="import {reduceEvents} from './web/frontend/state.js';let t='';for await(const c of process.stdin)t+=c;const x=JSON.parse(t);process.stdout.write(JSON.stringify(reduceEvents(x.e,x.c,x.p)));"
        actual=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],input=json.dumps(dict(e=events,c=C,p=P)).encode(),cwd=ROOT))
        self.assertEqual(actual,expected)
        self.assertEqual(expected['affection_breakdown'],dict(tests=60,practice=3,time=16))
if __name__=='__main__':unittest.main()
