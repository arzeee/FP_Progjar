import socket
import threading
import pickle
import time

# Konfigurasi Server
HOST = "0.0.0.0"
PORT = 6002  # Ganti sesuai dengan port yang diberikan oleh load balancer

players = {}
lock = threading.Lock()

RESPAWN_DELAY = 15
DAMAGE = 20

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
        self.username = f"Player {pid}"
        self.score = 0
        self.death_time = None

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
            "username": self.username,
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

                if not player.username and recv_data.get("username"):
                    player.username = recv_data["username"]

                if player.is_attacking and not player.is_dead and "attack_range" in recv_data:
                    player.attack_range = recv_data["attack_range"]
                    for pid2, target in players.items():
                        if pid2 != pid and not target.is_dead:
                            target_rect = (target.x + 40, target.y + 50, 45, 80)
                            atk_rect = recv_data["attack_range"]
                            atk_rect = pygame.Rect(*atk_rect)
                            target_hitbox = pygame.Rect(*target_rect)
                            if atk_rect.colliderect(target_hitbox):
                                target.hp = max(0, target.hp - DAMAGE)
                                if target.hp == 0:
                                    target.is_dead = True
                                    target.death_time = time.time()
                                    player.score += 1

                # Respawn
                if player.is_dead and player.death_time:
                    if time.time() - player.death_time >= RESPAWN_DELAY:
                        player.hp = 100
                        player.is_dead = False
                        player.death_time = None
                        player.x = 100 + int(pid) * 50
                        player.y = 300

                all_data = {p_id: p.to_dict() for p_id, p in players.items()}
                conn.sendall(pickle.dumps({"players": all_data}))

        except Exception as e:
            print(f"[ERROR] Player {pid}: {e}")
            break

    print(f"[DISCONNECT] Player {pid} disconnected")
    with lock:
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
        thread = threading.Thread(target=handle_client, args=(conn, addr, pid))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    import pygame  # Pastikan pygame diimpor untuk pygame.Rect di server
    start()
