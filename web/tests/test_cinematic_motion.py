"""从 Blender 读回报告回归植足、屈膝与发衣连续性。"""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'data/cinematics/phainon-wheat-v3.json').read_text(encoding='utf-8'))
OUT=ROOT/CFG['output_dir']

@unittest.skipUnless((OUT/'motion-readback.json').is_file(),'需要本地 Blender 工程读回报告')
class CinematicMotionTests(unittest.TestCase):
 def test_feet_remain_planted_through_descent_and_settling(self):
  report=json.loads((OUT/'motion-readback.json').read_text(encoding='utf-8'))
  self.assertLess(max(report['foot_plant_max_displacement_m'].values()),.006)
  seated=[row for row in report['pose_samples'] if row['time']>=30]
  self.assertTrue(seated)
  for row in seated:
   for value in row['knee_flexion_degrees'].values():self.assertTrue(65<value<120)

 def test_hair_and_cloth_curves_have_no_single_frame_flip(self):
  report=json.loads((OUT/'motion-continuity.json').read_text(encoding='utf-8'))
  self.assertGreater(report['bones'],20)
  self.assertLess(report['max_adjacent_frame_rotation_after_degrees'],4.7)
  self.assertLess(report['max_adjacent_frame_rotation_after_degrees'],report['max_adjacent_frame_rotation_before_degrees'])

 def test_secondary_simulation_limits_are_preserved(self):
  report=json.loads((OUT/'motion-report.json').read_text(encoding='utf-8'))
  self.assertGreater(report['secondary_bones'],20)
  self.assertLessEqual(report['max_secondary_joint_radians'],.321)
  self.assertFalse(report['full_mesh_cloth_simulation'])

 def test_all_four_responses_keep_secondary_motion_continuous(self):
  for cue in CFG['interactions']:
   for choice in cue['choices']:
    report=json.loads((OUT/'responses'/(cue['id']+'-'+choice['id'])/'motion-continuity.json').read_text(encoding='utf-8'))
    self.assertGreater(report['bones'],20)
    self.assertLess(report['max_adjacent_frame_rotation_after_degrees'],4.7)

if __name__=='__main__':unittest.main()
