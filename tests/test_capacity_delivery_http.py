"""Prove socket identity and complete transport for the load instrument itself."""

import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from capacity_delivery_http import SourceHTTPHandler, post


@pytest.mark.parametrize("address", ["127.0.0.2", "127.0.0.3"])
def test_capacity_client_uses_actual_bound_peer_and_consumes_whole_body(address):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            incoming = self.rfile.read(int(self.headers["Content-Length"]))
            body = json.dumps({"peer": self.client_address[0], "incoming": incoming.decode(),
                               "forwarded": self.headers.get("X-Forwarded-For"),
                               "payload": "synthetic-transport" * 65536}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "private, no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        handler = SourceHTTPHandler(address)
        client = urllib.request.build_opener(handler)
        result = post(client, f"http://127.0.0.1:{server.server_port}/", "synthetic-csrf",
                      {"purpose": "complete synthetic transport"})
        assert result.status == 200 and "no-store" in result.headers["Cache-Control"]
        body = json.loads(result.body)
        assert body["peer"] == address and handler.observed_addresses == [address]
        assert body["forwarded"] is None
        assert body["incoming"] == "purpose=complete+synthetic+transport"
        assert body["payload"] == "synthetic-transport" * 65536
        assert result.seconds == result.interval[1] - result.interval[0] > 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()
