"""补入无答案数学题面原图和2025英语一答案，保留每份来源哈希。"""
import concurrent.futures,json,urllib.parse,zipfile
from fetch_postgrad_exams import ROOT,BUILD,fetch
if __name__=='__main__':
 source=json.loads((BUILD/'math-image-sources.json').read_text(encoding='utf-8'));repo=source['repository'];commit=source['commit'];jobs=[]
 for f in source['files']:
  path=f['path'];name=path.split('/')[-1];jobs.append(dict(level='math1',year=f['year'],kind='question_image',repository='https://github.com/'+repo,commit=commit,upstream_path=path,git_sha=f['sha'],bytes=f['size'],local_path=f'assets/exams/postgrad/math1/{f["year"]}-images/'+name,url=f'https://raw.githubusercontent.com/{repo}/{commit}/'+urllib.parse.quote(path),source_url=f'https://github.com/{repo}/blob/{commit}/'+urllib.parse.quote(path)))
 repo='Gatsby666-jay/Kaoyan-English-2a';commit='eaea914e59270697c03c61bae0dd6c1983350e0f';path='2025考研英语真题和答案/2025考研英语一真题及答案/2025考研英语一答案.pdf'
 jobs.append(dict(level='english1',year=2025,kind='solution',repository='https://github.com/'+repo,commit=commit,upstream_path=path,git_sha='6e7646c9b2a073e34a00dbfbfd5ed2889adb25d2',bytes=3526657,local_path='assets/exams/postgrad/english1/2025-solution.pdf',url=f'https://raw.githubusercontent.com/{repo}/{commit}/'+urllib.parse.quote(path),source_url=f'https://github.com/{repo}/blob/{commit}/'+urllib.parse.quote(path)))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch,jobs))
 (BUILD/'supplements.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 for year in [2023,2024,2025]:
  rows=sorted([r for r in results if r['year']==year and r['kind']=='question_image'],key=lambda r:r['local_path']);assert len(rows)==22
  target=ROOT/f'assets/exams/postgrad/math1/{year}-question-images.zip'
  with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED) as z:
   for r in rows:
    info=zipfile.ZipInfo(r['local_path'].split('/')[-1],date_time=(2026,10,29,0,0,0));z.writestr(info,(ROOT/r['local_path']).read_bytes())
 print(json.dumps(dict(question_images=66,english_2025_solution=True,all_git_hashes_verified=True)))
