import socket
import threading

# Daftar backend server
BACKEND_SERVERS = [
    ('localhost', 6001),
    # ('localhost', 6002)
    #('localhost', 6003)
]

server_index = 0
server_lock = threading.Lock()

def handle_client(client_socket):
    global server_index

    with server_lock:
        target_host, target_port = BACKEND_SERVERS[server_index]
        server_index = (server_index + 1) % len(BACKEND_SERVERS)

    try:
        backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backend_socket.connect((target_host, target_port))

        def forward(source, destination):
            try:
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.sendall(data)
            except:
                pass
            finally:
                source.close()
                destination.close()

        threading.Thread(target=forward, args=(client_socket, backend_socket), daemon=True).start()
        threading.Thread(target=forward, args=(backend_socket, client_socket), daemon=True).start()

    except Exception as e:
        print(f"[!] Error forwarding to backend: {e}")
        client_socket.close()

def start_load_balancer(host='localhost', port=5555):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    print(f"[LOAD BALANCER] Listening on {host}:{port}")
    print(f"[LOAD BALANCER] Backend servers: {BACKEND_SERVERS}")

    while True:
        client_socket, addr = server.accept()
        print(f"[NEW CONNECTION] Client connected from {addr}")
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

if __name__ == "__main__":
    start_load_balancer()
