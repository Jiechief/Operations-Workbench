# -*- coding: utf-8 -*-
"""本地服务器：静态文件 + /proxy 外部 API 转发（绕过浏览器跨域限制）。

用法：py server.py [端口]，默认 8000，仅监听 127.0.0.1。
页面调用外部大模型接口时改为请求同源 /proxy，由本脚本转发，避免浏览器 CORS 拦截。
"""
import json
import os
import sys
import traceback
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

os.chdir(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
              "te", "trailers", "transfer-encoding", "upgrade", "host",
              "content-length", "accept-encoding", "origin", "referer"}


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/proxy":
            self.send_error(404, "Not Found")
            return
        target = unquote(parsed.query)
        if not target:
            self.send_error(400, "missing target url in query")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        body = self.rfile.read(length) if length > 0 else None
        req = urllib.request.Request(target, data=body, method="POST")
        for key, value in self.headers.items():
            if key.lower() not in HOP_BY_HOP:
                req.add_header(key, value)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
                status = resp.status
                ctype = resp.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as e:
            data = e.read()
            status = e.code
            ctype = e.headers.get("Content-Type", "application/json")
        except Exception as e:  # 网络错误等
            payload = json.dumps({"error": str(e)}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        try:
            with open("server_err.log", "a", encoding="utf-8") as f:
                f.write(traceback.format_exc())
        except Exception:
            pass


if __name__ == "__main__":
    server = Server(("127.0.0.1", PORT), Handler)
    print("Serving HTTP on 127.0.0.1 port %d (http://127.0.0.1:%d/)" % (PORT, PORT))
    print("proxy enabled: POST /proxy?<external-url>")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
