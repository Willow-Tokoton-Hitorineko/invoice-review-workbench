"""Loopback-only UI, with no data persistence or external services."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from workbench import load, evaluate, export_csv

PUBLIC=Path(__file__).parent/'public'
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def send(self,status,body,kind='application/json; charset=utf-8'):
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path=='/sample':
            return self.send(200,(PUBLIC.parent/'samples/synthetic.json').read_bytes())
        if self.path in ('/app.js','/app.css'):
            kind='text/javascript; charset=utf-8' if self.path.endswith('.js') else 'text/css; charset=utf-8'
            return self.send(200,(PUBLIC/self.path[1:]).read_bytes(),kind)
        if self.path=='/': return self.send(200,(PUBLIC/'index.html').read_bytes(),'text/html; charset=utf-8')
        self.send(404,b'{}')
    def do_POST(self):
        if self.path not in ('/review','/export'): return self.send(404,b'{}')
        if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.send(415,b'{}')
        origin=self.headers.get('Origin')
        allowed={f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
        if origin and origin not in allowed: return self.send(403,b'{}')
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<1 or length>200_000: return self.send(413,b'{}')
            result=evaluate(load(json.loads(self.rfile.read(length))))
            if self.path=='/export': return self.send(200,export_csv(result).encode('utf-8-sig'),'text/csv; charset=utf-8')
            self.send(200,json.dumps(result,ensure_ascii=False).encode())
        except (ValueError,KeyError,TypeError) as exc:
            self.send(400,json.dumps({'error':str(exc)}).encode())

if __name__=='__main__':
    print('Local review UI: http://127.0.0.1:8791 (Ctrl+C stops; nothing is stored)')
    ThreadingHTTPServer(('127.0.0.1',8791),Handler).serve_forever()
