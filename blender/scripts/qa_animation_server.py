from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=self.path.split('?')[0]
        if path=='/':
            body=b'<!doctype html><meta charset="utf-8"><link rel="icon" href="data:,"><script type="module" src="/viewer.js"></script>'
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(body);return
        files={'/viewer.js':ROOT/'blender/animation-reports/viewer.bundle.js'}
        for cid in ('anaxa','hyacine','castor','phainon'):
            files[f'/models/{cid}.glb']=ROOT/f'blender/animated/{cid}.glb'
            files[f'/report/{cid}.json']=ROOT/f'blender/animation-reports/{cid}.json'
        file=files.get(path)
        if not file or not file.exists():self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type','application/javascript' if path.endswith('.js') else 'application/json' if path.endswith('.json') else 'model/gltf-binary');self.send_header('Cache-Control','no-store');self.end_headers()
        try:
            with file.open('rb') as f:
                while chunk:=f.read(65536):self.wfile.write(chunk)
        except (BrokenPipeError,ConnectionResetError):pass
    def log_message(self,*args):pass
ThreadingHTTPServer(('127.0.0.1',8769),Handler).serve_forever()
