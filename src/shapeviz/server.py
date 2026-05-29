"""A tiny, throwaway HTTP server for delivering the viewer to the browser.

We use Python's built-in :mod:`http.server` so there are no extra dependencies.
The server holds the generated HTML in memory and serves it on a free localhost
port. It runs in a background daemon thread so it never blocks the interpreter,
and it self-terminates after an idle timeout so we don't leak threads/ports in
long-lived sessions (e.g. notebooks).
"""

from __future__ import annotations

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional


class _ViewerHandler(BaseHTTPRequestHandler):
    html: bytes = b""
    last_request: float = 0.0

    def do_GET(self):  # noqa: N802 - http.server naming
        type(self).last_request = time.time()
        if self.path in ("/", "/index.html"):
            body = type(self).html
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/health":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):  # silence default stderr logging
        pass


class ViewerServer:
    """Serve a single HTML document on a background thread."""

    def __init__(self, html: str, host: str = "127.0.0.1", port: int = 0,
                 idle_timeout: Optional[float] = 600.0):
        handler = type("_BoundHandler", (_ViewerHandler,), {
            "html": html.encode("utf-8"),
            "last_request": time.time(),
        })
        self._handler = handler
        self._httpd = ThreadingHTTPServer((host, port), handler)
        self.host, self.port = self._httpd.server_address[0], self._httpd.server_address[1]
        self.idle_timeout = idle_timeout
        self._thread: Optional[threading.Thread] = None
        self._reaper: Optional[threading.Thread] = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"

    def start(self) -> "ViewerServer":
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        if self.idle_timeout:
            self._reaper = threading.Thread(target=self._reap, daemon=True)
            self._reaper.start()
        return self

    def _reap(self):
        # Shut down after a period with no requests, so we never hang around.
        while True:
            time.sleep(5)
            idle = time.time() - self._handler.last_request
            if idle > (self.idle_timeout or 1e18):
                self.stop()
                break

    def stop(self):
        try:
            self._httpd.shutdown()
            self._httpd.server_close()
        except Exception:  # noqa: BLE001 - best-effort teardown
            pass

    def serve_blocking(self):
        """Serve in the foreground until interrupted (used by the CLI)."""
        try:
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
