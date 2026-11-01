"""指定 PDF 词库：原图溯源与拼写判题。"""
import json,re,unicodedata
from pathlib import Path
from fastapi import HTTPException,Response
def normalized(text):return re.sub(r'\s+','',unicodedata.normalize('NFKC',text)).lower().replace('’',"'")
def grade(entry,mode,response):
    if mode=='self_review':
        if response not in ('remembered','again'):raise ValueError('未知自评选项')
        return None
    if mode!='spelling' or not isinstance(response,str) or not 1<=len(response.strip())<=120:raise ValueError('请填写有效的单词拼写')
    return normalized(response) in {normalized(x) for x in entry.get('accepted_spellings',[entry['word']])}
def install_vocabulary(app,root):
    path=root/'data/vocabulary/cet4-core.json'
    bank=json.loads(path.read_text(encoding='utf-8'));entries={e['id']:e for e in bank['entries']}
    @app.get('/api/vocabulary/cet4/source/{entry_id}')
    def source(entry_id:str,page:int=0,full:bool=False,part:int=0):
        entry=entries.get(entry_id)
        if not entry:raise HTTPException(404,'词条不存在')
        continuations=entry.get('continuations',[])
        if part<0 or part>len(continuations):raise HTTPException(404,'释义片段不存在')
        if part:page=continuations[part-1]['page']
        pages=[entry['page']]+[r['page'] for r in continuations]
        page=page or entry['page']
        if page not in pages:raise HTTPException(404,'此页不属于该词条')
        import sys
        sys.path.insert(0,str(root/'web/.deps'))
        import pymupdf
        with pymupdf.open(root/bank['source']['file']) as pdf:
            clip=None
            if not full:
                rect=continuations[part-1]['rect'] if part else entry.get('source_rect') if page==entry['page'] else next(r['rect'] for r in continuations if r['page']==page)
                if rect:clip=pymupdf.Rect(*(v/2.5 for v in rect))
            pix=pdf[page-1].get_pixmap(matrix=pymupdf.Matrix(2,2),clip=clip,alpha=False)
            return Response(pix.tobytes('jpeg'),media_type='image/jpeg')
