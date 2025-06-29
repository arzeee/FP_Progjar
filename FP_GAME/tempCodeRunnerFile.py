import socket
import pickle
from concurrent.futures import ThreadPoolExecutor
import threading
import pygame  
import time

HOST = "0.0.0.0"
PORT = 5555

players = {}  # id: {x, y, hp, is_dead, is_attacking, death_time, attack_done}
lock = threading.Lock()

RESPAWN_DELAY = 15000  # 15 detik
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 600

def respawn_player():
    global players
    while True:
        with lock:
            now = pygame.time.get_ticks()
            for tid, target in players.items():
                if target["is_dead"] and target["death_time"] is not None:
                    if now - target["death_time"] >= RESPAWN_DELAY:
                        # Reset status pemain
                        target["hp"] = 100
                        target["is_dead"] = False
                        target["death_time"] = None
                        # Atur posisi respawn ke tengah layar
                        target["x"] = SCREEN_WIDTH // 2
                        target["y"] = SCREEN_HEIGHT // 2
                        print(f"[RESPAWN] Player {tid} respawned.")
        
        # efisiensi CPU
        time.sleep(1/30)

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

                # Cek apakah ini serangan baru untuk me-reset 'attack_done'
                if data.get("is_attacking", False) and not player["is_attacking"]:
                    player["attack_done"] = False

                # Update posisi dan status dari client
                player["x"] = data["x"]
                player["y"] = data["y"]
                player["is_attacking"] = data.get("is_attacking", False)
                player["facing"] = data.get("facing", "right")
                player["is_moving"] = data.get("is_moving", False)

                # Deteksi serangan (hanya jika player hidup, menyerang, dan belum mendaratkan pukulan)
                if data.get("attack_range") and player["is_attacking"] and not player["attack_done"] and not player["is_dead"]:
                    arx, ary, aw, ah = data["attack_range"]
                    attacker_rect = pygame.Rect(arx, ary, aw, ah)

                    for tid, target in players.items():
                        if tid == pid or target["is_dead"]:
                            continue

                        # Hitbox target (sesuaikan dengan ukuran di client)
                        hitbox = pygame.Rect(target["x"] + 40, target["y"] + 50, 45, 80)

                        if attacker_rect.colliderect(hitbox):
                            if target["hp"] > 0:
                                target["hp"] = max(0, target["hp"] - 20) # Kurangi HP, minimal 0
                                print(f"[HIT] Player {pid} hit Player {tid}, HP: {target['hp']}")
                                if target["hp"] == 0:
                                    target["is_dead"] = True
                                    target["death_time"] = pygame.time.get_ticks()
                                    print(f"[DEAD] Player {tid} has died.")
                    
                    player["attack_done"] = True  # Tandai serangan ini sudah mendaratkan pukulan

                # Kirim state game terbaru ke client
                conn.sendall(pickle.dumps({"players": players}))

    except (ConnectionResetError, EOFError, pickle.UnpicklingError) as e:
        print(f"[ERROR/DISCONNECT] Player {player_id}: {e}")
    finally:
        with lock:
            if str(player_id) in players:
                print(f"[DISCONNECTED] Player {player_id} disconnected")
                del players[str(player_id)]
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER STARTED] Listening on port {PORT}...")

    logic_thread = threading.Thread(target=respawn_player, daemon=True)
    logic_thread.start()
    print("[GAME LOGIC] Game logic thread has started.")

    player_id = 1
    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            conn, addr = server.accept()
            executor.submit(handle_client, conn, addr, player_id)
            player_id += 1

if __name__ == "__main__":
    pygame.init()  # Dibutuhkan untuk Rect dan tick
    start_server()
