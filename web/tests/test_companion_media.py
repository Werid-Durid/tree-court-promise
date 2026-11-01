import json,unittest
from pathlib import Path
from fastapi.testclient import TestClient
from web.tests.test_backend import app
ROOT=Path(__file__).resolve().parents[2]
class CompanionMediaTests(unittest.TestCase):
 def test_all_four_have_distinct_appropriate_films(self):
  with TestClient(app) as c:
   films=c.get('/api/cinematics').json()['films']
   self.assertEqual({f['character'] for f in films},{'anaxa','hyacine','castor','phainon'})
   self.assertEqual(len({f['title'] for f in films}),4)
   for f in films:
    self.assertTrue(f['character_name']);self.assertEqual(len(f['interactions']),2)
    for cue in f['interactions']:
     self.assertEqual(len(cue['choices']),2)
     self.assertFalse(any(line['start']<=cue['at']<=line['end'] for line in f['lines']))
 def test_study_lists_exactly_four_single_companion_assets(self):
  with TestClient(app) as c:
   people=c.get('/api/study-companions').json()['companions']
   self.assertEqual(len(people),4)
   self.assertEqual({p['id'] for p in people},{'anaxa','hyacine','castor','phainon'})
   for p in people:self.assertIn('/'+p['id']+'/',p['url'])
 def test_whitelist_rejects_sources_and_unknown_characters(self):
  with TestClient(app) as c:
   for url in ['/study-media/anaxa/anaxa_study.blend','/study-media/unknown/loop.mp4','/cinematics/anaxa-rain/anaxa_outing.blend','/cinematics/unknown/film.mp4']:
    self.assertEqual(c.get(url).status_code,404,url)
 def test_completed_new_media_can_be_read_with_ranges(self):
  with TestClient(app) as c:
   urls=[p['url'] for p in c.get('/api/study-companions').json()['companions'] if p['ready']]
   for film in c.get('/api/cinematics').json()['films']:
    if film['ready']:
     urls.extend([film['url'],film['download_url']]);urls.extend(x['clip_url'] for q in film['interactions'] for x in q['choices'])
   self.assertTrue(urls)
   for url in urls:
    response=c.get(url,headers={'Range':'bytes=0-63'});self.assertEqual(response.status_code,206,url);self.assertEqual(len(response.content),64)
