"""只公开模型验收页和四个派生 GLB 的本机 QA 服务。"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=self.path.split('?')[0]
        if path=='/':
            body=b'<!doctype html><html><meta charset="utf-8"><link rel="icon" href="data:,"><script type="module" src="/viewer.js"></script></html>'
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(body);return
        mapping={'/viewer.js':ROOT/'blender/repair-reports/viewer.bundle.js'}
        mapping.update({f'/models/{cid}.glb':ROOT/f'blender/generated/{cid}.glb' for cid in ('anaxa','hyacine','castor','phainon')})
        baseline=ROOT/'blender/shading-reports/baseline.json'
        if baseline.exists():
            backup=Path(json.loads(baseline.read_text(encoding='utf-8'))['backup'])
            mapping.update({f'/baseline/models/{cid}.glb':backup/f'{cid}.glb' for cid in ('anaxa','hyacine','castor','phainon')})
        file=mapping.get(path)
        if not file or not file.exists():self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type','text/javascript' if path.endswith('.js') else 'model/gltf-binary');self.send_header('Cache-Control','no-store');self.end_headers()
        try:
            with file.open('rb') as f:
                while chunk:=f.read(65536):self.wfile.write(chunk)
        except (BrokenPipeError,ConnectionResetError):pass
    def log_message(self,*args):pass
ThreadingHTTPServer(('127.0.0.1',8767),Handler).serve_forever()
