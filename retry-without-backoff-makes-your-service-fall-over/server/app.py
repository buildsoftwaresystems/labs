import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.getenv("PORT", "8080"))
READY_AFTER_SECONDS = float(os.getenv("READY_AFTER_SECONDS", "0.5"))
FAIL_RATE = float(os.getenv("FAIL_RATE", "0.9"))
SERVER_DELAY_MS = int(os.getenv("SERVER_DELAY_MS", "25"))

state = {
    "requests": 0,
    "errors": 0,
    "started": time.time(),
    "lock": threading.Lock(),
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        with state["lock"]:
            state["requests"] += 1

        elapsed = time.time() - state["started"]
        should_fail = elapsed < READY_AFTER_SECONDS and (os.urandom(1)[0] % 100) / 100.0 < FAIL_RATE

        time.sleep(SERVER_DELAY_MS / 1000.0)

        if should_fail:
            with state["lock"]:
                state["errors"] += 1
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "data-not-ready"}).encode())
            return

        payload = {"status": "ok", "data": {"value": 42}}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"server listening on :{PORT}")
    server.serve_forever()
