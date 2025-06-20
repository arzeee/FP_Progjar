import pygame
import socket
import pickle
import sys

WIDTH, HEIGHT = 600, 400
PLAYER_SIZE = 50
VELOCITY = 5
BULLET_SPEED = 7
MAX_HP = 100

# Warna
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("localhost", 5555))

player_pos = pickle.loads(client_socket.recv(1024))
player_hp = MAX_HP
enemy_pos = {"x": 0, "y": 0}
enemy_hp = MAX_HP

bullets = []
last_direction = "RIGHT"  # default arah awal

def send_and_receive(pos):
    try:
        client_socket.send(pickle.dumps(pos))
        return pickle.loads(client_socket.recv(1024))
    except:
        return None

def draw_hp_bar(screen, x, y, hp):
    hp_ratio = hp / MAX_HP
    pygame.draw.rect(screen, RED, (x, y, PLAYER_SIZE, 5))
    pygame.draw.rect(screen, GREEN, (x, y, PLAYER_SIZE * hp_ratio, 5))

def game_over_screen(screen, text):
    font = pygame.font.SysFont("Arial", 48)
    label = font.render(text, True, BLACK)
    screen.blit(label, (WIDTH // 2 - label.get_width() // 2, HEIGHT // 2 - label.get_height() // 2))
    pygame.display.update()
    pygame.time.delay(3000)

def main():
    global player_pos, player_hp, enemy_pos, enemy_hp, last_direction

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Multiplayer Battle Arena")

    clock = pygame.time.Clock()
    run = True

    while run:
        clock.tick(60)
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        keys = pygame.key.get_pressed()
        move = False

        # Gerakan player + simpan arah terakhir
        if keys[pygame.K_LEFT] and player_pos["x"] > 0:
            player_pos["x"] -= VELOCITY
            last_direction = "LEFT"
            move = True
        if keys[pygame.K_RIGHT] and player_pos["x"] < WIDTH - PLAYER_SIZE:
            player_pos["x"] += VELOCITY
            last_direction = "RIGHT"
            move = True
        if keys[pygame.K_UP] and player_pos["y"] > 0:
            player_pos["y"] -= VELOCITY
            last_direction = "UP"
            move = True
        if keys[pygame.K_DOWN] and player_pos["y"] < HEIGHT - PLAYER_SIZE:
            player_pos["y"] += VELOCITY
            last_direction = "DOWN"
            move = True

        # Tembak peluru
        if keys[pygame.K_SPACE]:
            bullets.append({
                "x": player_pos["x"] + PLAYER_SIZE // 2,
                "y": player_pos["y"] + PLAYER_SIZE // 2,
                "dir": last_direction
            })

        # Update peluru
        for bullet in bullets[:]:
            if bullet["dir"] == "LEFT":
                bullet["x"] -= BULLET_SPEED
            elif bullet["dir"] == "RIGHT":
                bullet["x"] += BULLET_SPEED
            elif bullet["dir"] == "UP":
                bullet["y"] -= BULLET_SPEED
            elif bullet["dir"] == "DOWN":
                bullet["y"] += BULLET_SPEED

            # Hapus jika keluar layar
            if not (0 <= bullet["x"] <= WIDTH and 0 <= bullet["y"] <= HEIGHT):
                bullets.remove(bullet)
                continue

            # Cek tabrakan dengan musuh
            if (enemy_pos["x"] < bullet["x"] < enemy_pos["x"] + PLAYER_SIZE and
                enemy_pos["y"] < bullet["y"] < enemy_pos["y"] + PLAYER_SIZE):
                bullets.remove(bullet)
                enemy_hp = max(0, enemy_hp - 10)

        # Sync posisi player
        enemy_data = send_and_receive(player_pos)
        if enemy_data:
            enemy_pos = enemy_data

        # Cek game over
        if enemy_hp <= 0:
            game_over_screen(screen, "Kamu Menang!")
            break
        if player_hp <= 0:
            game_over_screen(screen, "Kamu Kalah!")
            break

        # Gambar player dan musuh
        pygame.draw.rect(screen, BLUE, (player_pos["x"], player_pos["y"], PLAYER_SIZE, PLAYER_SIZE))
        draw_hp_bar(screen, player_pos["x"], player_pos["y"] - 10, player_hp)

        pygame.draw.rect(screen, RED, (enemy_pos["x"], enemy_pos["y"], PLAYER_SIZE, PLAYER_SIZE))
        draw_hp_bar(screen, enemy_pos["x"], enemy_pos["y"] - 10, enemy_hp)

        # Gambar peluru
        for bullet in bullets:
            pygame.draw.rect(screen, BLACK, (bullet["x"], bullet["y"], 10, 5))

        pygame.display.update()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
