import socket
import pickle
from concurrent.futures import ThreadPoolExecutor
import threading
import pygame  # Untuk deteksi tabrakan rect

HOST = "0.0.0.0"
PORT = 5555

players = {}  # { id: {"x": int, "y": int, "hp": int, "is_attacking": bool, "is_dead": bool} }
lock = threading.Lock()

def handle_client(conn, addr, player_id):
    global players
    print(f"[CONNECTED] Player {player_id} connected from {addr}")
    conn.send(pickle.dumps(player_id))  # Kirim ID ke client

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            data = pickle.loads(data)
            pid = str(player_id)

            with lock:
                # Inisialisasi jika belum ada
                if pid not in players:
                    players[pid] = {
                        "x": data["x"],
                        "y": data["y"],
                        "hp": 100,
                        "is_attacking": False,
                        "is_dead": False
                    }

                # Update posisi dan aksi dari client
                players[pid]["x"] = data["x"]
                players[pid]["y"] = data["y"]
                players[pid]["is_attacking"] = data.get("is_attacking", False)

                # Jika ada aksi serangan, cek collision dan berikan damage
                if data.get("attack_range"):
                    arx, ary, aw, ah = data["attack_range"]
                    attacker_rect = pygame.Rect(arx, ary, aw, ah)

                    for tid, target in players.items():
                        if tid == pid or target["is_dead"]:
                            continue

                        tx, ty = target["x"], target["y"]
                        hitbox = pygame.Rect(tx + 40, ty + 50, 45, 80)

                        if attacker_rect.colliderect(hitbox):
                            target["hp"] = max(0, target["hp"] - 20)
                            if target["hp"] == 0:
                                target["is_dead"] = True
                                print(f"Player {tid} mati oleh Player {pid}")

                # Kirim state semua player ke client
                conn.sendall(pickle.dumps({"players": players}))

    except Exception as e:
        print(f"[ERROR] Player {player_id}: {e}")
    finally:
        with lock:
            if str(player_id) in players:
                del players[str(player_id)]
        conn.close()
        print(f"[DISCONNECTED] Player {player_id} disconnected")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER STARTED] Listening on port {PORT}...")

    player_id = 1
    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            conn, addr = server.accept()
            executor.submit(handle_client, conn, addr, player_id)
            player_id += 1

if __name__ == "__main__":
    start_server()
