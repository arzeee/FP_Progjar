
# server_thread_game.py (MODIFIED)
import socket
import threading
import logging
from http import HttpServer

httpserver = HttpServer()

class ClientHandler(threading.Thread):
    def __init__(self, conn, addr):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.player_id = None # Untuk melacak ID pemain di koneksi ini

    def run(self):
        logging.info(f"Connection from {self.addr}")
        rcv_buffer = "" # Gunakan buffer untuk menampung data yang masuk
        while True:
            try:
                data = self.conn.recv(1024)
                if not data:
                    # Klien menutup koneksi
                    logging.info(f"Client {self.addr} has disconnected.")
                    break
                
                rcv_buffer += data.decode()
                
                # Proses semua perintah lengkap yang ada di buffer
                # Mungkin saja klien mengirim beberapa perintah sekaligus
                while "\r\n\r\n" in rcv_buffer:
                    # Pisahkan perintah pertama dari sisa buffer
                    command_part, rcv_buffer = rcv_buffer.split("\r\n\r\n", 1)
                    
                    # Proses perintah
                    response = httpserver.proses(command_part.strip())
                    
                    # Kirim balasan ke klien
                    self.conn.sendall(response)

            except Exception as e:
                logging.error(f"Error handling client {self.addr}: {e}")
                break
        
        # Cleanup saat koneksi terputus
        if self.player_id:
            httpserver.proses(f"disconnect {self.player_id}")
            logging.info(f"Player {self.player_id} from {self.addr} has been cleaned up.")

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
