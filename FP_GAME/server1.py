import socket
import threading
import pickle
import time
import pygame
import logging

# Konfigurasi Server
HOST = "0.0.0.0"
PORT = 6001  # Default port
RESPAWN_DELAY = 5
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
        self.has_hit = False

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

class ProcessTheClient(threading.Thread):
    def __init__(self, conn, addr, pid):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.pid = pid

    def run(self):
        global players
        logging.warning(f"[NEW CONNECTION] Player {self.pid} connected from {self.addr}")
        self.conn.sendall(pickle.dumps(self.pid))

        with lock:
            players[self.pid] = Player(self.conn, self.addr, self.pid)

        while True:
            try:
                data = self.conn.recv(4096)
                if not data:
                    break
                recv_data = pickle.loads(data)

                with lock:
                    player = players[self.pid]
                    player.x = recv_data["x"]
                    player.y = recv_data["y"]
                    player.is_attacking = recv_data["is_attacking"]
                    player.facing = recv_data.get("facing", "right")
                    player.is_moving = recv_data.get("is_moving", False)

                    if player.username is None and "username" in recv_data:
                        player.username = recv_data["username"]

                    if not player.is_attacking:
                        player.has_hit = False

                    if player.is_attacking and not player.has_hit and not player.is_dead and "attack_range" in recv_data:
                        atk_rect = pygame.Rect(*recv_data["attack_range"])
                        for pid2, target in players.items():
                            if pid2 != self.pid and not target.is_dead:
                                target_rect = pygame.Rect(target.x + 40, target.y + 50, 45, 80)
                                if atk_rect.colliderect(target_rect):
                                    target.hp = max(0, target.hp - DAMAGE)
                                    player.has_hit = True
                                    if target.hp == 0:
                                        target.is_dead = True
                                        target.death_time = time.time()
                                        player.score += 1
                                    break

                    if player.is_dead and player.death_time:
                        if time.time() - player.death_time >= RESPAWN_DELAY:
                            player.hp = 100
                            player.is_dead = False
                            player.death_time = None
                            # Respawn di posisi terakhir

                    all_data = {p_id: p.to_dict() for p_id, p in players.items()}
                    self.conn.sendall(pickle.dumps({"players": all_data}))

            except Exception as e:
                logging.error(f"[ERROR] Player {self.pid}: {e}")
                break

        logging.warning(f"[DISCONNECT] Player {self.pid} disconnected")
        with lock:
            if self.pid in players:
                del players[self.pid]
        self.conn.close()

class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        self.next_id = 1

    def run(self):
        self.socket.bind((HOST, PORT))
        self.socket.listen(5)
        logging.warning(f"[SERVER] Running on {HOST}:{PORT}")

        while True:
            conn, addr = self.socket.accept()
            pid = str(self.next_id)
            self.next_id += 1
            client_thread = ProcessTheClient(conn, addr, pid)
            client_thread.start()
            self.clients.append(client_thread)
            logging.warning(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

def main():
    server = Server()
    server.start()

if __name__ == "__main__":
    main()
