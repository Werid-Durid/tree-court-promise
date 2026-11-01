"""从固定GitHub提交下载原卷；不执行仓库脚本、不覆盖不同内容的现有文件。"""
import concurrent.futures,hashlib,json,time,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BUILD=ROOT/'knowledge/build/postgrad-exams';DEST=ROOT/'assets/exams/postgrad'
REPOS={'math-extra':('youngflysky/KaoYanZhenTi-PDF','43c9c2d7c57a8f7ec61a7848c7174c2648b074ea'),'mathonline':('fjw345/mathonline','bc8d40210cd831b56603595914ef2876876ab1ac'),'english':('Destinnnnn/kaoyan-english-1-2005-2026','90b39d12d0d801585efed6ece63662a3d3e77a0a'),'english-sol':('Gatsby666-jay/Kaoyan-English-2b-2','e559cb88cd7268171e05d779ee6a46cf0d47f94a')}
def plan():
 trees={k:json.loads((BUILD/(k+'-tree.json')).read_text(encoding='utf-8'))['tree'] for k in REPOS};jobs=[]
 def add(key,year,kind,path,level):
  node=next(f for f in trees[key] if f['path']==path);repo,commit=REPOS[key]
  jobs.append(dict(level=level,year=year,kind=kind,repository='https://github.com/'+repo,commit=commit,upstream_path=path,git_sha=node['sha'],bytes=node['size'],local_path=f'assets/exams/postgrad/{level}/{year}-{kind}.pdf',url=f'https://raw.githubusercontent.com/{repo}/{commit}/'+urllib.parse.quote(path),source_url=f'https://github.com/{repo}/blob/{commit}/'+urllib.parse.quote(path)))
 for y in range(2017,2027):
  add('english',y,'paper',f'真题/{y}年考研英语一真题.pdf','english1')
  if y<=2024:
   p=next(f['path'] for f in trees['english-sol'] if f['path'].endswith(f'{y}年考研英语一真题解析.pdf'));add('english-sol',y,'solution',p,'english1')
  if y<=2022:
   p=next(f['path'] for f in trees['math-extra'] if f['path'].startswith('数一历年真题/01.') and f['path'].endswith('/'+str(y)+'.pdf'));add('math-extra',y,'paper',p,'math1')
   p=next(f['path'] for f in trees['math-extra'] if f['path'].startswith('数一历年真题/03.') and f['path'].endswith('/'+str(y)+'解析.pdf'));add('math-extra',y,'solution',p,'math1')
  else:
   files=[f['path'] for f in trees['mathonline'] if f['path'].startswith('resource/') and '数学 (一)' in f['path'] and f['path'].endswith('.pdf')]
   if y==2026:
    add('mathonline',y,'paper',next(p for p in files if p.endswith('/26数一真题.pdf')),'math1');add('mathonline',y,'solution',next(p for p in files if p.endswith('/26数一参考答案.pdf')),'math1')
   else:add('mathonline',y,'combined',next(p for p in files if str(y) in p.split('/')[-1]),'math1')
 return jobs
def fetch(job):
 p=ROOT/job['local_path'];p.parent.mkdir(parents=True,exist_ok=True)
 raw=p.read_bytes() if p.exists() else None
 if raw is None:
  for attempt in range(3):
   try:raw=urllib.request.urlopen(urllib.request.Request(job['url'],headers={'User-Agent':'TreeCourt-exam-import'}),timeout=65).read();break
   except Exception:
    if attempt==2:raise
    time.sleep(1)
 assert raw.startswith(b'\x89PNG\r\n\x1a\n' if p.suffix=='.png' else b'%PDF-'),job['local_path']
 assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==job['git_sha'],('Git文件哈希不符',job['local_path'])
 if not p.exists():tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_bytes(raw);tmp.replace(p)
 return {**job,'sha256':hashlib.sha256(raw).hexdigest()}
if __name__=='__main__':
 jobs=plan();BUILD.mkdir(parents=True,exist_ok=True);(BUILD/'download-plan.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch,jobs))
 (BUILD/'downloads.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(files=len(results),years=list(range(2017,2027)),all_git_hashes_verified=True)))
