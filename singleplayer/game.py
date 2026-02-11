import pygame
import time
import random
from shared.player import Player
from controller.joystick import ArduinoJoystick

# Simple menu palette
MENU_COLORS = {
    'selected_bg': '#7b61ff',
    'selected_fg': '#ff4b81',
    'fg': '#00e5ff',
}

BACKGROUND_IMAGE = r'assets\backgroundS.jpg'
COUNTDOWN_START = 3  # friendly short countdown for novices


def _hex_to_rgb(hexstr):
    hexstr = hexstr.lstrip('#')
    return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))


def _countdown(screen, seconds):
    """Blocking, centered countdown so beginners understand what's happening."""
    font = pygame.font.SysFont(None, 120)
    for n in range(seconds, 0, -1):
        screen.fill((8, 8, 16))
        txt = font.render(str(n), True, (255, 255, 0))
        screen.blit(txt, ((screen.get_width() - txt.get_width()) // 2,
                          (screen.get_height() - txt.get_height()) // 2))
        pygame.display.flip()
        time.sleep(1)


def _overlay_menu(screen, font, winner_text, winner_lives, joystick=None):
    """Simple translucent overlay menu. Return 'replay', 'menu' or 'quit'."""
    options = ["Play Again", "Back to Menu", "Quit"]
    selected = 0
    clock = pygame.time.Clock()

    sel_bg = _hex_to_rgb(MENU_COLORS['selected_bg'])
    sel_fg = _hex_to_rgb(MENU_COLORS['selected_fg'])
    fg = _hex_to_rgb(MENU_COLORS['fg'])

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif ev.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return ["replay", "menu", "quit"][selected]

        # minimal joystick support
        if joystick:
            try:
                joystick.poll()
                d = joystick.get_direction()
                data = joystick.last_data or {}
                if d == "UP":
                    selected = (selected - 1) % len(options)
                elif d == "DOWN":
                    selected = (selected + 1) % len(options)
                if data.get("a") == 1:
                    return ["replay", "menu", "quit"][selected]
            except Exception:
                pass  # keep menu usable even if joystick misbehaves

        # draw overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        overlay.blit(font.render(winner_text, True, fg), (20, 40))
        overlay.blit(font.render(f"Lives: {winner_lives}", True, fg), (20, 80))

        for i, opt in enumerate(options):
            y = 160 + i * 48
            if i == selected:
                txt = font.render(opt, True, sel_fg)
                rect = txt.get_rect(topleft=(60, y))
                pygame.draw.rect(overlay, sel_bg + (160,), rect)
                overlay.blit(txt, rect)
            else:
                txt = font.render(opt, True, fg)
                overlay.blit(txt, (60, y))

        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(30)


def _cleanup(joystick=None):
    """Close joystick and quit pygame cleanly."""
    if joystick:
        try:
            joystick.close()
        except Exception:
            pass
    pygame.quit()


def run(p1_config):
    """Main loop for single-player match (simplified for novices)."""
    pygame.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption("Street Fighter - Single Player")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    # load background once (may be None)
    bg_orig = None
    try:
        if BACKGROUND_IMAGE:
            bg_orig = pygame.image.load(BACKGROUND_IMAGE).convert()
    except Exception:
        bg_orig = None

    def make_players():
        sw = screen.get_width()
        size = 120
        p1 = Player(x=50, y=280, character=p1_config.get("character", "Ryu"),
                    special=p1_config.get("special", "fireball"), color=(0, 200, 80),
                    sprite=r'assets\sp1.png', size=size)
        p2_x = max(50, sw - 50 - size)
        p2 = Player(x=p2_x, y=280, character="CPU", special="spread",
                    color=(200, 50, 50), bullet_speed=-10,
                    sprite=r'assets\sp2.png', size=size)
        p1.bullet_sprite = r'assets\LasserP.png'
        p1.special_sprite = r'assets\FireBall.png'
        p2.bullet_sprite = r'assets\LasserTeal.png'
        p2.special_sprite = r'assets\FireBall.png'
        return p1, p2

    # optional joystick (open once)
    joy = None
    if p1_config.get("port"):
        try:
            joy = ArduinoJoystick(port=p1_config.get("port"))
        except Exception:
            joy = None

    try:
        while True:
            player1, player2 = make_players()
            # short countdown
            try:
                _countdown(screen, COUNTDOWN_START)
            except Exception:
                pass

            game_over = False
            last_ai = time.time()
            ai_interval = 0.7
            ai_dir = 0
            last_ai_shot = 0

            while not game_over:
                now = time.time()
                # draw background (rescale if needed)
                if bg_orig:
                    bg = pygame.transform.scale(bg_orig, screen.get_size())
                    screen.blit(bg, (0, 0))
                else:
                    screen.fill((8, 8, 16))

                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        return "quit"
                    if ev.type == pygame.VIDEORESIZE:
                        screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                        # clamp players after resize
                        try:
                            player1.rect.y = min(player1.rect.y, screen.get_height() - player1.rect.height)
                            player2.rect.y = min(player2.rect.y, screen.get_height() - player2.rect.height)
                        except Exception:
                            pass

                # joystick input (simple)
                if joy:
                    try:
                        joy.poll()
                        dir1 = joy.get_direction()
                        data1 = joy.last_data or {}
                    except Exception:
                        dir1 = None
                        data1 = {}
                else:
                    dir1 = None
                    data1 = {}

                # keyboard + joystick mapping
                keys = pygame.key.get_pressed()
                if dir1 == "UP" or keys[pygame.K_w]:
                    player1.move_up()
                if dir1 == "DOWN" or keys[pygame.K_s]:
                    player1.move_down()
                if keys[pygame.K_SPACE] or data1.get("a") == 1:
                    player1.shoot()
                if keys[pygame.K_LSHIFT] or data1.get("b") == 1:
                    player1.special_attack()

                # very simple CPU AI
                if now - last_ai > ai_interval:
                    last_ai = now
                    ai_interval = random.uniform(0.4, 1.2)
                    ai_dir = random.choice([-1, 0, 1])
                if ai_dir == -1:
                    player2.move_up()
                elif ai_dir == 1:
                    player2.move_down()
                if now - last_ai_shot > 0.8 and random.random() < 0.35:
                    player2.shoot()
                    last_ai_shot = now
                if random.random() < 0.02:
                    player2.special_attack()

                # collisions: bullets vs players
                for b in player1.bullets[:]:
                    if b.rect.colliderect(player2.rect):
                        player2.hit()
                        try:
                            player1.bullets.remove(b)
                        except ValueError:
                            pass
                for b in player2.bullets[:]:
                    if b.rect.colliderect(player1.rect):
                        player1.hit()
                        try:
                            player2.bullets.remove(b)
                        except ValueError:
                            pass

                # update entities
                player1.update(screen)
                player2.update(screen)
                player1.update_invulnerability()
                player2.update_invulnerability()

                # HUD
                screen.blit(font.render(f"Lives P1: {player1.lives}", True, (255, 255, 255)), (12, 12))
                cpu_x = max(200, screen.get_width() - 180)
                screen.blit(font.render(f"Lives CPU: {player2.lives}", True, (255, 255, 255)), (cpu_x, 12))

                pygame.display.flip()
                clock.tick(60)

                if player1.lives <= 0 or player2.lives <= 0:
                    game_over = True

            # decide winner
            if player1.lives > player2.lives:
                winner_text = "Player 1 won!"
                winner_lives = player1.lives
            else:
                winner_text = "CPU won!"
                winner_lives = player2.lives

            choice = _overlay_menu(screen, font, winner_text, winner_lives, joystick=joy)
            if choice == "replay":
                continue
            if choice == "menu":
                _cleanup(joy)
                return "menu"
            _cleanup(joy)
            return "quit"
    finally:
        _cleanup(joy)
