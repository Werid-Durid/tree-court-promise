"""为四人构建物理版角色：导入 PHYSICS -> build_rig -> 保存到 blender/physics/。"""
import bpy
import json
import sys
import time
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

MODELS = {'anaxa': '那刻夏', 'hyacine': '风堇', 'castor': '遐蝶', 'phainon': '白厄'}
reports = []
for cid, label in MODELS.items():
    start = time.time()
    try:
        candidates = [p for p in ROOT.glob('星穹铁道*/**/*.pmx') if label in p.name and '变身' not in str(p)]
        source = min(candidates, key=lambda p: len(str(p)))
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.ops.mmd_tools.import_model(filepath=str(source), scale=0.08,
                                       types={'MESH', 'ARMATURE', 'MORPHS', 'PHYSICS'})
        root = next(o for o in bpy.data.objects if getattr(o, 'mmd_type', None) == 'ROOT')
        bpy.ops.object.select_all(action='DESELECT')
        root.select_set(True)
        bpy.context.view_layer.objects.active = root
        bpy.ops.mmd_tools.build_rig()
        arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
        info = {
            'id': cid, 'status': 'built', 'source': str(source),
            'rigid_bodies': sum(1 for o in bpy.data.objects if getattr(o, 'rigid_body', None)),
            'joints': sum(1 for o in bpy.data.objects if getattr(o, 'rigid_body_constraint', None)),
            'bones': len(arm.data.bones),
            'elapsed': round(time.time() - start, 1),
        }
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f'{cid}.blend'))
        reports.append(info)
        print('PHYSICS_BUILT ' + json.dumps(info, ensure_ascii=False), flush=True)
    except Exception as exc:
        reports.append({'id': cid, 'status': 'error', 'error': str(exc)})
        print('PHYSICS_ERROR ' + cid + ' ' + str(exc), flush=True)

(OUT / 'report.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf-8')
print('PHYSICS_DONE', len([r for r in reports if r.get('status') == 'built']), '/', len(MODELS))
