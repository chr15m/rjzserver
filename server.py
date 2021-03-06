#
#	RjzServer
#	By Chris McCormick
# 	GPLv3
#	
#	See the files README and COPYING for details.
#

from os import listdir, path, environ, sep
import zipfile
from cStringIO import *
from sys import argv
import sys
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import socket
from time import sleep
from config import config
import webbrowser

from mako.template import Template

if sys.platform == "win32":
	basedir = sep.join(sys.path[0].split(sep)[:-1])
else:
	basedir = sys.path[0]
port = 8314

def getIP():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(('91.121.94.180', 80)) # doesn't matter if it fails
	addr = s.getsockname()[0] 
	s.close()
	return addr

def zipall(d, zip, base=""):
	for f in [dir for dir in listdir(path.join(base, d)) if dir[0] != "."]:
		z = path.join(d, f)
		if path.isdir(path.join(base, z)):
			zipall(z, zip, base)
		else:
			zip.write(path.join(base, z), z)

def zipdir(rjdir, base, fp):
	zip = zipfile.ZipFile(fp, 'w')
	zipall(rjdir, zip, base=base)

class RjzHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		urlpath = self.path
		if urlpath.startswith("http://"):
			urlpath = "/" + "/".join(urlpath.split("/")[3:])
		if urlpath.endswith(".rjz"):
			self.send_response(200)
			self.send_header('Content-type', 'application/zip')
			
			rjzfile = path.basename(urlpath)
			tmpfile = StringIO()
			zipdir(rjzfile[:-1], config.Get("scenedir", default="."), tmpfile)
			tmpfile.seek(0)
			rjz = tmpfile.read()
			tmpfile.close()
			
			self.send_header('Content-length', len(rjz))
			self.end_headers()
			
			self.wfile.write(rjz)
			return
		elif urlpath.startswith("/media/"):
			# really insecure mini media server
			diskfile = basedir + sep.join(urlpath.split("/"))
			if path.isfile(diskfile):
				types = {"jpeg": "jpeg", "jpg": "jpeg", "gif": "gif", "png": "png"}
				for t in types:
					if urlpath[-len(t):].lower() == t:
						contentType = "image/" + t
				if urlpath[-3:].lower() == "css":
					contentType = "text/css"
				if contentType:
					content = file(diskfile).read()
					self.send_response(200)
					self.send_header('Content-type', contentType)
					self.send_header('Content-length', str(len(content)))
					self.end_headers()
					self.wfile.write(content)
				else:
					self.send_response(404)
					self.wfile.write("Don't support files of that type")
			else:
				self.send_response(404)
				self.wfile.write("%s does not exist" % urlpath)
			return
		else:
			config.SetFilename("rjzserver.cfg")
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			
			rjzs = [d for d in listdir(config.Get("scenedir", default=".")) if d[-3:] == ".rj"]
			
			self.wfile.write(Template(file(path.join(basedir, "media", "templates", "index.html")).read()).render(rjzs=rjzs, headers=self.headers, listen=self.server.listen))
			return
		return
	
	def log_message(self, format, *args):
		self.server.Output("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format%args))

class RjzServer(HTTPServer):
	def __init__(self, outputfn):
		config.SetFilename("rjzserver.cfg")
		self.Output = outputfn
		listen = (getIP(), port)
		self.listen = listen
		HTTPServer.__init__(self, listen, RjzHandler)
		self.Output("RjzServer launched")
		self.Output("Listening on http://%s:%d/" % listen)
		webbrowser.open("http://%s:%d/" % listen)
		self.Output("Using directory %s" % config.Get("scenedir", default="."))
		self.Output(str(sys.path))
		self.Output(str(basedir))
		self.Output("Select Help from the File menu for instructions on how to use RjzServer!")
		self.quit = False
	
	def Launch(self):
		self.serve_forever()

if __name__ == '__main__':
	def Output(txt):
		print txt
	server = RjzServer(outputfn=Output)
	try:
		server.Launch()
	except KeyboardInterrupt:
		server.Output("Shutting down RjzServer")

