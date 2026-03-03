import pygame
import time
import os

class Bullet:
    def __init__(self, x, y, speed=10, color=(255, 255, 255), width=10, height=5, sprite=None):
        """Projectile. Supports a sprite (path or Surface) or falls back to a rect.

        x,y are the intended center x,y (keeps compatibility with previous code that
        used rect.right / centery values). If sprite is provided and loadable,
        the image is scaled to (width, height) and its rect is centered at (x,y).
        """
        self.speed = speed
        self.color = color
        self.image = None
        # load sprite if provided
        if sprite:
            try:
                img = None
                if isinstance(sprite, pygame.Surface):
                    img = sprite
                else:
                    # try absolute/relative path
                    if os.path.exists(sprite):
                        img = pygame.image.load(sprite).convert_alpha()
                    else:
                        base = os.path.dirname(__file__)
                        alt = os.path.join(base, '..', sprite)
                        if os.path.exists(alt):
                            img = pygame.image.load(alt).convert_alpha()
                if img:
                    # ensure the sprite is exactly the requested size
                    try:
                        scaled = pygame.transform.scale(img, (width, height))
                    except Exception:
                        scaled = img
                    # flip projectile image if it's moving left
                    if self.speed < 0:
                        try:
                            scaled = pygame.transform.flip(scaled, True, False)
                        except Exception:
                            pass
                    self.image = scaled
                    # use center coordinates (x,y) as intended
                    self.rect = self.image.get_rect(center=(x, y))
                else:
                    # when no sprite is available, make a rect centered at (x,y)
                    self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
            except Exception:
                self.image = None
                # fallback: ensure rect is centered at (x,y)
                self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        else:
            # no sprite: center the fallback rect on (x,y)
            self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)

    def update(self, screen):
        self.rect.x += self.speed
        if self.image:
            try:
                screen.blit(self.image, self.rect)
            except Exception:
                # fallback to rect if blit fails
                pygame.draw.rect(screen, self.color, self.rect)
        else:
            pygame.draw.rect(screen, self.color, self.rect)


class Player:
    def __init__(self, x, y, color=(0, 255, 0), shoot_cooldown=0.3, bullet_speed=10,
                 character="Ryu", special="fireball", sprite=None, size=40):
        # position/size
        self.size = size
        self.rect = pygame.Rect(x, y, self.size, self.size)
        # gameplay
        self.color = color
        self.speed = 5
        self.bullets = []
        self.shoot_cooldown = shoot_cooldown
        self.last_shot_time = 0
        self.lives = 3
        self.invulnerable = False
        self.invulnerable_start = 0
        self.bullet_speed = bullet_speed
        self.character = character
        self.special = special
        # appearance
        self.sprite = None
        if sprite:
            try:
                # allow passing a pygame.Surface directly
                if isinstance(sprite, pygame.Surface):
                    self.sprite = pygame.transform.scale(sprite, (self.size, self.size))
                else:
                    # treat sprite as a path
                    if os.path.exists(sprite):
                        img = pygame.image.load(sprite).convert_alpha()
                        self.sprite = pygame.transform.scale(img, (self.size, self.size))
                    else:
                        # try relative to project root/assets
                        base = os.path.dirname(__file__)
                        alt = os.path.join(base, '..', sprite)
                        if os.path.exists(alt):
                            img = pygame.image.load(alt).convert_alpha()
                            self.sprite = pygame.transform.scale(img, (self.size, self.size))
            except Exception:
                self.sprite = None

        # accept sprite paths/surfaces for bullets/specials via kwargs on construction
        # (these may be set by the game code after importing Player)
        # NOTE: code that constructs Player may fill self.bullet_sprite / self.special_sprite
        # directly if desired.
        self.bullet_sprite = None
        self.special_sprite = None
        self.last_special_time = 0

    def move_up(self):
        self.rect.y -= self.speed
        if self.rect.y < 0:
            self.rect.y = 0

    def move_down(self):
        self.rect.y += self.speed
        # clamp to current display height (handles resizable window)
        try:
            surf = pygame.display.get_surface()
            max_h = surf.get_height() if surf else 600
        except Exception:
            max_h = 600
        if self.rect.y > max_h - self.rect.height:
            self.rect.y = max_h - self.rect.height

    def shoot(self):
        current_time = time.time()
        if (current_time - self.last_shot_time) >= self.shoot_cooldown:
            x = self.rect.right if self.bullet_speed > 0 else self.rect.left - 10
            # projectile size: make both width and height 1/3 of player size (with minimums)
            bw = max(8, int(self.size / 3))
            bh = max(8, int(self.size / 3))
            # spawn bullet just outside the player's rectangle so it doesn't overlap on creation
            spawn_x = (self.rect.right + bw // 2) if self.bullet_speed > 0 else (self.rect.left - bw // 2)
            bullet = Bullet(spawn_x, self.rect.centery, speed=self.bullet_speed, color=self.color, width=bw, height=bh, sprite=self.bullet_sprite)
            self.bullets.append(bullet)
            self.last_shot_time = current_time

    def special_attack(self):
        now = time.time()
        # fireball special has a longer cooldown (10s) per requirements; other specials use shoot_cooldown
        cooldown_required = 10.0 if self.special == "fireball" else self.shoot_cooldown
        if (now - self.last_special_time) < cooldown_required:
            return
        if self.special == "fireball":
            # fireball uses the special sprite if provided; make it 1/3 of player size per requirement
            fw = max(8, int(self.size / 3))
            fh = max(8, int(self.size / 3))
            spawn_x = (self.rect.right + fw // 2) if self.bullet_speed > 0 else (self.rect.left - fw // 2)
            b = Bullet(spawn_x, self.rect.centery, speed=int(self.bullet_speed * 1.6), color=(255,120,20), width=fw, height=fh, sprite=self.special_sprite)
            self.bullets.append(b)
        elif self.special == "dash":
            b = Bullet(self.rect.right, self.rect.centery, speed=int(self.bullet_speed * 3), color=(200,200,255), width=20, height=6, sprite=self.special_sprite)
            self.bullets.append(b)
        elif self.special == "spread":
            # spread uses normal bullet sprite (same 1/3 sizing)
            bw = max(8, int(self.size / 3))
            bh = max(8, int(self.size / 3))
            spawn_x = (self.rect.right + bw // 2) if self.bullet_speed > 0 else (self.rect.left - bw // 2)
            self.bullets.append(Bullet(spawn_x, self.rect.centery - 10, speed=int(self.bullet_speed), color=self.color, width=bw, height=bh, sprite=self.bullet_sprite))
            self.bullets.append(Bullet(spawn_x, self.rect.centery, speed=int(self.bullet_speed), color=self.color, width=bw, height=bh, sprite=self.bullet_sprite))
            self.bullets.append(Bullet(spawn_x, self.rect.centery + 10, speed=int(self.bullet_speed), color=self.color, width=bw, height=bh, sprite=self.bullet_sprite))
        self.last_shot_time = now
        self.last_special_time = now

    def update(self, screen):
        if not (self.invulnerable and int(time.time() * 5) % 2 == 0):
            if self.sprite:
                img = self.sprite
                # flip when facing left (negative bullet speed)
                if self.bullet_speed < 0:
                    try:
                        img = pygame.transform.flip(self.sprite, True, False)
                    except Exception:
                        img = self.sprite
                screen.blit(img, self.rect.topleft)
            else:
                pygame.draw.rect(screen, self.color, self.rect)
        for bullet in self.bullets[:]:
            bullet.update(screen)
            try:
                sw = screen.get_width()
            except Exception:
                sw = 800
            if bullet.rect.x < 0 or bullet.rect.x > sw:
                try:
                    self.bullets.remove(bullet)
                except ValueError:
                    pass

    def hit(self):
        if not self.invulnerable:
            self.lives -= 1
            self.invulnerable = True
            self.invulnerable_start = time.time()

    def update_invulnerability(self):
        if self.invulnerable and (time.time() - self.invulnerable_start) > 5:
            self.invulnerable = False