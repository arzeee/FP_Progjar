import socket
import pickle
from concurrent.futures import ThreadPoolExecutor
import threading
import pygame  # Untuk Rect collision

HOST = "0.0.0.0"
PORT = 5555

players = {}  # id: {x, y, hp, is_dead, is_attacking, death_time, attack_done}
lock = threading.Lock()

RESPAWN_DELAY = 15000  # 15 detik

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
                # Inisialisasi player jika belum ada
                if pid not in players:
                    players[pid] = {
                        "x": data["x"],
                        "y": data["y"],
                        "hp": 100,
                        "is_attacking": False,
                        "attack_done": False,
                        "is_dead": False,
                        "death_time": None,
                        "facing": data.get("facing", "right"),
                        "is_moving": data.get("is_moving", False)
                    }


                player = players[pid]

                # Cek apakah ini serangan baru
                if data.get("is_attacking", False) and not player["is_attacking"]:
                    player["attack_done"] = False

                # Update posisi dan status serangan
                player["x"] = data["x"]
                player["y"] = data["y"]
                player["is_attacking"] = data.get("is_attacking", False)
                player["facing"] = data.get("facing", "right")  # default ke kanan
                player["is_moving"] = data.get("is_moving", False)


                # Deteksi serangan (jika belum attack_done dan masih hidup)
                if data.get("attack_range") and player["is_attacking"] and not player["attack_done"] and not player["is_dead"]:
                    arx, ary, aw, ah = data["attack_range"]
                    attacker_rect = pygame.Rect(arx, ary, aw, ah)

                    for tid, target in players.items():
                        if tid == pid or target["is_dead"]:
                            continue

                        tx, ty = target["x"], target["y"]
                        hitbox = pygame.Rect(tx + 40, ty + 50, 45, 80)

                        if attacker_rect.colliderect(hitbox):
                            if target["hp"] > 0:
                                target["hp"] = max(0, target["hp"] - 20)
                                print(f"[HIT] Player {pid} hit Player {tid}, HP: {target['hp']}")
                                if target["hp"] == 0:
                                    target["is_dead"] = True
                                    target["death_time"] = pygame.time.get_ticks()
                                    print(f"[DEAD] Player {tid} has died.")

                    player["attack_done"] = True  # hanya boleh sekali per animasi serang

                # Cek respawn
                now = pygame.time.get_ticks()
                for tid, target in players.items():
                    if target["is_dead"] and target["death_time"] is not None:
                        if now - target["death_time"] >= RESPAWN_DELAY:
                            target["hp"] = 100
                            target["is_dead"] = False
                            target["death_time"] = None
                            print(f"[RESPAWN] Player {tid} respawned.")

                # Kirim data ke client
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
    pygame.init()  # Dibutuhkan untuk Rect dan tick
    start_server()
