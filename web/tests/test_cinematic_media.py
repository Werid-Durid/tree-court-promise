"""回归用户指出的强制加速与手部—木牌相交问题。"""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'data/cinematics/phainon-wheat.json').read_text(encoding='utf-8'))
OUT=ROOT/CFG['output_dir']

@unittest.skipUnless((OUT/'audio-report.json').is_file(),'需要本地音频与 Blender 生成报告')
class CinematicMediaTests(unittest.TestCase):
 def test_every_authored_voice_keeps_original_speed(self):
  report=json.loads((OUT/'audio-report.json').read_text(encoding='utf-8'))
  self.assertTrue(report['time_compression_forbidden'])
  self.assertEqual(len(report['lines']),14);self.assertEqual(len(report['responses']),4)
  for line in report['lines']+report['responses']:self.assertEqual(line['tempo'],1.0)
  bad_line=report['lines'][10]
  self.assertGreaterEqual(bad_line['aligned_duration'],bad_line['source_duration'])
  self.assertGreaterEqual(CFG['lines'][10]['end']-CFG['lines'][10]['start'],5.1)

 def test_original_recording_for_53_second_line_is_preserved(self):
  manifest=json.loads((OUT/'audio/manifest.json').read_text(encoding='utf-8'));entry=manifest['lines'][10]
  new=OUT/'audio'/Path(entry['file']).name
  originals=json.loads((OUT/'source-audio-checksums.json').read_text(encoding='utf-8'))
  self.assertEqual(hashlib.sha256(new.read_bytes()).hexdigest(),originals['sha256'][new.name])

 def test_hand_waymark_samples_have_clearance(self):
  report=json.loads((OUT/'build-report.json').read_text(encoding='utf-8'))
  self.assertGreaterEqual(len(report['hand_prop_contacts']),30)
  self.assertTrue(all(s['penetrating_vertices']==0 for s in report['hand_prop_contacts']))
  self.assertGreater(min(s['hand_to_waymark_min_m'] for s in report['hand_prop_contacts']),.02)

if __name__=='__main__':unittest.main()
