import socket
import threading
import logging
from http import HttpServer 

httpserver = HttpServer()

class ClientHandler(threading.Thread):
    def __init__(self, conn, addr):
        super().__init__()
        self.conn = conn
        self.addr = addr
        self.buffer = b""

    def run(self):
        logging.info(f"[CONNECTED] Client: {self.addr}")
        try:
            while True:
                data = self.conn.recv(1024)
                if not data:
                    logging.info(f"[DISCONNECTED] Client: {self.addr}")
                    break

                self.buffer += data

                if b"\r\n\r\n" in self.buffer:
                    request_part, self.buffer = self.buffer.split(b"\r\n\r\n", 1)
                    full_request = request_part.decode(errors="ignore") + "\r\n\r\n"

                    first_line = full_request.splitlines()[0] if full_request else ""
                    logging.info(f"[REQUEST] {self.addr}: {first_line}")

                    response = httpserver.proses(full_request)
                    self.conn.sendall(response)
        except Exception as e:
            logging.error(f"[ERROR] {self.addr}: {e}")
        finally:
            self.conn.close()
            logging.info(f"[CLOSED] Connection with {self.addr}")

class GameServerThread(threading.Thread):
    def __init__(self, host="0.0.0.0", port=6001):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(10)
        logging.info(f"[STARTED] HTTP Game Server on {self.host}:{self.port}")

    def run(self):
        try:
            while True:
                conn, addr = self.sock.accept()
                handler = ClientHandler(conn, addr)
                handler.start()
        except Exception as e:
            logging.error(f"[FATAL ERROR] {e}")
        finally:
            self.sock.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    server = GameServerThread()
    server.start()
