#!/usr/bin/env python
import sys, os, BaseHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import logging
from logging.handlers import RotatingFileHandler

if sys.argv[1:]:
    appliance_type = sys.argv[1]
else:
    sys.stderr.write("No appliance type specified\n")
    sys.exit(1)

if appliance_type == 'mgt':
    vpn_ip = '10.80.0.1'
elif appliance_type == 'dmz':
    vpn_ip = '10.80.1.1'
else:
    sys.stderr.write("Unrecognized appliance type: %s\n" % (appliance_type))
    sys.exit(1)

FORK = False 
PORT = 8041
LOGFILE = "/var/log/symphony-detector-endpoint.log"
JSON = '{"version": "1", "type": "' + appliance_type + '"}'

LOGGER = logging.getLogger("detector-endpoint")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = RotatingFileHandler(LOGFILE, mode='wa', maxBytes=1 << 20, backupCount=2)
fh.setFormatter(formatter)
fh.setLevel(logging.INFO)
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(fh)
LOGGER.info("Starting detector endpoint")

class HTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args):
        self.logger = LOGGER
        BaseHTTPRequestHandler.__init__(self,*args)

    def log_message(self, format, *args):
        self.logger.info("%s - - [%s] %s" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format%args))

    def do_HEAD(self):
        if self.path == "/endpoint.json":
            self.send_header("Content-type", "application/json")
            self.send_response(200)
        else:
            self.send_response(404)

    def do_GET(self):
        if self.path == "/endpoint.json":
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(JSON)
        else:
            self.send_response(404)
            self.send_header("Access-Control-Allow-Origin", "*")

if FORK:
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("Could not fork: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    os.chdir('/')
    os.setsid()
    os.umask(0)
    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()

HandlerClass = HTTPRequestHandler
ServerClass  = BaseHTTPServer.HTTPServer
Protocol     = "HTTP/1.0"
HandlerClass.protocol_version = Protocol
httpd = ServerClass((vpn_ip, PORT), HandlerClass)

sa = httpd.socket.getsockname()
#print "Serving HTTP on", sa[0], "port", sa[1], "..."
httpd.serve_forever()
