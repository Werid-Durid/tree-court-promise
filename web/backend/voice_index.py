"""按角色和台词哈希精确解析录音，避免每次朗读传输整本音频清单。"""
import json,re
from pathlib import Path
from fastapi import HTTPException

_cache={}
def manifest(root):
    path=root/'data/voice/manifest.json'
    if not path.exists():return {'clips':[]}
    stat=path.stat();key=(str(path.resolve()),stat.st_mtime_ns,stat.st_size)
    if key not in _cache:
        data=json.loads(path.read_text(encoding='utf-8'))
        _cache.clear();_cache[key]=data
    return _cache[key]

def generation(root):
    paths=[root/'data/voice/research'/name for name in ('vocabulary-progress.json','all-course-progress.json')]
    paths=[path for path in paths if path.exists()]
    if not paths:return {'status':'not_started'}
    path=max(paths,key=lambda p:p.stat().st_mtime_ns)
    data=json.loads(path.read_text(encoding='utf-8'))
    result={k:data.get(k) for k in ('status','total_jobs','completed_jobs','updated_at','scope')}
    # 心跳停止时不继续向页面宣称正在生成；已完成音频仍然可用。
    from datetime import datetime,timezone
    if result['status'] in ('running','starting'):
        try:
            if (datetime.now(timezone.utc)-datetime.fromisoformat(result['updated_at'])).total_seconds()>1800:result['status']='interrupted'
        except (ValueError,TypeError):result['status']='interrupted'
    return result

def all_course_coverage(root,catalog):
    from voice.dialogue import collect_lines
    lines=collect_lines(catalog);clips={x['id']:x for x in manifest(root).get('clips',[])}
    subjects={s['id']:dict(id=s['id'],name=s['name'],status=s['status'],expected=0,ready=0,modules={}) for s in catalog['subjects']}
    total=0
    for line in lines:
        entry=clips.get(line['id'],{})
        ready=bool(entry.get('synthetic') and entry.get('status')=='generated' and entry.get('character')==line['character'] and entry.get('text_sha256')==line['text_sha256'] and (root/entry.get('file','missing')).is_file())
        total+=ready
        subject=subjects.get(line.get('subject_id'))
        if subject:
            subject['expected']+=1;subject['ready']+=ready
            module=subject['modules'].setdefault(line.get('module','未分板块'),dict(expected=0,ready=0))
            module['expected']+=1;module['ready']+=ready
    return dict(expected=len(lines),ready=total,subjects=list(subjects.values()),generation=generation(root),complete=total==len(lines))

def vocabulary_coverage(root,catalog):
    from voice.dialogue import collect_lines
    lines=[x for x in collect_lines(catalog) if x['id'].startswith(('pronounce-cet4core-','chapter-cet4-core-class-')) or 'class-cet4core-' in x['id']]
    clips={x['id']:x for x in manifest(root).get('clips',[])}
    counts={'pronunciations':{'expected':0,'ready':0},'dialogue':{'expected':0,'ready':0}}
    for line in lines:
        group=counts['pronunciations' if line['id'].startswith('pronounce-') else 'dialogue'];group['expected']+=1
        entry=clips.get(line['id'],{})
        if entry.get('status')=='generated' and entry.get('synthetic') and entry.get('character')==line['character'] and entry.get('text_sha256')==line['text_sha256'] and (root/entry.get('file','missing')).is_file():group['ready']+=1
    return {**counts,'generation':generation(root)}

def resolve(root,character,sha):
    if character not in ('anaxa','hyacine','castor','phainon') or not re.fullmatch('[a-f0-9]{64}',sha):
        raise HTTPException(400,'角色或台词指纹无效')
    folder=(root/'data/voice/generated').resolve()
    for clip in manifest(root).get('clips',[]):
        if clip.get('character')!=character or clip.get('text_sha256')!=sha or not clip.get('synthetic') or clip.get('status')!='generated':continue
        path=(root/clip.get('file','missing')).resolve()
        if path.is_relative_to(folder) and path.is_file() and re.fullmatch(r'/voice/[A-Za-z0-9_-]+\.(wav|mp3)',clip.get('url','')):
            return {'ready':True,'clip':clip}
    return {'ready':False,'generating':generation(root).get('status') in ('running','starting')}
