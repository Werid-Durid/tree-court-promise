"""原卷练习与限时答题独立存储，不改动旧学习事件与好感度。"""
import io,json,sqlite3,sys,time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from fastapi import Depends,HTTPException,Response
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field

class Start(BaseModel):
    paper_id:str
    mode:str
    minutes:int|None=Field(default=None,ge=1,le=300)
class Answers(BaseModel):
    answers:dict[str,str]
    revision:int=Field(ge=0)
    submit:bool=False

def install_exams(app,root,runtime,profile):
    index=json.loads((root/'data/exams/index.json').read_text(encoding='utf-8'))
    for name in ('cs408.json','postgrad.json'):
        extra=root/'data/exams'/name
        if extra.is_file():index['papers']+=json.loads(extra.read_text(encoding='utf-8'))['papers']
    papers={p['id']:p for p in index['papers']}
    sys.path.insert(0,str(root/'web/.deps'))
    import pymupdf
    dbpath=runtime/'exams.sqlite3'
    @contextmanager
    def connect():
        db=sqlite3.connect(dbpath,timeout=15);db.row_factory=sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback();raise
        finally:db.close()
    with connect() as db:db.execute('CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, profile TEXT NOT NULL, body TEXT NOT NULL)')
    def store(db,s,pid):db.execute('INSERT OR REPLACE INTO sessions VALUES(?,?,?)',(s['id'],pid,json.dumps(s,ensure_ascii=False)))
    def load(db,sid,pid):
        row=db.execute('SELECT body FROM sessions WHERE id=? AND profile=?',(sid,pid)).fetchone()
        if not row:raise HTTPException(404,'答卷不存在')
        s=json.loads(row['body'])
        # 截止时间由服务端保存，刷新或关闭页面都不重置考试。
        if s['status']=='active' and s['deadline'] and time.time()>=s['deadline']:
            s.update(status='submitted',submitted_at=s['deadline'],timed_out=True,revision=s['revision']+1);store(db,s,pid)
        return s
    @app.get('/api/exams')
    def listing():
        return {'papers':[{k:v for k,v in p.items() if k!='files'}|{'files':[{k:v for k,v in f.items() if k not in ('path','pdf_path','image_pages')} for f in p['files']]} for p in index['papers']],'unclassified':index['unclassified'],'resources':[{k:v for k,v in f.items() if k!='path'} for f in index.get('resources',[])],'audio_available':False}
    @app.get('/api/exams/resources/{fid}')
    def resource(fid:str,pid:str=Depends(profile)):
        f=next((f for f in index.get('resources',[]) if f['id']==fid),None)
        if not f:raise HTTPException(404,'资料不存在')
        return FileResponse(root/'四六级真题'/f['path'],filename=f['name'])
    @app.get('/api/exams/sessions')
    def sessions(pid:str=Depends(profile)):
        with connect() as db:
            ids=[r['id'] for r in db.execute('SELECT id FROM sessions WHERE profile=? ORDER BY rowid DESC LIMIT 100',(pid,))]
            return {'sessions':[load(db,sid,pid) for sid in ids]}
    @app.post('/api/exams/sessions')
    def start(body:Start,pid:str=Depends(profile)):
        p=papers.get(body.paper_id)
        if not p or not p['ready']:raise HTTPException(400,'该资料暂无可展示的原卷')
        if body.mode not in ('practice','exam'):raise HTTPException(400,'未知模式')
        if body.mode=='exam' and not p['exam_ready']:raise HTTPException(400,'本卷答案页尚未可靠分离，请先使用刷题模式')
        minutes=body.minutes or p.get('duration_minutes',125)
        now=time.time();s=dict(id=str(uuid4()),paper_id=p['id'],mode=body.mode,started_at=now,deadline=now+minutes*60 if body.mode=='exam' else None,status='active',answers={},revision=0,timed_out=False)
        with connect() as db:store(db,s,pid)
        return s
    @app.get('/api/exams/sessions/{sid}')
    def get(sid:str,pid:str=Depends(profile)):
        with connect() as db:return load(db,sid,pid)
    @app.put('/api/exams/sessions/{sid}')
    def save(sid:str,body:Answers,pid:str=Depends(profile)):
        if len(body.answers)>110 or any(k not in {str(n) for n in range(1,101)}|{'writing','translation','notes'} or len(v)>15000 for k,v in body.answers.items()):raise HTTPException(400,'答题卡格式超出限制')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');s=load(db,sid,pid)
            p=papers[s['paper_id']]
            if p['level']=='cs408':
                if any(k not in {str(n) for n in range(1,48)}|{'notes'} for k in body.answers):raise HTTPException(400,'408答题卡仅支持第1–47题和草稿')
                if any(k.isdigit() and int(k)<=40 and v not in ('','A','B','C','D') for k,v in body.answers.items()):raise HTTPException(400,'408单项选择题请填写A、B、C或D')
            if p['level'] in ('math1','english1'):
                schema=p['answer_schema'];last=schema.get('written_last',schema.get('writing_last'));choice_last=schema['choice_last']
                if any(k not in {str(n) for n in range(1,last+1)}|{'notes'} for k in body.answers):raise HTTPException(400,'答题卡题号超出本卷范围')
                if any(k.isdigit() and int(k)<=choice_last and v not in ('','A','B','C','D') for k,v in body.answers.items()):raise HTTPException(400,'单项选择题请填写A、B、C或D')
                if p['level']=='english1' and any(k.isdigit() and 41<=int(k)<=45 and v not in ('','A','B','C','D','E','F','G') for k,v in body.answers.items()):raise HTTPException(400,'新题型请按原卷填写A—G')
            if s['status']!='active':return s
            if body.revision!=s['revision']:raise HTTPException(409,'另一个页面已更新答卷，请重新打开本答卷')
            s.update(answers=body.answers,revision=s['revision']+1)
            if body.submit:s.update(status='submitted',submitted_at=time.time())
            store(db,s,pid);return s
    def selected(s,file_id):
        p=papers[s['paper_id']];fid=file_id or p['paper_id'];f=next((f for f in p['files'] if f['id']==fid),None)
        if not f:raise HTTPException(404,'原文件不存在')
        if s['mode']=='exam' and s['status']=='active' and fid!=p['paper_id']:raise HTTPException(403,'交卷后才能查看配套资料')
        return p,f
    @app.get('/api/exams/sessions/{sid}/page')
    def page(sid:str,page:int=1,file_id:str='',pid:str=Depends(profile)):
        with connect() as db:s=load(db,sid,pid)
        p,f=selected(s,file_id)
        if not f.get('pdf_path') and not f.get('image_pages'):raise HTTPException(404,'本文件暂无页图，请下载原稿后在本机打开，答题卡照常保存')
        limit=f['question_pages'] if s['mode']=='exam' and s['status']=='active' else f['pages']
        if not 1<=page<=limit:raise HTTPException(404,'本页不属于当前可阅范围')
        if f.get('image_pages'):
            # 逐题原图保持原字节，索引中的路径仅由本地发布脚本生成。
            return FileResponse(root/f['image_pages'][page-1]['path'],media_type='image/png',headers={'Cache-Control':'private, no-store'})
        if not f.get('pdf_path'):raise HTTPException(404,'Word 原稿请下载后在本机打开，答题卡照常保存')
        with pymupdf.open(root/f['pdf_path']) as doc:
            clip=None
            if s['mode']=='exam' and s['status']=='active' and page==limit and f.get('question_last_clip'):
                clip=pymupdf.Rect(0,0,doc[page-1].rect.width,f['question_last_clip'])
            pix=doc[page-1].get_pixmap(matrix=pymupdf.Matrix(1.8,1.8),alpha=False,clip=clip)
            return Response(pix.tobytes('jpeg'),media_type='image/jpeg',headers={'Cache-Control':'private, no-store'})
    @app.get('/api/exams/sessions/{sid}/download')
    def download(sid:str,file_id:str='',pid:str=Depends(profile)):
        with connect() as db:s=load(db,sid,pid)
        p,f=selected(s,file_id)
        if s['mode']=='exam' and s['status']=='active' and not p.get('external_word'):raise HTTPException(403,'请先交卷，再下载原文件')
        folder='assets/exams/postgrad' if p['level'] in ('math1','english1') else '408真题' if p['level']=='cs408' else '四六级真题'
        source=root/folder/f['path']
        return FileResponse(source,filename=f['name'])
