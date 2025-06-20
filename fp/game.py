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

class Samurai:
   def __init__(self, id='1', isremote=False):
      self.id = id
      self.hp = 100
      self.damage = 20
      self.isremote = isremote
      self.direction = "down"
      self.x = WIDTH // 2
      self.y = HEIGHT // 2
      self.speed = 3
      self.is_moving = False
      self.is_attacking = False

      # Load sprite sheets
      self.idle_sheet = pygame.image.load("asset/craftpix-net-123681-free-samurai-pixel-art-sprite-sheets/Samurai_Archer/Idle.png").convert_alpha()
      self.walk_sheet = pygame.image.load("asset/craftpix-net-123681-free-samurai-pixel-art-sprite-sheets/Samurai_Archer/Walk.png").convert_alpha()
      self.attack_sheet = pygame.image.load("asset/craftpix-net-123681-free-samurai-pixel-art-sprite-sheets/Samurai_Archer/Attack_2.png").convert_alpha()

      # Ambil frame idle
      self.idle_frames = [
            self.idle_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT))
            for i in range(NUM_IDLE_FRAMES)
      ]

      # Ambil frame jalan
      self.walk_frames = [
            self.walk_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT))
            for i in range(NUM_WALK_FRAMES)
      ]

      # Ambil frame attack
      self.attack_frames = [
            self.attack_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT))
            for i in range(NUM_ATCK_FRAMES)
      ]

      # Animasi
      self.current_frame = 0
      self.animation_counter = 0
      self.animation_delay = 10
      self.animation_atck_delay = 4

   def move(self, keys):
      if not self.isremote and not self.is_attacking:  # hanya bisa gerak kalau tidak sedang attack
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
            self.is_moving = True
         elif keys[pygame.K_RIGHT]:
            self.x += self.speed
            self.direction = "right"
            self.is_moving = True

         if self.is_moving and not prev_state:
               self.current_frame = 0
               self.animation_counter = 0

   def draw(self, surface):
      self.animation_counter += 1

      if self.is_attacking:
         if self.animation_counter >= self.animation_atck_delay:
            self.animation_counter = 0
            self.current_frame += 1
            if self.current_frame >= len(self.attack_frames):
               self.current_frame = 0
               self.is_attacking = False
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

      surface.blit(image, (self.x, self.y))

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

class Samurai:
    def __init__(self, id='1', isremote=False):
        self.id = id
        self.hp = 100
        self.damage = 20
        self.isremote = isremote
        self.direction = "down"
        self.facing = "right"  # hadap kanan default
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.speed = 3
        self.is_moving = False
        self.is_attacking = False

        self.idle_sheet = pygame.image.load("asset/craftpix-net-123681-free-samurai-pixel-art-sprite-sheets/Samurai_Archer/Idle.png").convert_alpha()
        self.walk_sheet = pygame.image.load("asset/craftpix-net-123681-free-samurai-pixel-art-sprite-sheets/Samurai_Archer/Walk.png").convert_alpha()
        self.attack_sheet = pygame.image.load("asset/craftpix-net-123681-free-samurai-pixel-art-sprite-sheets/Samurai_Archer/Attack_2.png").convert_alpha()

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

        self.current_frame = 0
        self.animation_counter = 0
        self.animation_delay = 10
        self.animation_atck_delay = 4

    def move(self, keys):
        if not self.isremote and not self.is_attacking:
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

    def draw(self, surface):
        self.animation_counter += 1

        if self.is_attacking:
            if self.animation_counter >= self.animation_atck_delay:
                self.animation_counter = 0
                self.current_frame += 1
                if self.current_frame >= len(self.attack_frames):
                    self.current_frame = 0
                    self.is_attacking = False
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

        # Balik arah jika menghadap kiri
        if self.facing == "left":
            image = pygame.transform.flip(image, True, False)

        surface.blit(image, (self.x, self.y))

        # Kotak indikasi range attack
        range_width = 40
        range_height = 80
        offset_x = -37.5
        if self.facing == "right":
            range_rect = pygame.Rect(self.x + FRAME_WIDTH + offset_x, self.y + 30, range_width, range_height)
        else:
            range_rect = pygame.Rect(self.x - range_width - offset_x, self.y + 30, range_width, range_height)
        pygame.draw.rect(surface, (255, 0, 0), range_rect, 2)

        # Health bar
        bar_width = 60
        bar_height = 8
        health_ratio = self.hp / 100  # anggap maksimal HP = 100
        bar_x = self.x + (FRAME_WIDTH - bar_width) // 2
        bar_y = self.y + 20

        # Bar background (merah)
        pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # Bar HP (hijau)
        pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

         
         

# Buat pemain utama
current_player = Samurai("1")

# Pemain lain (diam)
players = {
    "2": Samurai("2", isremote=True),
    "3": Samurai("3", isremote=True)
}

# Game Loop
while True:
    screen.fill((255, 255, 255))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_k and not current_player.is_attacking:
                current_player.is_attacking = True
                current_player.current_frame = 0
                current_player.animation_counter = 0

    keys = pygame.key.get_pressed()
    current_player.move(keys)
    current_player.draw(screen)

    for p in players.values():
        p.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

# Buat pemain utama
current_player = Samurai("1")

# Pemain lain (tetap diam)
players = {
   "2": Samurai("2", isremote=True),
   "3": Samurai("3", isremote=True)
}

# Game Loop
while True:
   screen.fill((255, 255, 255))

   for event in pygame.event.get():
      if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
      elif event.type == pygame.KEYDOWN:
         if event.key == pygame.K_k and not current_player.is_attacking:
            current_player.is_attacking = True
            current_player.current_frame = 0
            current_player.animation_counter = 0

   keys = pygame.key.get_pressed()
   current_player.move(keys)
   current_player.draw(screen)

   for p in players.values():
      p.draw(screen)

   pygame.display.flip()
   clock.tick(FPS)
