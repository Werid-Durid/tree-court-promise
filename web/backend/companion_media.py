"""Whitelisted, read-only animation and study media for the four companions."""
import json
from fastapi import HTTPException
from fastapi.responses import FileResponse

FILMS=('phainon-wheat','anaxa-rain','hyacine-tea','castor-dusk')
PEOPLE={'anaxa':'那刻夏','hyacine':'风堇','castor':'遐蝶','phainon':'白厄'}

def install_companion_media(app,root):
 def spec_for(slug):
  if slug not in FILMS:raise HTTPException(404,'未知动画')
  return json.loads((root/'data/cinematics'/f'{slug}.json').read_text(encoding='utf-8'))
 def names_for(spec):
  names={'film.mp4':'interactive.mp4','continuous.mp4':spec.get('continuous_file','phainon-wheat-74s.mp4'),'poster.jpg':'poster.jpg' if spec['character']=='phainon' else 'poster.png'}
  names.update({q['id']+'-'+c['id']+'.mp4':q['id']+'-'+c['id']+'.mp4' for q in spec['interactions'] for c in q['choices']})
  return names
 @app.get('/api/cinematics')
 def cinematics():
  films=[]
  for slug in FILMS:
   spec=spec_for(slug);folder=root/spec['output_dir'];names=names_for(spec);verification=folder/'verification.json';report=json.loads(verification.read_text()) if verification.is_file() else {}
   complete=all((folder/n).is_file() for n in names.values())
   ready=complete and report.get('passed') is True and report.get('interactive_complete') is True and report.get('bytes')==(folder/names['continuous.mp4']).stat().st_size
   version='?v='+str(spec.get('media_revision',spec.get('revision',1)));base='/cinematics/'+slug+'/'
   cues=[{**q,'choices':[{**c,'clip_url':base+q['id']+'-'+c['id']+'.mp4'+version} for c in q['choices']]} for q in spec['interactions']]
   films.append(dict(id=spec['id'],revision=spec.get('revision',1),character=spec['character'],character_name=PEOPLE[spec['character']],title=spec['title'],description=spec['description'],duration_seconds=spec['duration'],ready=ready,url=base+'film.mp4'+version,download_url=base+'continuous.mp4'+version,poster=base+'poster.jpg'+version,interactions=cues,lines=spec['lines'],quiet_label=spec.get('quiet_label','麦田里的晚风'),silence=spec.get('silence','他没有催你。风吹过麦穗，你们仍坐在彼此看得见的地方。'),disclosure='树庭原创剧情 · 角色参考音色 AI 二创配音，非官方录音。'))
  return {'films':films}
 @app.get('/cinematics/{slug}/{asset}')
 def cinematic_asset(slug:str,asset:str):
  spec=spec_for(slug);names=names_for(spec)
  if asset not in names:raise HTTPException(404,'未知动画资源')
  path=root/spec['output_dir']/names[asset]
  if not path.is_file():raise HTTPException(404,'动画尚未生成')
  return FileResponse(path,media_type='video/mp4' if asset.endswith('.mp4') else ('image/png' if path.suffix=='.png' else 'image/jpeg'))
 @app.get('/api/study-companions')
 def study_companions():
  people=[]
  for cid,name in PEOPLE.items():
   folder=root/'blender/build/study-companions'/cid;check=folder/'verification.json';report=json.loads(check.read_text()) if check.is_file() else {}
   version=report.get('media_revision',1)
   people.append(dict(id=cid,name=name,ready=report.get('passed') is True and (folder/'loop.mp4').is_file(),url=f'/study-media/{cid}/loop.mp4?v={version}',poster=f'/study-media/{cid}/poster.png?v={version}'))
  return {'companions':people}
 @app.get('/study-media/{cid}/{asset}')
 def study_asset(cid:str,asset:str):
  if cid not in PEOPLE or asset not in ('loop.mp4','poster.png'):raise HTTPException(404,'未知自习室资源')
  path=root/'blender/build/study-companions'/cid/asset
  if not path.is_file():raise HTTPException(404,'自习室动画尚未生成')
  return FileResponse(path,media_type='video/mp4' if asset.endswith('.mp4') else 'image/png')
