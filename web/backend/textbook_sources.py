"""公开三本教材的课时页图；白名单不含计算机网络，不接受用户文件路径。"""
import json,sys
from functools import lru_cache
from fastapi import HTTPException,Response

def install_textbook_sources(app,root):
    manifest=json.loads((root/'knowledge/408_textbook_mapping.json').read_text(encoding='utf-8'))
    coverage=json.loads((root/'knowledge/408_textbook_coverage.json').read_text(encoding='utf-8'))
    allowed={lesson['point_id']:lesson for lesson in manifest['lessons']}
    book_ids={'wangdao2027-co','wangdao2027-os','wangdao2027-ds'}
    books={book['id']:dict(book) for book in manifest['books'] if book['id'] in book_ids}
    base=(root/'408教材').resolve()
    for book in books.values():
        source=(root/book['file']).resolve()
        if not source.is_relative_to(base) or source.suffix.lower()!='.pdf':raise ValueError('教材路径必须在指定教材目录内')
        book['path']=source

    @app.get('/api/textbooks/info')
    def info():
        # 仅返回公开映射，不暴露内部绝对路径与文件任意读取能力。
        return manifest

    @app.get('/api/textbooks/coverage')
    def syllabus_coverage():return coverage

    @lru_cache(maxsize=24)
    def rendered(book_id,page):
        sys.path.insert(0,str(root/'web/.deps'))
        import pymupdf
        source=books[book_id]['path']
        if not source.is_file():raise HTTPException(503,'原书暂不可读，请检查教材是否仍在原目录')
        with pymupdf.open(source) as pdf:
            if page>len(pdf):raise HTTPException(404,'教材无此页')
            return pdf[page-1].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False).tobytes('jpeg')

    @app.get('/api/textbook/{point_id}/page/{page}')
    def page(point_id:str,page:int):
        lesson=allowed.get(point_id)
        if not lesson or lesson['book_id'] not in books or not any(lo<=page<=hi for lo,hi in lesson['pages']):
            raise HTTPException(404,'此页不在本课教材页段中')
        return Response(rendered(lesson['book_id'],page),media_type='image/jpeg',headers={'Cache-Control':'private, max-age=3600'})
