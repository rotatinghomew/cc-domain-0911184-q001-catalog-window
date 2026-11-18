import copy
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class CatalogState:
    def __init__(self):
        self.records = [
            {'id': 'series-a', 'revision': 1, 'title': '山间来信'},
            {'id': 'series-b', 'revision': 2, 'title': '灯火未眠'},
            {'id': 'series-c', 'revision': 1, 'title': '归途'},
        ]
        self.generation = 1
        self.windows = {}
        self.counter = 0
        self.expired = set()
        self.requests = []
        self.lock = threading.RLock()

    def request(self, path):
        parsed = urlparse(path)
        query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
        self.requests.append(query)
        region = query.get('region', 'east')
        if parsed.path == '/window':
            self.counter += 1
            token = f'window-{self.counter}'
            self.windows[token] = (self.generation, copy.deepcopy(self.records))
            return 200, {'window': token, 'region': region, 'generation': self.generation}
        if parsed.path != '/catalog':
            return 404, {'error': 'unknown endpoint'}
        token = query.get('window')
        if token in self.expired or token and token not in self.windows:
            return 410, {'error': 'window_expired'}
        generation, records = self.windows[token] if token else (self.generation, self.records)
        cursor = query.get('cursor', '')
        if token and cursor and not cursor.startswith(token + ':'):
            return 409, {'error': 'cursor_window_mismatch'}
        try:
            offset = int(cursor.rsplit(':', 1)[-1]) if cursor else 0
        except ValueError:
            return 400, {'error': 'invalid_cursor'}
        stop = offset + 2
        next_cursor = (f'{token}:{stop}' if token else str(stop)) if stop < len(records) else None
        return 200, {'region': region, 'generation': generation, 'window': token,
                     'items': records[offset:stop], 'next': next_cursor}


@contextmanager
def serve(state=None):
    state = state or CatalogState()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            with state.lock:
                status, payload = state.request(self.path)
            data = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', state
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
