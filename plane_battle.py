import random
import sys
from dataclasses import dataclass

import pygame

# Screen dimensions
WIDTH, HEIGHT = 480, 640
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 60)
GREEN = (34, 177, 76)
BLUE = (65, 105, 225)
YELLOW = (255, 215, 0)


@dataclass
class Bullet:
    rect: pygame.Rect
    speed: float
    damage: int
    color: tuple

    def update(self):
        self.rect.y += self.speed

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.color, self.rect)


class Player:
    def __init__(self, x: int, y: int):
        self.rect = pygame.Rect(x, y, 48, 48)
        self.speed = 5
        self.max_health = 12
        self.health = self.max_health
        self.cooldown = 0

    def move(self, dx: int, dy: int):
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x + dx * self.speed))
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y + dy * self.speed))

    def shoot(self):
        if self.cooldown == 0:
            bullet_rect = pygame.Rect(self.rect.centerx - 3, self.rect.top - 12, 6, 12)
            bullet = Bullet(bullet_rect, -10, 2, YELLOW)
            self.cooldown = 10
            return bullet
        return None

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, BLUE, self.rect)


class Enemy:
    def __init__(self):
        width, height = 40, 40
        x = random.randint(0, WIDTH - width)
        y = random.randint(-120, -40)
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = random.uniform(2, 3.5)
        self.max_health = 6
        self.health = self.max_health
        self.shoot_timer = random.randint(60, 120)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.rect.y = random.randint(-200, -60)
            self.rect.x = random.randint(0, WIDTH - self.rect.width)
            self.health = self.max_health

        self.shoot_timer -= 1

    def ready_to_shoot(self) -> bool:
        return self.shoot_timer <= 0

    def reset_shoot_timer(self):
        self.shoot_timer = random.randint(75, 140)

    def shoot(self):
        bullet_rect = pygame.Rect(self.rect.centerx - 4, self.rect.bottom, 8, 14)
        return Bullet(bullet_rect, 5, 1, RED)

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, RED, self.rect)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("简易飞机大战")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("SimHei", 20)

        self.player = Player(WIDTH // 2 - 24, HEIGHT - 80)
        self.enemies = [Enemy() for _ in range(4)]
        self.player_bullets: list[Bullet] = []
        self.enemy_bullets: list[Bullet] = []
        self.score = 0
        self.running = True
        self.game_over = False

    def spawn_enemy(self):
        self.enemies.append(Enemy())

    def handle_input(self):
        keys = pygame.key.get_pressed()
        dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        self.player.move(dx, dy)

    def update(self):
        self.player.update()
        for enemy in self.enemies:
            enemy.update()
            if enemy.ready_to_shoot():
                self.enemy_bullets.append(enemy.shoot())
                enemy.reset_shoot_timer()

        for bullet in self.player_bullets[:]:
            bullet.update()
            if bullet.rect.bottom < 0:
                self.player_bullets.remove(bullet)

        for bullet in self.enemy_bullets[:]:
            bullet.update()
            if bullet.rect.top > HEIGHT:
                self.enemy_bullets.remove(bullet)

        self.handle_collisions()

        # Slightly increase difficulty over time
        if random.random() < 0.002 and len(self.enemies) < 8:
            self.spawn_enemy()

    def handle_collisions(self):
        for enemy in self.enemies[:]:
            for bullet in self.player_bullets[:]:
                if enemy.rect.colliderect(bullet.rect):
                    enemy.health -= bullet.damage
                    self.player_bullets.remove(bullet)
                    if enemy.health <= 0:
                        self.score += 100
                        self.enemies.remove(enemy)
                        self.spawn_enemy()
                    break

            if enemy.rect.colliderect(self.player.rect):
                self.player.health -= 2
                enemy.health = 0
                enemy.rect.y = HEIGHT + 100

        for bullet in self.enemy_bullets[:]:
            if bullet.rect.colliderect(self.player.rect):
                self.player.health -= bullet.damage
                self.enemy_bullets.remove(bullet)

        self.player.health = max(self.player.health, 0)
        if self.player.health <= 0:
            self.game_over = True

    def draw_health_bar(self, x: int, y: int, current: int, maximum: int, color: tuple):
        bar_width = 120
        bar_height = 14
        ratio = current / maximum if maximum > 0 else 0
        pygame.draw.rect(self.screen, WHITE, (x - 2, y - 2, bar_width + 4, bar_height + 4), 1)
        pygame.draw.rect(self.screen, color, (x, y, bar_width * ratio, bar_height))

    def draw_ui(self):
        self.draw_health_bar(20, HEIGHT - 30, self.player.health, self.player.max_health, BLUE)
        player_text = self.font.render(f"我方血量: {self.player.health}/{self.player.max_health}", True, WHITE)
        self.screen.blit(player_text, (20, HEIGHT - 55))

        enemy_health = sum(enemy.health for enemy in self.enemies)
        enemy_text = self.font.render(f"敌方总血量: {enemy_health}", True, WHITE)
        self.screen.blit(enemy_text, (20, 20))

        score_text = self.font.render(f"得分: {self.score}", True, WHITE)
        self.screen.blit(score_text, (WIDTH - 150, 20))

    def draw(self):
        self.screen.fill(BLACK)
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for bullet in self.player_bullets:
            bullet.draw(self.screen)
        for bullet in self.enemy_bullets:
            bullet.draw(self.screen)
        self.draw_ui()

        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            text = self.font.render("游戏结束 - 按 R 重来", True, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(text, text_rect)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.game_over:
                        bullet = self.player.shoot()
                        if bullet:
                            self.player_bullets.append(bullet)
                    if event.key == pygame.K_r and self.game_over:
                        self.__init__()
                elif event.type == pygame.KEYUP:
                    pass

            if not self.game_over:
                self.handle_input()
                self.update()

            self.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
