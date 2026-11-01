"""肤色校准前备份派生资产，记录场景和学习功能的基线。"""
import hashlib,json,shutil
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'blender/shading-reports'
OUT.mkdir(exist_ok=True)
backup=ROOT/'blender/model-backups'/('shading-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True)
for cid in ('anaxa','hyacine','castor','phainon'):
    for ext in ('.blend','.glb','.fbx'):
        shutil.copy2(ROOT/f'blender/generated/{cid}{ext}',backup/f'{cid}{ext}')
shutil.copytree(ROOT/'ue5/TreeCourt/Content/TreeCourt/Characters',backup/'ue-characters')
paths=[]
for folder in ('web/frontend','web/backend','data','ue5/TreeCourt/Config','ue5/TreeCourt/Content/TreeCourt/Materials'):
    paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p))
paths.extend((ROOT/'ue5/TreeCourt/Content/TreeCourt').glob('*.umap'))
paths.extend((ROOT/'ue5/TreeCourt/Content/TreeCourt').glob('*.uasset'))
paths.extend([ROOT/'web/renderer/scene.js'])
for p in (ROOT/'web/renderer/scene.js',ROOT/'web/frontend/scene.bundle.js'):
    shutil.copy2(p,backup/p.name)
(OUT/'baseline.json').write_text(json.dumps({'backup':str(backup),'hashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}},ensure_ascii=False,indent=2),encoding='utf-8')
print(backup)
