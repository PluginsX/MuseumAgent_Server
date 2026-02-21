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
        super().end_headers()

def main():
    parser = argparse.ArgumentParser(description='SSL HTTP Server for MuseumAgent Demo')
    parser.add_argument('--port', type=int, default=12302, help='Server port')
    parser.add_argument('--ssl', action='store_true', help='Enable SSL')
    parser.add_argument('--cert', type=str, default='../../../config/SSL/www.soulflaw.com_nginx/www.soulflaw.com_bundle.pem', help='SSL certificate file')
    parser.add_argument('--key', type=str, default='../../../config/SSL/www.soulflaw.com_nginx/www.soulflaw.com.key', help='SSL private key file')
    
    args = parser.parse_args()
    
    PORT = args.port
    
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
        
        print(f"Starting HTTPS server on port {PORT}...")
        print(f"Server address: https://museum.soulflaw.com:{PORT}")
        print(f"Using certificate: {cert_path}")
        print(f"Using private key: {key_path}")
    else:
        print(f"Starting HTTP server on port {PORT}...")
        print(f"Server address: http://museum.soulflaw.com:{PORT}")
    
    with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
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
