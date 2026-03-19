#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSL HTTP Server for MuseumAgent Demo
支持SSL的HTTP服务器，用于Demo项目的HTTPS访问
"""

import http.server
import socketserver
import ssl
import argparse
import os

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 设置默认目录为当前目录
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def end_headers(self):
        # 添加CORS头，允许跨域请求
        self.send_header('Access-Control-Allow-Origin', '*')
        # 添加Content Security Policy头，允许unsafe-eval以支持Unity通信
        self.send_header('Content-Security-Policy', "script-src 'self' 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval' blob:")
        # ✅ 启用 SharedArrayBuffer 支持（COOP + COEP）
        # 这是 @ricky0123/vad-web (Silero VAD) 和其他 WASM 库的必要条件
        # 同时也是 AudioWorklet 在某些浏览器上的性能优化条件
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        super().end_headers()
        
    def send_head(self):
        """Handle a HEAD request or a GET request with no body."""
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # Redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header('Location', self.path + '/')
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
                else:
                    return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None
        
        # 处理 Range 请求
        if 'Range' in self.headers:
            try:
                range_header = self.headers['Range']
                start, end = range_header.strip().split('=')[1].split('-')
                start = int(start)
                end = int(end) if end else None
            except:
                self.send_error(400, "Invalid Range header")
                return None
            
            # 获取文件大小
            file_size = os.path.getsize(path)
            if end is None or end >= file_size:
                end = file_size - 1
            
            # 调整文件指针位置
            f.seek(start)
            content_length = end - start + 1
            
            # 发送 206 Partial Content 响应
            self.send_response(206)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            self.send_header('Content-Length', str(content_length))
            self.send_header('Accept-Ranges', 'bytes')
            self.end_headers()
            return f
        else:
            # 处理常规请求
            try:
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                fs = os.fstat(f.fileno())
                self.send_header('Content-Length', str(fs[6]))
                self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                return f
            except:
                f.close()
                raise

def main():
    parser = argparse.ArgumentParser(description='SSL HTTP Server for MuseumAgent Demo')
    parser.add_argument('--port', type=int, default=12302, help='Server port')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Server host address')
    parser.add_argument('--ssl', action='store_true', help='Enable SSL')
    parser.add_argument('--cert', type=str, default='../../../config/SSL/www.soulflaw.com_nginx/www.soulflaw.com_bundle.pem', help='SSL certificate file')
    parser.add_argument('--key', type=str, default='../../../config/SSL/www.soulflaw.com_nginx/www.soulflaw.com.key', help='SSL private key file')
    
    args = parser.parse_args()
    
    PORT = args.port
    HOST = args.host
    
    # 检查证书文件是否存在
    cert_path = os.path.abspath(args.cert)
    key_path = os.path.abspath(args.key)
    
    if args.ssl:
        if not os.path.exists(cert_path):
            print(f"Error: Certificate file not found: {cert_path}")
            return
        if not os.path.exists(key_path):
            print(f"Error: Private key file not found: {key_path}")
            return
        
        print(f"Starting HTTPS server on {HOST}:{PORT}...")
        print(f"Server address: https://museum.soulflaw.com:{PORT}")
        print(f"Using certificate: {cert_path}")
        print(f"Using private key: {key_path}")
    else:
        print(f"Starting HTTP server on {HOST}:{PORT}...")
        print(f"Server address: http://museum.soulflaw.com:{PORT}")
    
    with socketserver.TCPServer((HOST, PORT), MyHTTPRequestHandler) as httpd:
        if args.ssl:
            # 包装socket以支持SSL
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=cert_path, keyfile=key_path)
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()
