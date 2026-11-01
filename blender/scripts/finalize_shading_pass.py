"""最后检查修改范围和 UE 四人结果，保留原课堂的实际游戏截图。"""
import json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'blender/shading-reports'
baseline=json.loads((OUT/'baseline.json').read_text(encoding='utf-8'))
allowed={'web/renderer/scene.js','web/frontend/scene.bundle.js'}
changed=[p for p,h in baseline['hashes'].items() if p not in allowed and hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
# 正在运行的网站会写自己的学习数据库；不可回滚用户的实时存档。
runtime=[p for p in changed if p.startswith('data/runtime/')]
unexpected=[p for p in changed if p not in runtime]
assert not unexpected,unexpected
native=json.loads((OUT/'ue-style.json').read_text(encoding='utf-8'))
assert native['status']=='styled' and len(native['characters'])==4
assert json.loads((OUT/'verification.json').read_text(encoding='utf-8'))['passed']
assert json.loads((ROOT/'blender/repair-reports/styled/browser-errors.json').read_text())==[]
shots=ROOT/'ue5/TreeCourt/Saved/Screenshots/WindowsEditor'
latest=max(shots.glob('HighresScreenshot*.png'),key=lambda p:p.stat().st_mtime)
assert latest.name!='HighresScreenshot00004.png','需要当前 UE 截图'
shutil.copy2(latest,OUT/'ue-classroom.png')
(OUT/'final-check.json').write_text(json.dumps({'passed':True,'ue_characters':4,'browser_shader_errors':[],
  'unrelated_changes':unexpected,'live_runtime_files_excluded':runtime,'source_ue_screenshot':str(latest),'original_map_unchanged':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('FINAL_SHADING_CHECK_PASSED')
