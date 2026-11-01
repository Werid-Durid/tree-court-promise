"""仅备份四人派生资产，并记录不应被模型修复改动的文件哈希。"""
import hashlib
import json
import shutil
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'blender/repair-reports'
REPORT.mkdir(exist_ok=True)
backup=ROOT/'blender/model-backups'/datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d-%H%M%S')
backup.mkdir(parents=True)
for cid in ('anaxa','hyacine','castor','phainon'):
    for suffix in ('.blend','.fbx','.glb'):
        source=ROOT/f'blender/generated/{cid}{suffix}'
        shutil.copy2(source,backup/source.name)
characters=ROOT/'ue5/TreeCourt/Content/TreeCourt/Characters'
shutil.copytree(characters,backup/'ue-characters')
paths=[]
for folder in ('web/backend','web/frontend','data/curriculum','data/voice','ue5/TreeCourt/Config','ue5/TreeCourt/Content/TreeCourt/Materials'):
    paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p))
paths.extend((ROOT/'ue5/TreeCourt/Content/TreeCourt').glob('*.uasset'))
paths.extend((ROOT/'ue5/TreeCourt/Content/TreeCourt').glob('*.umap'))
paths.extend([ROOT/'data/teaching-policy.json',ROOT/'web/renderer/scene.js',ROOT/'ue5/build_classroom.py'])
guard={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(REPORT/'scope-guard.json').write_text(json.dumps({'backup':str(backup),'unchanged_files':guard},ensure_ascii=False,indent=2),encoding='utf-8')
print('Model backups:',backup)
print('Unrelated files guarded:',len(guard))
