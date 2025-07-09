#!/usr/bin/env python3
"""Micro dashboard server for DPR launcher."""
import os, signal, argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HTML_FILE = Path(__file__).with_name("status.html")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = HTML_FILE.read_text("utf‑8")
            html = (html.replace(":PORT", os.getenv("APP_PORT", ""))
                         .replace("SUBDOMAIN", os.getenv("SUBDOMAIN", ""))
                         .replace("TUNPWD", os.getenv("LT_PASSWORD", "")))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/shutdown":
            self.send_response(200); self.end_headers()
            # tell parent bash script to trigger its trap
            os.kill(os.getppid(), signal.SIGTERM)
        else:
            self.send_error(404)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860)
    httpd = HTTPServer(("0.0.0.0", parser.parse_args().port), Handler)
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass