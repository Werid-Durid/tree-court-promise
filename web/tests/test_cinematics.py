"""动画入口只读、资源白名单、成片与元数据契约。"""
import json,unittest
from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient
# 复用现有隔离档案夹；不能在 test_backend 设置临时环境前导入生产 app。
from web.tests.test_backend import app
ROOT=Path(__file__).resolve().parents[2]

class CinematicTests(unittest.TestCase):
 def test_metadata_and_read_only_viewing(self):
  with TestClient(app) as client:
   headers={'Authorization':'Bearer '+str(uuid4())}
   before=client.get('/api/user',headers=headers).json()
   response=client.get('/api/cinematics');self.assertEqual(response.status_code,200)
   film=response.json()['films'][0]
   self.assertEqual(film['character'],'phainon');self.assertEqual(film['duration_seconds'],74)
   self.assertEqual(film['revision'],json.loads((ROOT/'data/cinematics/phainon-wheat.json').read_text(encoding='utf-8'))['revision']);self.assertEqual(len(film['interactions']),2)
   self.assertEqual(sum(len(c['choices']) for c in film['interactions']),4)
   for cue in film['interactions']:
    for choice in cue['choices']:self.assertTrue(choice['clip_url'].startswith('/cinematics/phainon-wheat/'))
   self.assertIn('AI',film['disclosure']);self.assertIsInstance(film['ready'],bool)
   after=client.get('/api/user',headers=headers).json();self.assertEqual(before,after)

 def test_blender_sources_and_reference_media_are_not_served(self):
  with TestClient(app) as client:
   for asset in ['phainon_wheat_film.blend','reference.mp4','audio.wav','verification.json']:
    self.assertEqual(client.get('/cinematics/phainon-wheat/'+asset).status_code,404)

 def test_completed_assets_can_be_read_in_ranges(self):
  with TestClient(app) as client:
   film=client.get('/api/cinematics').json()['films'][0]
   if not film['ready']:self.skipTest('成片不在当前环境，媒体导出后运行此项')
   urls=[film['url'],film['download_url']]+[choice['clip_url'] for cue in film['interactions'] for choice in cue['choices']]
   for url in urls:
    response=client.get(url,headers={'Range':'bytes=0-63'})
    self.assertEqual(response.status_code,206,url);self.assertEqual(len(response.content),64)
    self.assertTrue(response.headers['content-range'].startswith('bytes 0-63/'))
    self.assertEqual(response.headers['content-type'],'video/mp4')

 def test_storyboard_is_sequential_and_original(self):
  spec=json.loads((ROOT/'data/cinematics/phainon-wheat.json').read_text(encoding='utf-8'))
  self.assertTrue(spec['original']);self.assertEqual(spec['shots'][0]['start'],0);self.assertEqual(spec['shots'][-1]['end'],74)
  for a,b in zip(spec['shots'],spec['shots'][1:]):self.assertEqual(a['end'],b['start'])
  for a,b in zip(spec['lines'],spec['lines'][1:]):self.assertLess(a['end'],b['start'])
  for line in spec['lines']:self.assertTrue(0<=line['start']<line['end']<=74)
  for cue in spec['interactions']:self.assertFalse(any(line['start']<=cue['at']<=line['end'] for line in spec['lines']))

if __name__=='__main__':unittest.main()
