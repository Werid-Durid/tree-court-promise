"""验证 MMD 物理导入：带 PHYSICS 导入 Anaxa，统计刚体/关节/动态骨，保存物理版副本。"""
import bpy
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'blender/physics'
OUT.mkdir(parents=True, exist_ok=True)
VENDOR = ROOT / 'blender/vendor'
ADDON = VENDOR / 'mmd_tools'
ZIP = Path('D:/Blender插件/01_插件_addons/mmd_tools-v4.5.13-bl4.2.zip')
if not ADDON.exists():
    ADDON.mkdir(parents=True)
    with zipfile.ZipFile(ZIP) as archive:
        for item in archive.infolist():
            target = (ADDON / item.filename).resolve()
            if not target.is_relative_to(ADDON.resolve()):
                raise RuntimeError('插件压缩包路径越界')
            archive.extract(item, ADDON)
sys.path.insert(0, str(VENDOR))
LIBS = VENDOR / 'pythonlibs'
LIBS.mkdir(exist_ok=True)
for wheel in (ADDON / 'wheels').glob('*.whl'):
    with zipfile.ZipFile(wheel) as archive:
        for item in archive.infolist():
            if not (LIBS / item.filename).resolve().is_relative_to(LIBS.resolve()):
                raise RuntimeError('依赖压缩包路径越界')
            archive.extract(item, LIBS)
sys.path.insert(0, str(LIBS))
import mmd_tools  # noqa: E402
mmd_tools.register()

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

LABEL = '那刻夏'
candidates = [p for p in ROOT.glob('星穹铁道*/**/*.pmx') if LABEL in p.name and '变身' not in str(p)]
source = min(candidates, key=lambda p: len(str(p)))
print('SOURCE', source, flush=True)
bpy.ops.mmd_tools.import_model(filepath=str(source), scale=0.08,
                               types={'MESH', 'ARMATURE', 'MORPHS', 'PHYSICS'})
print('IMPORTED', flush=True)

objs = list(bpy.data.objects)
arm = next(o for o in objs if o.type == 'ARMATURE')
rigid = [o for o in objs if getattr(o, 'rigid_body', None)]
joints = [o for o in objs if getattr(o, 'rigid_body_constraint', None)]
collections = sorted({c.name for o in objs for c in o.users_collection})

info = {
    'objects': len(objs),
    'armatures': [o.name for o in objs if o.type == 'ARMATURE'],
    'rigid_bodies': len(rigid),
    'joints': len(joints),
    'collections': collections,
    'bones': len(arm.data.bones),
    'has_rigidbody_world': bpy.context.scene.rigidbody_world is not None,
}
print('PHYSICS_IMPORT ' + json.dumps(info, ensure_ascii=False), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'anaxa.blend'))
print('SAVED', OUT / 'anaxa.blend', flush=True)
