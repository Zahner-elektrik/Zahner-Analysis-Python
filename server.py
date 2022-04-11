#!/usr/bin/env python3
# A web server to echo back a request's headers and data.
#
# Usage: ./webserver
#        ./webserver 0.0.0.0:5000

from http.server import HTTPServer, BaseHTTPRequestHandler
from sys import argv
import cgi
from urllib import parse

BIND_HOST = 'localhost'
PORT = 8081
sensornames = dict()


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("GET:")
        self.write_response(b'')

    def do_POST(self):
        print("POST:")
        content_length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(content_length)
        self.write_response(body)

    def write_response(self, content):
        print(self.headers)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(content)
        print(content.decode('utf-8'))
        


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        global sensornames
        print("GET:")
        print(self.path)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        if "tempsrefresh" in self.path:
            import random
            temp = dict()
            temp["temp1"] = random.randint(1,1000)/random.randint(1,100)
            temp["temp2"] = random.randint(1,1000)/random.randint(1,100)
            temp["temp3"] = random.randint(1,1000)/random.randint(1,100)
            import json
            user_encode_data = json.dumps(temp).encode('utf-8')
            self.wfile.write(user_encode_data)
        elif "telegram" in self.path:
            asfd = 4
        elif "wifi" in self.path:
            asfd = 4
        elif "setsensorname" in self.path:
            sensornames = dict(parse.parse_qsl(parse.urlsplit(self.path).query))
            asdf = 3
        elif "getsensorname" in self.path:
            import json
            user_encode_data = json.dumps(sensornames).encode('utf-8')
            self.wfile.write(user_encode_data)
            
        else:
            self.wfile.write(open(r"C:\Users\maxim\Documents\ESP32\index.html","rb").read())
        #self.wfile.write(bytes(open(r"C:\Users\maxim\Documents\ESP32\index.html","rb").read(), "utf-8"))

    def do_POST(self):
        print("POST:")
        content_length = int(self.headers.get('content-length', 0))
        self.send_response(200)
        self.end_headers()
        
        ctype, pdict = cgi.parse_header(
            self.headers.get('content-type'))
        
        if ctype == 'multipart/form-data':
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            pdict['CONTENT-LENGTH'] = self.headers.get('content-length')
            fields = cgi.parse_multipart(self.rfile, pdict)
            print(fields)

if len(argv) > 1:
    arg = argv[1].split(':')
    BIND_HOST = arg[0]
    PORT = int(arg[1])

print(f'Listening on http://{BIND_HOST}:{PORT}\n')

# httpd = HTTPServer((BIND_HOST, PORT), SimpleHTTPRequestHandler)
httpd = HTTPServer((BIND_HOST, PORT), MyServer)
httpd.serve_forever()