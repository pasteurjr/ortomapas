"""Small NodeODM API contract double for retry/cancel/recovery tests only."""
from __future__ import annotations

import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.tasks: dict[str, dict] = {}
        self.create_calls = 0
        self.cancel_calls = 0
        self.fail_next = False


STATE = State()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length) if length else b""

    def do_GET(self):
        with STATE.lock:
            if self.path == "/task/list":
                return self._json(200, [{"uuid": key, **value} for key, value in STATE.tasks.items()])
            if self.path == "/_test/stats":
                return self._json(200, {"create_calls": STATE.create_calls, "cancel_calls": STATE.cancel_calls, "task_count": len(STATE.tasks)})
            if self.path.endswith("/info") and self.path.startswith("/task/"):
                task_id = self.path.split("/")[2]
                task = STATE.tasks.get(task_id)
                if task is None:
                    return self._json(404, {"error": "Task not found"})
                return self._json(200, {"uuid": task_id, "status": {"code": task["code"], "name": task["name"]}, "progress": task["progress"]})
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/_test/fail-next":
            with STATE.lock:
                STATE.fail_next = True
            self._body()
            return self._json(200, {"armed": True})
        if self.path == "/task/new":
            self._body()
            with STATE.lock:
                if STATE.fail_next:
                    STATE.fail_next = False
                    return self._json(503, {"error": "controlled contract failure"})
                STATE.create_calls += 1
                task_id = self.headers.get("set-uuid") or str(uuid.uuid4())
                STATE.tasks[task_id] = {"code": 20, "name": "Processing", "progress": 0.25}
            return self._json(201, {"uuid": task_id})
        if self.path == "/task/cancel":
            try:
                task_id = json.loads(self._body()).get("uuid")
            except Exception:
                return self._json(400, {"success": False, "error": "invalid request"})
            with STATE.lock:
                task = STATE.tasks.get(task_id)
                if task is None:
                    return self._json(404, {"success": False, "error": "Task not found"})
                task.update(code=50, name="Canceled")
                STATE.cancel_calls += 1
            return self._json(200, {"success": True})
        if self.path == "/task/remove":
            try:
                task_id = json.loads(self._body()).get("uuid")
            except Exception:
                return self._json(400, {"success": False})
            with STATE.lock:
                STATE.tasks.pop(task_id, None)
            return self._json(200, {"success": True})
        self._body()
        return self._json(404, {"error": "not found"})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 18022), Handler).serve_forever()
