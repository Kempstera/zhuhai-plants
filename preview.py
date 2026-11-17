#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地预览服务器：模拟 Cloudflare Pages 的无后缀 URL 行为。

    python3 preview.py [port]     # 默认 8765
"""
import http.server
import os
import socketserver
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def translate_path(self, path):
        p = super().translate_path(path)
        # /atlas -> /atlas.html ; /species/x -> /species/x.html
        if not os.path.exists(p):
            if os.path.isfile(p + ".html"):
                return p + ".html"
            if os.path.isdir(p) and os.path.isfile(os.path.join(p, "index.html")):
                return os.path.join(p, "index.html")
        if os.path.isdir(p) and os.path.isfile(os.path.join(p, "index.html")):
            return os.path.join(p, "index.html")
        return p

    def log_message(self, fmt, *args):
        sys.stderr.write("%s\n" % (fmt % args))


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"serving dist/ at http://127.0.0.1:{PORT}")
        httpd.serve_forever()
