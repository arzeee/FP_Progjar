import socket
import pickle
from concurrent.futures import ThreadPoolExecutor

# Game State (dictionary posisi 2 player)
players = [
    {"x": 50, "y": 50},
    {"x": 350, "y": 350}
]

# Kirim posisi musuh ke masing-masing player
def handle_client(conn, player_id):
    print(f"[INFO] Player {player_id + 1} connected.")
    conn.send(pickle.dumps(players[player_id]))  # Kirim posisi awal

    while True:
        try:
            data = pickle.loads(conn.recv(1024))  # Terima posisi baru dari client
            players[player_id] = data  # Update posisi player ini
            enemy_id = 1 - player_id   # ID lawan

            conn.send(pickle.dumps(players[enemy_id]))  # Kirim posisi musuh
        except:
            print(f"[DISCONNECT] Player {player_id + 1} disconnected.")
            break

    conn.close()


def start_server():
    host = "0.0.0.0"
    port = 5555

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(2)
    print(f"[SERVER STARTED] Listening on port {port}...")

    with ThreadPoolExecutor(max_workers=2) as executor:
        player_count = 0

        while player_count < 2:
            conn, addr = server_socket.accept()
            executor.submit(handle_client, conn, player_count)
            player_count += 1


if __name__ == "__main__":
    start_server()
