import socket
import pickle
from concurrent.futures import ThreadPoolExecutor
import threading
import pygame  
import time

HOST = "0.0.0.0"
PORT = 5555

players = {}  # id: {x, y, hp, is_dead, is_attacking, death_time, score, username}
lock = threading.Lock()

RESPAWN_DELAY = 10000  # 10 detik
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
                        print(f"[RESPAWN] Player {tid} ({target.get('username', 'N/A')}) respawned.")
        
        # efisiensi CPU
        time.sleep(1/30) # Cek 30 kali per detik

def handle_client(conn, addr, player_id):
    global players
    pid = str(player_id)
    print(f"[CONNECTED] Player {pid} connected from {addr}")
    conn.send(pickle.dumps(pid))  # Kirim ID ke client

    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            data = pickle.loads(data)

            with lock:
                # Inisialisasi player jika belum ada
                if pid not in players:
                    players[pid] = {
                        "username": data.get("username", f"Player {pid}"),
                        "x": data["x"],
                        "y": data["y"],
                        "hp": 100,
                        "score": 0,
                        "is_attacking": False,
                        "is_dead": False,
                        "death_time": None,
                        "facing": data.get("facing", "right"),
                        "is_moving": data.get("is_moving", False),
                        "hit_in_attack": set() 
                    }
                    print(f"[NEW PLAYER] Player {pid} registered as '{players[pid]['username']}'.")

                player = players[pid]

                if data.get("is_attacking", False) and not player["is_attacking"]:
                    player["hit_in_attack"] = set()

                # Update posisi dan status dari client
                player.update({
                    "x": data["x"], 
                    "y": data["y"],
                    "is_attacking": data.get("is_attacking", False),
                    "facing": data.get("facing", "right"),
                    "is_moving": data.get("is_moving", False)
                })

                # Deteksi serangan
                if data.get("attack_range") and player["is_attacking"] and not player["is_dead"]:
                    arx, ary, aw, ah = data["attack_range"]
                    attacker_rect = pygame.Rect(arx, ary, aw, ah)
                    
                    for tid, target in players.items():
                        if tid == pid or target["is_dead"] or tid in player["hit_in_attack"]:
                            continue

                        # Hitbox target 
                        hitbox = pygame.Rect(target["x"] + 40, target["y"] + 50, 45, 80)

                        if attacker_rect.colliderect(hitbox):
                            if target["hp"] > 0:
                                target["hp"] = max(0, target["hp"] - 20)
                                player["hit_in_attack"].add(tid) # Catat target yang sudah dipukul
                                print(f"[HIT] Player {pid} ({player['username']}) hit Player {tid} ({target['username']}), HP: {target['hp']}")
                                
                                if target["hp"] == 0:
                                    target["is_dead"] = True
                                    target["death_time"] = pygame.time.get_ticks()
                                    if pid in players:
                                        players[pid]["score"] += 1
                                    print(f"[DEAD] Player {tid} ({target['username']}) has died.")
                
                conn.sendall(pickle.dumps({"players": players}))

    except (ConnectionResetError, EOFError, pickle.UnpicklingError) as e:
        print(f"[ERROR/DISCONNECT] Player {player_id}: {e}")
    finally:
        with lock:
            if str(player_id) in players:
                username = players[str(player_id)].get('username', 'N/A')
                print(f"[DISCONNECTED] Player {player_id} ({username}) disconnected")
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
