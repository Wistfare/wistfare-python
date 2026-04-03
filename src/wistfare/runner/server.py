"""HTTP server that runs inside function containers."""

from __future__ import annotations
import json
import os
import signal
import sys
import time
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable


class FunctionHandler(BaseHTTPRequestHandler):
    handler_fn: Callable = None
    on_start_result: Any = None

    def do_POST(self):
        if self.path == "/":
            self._handle_invoke()
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == "/health":
            self._handle_health()
        else:
            self.send_error(404)

    def _handle_invoke(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            payload = {}

        start = time.time()
        try:
            from wistfare.context import Context
            ctx = Context(
                on_start_result=self.on_start_result,
                function_id=os.environ.get("WISTFARE_FUNCTION_ID", ""),
                invocation_id=self.headers.get("X-Invocation-ID", ""),
                container_id=os.environ.get("WISTFARE_CONTAINER_ID", ""),
            )
            result = self.handler_fn(ctx, **payload)
            duration_ms = int((time.time() - start) * 1000)

            response = json.dumps({
                "result": result,
                "duration_ms": duration_ms,
            }).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            error_response = json.dumps({
                "error": str(e),
                "traceback": traceback.format_exc(),
                "duration_ms": duration_ms,
            }).encode()

            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_response)))
            self.end_headers()
            self.wfile.write(error_response)

    def _handle_health(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        response = b'{"status":"healthy"}'
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        pass  # Suppress default logging.


def run_server(handler_fn: Callable, on_start_fn: Callable | None = None, port: int = 8080):
    """Start the function runner HTTP server."""
    # Run on_start hook.
    on_start_result = None
    if on_start_fn:
        print(f"Running on_start hook...")
        from wistfare.context import Context
        ctx = Context(function_id=os.environ.get("WISTFARE_FUNCTION_ID", ""))
        on_start_result = on_start_fn(ctx)
        print(f"on_start complete.")

    FunctionHandler.handler_fn = staticmethod(handler_fn)
    FunctionHandler.on_start_result = on_start_result

    server = HTTPServer(("0.0.0.0", port), FunctionHandler)

    def shutdown(sig, frame):
        print("Shutting down...")
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    print(f"Function server listening on :{port}")
    server.serve_forever()
