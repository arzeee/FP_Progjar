import pygame
import sys
import socket
import json

WIDTH, HEIGHT = 1200, 600
FPS = 60
FRAME_WIDTH = 128
FRAME_HEIGHT = 128
NUM_IDLE_FRAMES = 9
NUM_WALK_FRAMES = 8
NUM_ATCK_FRAMES = 5
NUM_DEAD_FRAMES = 5
ATTACK_RANGE = 75
ATTACK_COOLDOWN = 30
DAMAGE = 20

pygame.init()
pygame.mixer.pre_init()
pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Samurai Battle Arena")
clock = pygame.time.Clock()

try:
    pygame.mixer.music.load("asset/Epic Japanese Music – Samurai Warrior_1.mp3")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(loops=-1)
except pygame.error as e:
    print(f"Peringatan: Tidak dapat memuat file BGM. Error: {e}")

background = pygame.image.load("asset/Map2.jpg")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

class ClientInterface:
    def __init__(self):
        self.server_address = ('localhost', 5555)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connect_to_server()
        self.idplayer = self.request_id()
        if not self.idplayer:
            print("Tidak dapat terhubung atau mendapatkan ID dari server. Keluar.")
            pygame.quit()
            sys.exit()

    def _connect_to_server(self):
        try:
            print("Menghubungkan ke server...")
            self.sock.connect(self.server_address)
            print("Berhasil terhubung ke server.")
        except socket.error as e:
            print(f"Gagal terhubung ke server di {self.server_address}: {e}")
            self.sock = None

    def send_http_request(self, method, path):
        if not self.sock:
            print("Tidak ada koneksi aktif ke server.")
            return None
        try:
            request = f"{method} {path} HTTP/1.0\r\nHost: localhost\r\n\r\n"
            self.sock.sendall(request.encode())

            data = b""
            while True:
                chunk = self.sock.recv(1024)
                if not chunk:
                    break
                data += chunk
                if b"\r\n\r\n" in data:
                    break

            if b"\r\n\r\n" not in data:
                return None

            _, body = data.split(b"\r\n\r\n", 1)
            return json.loads(body.decode().strip())
        except (socket.error, ConnectionResetError, json.JSONDecodeError) as e:
            print(f"Error komunikasi dengan server: {e}")
            self.disconnect()
            return None

    def request_id(self):
        result = self.send_http_request("GET", "/connect")
        return result.get("id", None) if result else None

    def set_location(self, x, y, attacking=False, facing="right", is_moving=False):
        path = f"/set_location/{self.idplayer}/{x}/{y}/{attacking}/{facing}/{is_moving}"
        return self.send_http_request("POST", path)

    def get_all_players(self):
        result = self.send_http_request("GET", "/get_all_players")
        if result and result["status"] == "OK":
            return result["players"]
        return []

    def send_attack(self, attacker_id, x, y, facing, attack_range):
        path = f"/attack/{attacker_id}/{x}/{y}/{facing}/{attack_range}"
        return self.send_http_request("POST", path)

    def get_players_state(self):
        result = self.send_http_request("GET", "/get_players_state")
        if result and result["status"] == "OK":
            return result["players"]
        return {}

    def disconnect(self):
        if self.sock:
            try:
                self.send_http_request("POST", f"/disconnect/{self.idplayer}")
            except socket.error as e:
                print(f"Gagal mengirim pesan disconnect: {e}")
            finally:
                self.sock.close()
                self.sock = None
                print("Disconnected from server.")


class Samurai:
    def __init__(self, id, isremote=False, client=None):
        self.id = id
        self.isremote = isremote
        self.client = client
        self.x = 100
        self.y = HEIGHT // 2
        self.facing = "right"
        self.is_moving = False
        self.is_attacking = False
        self.is_dead = False
        self.hp = 100
        self.attack_cooldown = 0
        self.hit_flash = 0

        self.idle_sheet = pygame.image.load("asset/Samurai_Archer/Idle.png").convert_alpha()
        self.walk_sheet = pygame.image.load("asset/Samurai_Archer/Walk.png").convert_alpha()
        self.attack_sheet = pygame.image.load("asset/Samurai_Archer/Attack_2.png").convert_alpha()
        self.dead_sheet = pygame.image.load("asset/Samurai_Archer/Dead.png").convert_alpha()

        self.idle_frames = [self.idle_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT)) for i in range(NUM_IDLE_FRAMES)]
        self.walk_frames = [self.walk_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT)) for i in range(NUM_WALK_FRAMES)]
        self.attack_frames = [self.attack_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT)) for i in range(NUM_ATCK_FRAMES)]
        self.dead_frames = [self.dead_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT)) for i in range(NUM_DEAD_FRAMES)]

        self.current_frame = 0
        self.animation_counter = 0
        self.animation_delay = 5
        self.attack_animating = False

        self.is_walking_sound_playing = False
        if not self.isremote:
            try:
                self.walk_sound = pygame.mixer.Sound("asset/Footsteps Grass Sound Effect (HD)_1.mp3")
                self.attack_sound = pygame.mixer.Sound("asset/sword slash (sound effects) __ mani creation ___1_1_1.mp3")
                self.hit_sound = pygame.mixer.Sound("asset/Male Pain_Hurt Sound Effects - 8 Sounds_1_1_1.mp3")
                self.death_sound = pygame.mixer.Sound("asset/Dead Rails Death Sound Effect_1_1.mp3")
                self.walk_sound.set_volume(0.9)
                self.attack_sound.set_volume(0.8)
                self.hit_sound.set_volume(0.7)
                self.death_sound.set_volume(0.5)
            except pygame.error as e:
                print(f"Peringatan: Gagal memuat salah satu file SFX. Error: {e}")
                self.walk_sound = self.attack_sound = self.hit_sound = self.death_sound = None

    def move(self, keys=None):
        if self.isremote or self.is_dead:
            if self.is_walking_sound_playing and self.walk_sound:
                self.walk_sound.stop()
                self.is_walking_sound_playing = False
            return

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        self.is_moving = False

        if keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d]:
            self.is_moving = True
            if keys[pygame.K_w]: self.y -= 4
            if keys[pygame.K_s]: self.y += 4
            if keys[pygame.K_a]:
                self.x -= 4
                self.facing = "left"
            if keys[pygame.K_d]:
                self.x += 4
                self.facing = "right"

        if keys[pygame.K_SPACE] and self.attack_cooldown == 0:
            self.is_attacking = True
            self.attack_animating = True
            self.current_frame = 0
            self.attack_cooldown = ATTACK_COOLDOWN
            if self.attack_sound: self.attack_sound.play()
            self.client.send_attack(self.id, self.x, self.y, self.facing, ATTACK_RANGE)

        if self.walk_sound:
            if self.is_moving and not self.is_walking_sound_playing:
                self.walk_sound.play(loops=-1)
                self.is_walking_sound_playing = True
            elif not self.is_moving and self.is_walking_sound_playing:
                self.walk_sound.stop()
                self.is_walking_sound_playing = False

        self.x = max(0, min(self.x, WIDTH - FRAME_WIDTH))
        self.y = max(0, min(self.y, HEIGHT - FRAME_HEIGHT))

        self.client.set_location(self.x, self.y, self.is_attacking, self.facing, self.is_moving)

    def draw(self, surface):
        self.animation_counter += 1
        if self.animation_counter >= self.animation_delay:
            self.animation_counter = 0
            self.current_frame += 1

        if self.is_dead:
            frames = self.dead_frames
            if self.current_frame >= len(frames):
                self.current_frame = len(frames) - 1
        elif self.attack_animating:
            frames = self.attack_frames
            if self.current_frame >= len(frames):
                self.current_frame = 0
                self.attack_animating = False
                self.is_attacking = False
        elif self.is_moving:
            frames = self.walk_frames
            if self.current_frame >= len(frames):
                self.current_frame = 0
        else:
            frames = self.idle_frames
            if self.current_frame >= len(frames):
                self.current_frame = 0

        frame = frames[self.current_frame]
        if self.facing == "left":
            frame = pygame.transform.flip(frame, True, False)
        surface.blit(frame, (self.x, self.y))

        health_width = 50
        health_height = 5
        health_x = self.x + (FRAME_WIDTH - health_width) // 2
        health_y = self.y - 10
        pygame.draw.rect(surface, (100, 100, 100), (health_x, health_y, health_width, health_height))
        health_fill = (self.hp / 100) * health_width
        pygame.draw.rect(surface, (0, 255, 0), (health_x, health_y, health_fill, health_height))

        if self.is_dead:
            font = pygame.font.SysFont(None, 24)
            text = font.render("DEAD", True, (255, 0, 0))
            surface.blit(text, (self.x + FRAME_WIDTH // 2 - text.get_width() // 2, self.y - 30))

def draw_game_over_screen():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    font_game_over = pygame.font.SysFont('Arial', 80, bold=True)
    text_game_over = font_game_over.render("ANDA MATI", True, (255, 50, 50))
    text_rect_go = text_game_over.get_rect(center=(WIDTH/2, HEIGHT/2 - 40))
    screen.blit(text_game_over, text_rect_go)

    font_prompt = pygame.font.SysFont('Arial', 30)
    text_prompt = font_prompt.render("Tekan ENTER untuk keluar", True, (255, 255, 255))
    text_rect_prompt = text_prompt.get_rect(center=(WIDTH/2, HEIGHT/2 + 40))
    screen.blit(text_prompt, text_rect_prompt)

client = ClientInterface()

current_player = Samurai(client.idplayer, isremote=False, client=client)

players = {}

all_player_ids = client.get_all_players()
if all_player_ids:
    for pid in all_player_ids:
        if pid != current_player.id:
            players[pid] = Samurai(pid, isremote=True, client=client)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if current_player.is_dead and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                running = False

    if not current_player.is_dead:
        keys = pygame.key.get_pressed()
        current_player.move(keys)

        players_state = client.get_players_state()
        if players_state is None:
            print("Koneksi ke server hilang, game akan berhenti.")
            running = False
            continue

        for pid, state in players_state.items():
            if pid == current_player.id:
                if current_player.hp > state["hp"] and current_player.hit_sound:
                    current_player.hit_sound.play()
                
                if not current_player.is_dead and state["is_dead"] and current_player.death_sound:
                    current_player.death_sound.play()

                current_player.hp = state["hp"]
                current_player.is_dead = state["is_dead"]

            elif pid in players:
                p = players[pid]
                p.x = state["x"]
                p.y = state["y"]
                p.hp = state["hp"]
                p.is_dead = state["is_dead"]
                p.facing = state["facing"]
                p.is_moving = state["is_moving"]
                p.is_attacking = state["attacking"]
                if p.is_attacking:
                    p.attack_animating = True
                    p.current_frame = 0
            elif pid not in players:
                players[pid] = Samurai(pid, isremote=True, client=client)

        current_server_pids = set(players_state.keys())
        client_pids_to_remove = []
        for pid in players:
            if pid not in current_server_pids:
                client_pids_to_remove.append(pid)
        for pid in client_pids_to_remove:
            del players[pid]

        screen.blit(background, (0, 0))
        current_player.draw(screen)
        for samurai in players.values():
            samurai.draw(screen)

    else: 
        screen.blit(background, (0, 0))
        for samurai in players.values():
            samurai.draw(screen)
        current_player.draw(screen)
        draw_game_over_screen()

    pygame.display.flip()
    clock.tick(FPS)

client.disconnect()
pygame.quit()
sys.exit()
