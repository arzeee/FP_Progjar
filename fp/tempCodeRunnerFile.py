import pygame
import sys

# Initialize Pygame
pygame.init()

WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("samurai battle arena")

clock = pygame.time.Clock()
FPS = 60

# Ukuran asli frame di sprite sheet
FRAME_WIDTH = 64
FRAME_HEIGHT = 64
NUM_FRAMES = 5  # jumlah frame dalam 1 baris

class samurai:
    def __init__(self, id='1', isremote=False):
        self.id = id
        self.isremote = isremote
        self.direction = "down"
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.speed = 5

        # Load sprite sheet
        self.sheet = pygame.image.load("asset\craftpix-net-123681-free-samurai-pixel-art-sprite-sheets\Samurai_Commander\Idle.png").convert_alpha()

        # Potong setiap frame dari sprite sheet
        self.frames = []
        for i in range(NUM_FRAMES):
            frame = self.sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT))
            self.frames.append(frame)

        # Kontrol animasi
        self.current_frame = 0
        self.animation_counter = 0
        self.animation_delay = 50  # semakin kecil semakin cepat animasinya

    def move(self, keys):
        if not self.isremote:
            if keys[pygame.K_UP]:
                self.y -= self.speed
                self.direction = "up"
            elif keys[pygame.K_DOWN]:
                self.y += self.speed
                self.direction = "down"
            elif keys[pygame.K_LEFT]:
                self.x -= self.speed
                self.direction = "left"
            elif keys[pygame.K_RIGHT]:
                self.x += self.speed
                self.direction = "right"

    def draw(self, surface):
        self.animation_counter += 1
        if self.animation_counter >= self.animation_delay:
            self.animation_counter = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)

        surface.blit(self.frames[self.current_frame], (self.x, self.y))

# Simulasi pemain utama
current_player = samurai("1")

# Simulasi pemain lain (tetap diam)
players = {
    "2": samurai("2", isremote=True),
    "3": samurai("3", isremote=True)
}

# Game Loop
while True:
    screen.fill((255, 255, 255))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    current_player.move(keys)
    current_player.draw(screen)

    for p in players.values():
        p.move(keys)
        p.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
