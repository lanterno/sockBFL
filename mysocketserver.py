import socketserver
import threading
import time


class Mysocketserver(socketserver.BaseRequestHandler):

    def handle(self):
        data = ""
        self.data = self.request.recv(1024).strip()
        self.request.sendall(self.data)


class ThreadServer(socketserver.ThreadingMixIn, socketserver.ForkingTCPServer):
    pass


host = "localhost"
port = 8888
server = ThreadServer((host, port), Mysocketserver)
server_thread = threading.Thread(target=server.serve_forever)
server_thread.start()
print("We are here in the code.")
