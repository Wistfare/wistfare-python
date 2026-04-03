"""Tests for the function runner server."""

import json
import threading
import time
from http.client import HTTPConnection

from wistfare.runner.server import FunctionHandler, run_server


def test_function_handler_health():
    """Test health endpoint."""
    from http.server import HTTPServer

    def handler(ctx, **kwargs):
        return {"test": True}

    FunctionHandler.handler_fn = staticmethod(handler)
    FunctionHandler.on_start_result = None

    server = HTTPServer(("127.0.0.1", 0), FunctionHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.handle_request)
    thread.start()

    conn = HTTPConnection("127.0.0.1", port)
    conn.request("GET", "/health")
    resp = conn.getresponse()
    assert resp.status == 200
    data = json.loads(resp.read())
    assert data["status"] == "healthy"

    conn.close()
    thread.join(timeout=2)


def test_function_handler_invoke():
    """Test function invocation."""
    from http.server import HTTPServer

    def handler(ctx, **kwargs):
        return {"echo": kwargs.get("message", "")}

    FunctionHandler.handler_fn = staticmethod(handler)
    FunctionHandler.on_start_result = None

    server = HTTPServer(("127.0.0.1", 0), FunctionHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.handle_request)
    thread.start()

    conn = HTTPConnection("127.0.0.1", port)
    payload = json.dumps({"message": "hello"}).encode()
    conn.request("POST", "/", body=payload, headers={"Content-Length": str(len(payload))})
    resp = conn.getresponse()
    assert resp.status == 200
    data = json.loads(resp.read())
    assert data["result"]["echo"] == "hello"
    assert "duration_ms" in data

    conn.close()
    thread.join(timeout=2)
