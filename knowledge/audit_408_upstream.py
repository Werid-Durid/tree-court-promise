"""只读比对用户指定仓库固定归档和本地原卷，不覆盖PDF或答卷。"""
import argparse,hashlib,json,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
REPOSITORY='https://github.com/neville-studio/408-exam-paper'
def audit(archive,commit):
 if len(commit)!=40 or any(c not in '0123456789abcdef' for c in commit):raise ValueError('请提供40位固定提交SHA')
 rows=[]
 with zipfile.ZipFile(archive) as z:
  for name in z.namelist():
   relative='/'.join(name.split('/')[1:]);parts=PurePosixPath(relative)
   if name.endswith('/') or not relative.endswith('.pdf'):continue
   if parts.is_absolute() or '..' in parts.parts or len(parts.parts)!=2 or parts.parts[0] not in ('answers','papers-rebuild'):raise ValueError('未预期的原卷路径')
   raw=z.read(name);path=ROOT/'408真题'/relative;local=path.read_bytes() if path.exists() else None
   rows.append(dict(path=relative,upstream_sha256=hashlib.sha256(raw).hexdigest(),local_sha256=hashlib.sha256(local).hexdigest() if local is not None else None,matches=raw==local,exists=local is not None,bytes=len(raw)))
 expected={f'papers-rebuild/{y}.pdf' for y in range(2009,2027)}|{f'answers/{y}-answer.pdf' for y in range(2009,2027)}
 if {r['path'] for r in rows}!=expected or len(rows)!=36:raise ValueError('仓库年份或文件结构变化，需重新核对，未覆盖本地文件')
 report=dict(repository=REPOSITORY,branch='main',commit=commit,verified_on='2026-10-26',archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),files=rows)
 target=ROOT/'knowledge/build/408-upstream/comparison.json';target.parent.mkdir(parents=True,exist_ok=True);temp=target.with_suffix('.json.tmp');temp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(target)
 if not all(r['matches'] for r in rows):raise ValueError('发现版本差异；仅保存比对报告，未改原卷或索引')
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--commit',required=True);a=p.parse_args();r=audit(a.archive,a.commit);print(json.dumps(dict(files=len(r['files']),identical=True,commit=r['commit'])))
