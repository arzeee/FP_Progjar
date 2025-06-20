import pygame
import sys

# Inisialisasi Pygame
pygame.init()

WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Samurai Battle Arena")

clock = pygame.time.Clock()
FPS = 60

# Ukuran frame berdasarkan sprite sheet
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
        self.damage = 20
        self.isremote = isremote
        self.direction = "down"
        self.facing = "right"
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.speed = 3
        self.is_moving = False
        self.is_attacking = False
        self.attack_done = False
        self.show_box = False
        self.is_dead = False
        self.death_done = False

        

        # coba
        # self.last_hp_tick = pygame.time.get_ticks()
        # self.hp_interval = 1000  # dalam milidetik (1 detik)


        self.idle_sheet = pygame.image.load("asset/craftpix-net-123681-free-samurai-pixel-art-sprite-sheets/Samurai_Archer/Idle.png").convert_alpha()
        self.walk_sheet = pygame.image.load("asset/craftpix-net-123681-free-samurai-pixel-art-sprite-sheets/Samurai_Archer/Walk.png").convert_alpha()
        self.attack_sheet = pygame.image.load("asset/craftpix-net-123681-free-samurai-pixel-art-sprite-sheets/Samurai_Archer/Attack_2.png").convert_alpha()
        self.dead_sheet = pygame.image.load("asset/craftpix-net-123681-free-samurai-pixel-art-sprite-sheets/Samurai_Archer/Dead.png").convert_alpha()

        self.idle_frames = [
            self.idle_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT))
            for i in range(NUM_IDLE_FRAMES)
        ]
        self.walk_frames = [
            self.walk_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT))
            for i in range(NUM_WALK_FRAMES)
        ]
        self.attack_frames = [
            self.attack_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT))
            for i in range(NUM_ATCK_FRAMES)
        ]
        self.dead_frames = [
            self.dead_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT))
            for i in range(NUM_DEAD_FRAMES)
        ]

        self.current_frame = 0
        self.animation_counter = 0
        self.animation_delay = 10
        self.animation_atck_delay = 4
        self.animation_dead_delay = 10

    # coba
   #  def update_hp_per_second(self):
   #    now = pygame.time.get_ticks()
   #    if not self.is_dead and now - self.last_hp_tick >= self.hp_interval:
   #      self.hp = max(0, self.hp - 20)
   #      self.last_hp_tick = now
   #      if self.hp == 0:
   #          self.is_dead = True
   #          self.current_frame = 0
   #          self.animation_counter = 0


    def move(self, keys):
        if self.isremote or self.is_attacking or self.is_dead:
            return

        prev_state = self.is_moving
        self.is_moving = False

        if keys[pygame.K_UP]:
            self.y -= self.speed
            self.direction = "up"
            self.is_moving = True
        elif keys[pygame.K_DOWN]:
            self.y += self.speed
            self.direction = "down"
            self.is_moving = True
        elif keys[pygame.K_LEFT]:
            self.x -= self.speed
            self.direction = "left"
            self.facing = "left"
            self.is_moving = True
        elif keys[pygame.K_RIGHT]:
            self.x += self.speed
            self.direction = "right"
            self.facing = "right"
            self.is_moving = True

        if self.is_moving and not prev_state:
            self.current_frame = 0
            self.animation_counter = 0

    def attack(self, enemies):
        if self.is_dead:
            return

        range_width = 40
        range_height = 80
        offset_x = -37.5
        if self.facing == "right":
            range_rect = pygame.Rect(self.x + FRAME_WIDTH + offset_x, self.y + 30, range_width, range_height)
        else:
            range_rect = pygame.Rect(self.x - range_width - offset_x, self.y + 30, range_width, range_height)

        for enemy in enemies:
            if enemy.hp > 0 and range_rect.colliderect(enemy.get_hitbox()):
                enemy.hp = max(0, enemy.hp - self.damage)
                if enemy.hp == 0:
                    enemy.is_dead = True
                    enemy.current_frame = 0
                    enemy.animation_counter = 0

    def get_hitbox(self):
        return pygame.Rect(self.x + 40, self.y + 50, 45, 80)

    def draw(self, surface, enemies=[]):
        self.animation_counter += 1

        if self.is_dead:
            if self.current_frame < len(self.dead_frames) - 1:
                if self.animation_counter >= self.animation_dead_delay:
                    self.animation_counter = 0
                    self.current_frame += 1
            image = self.dead_frames[self.current_frame]

        elif self.is_attacking:
            if self.animation_counter >= self.animation_atck_delay:
                self.animation_counter = 0
                self.current_frame += 1

                if self.current_frame == len(self.attack_frames) // 2 and not self.attack_done:
                    self.attack(enemies)
                    self.attack_done = True

                if self.current_frame >= len(self.attack_frames):
                    self.current_frame = 0
                    self.is_attacking = False
                    self.attack_done = False

            image = self.attack_frames[self.current_frame]

        elif self.is_moving:
            if self.animation_counter >= self.animation_delay:
                self.animation_counter = 0
                self.current_frame = (self.current_frame + 1) % len(self.walk_frames)
            image = self.walk_frames[self.current_frame]

        else:
            if self.current_frame >= len(self.idle_frames):
                self.current_frame = 0
            if self.animation_counter >= self.animation_delay:
                self.animation_counter = 0
                self.current_frame = (self.current_frame + 1) % len(self.idle_frames)
            image = self.idle_frames[self.current_frame]

        if self.facing == "left":
            image = pygame.transform.flip(image, True, False)

        surface.blit(image, (self.x, self.y))

        # Kotak range attack & hitbox jika masih hidup
        if not self.is_dead and not self.show_box:
            range_width = 40
            range_height = 80
            offset_x = -37.5
            if self.facing == "right":
                range_rect = pygame.Rect(self.x + FRAME_WIDTH + offset_x, self.y + 30, range_width, range_height)
            else:
                range_rect = pygame.Rect(self.x - range_width - offset_x, self.y + 30, range_width, range_height)
            pygame.draw.rect(surface, (255, 0, 0), range_rect, 2)

            pygame.draw.rect(surface, (0, 0, 255), self.get_hitbox(), 2)

        # Health bar
        bar_width = 60
        bar_height = 8
        health_ratio = self.hp / 100
        bar_x = self.x + (FRAME_WIDTH - bar_width) // 2
        bar_y = self.y + 20
        pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

# Buat pemain utama
current_player = Samurai("1")

# Pemain lain
players = {
    "2": Samurai("2", isremote=True),
    "3": Samurai("3", isremote=True)
}
players["2"].x = 200
players["2"].y = 250
players["3"].x = 400
players["3"].y = 250

# Game Loop
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
                current_player.attack_done = False

    keys = pygame.key.get_pressed()
    current_player.move(keys)
    current_player.draw(screen, enemies=[p for p in players.values()])
    #current_player.update_hp_per_second()


    for p in players.values():
        p.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
