import pygame
import socket
import pickle
import sys

# Koneksi ke server
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("localhost", 5555))
    client_id = str(pickle.loads(client_socket.recv(1024)))
    print(f"Berhasil terhubung ke server sebagai Player {client_id}")
except ConnectionRefusedError:
    print("Koneksi ditolak. Pastikan server.py sudah berjalan.")
    sys.exit()
except Exception as e:
    print(f"Gagal terhubung ke server: {e}")
    sys.exit()

# Setup pygame
pygame.init()
WIDTH, HEIGHT = 1200, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Samurai Battle Arena - Player {client_id}")
clock = pygame.time.Clock()
FPS = 60

# score board
try:
    SCORE_FONT = pygame.font.Font(None, 30)
    PLAYER_NAME_FONT = pygame.font.Font(None, 20)
except pygame.error:
    SCORE_FONT = pygame.font.SysFont('Arial', 28)
    PLAYER_NAME_FONT = pygame.font.SysFont('Arial', 18)

FRAME_WIDTH = 128
FRAME_HEIGHT = 128
NUM_IDLE_FRAMES = 9
NUM_WALK_FRAMES = 8
NUM_ATCK_FRAMES = 5
NUM_DEAD_FRAMES = 5

# Load background
try:
    background = pygame.image.load("asset/Map2.jpg").convert()
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
except pygame.error as e:
    print(f"Gagal memuat aset. Pastikan folder 'asset' ada di direktori yang sama. Error: {e}")
    sys.exit()

class Samurai:
    def __init__(self, id='1', isremote=False):
        self.id = id
        self.hp = 100
        self.score = 0
        self.isremote = isremote
        self.is_dead = False
        self.is_attacking = False
        self.facing = "right"
        self.x = 100 + int(id) * 50
        self.y = HEIGHT // 2
        self.speed = 3
        self.is_moving = False
        self.current_frame = 0
        self.animation_counter = 0
        self.animation_delay = 10
        self.attack_delay = 4
        self.dead_delay = 10

        self.idle_sheet = pygame.image.load("asset/Samurai_Archer/Idle.png").convert_alpha()
        self.walk_sheet = pygame.image.load("asset/Samurai_Archer/Walk.png").convert_alpha()
        self.attack_sheet = pygame.image.load("asset/Samurai_Archer/Attack_2.png").convert_alpha()
        self.dead_sheet = pygame.image.load("asset/Samurai_Archer/Dead.png").convert_alpha()

        self.idle_frames = [self.idle_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT)) for i in range(NUM_IDLE_FRAMES)]
        self.walk_frames = [self.walk_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT)) for i in range(NUM_WALK_FRAMES)]
        self.attack_frames = [self.attack_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT)) for i in range(NUM_ATCK_FRAMES)]
        self.dead_frames = [self.dead_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT)) for i in range(NUM_DEAD_FRAMES)]

    def move(self, keys):
        if self.isremote or self.is_dead or self.is_attacking:
            self.is_moving = False
            return
            
        self.is_moving = False
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
            self.is_moving = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
            self.is_moving = True

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
            self.facing = "left"
            self.is_moving = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
            self.facing = "right"
            self.is_moving = True

        # Batasi pergerakan di dalam layar
        self.x = max(0, min(self.x, WIDTH - FRAME_WIDTH))
        self.y = max(0, min(self.y, HEIGHT - FRAME_HEIGHT))

    def get_attack_range_rect(self):
        range_width = 40
        range_height = 80
        offset_x = -37.5 
        if self.facing == "right":
            return pygame.Rect(self.x + FRAME_WIDTH + offset_x, self.y + 30, range_width, range_height)
        else: 
            return pygame.Rect(self.x - range_width - offset_x, self.y + 30, range_width, range_height)

    def draw(self, surface):
        self.animation_counter += 1

        if self.is_dead:
            if self.animation_counter >= self.dead_delay:
                self.animation_counter = 0
                if self.current_frame < len(self.dead_frames) - 1:
                    self.current_frame += 1
            frame = self.dead_frames[self.current_frame]

        elif self.is_attacking:
            if self.animation_counter >= self.attack_delay:
                self.animation_counter = 0
                self.current_frame += 1
                if self.current_frame >= len(self.attack_frames):
                    self.current_frame = 0
                    self.is_attacking = False
            self.current_frame %= len(self.attack_frames)
            frame = self.attack_frames[self.current_frame]

        elif self.is_moving:
            if self.animation_counter >= self.animation_delay:
                self.animation_counter = 0
                self.current_frame += 1
            self.current_frame %= len(self.walk_frames)
            frame = self.walk_frames[self.current_frame]
        else:
            if self.animation_counter >= self.animation_delay:
                self.animation_counter = 0
                self.current_frame += 1
            self.current_frame %= len(self.idle_frames)
            frame = self.idle_frames[self.current_frame]

        if self.facing == "left":
            frame = pygame.transform.flip(frame, True, False)

        surface.blit(frame, (self.x, self.y))

        # hp bar
        if not self.is_dead:
            bar_width = 60
            bar_height = 8
            health_ratio = self.hp / 100
            bar_x = self.x + (FRAME_WIDTH - bar_width) // 2
            bar_y = self.y + 20
            pygame.draw.rect(surface, (120, 0, 0), (bar_x, bar_y, bar_width, bar_height)) 
            pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

def sync_with_server(player):
    try:
        send_data = {
            "x": player.x,
            "y": player.y,
            "is_attacking": player.is_attacking,
            "facing": player.facing,
            "is_moving": player.is_moving
        }

        if player.is_attacking:
            r = player.get_attack_range_rect()
            send_data["attack_range"] = [r.x, r.y, r.width, r.height]

        client_socket.sendall(pickle.dumps(send_data))
        return pickle.loads(client_socket.recv(4096))
    except (socket.error, EOFError, pickle.UnpicklingError) as e:
        print(f"Koneksi ke server terputus: {e}")
        return None

def draw_scoreboard(surface, all_players, my_id):
    y_offset = 10
    title = SCORE_FONT.render("Scoreboard", True, (255, 215, 0)) 
    surface.blit(title, (WIDTH - 150, y_offset))
    y_offset += 30
    
    sorted_players = sorted(all_players, key=lambda p: p.score, reverse=True)

    for player in sorted_players:
        text = f"Player {player.id}: {player.score}"
        color = (0, 255, 0) if player.id == my_id else (255, 255, 255) # Sorot pemain lokal
        score_text = SCORE_FONT.render(text, True, color)
        surface.blit(score_text, (WIDTH - 150, y_offset))
        y_offset += 25

# Buat player lokal
current_player = Samurai(client_id)
players = {}

# Game loop
running = True
while running:
    screen.blit(background, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not current_player.is_attacking and not current_player.is_dead:
                current_player.is_attacking = True
                current_player.current_frame = 0
                current_player.animation_counter = 0

    keys = pygame.key.get_pressed()
    current_player.move(keys)

    # Sinkronisasi ke server
    state = sync_with_server(current_player)

    if state:
        all_data = state.get("players", {})
        server_player_ids = set(all_data.keys())
        local_remote_player_ids = set(players.keys())
        
        disconnected_ids = local_remote_player_ids - server_player_ids
        for pid in disconnected_ids:
            print(f"Player {pid} telah keluar, menghapus dari game.")
            del players[pid]

        for pid, pdata in all_data.items():
            if pid == current_player.id:
                was_alive = not current_player.is_dead
                was_dead_for_respawn = current_player.is_dead

                current_player.hp = pdata["hp"]
                current_player.score = pdata["score"]
                current_player.is_dead = pdata["is_dead"]

                if was_alive and current_player.is_dead:
                    current_player.current_frame = 0
                    print(f"Player {pid} has died. Resetting animation frame.")
                
                if was_dead_for_respawn and not current_player.is_dead:
                    print(f"Player {pid} respawned. Syncing position.")
                    current_player.x = pdata['x']
                    current_player.y = pdata['y']

            else:
                if pid not in players:
                    players[pid] = Samurai(pid, isremote=True)

                p = players[pid]

                was_remote_alive = not p.is_dead

                p.x = pdata["x"]
                p.y = pdata["y"]
                p.hp = pdata["hp"]
                p.score = pdata["score"]
                p.is_attacking = pdata["is_attacking"]
                p.is_dead = pdata["is_dead"]
                p.facing = pdata.get("facing", "right")
                p.is_moving = pdata.get("is_moving", False)

                if was_remote_alive and p.is_dead:
                    p.current_frame = 0
                    
                if not p.is_attacking and pdata["is_attacking"]:
                    p.current_frame = 0
                if not p.is_moving and pdata.get("is_moving", False):
                     p.current_frame = 0 
    else:
        print("Gagal menerima data dari server, keluar dari game.")
        running = False

    all_players_list = [current_player] + list(players.values())
    for p in sorted(all_players_list, key=lambda pl: pl.y):
        p.draw(screen)

    draw_scoreboard(screen, all_players_list, client_id)

    pygame.display.flip()
    clock.tick(FPS)

print("Menutup koneksi dan keluar dari game.")
client_socket.close()
pygame.quit()
sys.exit()