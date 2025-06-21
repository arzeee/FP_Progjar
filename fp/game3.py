import pygame
import socket
import pickle
import sys

# Socket setup
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("localhost", 5555))
client_id = str(pickle.loads(client_socket.recv(1024)))
print(f"Connected as Player {client_id}")

# Pygame setup
pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Samurai Battle Arena")
clock = pygame.time.Clock()
FPS = 60

FRAME_WIDTH = 128
FRAME_HEIGHT = 128
NUM_IDLE_FRAMES = 9
NUM_WALK_FRAMES = 8
NUM_ATCK_FRAMES = 5
NUM_DEAD_FRAMES = 5

class Samurai:
    def __init__(self, id='1', isremote=False):
        self.id = id
        self.hp = 100
        self.isremote = isremote
        self.is_dead = False
        self.is_attacking = False
        self.facing = "right"
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.speed = 3
        self.is_moving = False
        self.current_frame = 0
        self.animation_counter = 0
        self.animation_delay = 10
        self.attack_delay = 4
        self.dead_delay = 10

        # Load sprites
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
            return
        self.is_moving = False
        if keys[pygame.K_UP]:
            self.y -= self.speed
            self.is_moving = True
        elif keys[pygame.K_DOWN]:
            self.y += self.speed
            self.is_moving = True
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
            self.facing = "left"
            self.is_moving = True
        elif keys[pygame.K_RIGHT]:
            self.x += self.speed
            self.facing = "right"
            self.is_moving = True
        if self.is_moving:
            self.current_frame = 0
            self.animation_counter = 0

    def get_hitbox(self):
        return pygame.Rect(self.x + 40, self.y + 50, 45, 80)

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
            frame = self.dead_frames[min(self.current_frame, len(self.dead_frames) - 1)]
        elif self.is_attacking:
            if self.animation_counter >= self.attack_delay:
                self.animation_counter = 0
                self.current_frame += 1
                if self.current_frame >= len(self.attack_frames):
                    self.current_frame = 0
                    self.is_attacking = False
            frame = self.attack_frames[min(self.current_frame, len(self.attack_frames) - 1)]
        elif self.is_moving:
            if self.animation_counter >= self.animation_delay:
                self.animation_counter = 0
                self.current_frame = (self.current_frame + 1) % len(self.walk_frames)
            frame = self.walk_frames[self.current_frame]
        else:
            if self.animation_counter >= self.animation_delay:
                self.animation_counter = 0
                self.current_frame = (self.current_frame + 1) % len(self.idle_frames)
            frame = self.idle_frames[self.current_frame]

        if self.facing == "left":
            frame = pygame.transform.flip(frame, True, False)

        surface.blit(frame, (self.x, self.y))

        # HP Bar
        bar_width = 60
        bar_height = 8
        health_ratio = self.hp / 100
        bar_x = self.x + (FRAME_WIDTH - bar_width) // 2
        bar_y = self.y + 20
        pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

def sync_with_server(player):
    try:
        send_data = {
            "id": player.id,
            "x": player.x,
            "y": player.y,
            "is_attacking": player.is_attacking
        }
        if player.is_attacking:
            r = player.get_attack_range_rect()
            send_data["attack_range"] = [r.x, r.y, r.width, r.height]

        client_socket.sendall(pickle.dumps(send_data))
        return pickle.loads(client_socket.recv(4096))
    except:
        print("Koneksi ke server terputus.")
        pygame.quit()
        sys.exit()

# Inisialisasi player lokal
current_player = Samurai(client_id)

# Inisialisasi slot player lain
players = {
    pid: Samurai(pid, isremote=True)
    for pid in ['1', '2'] if pid != client_id
}

# Game loop
while True:
    screen.fill((255, 255, 255))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_k and not current_player.is_attacking and not current_player.is_dead:
                current_player.is_attacking = True
                current_player.current_frame = 0
                current_player.animation_counter = 0

    keys = pygame.key.get_pressed()
    current_player.move(keys)

    # Sync
    state = sync_with_server(current_player)
    if state:
        all_data = state.get("players", {})
        for pid, pdata in all_data.items():
            if pid == current_player.id:
                current_player.hp = pdata["hp"]
                current_player.is_dead = pdata["is_dead"]
            elif pid in players:
                p = players[pid]
                p.x = pdata["x"]
                p.y = pdata["y"]
                p.hp = pdata["hp"]
                p.is_attacking = pdata["is_attacking"]
                p.is_dead = pdata["is_dead"]

    # Render
    current_player.draw(screen)
    for p in players.values():
        p.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
