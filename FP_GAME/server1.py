import socket
import threading
import pickle
import time
import pygame 

# Konfigurasi Server
HOST = "localhost"
PORT = 6001  
RESPAWN_DELAY = 15
DAMAGE = 20

players = {}
lock = threading.Lock()

class Player:
    def __init__(self, conn, addr, pid):
        self.conn = conn
        self.addr = addr
        self.id = pid
        self.x = 100 + int(pid) * 50
        self.y = 300
        self.hp = 100
        self.is_dead = False
        self.is_attacking = False
        self.attack_range = None
        self.facing = 'right'
        self.is_moving = False
        self.username = None  
        self.score = 0
        self.death_time = None
        self.has_hit = False  # Tambahan untuk mencegah one-hit kill

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "is_dead": self.is_dead,
            "is_attacking": self.is_attacking,
            "facing": self.facing,
            "is_moving": self.is_moving,
            "score": self.score,
            "username": self.username or f"Player {self.id}",
        }

def handle_client(conn, addr, pid):
    global players
    print(f"[NEW CONNECTION] Player {pid} connected from {addr}")
    conn.sendall(pickle.dumps(pid))

    with lock:
        players[pid] = Player(conn, addr, pid)

    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            recv_data = pickle.loads(data)

            with lock:
                player = players[pid]
                player.x = recv_data["x"]
                player.y = recv_data["y"]
                player.is_attacking = recv_data["is_attacking"]
                player.facing = recv_data.get("facing", "right")
                player.is_moving = recv_data.get("is_moving", False)

                if player.username is None and "username" in recv_data:
                    player.username = recv_data["username"]

                # Reset has_hit saat tidak menyerang
                if not player.is_attacking:
                    player.has_hit = False

                if player.is_attacking and not player.has_hit and not player.is_dead and "attack_range" in recv_data:
                    atk_rect = pygame.Rect(*recv_data["attack_range"])
                    for pid2, target in players.items():
                        if pid2 != pid and not target.is_dead:
                            target_rect = pygame.Rect(target.x + 40, target.y + 50, 45, 80)
                            if atk_rect.colliderect(target_rect):
                                target.hp = max(0, target.hp - DAMAGE)
                                player.has_hit = True
                                if target.hp == 0:
                                    target.is_dead = True
                                    target.death_time = time.time()
                                    player.score += 1
                                break

                # Respawn
                if player.is_dead and player.death_time:
                    if time.time() - player.death_time >= RESPAWN_DELAY:
                        player.hp = 100
                        player.is_dead = False
                        player.death_time = None
                        # player.x = 100 + int(pid) * 50
                        # player.y = 300

                all_data = {p_id: p.to_dict() for p_id, p in players.items()}
                conn.sendall(pickle.dumps({"players": all_data}))

        except Exception as e:
            print(f"[ERROR] Player {pid}: {e}")
            break

    print(f"[DISCONNECT] Player {pid} disconnected")
    with lock:
        if pid in players:
            del players[pid]
    conn.close()

def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Running on {HOST}:{PORT}")

    next_id = 1
    while True:
        conn, addr = server.accept()
        pid = str(next_id)
        next_id += 1
        thread = threading.Thread(target=handle_client, args=(conn, addr, pid), daemon=True)
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start()
