"""Tiny JSON HTTP API using only the standard library."""
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import db, matching


def make_handler(conn):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status, body):
            data = json.dumps(body, indent=2).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = self.path.split("?")[0].rstrip("/") or "/"
            if path == "/candidates":
                rows = conn.execute("SELECT id, name, experience_years, availability FROM candidates").fetchall()
                return self._send(200, [dict(r) for r in rows])
            if path == "/jobs":
                rows = conn.execute("SELECT id, title, min_experience, tagline FROM jobs").fetchall()
                return self._send(200, [dict(r) for r in rows])
            m = re.fullmatch(r"/jobs/(\d+)/matches", path)
            if m:
                result = matching.matches_for_job(conn, int(m.group(1)))
                return self._send(404, {"error": "job not found"}) if result is None else self._send(200, result)
            m = re.fullmatch(r"/candidates/(\d+)/matches", path)
            if m:
                result = matching.matches_for_candidate(conn, int(m.group(1)))
                return self._send(404, {"error": "candidate not found"}) if result is None else self._send(200, result)
            self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path.rstrip("/") == "/seed":
                return self._send(200, db.seed(conn))
            self._send(404, {"error": "not found"})

    return Handler


def run(host="127.0.0.1", port=8000, db_path="recruiter_bot.db"):
    conn = db.connect(db_path)
    if db.is_empty(conn):
        db.seed(conn)
    print(f"Recruiter Bot listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), make_handler(conn)).serve_forever()
