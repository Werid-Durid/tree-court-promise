"""仅公开该讲义的页图与映射信息，不接受文件路径参数。"""
import json,sys
from fastapi import HTTPException,Response
def install_network_handout(app,root):
    manifest=json.loads((root/'knowledge/network_handout_mapping.json').read_text(encoding='utf-8'))
    source=root/manifest['source']['file'];allowed={x['point_id']:x for x in manifest['lessons']}
    @app.get('/api/network-handout/info')
    def info():return manifest
    @app.get('/api/network-handout/{point_id}/page/{page}')
    def page(point_id:str,page:int):
        lesson=allowed.get(point_id)
        if not lesson or not any(start<=page<=end for start,end in lesson['pages']):raise HTTPException(404,'此页不在本课讲义映射范围')
        sys.path.insert(0,str(root/'web/.deps'))
        import pymupdf
        with pymupdf.open(source) as pdf:
            pix=pdf[page-1].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False)
            return Response(pix.tobytes('jpeg'),media_type='image/jpeg',headers={'Cache-Control':'private, max-age=3600'})
