import socket
import threading
import itertools
import logging

LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = 5555 
BACKEND_SERVERS = [
    ('localhost', 6001),
    ('localhost', 6002),
]

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] (%(threadName)-10s) %(message)s')

class LoadBalancer:
    def __init__(self, host, port, server_list):
        self.host = host
        self.port = port
        self.server_pool = itertools.cycle(server_list)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        logging.info(f"Load Balancer berjalan di {self.host}:{self.port}")

    def run(self):
        """Menerima koneksi dari klien dan meneruskannya ke backend."""
        while True:
            try:
                client_socket, client_address = self.sock.accept()
                logging.info(f"Koneksi masuk dari {client_address}")
                
                backend_server = next(self.server_pool)
                logging.info(f"Meneruskan koneksi ke {backend_server}")
                
                handler_thread = threading.Thread(
                    target=self.handle_connection,
                    args=(client_socket, backend_server),
                    daemon=True
                )
                handler_thread.start()

            except Exception as e:
                logging.error(f"Error di loop utama: {e}")

    def handle_connection(self, client_socket, backend_address):
        """Menghubungkan ke backend dan menyalurkan data dua arah."""
        try:
            backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            backend_socket.connect(backend_address)
            
            client_to_backend = threading.Thread(
                target=self.forward_data,
                args=(client_socket, backend_socket),
                daemon=True
            )
            backend_to_client = threading.Thread(
                target=self.forward_data,
                args=(backend_socket, client_socket),
                daemon=True
            )

            client_to_backend.start()
            backend_to_client.start()

            client_to_backend.join()
            backend_to_client.join()

        except socket.error as e:
            logging.error(f"Gagal terhubung ke backend {backend_address}: {e}")
        finally:
            logging.info(f"Menutup koneksi antara klien dan {backend_address}")
            client_socket.close()

    def forward_data(self, source_socket, dest_socket):
        """Membaca data dari satu socket dan menulisnya ke socket lain."""
        try:
            while True:
                data = source_socket.recv(4096)
                if not data:
                    break
                dest_socket.sendall(data)
        except OSError:
            pass
        finally:
            source_socket.close()
            dest_socket.close()

if __name__ == "__main__":
    balancer = LoadBalancer(LISTEN_HOST, LISTEN_PORT, BACKEND_SERVERS)
    balancer.run()