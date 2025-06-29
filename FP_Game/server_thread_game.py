import socket
import threading
import logging
from game_server import GameServer

gameserver = GameServer()

class ClientHandler(threading.Thread):
    def __init__(self, conn, addr):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr

    def run(self):
        logging.info(f"Connection from {self.addr}")
        rcv = ""
        while True:
            try:
                data = self.conn.recv(1024)
                if data:
                    rcv += data.decode()
                    if "\r\n\r\n" in rcv:
                        response = gameserver.proses(rcv.strip())
                        self.conn.sendall(response)
                        break
                else:
                    break
            except Exception as e:
                logging.error(f"Error: {e}")
                break
        self.conn.close()

class GameServerThread(threading.Thread):
    def __init__(self, host='0.0.0.0', port=6001):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(5)
        logging.info(f"Game server running on {host}:{port}")

    def run(self):
        while True:
            conn, addr = self.sock.accept()
            handler = ClientHandler(conn, addr)
            handler.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = GameServerThread()
    server.start()
