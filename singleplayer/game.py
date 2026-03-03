import pygame
import time
import random
import serial
from contextlib import suppress
from shared.player import Player
from controller.joystick import ArduinoJoystick

BACKGROUND_IMAGE = r'assets\backgroundS.jpg'
COUNTDOWN = 3


def _countdown(screen, font, start=COUNTDOWN):
    for n in range(start, 0, -1):
        screen.fill((8, 8, 16))
        txt = font.render(str(n), True, (255, 255, 0))
        screen.blit(txt, ((screen.get_width() - txt.get_width()) // 2,
                          (screen.get_height() - txt.get_height()) // 2))
        pygame.display.flip()
        time.sleep(0.7)


def _overlay_menu(screen, font, title, joystick=None):
    opts = ["Play Again", "Back to Menu", "Quit"]
    sel = 0
    clock = pygame.time.Clock()
    last_move = last_btn = 0
    move_cd = 0.18
    btn_cd = 0.25

    while True:
        now = time.time()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return 'quit'
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    sel = (sel - 1) % len(opts)
                elif ev.key == pygame.K_DOWN:
                    sel = (sel + 1) % len(opts)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return ['replay', 'menu', 'quit'][sel]

        if joystick:
            try:
                joystick.poll()
                d = joystick.get_direction()
                data = joystick.last_data
                if d == 'UP' and (now - last_move) >= move_cd:
                    sel = (sel - 1) % len(opts)
                    last_move = now
                if d == 'DOWN' and (now - last_move) >= move_cd:
                    sel = (sel + 1) % len(opts)
                    last_move = now
                if data and data.get('a') == 1 and (now - last_btn) >= btn_cd:
                    last_btn = now
                    return ['replay', 'menu', 'quit'][sel]
            except (RuntimeError, OSError, serial.SerialException, AttributeError):
                pass

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        overlay.blit(font.render(title, True, (255, 255, 255)), (20, 40))
        for i, o in enumerate(opts):
            color = (255, 200, 0) if i == sel else (200, 200, 200)
            overlay.blit(font.render(o, True, color), (60, 160 + i * 48))
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)


def run(p1_config):
    pygame.init()
    # fullscreen for simplicity so background fills the screen
    try:
        info = pygame.display.Info()
        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    except (pygame.error, OSError):
        screen = pygame.display.set_mode((800, 600))

    pygame.display.set_caption('Street Fighter - Single Player (Simple)')

    # load and scale background
    bg = None
    bg_orig = None
    if BACKGROUND_IMAGE:
        try:
            bg_orig = pygame.image.load(BACKGROUND_IMAGE).convert()
            bg = pygame.transform.scale(bg_orig, screen.get_size())
        except (pygame.error, FileNotFoundError, OSError):
            bg = None

    font = pygame.font.SysFont(None, 36)

    def make_players():
        w, h = screen.get_size()
        size = 120
        p1 = Player(x=50, y=h // 2 - size // 2, character=p1_config.get('character', 'Ryu'),
                    special=p1_config.get('special', 'fireball'), color=(0, 200, 80), sprite=r'assets\\sp1.png', size=size)
        p2 = Player(x=w - 50 - size, y=h // 2 - size // 2, character='CPU', special='spread',
                    color=(200, 50, 50), bullet_speed=-10, sprite=r'assets\\sp2.png', size=size)
        p1.bullet_sprite = r'assets\\LasserP.png'
        p1.special_sprite = r'assets\\FireBall.png'
        p2.bullet_sprite = r'assets\\LasserTeal.png'
        p2.special_sprite = r'assets\\FireBall.png'
        return p1, p2

    # open joystick only if port provided
    joy = None
    try:
        if p1_config and p1_config.get('port'):
            try:
                joy = ArduinoJoystick(port=p1_config.get('port'))
            except (serial.SerialException, OSError, ValueError, AttributeError):
                joy = None
    except (AttributeError, TypeError):
        joy = None

    clock = pygame.time.Clock()

    try:
        while True:
            player1, player2 = make_players()

            # simple countdown
            try:
                _countdown(screen, pygame.font.SysFont(None, 120))
            except (pygame.error, OSError):
                pass

            # AI timers
            last_ai_move = time.time()
            ai_move_interval = 0.6
            ai_dir = 0
            last_ai_shot = 0
            ai_shoot_cd = 0.9
            last_ai_special = 0
            ai_special_cd = 5.0

            running = True
            while running:
                now = time.time()
                # draw background
                if bg:
                    screen.blit(bg, (0, 0))
                else:
                    screen.fill((8, 8, 16))

                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        return 'quit'
                    if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                        return 'menu'

                # poll joystick
                if joy:
                    try:
                        joy.poll()
                    except (RuntimeError, OSError, serial.SerialException, AttributeError):
                        pass
                    dir1 = joy.get_direction()
                    data1 = joy.last_data
                else:
                    dir1 = None
                    data1 = None

                # player controls (joystick or keyboard)
                keys = pygame.key.get_pressed()
                if dir1 == 'UP' or keys[pygame.K_w]:
                    player1.move_up()
                if dir1 == 'DOWN' or keys[pygame.K_s]:
                    player1.move_down()
                if keys[pygame.K_SPACE] or (data1 and data1.get('a') == 1):
                    player1.shoot()
                if keys[pygame.K_LSHIFT] or (data1 and data1.get('b') == 1):
                    player1.special_attack()

                # simple AI: random interval movement/shooting
                if now - last_ai_move > ai_move_interval:
                    last_ai_move = now
                    ai_move_interval = random.uniform(0.35, 1.2)
                    ai_dir = random.choice([-1, 0, 1])
                if ai_dir == -1:
                    player2.move_up()
                elif ai_dir == 1:
                    player2.move_down()
                if now - last_ai_shot > ai_shoot_cd and random.random() < 0.35:
                    player2.shoot()
                    last_ai_shot = now
                if now - last_ai_special > ai_special_cd and random.random() < 0.12:
                    player2.special_attack()
                    last_ai_special = now

                # collisions (small helper to avoid repetition)
                def handle_collisions(attacker, defender):
                    for b in list(attacker.bullets):
                        if b.rect.colliderect(defender.rect):
                            defender.hit()
                            with suppress(ValueError):
                                attacker.bullets.remove(b)

                handle_collisions(player1, player2)
                handle_collisions(player2, player1)

                player1.update(screen)
                player2.update(screen)
                player1.update_invulnerability()
                player2.update_invulnerability()

                # HUD
                screen.blit(font.render(f"Lives P1: {player1.lives}", True, (255, 255, 255)), (12, 12))
                screen.blit(font.render(f"Lives CPU: {player2.lives}", True, (255, 255, 255)), (screen.get_width() - 180, 12))

                pygame.display.flip()
                clock.tick(60)

                if player1.lives <= 0 or player2.lives <= 0:
                    running = False

            # end of match
            winner = 'Player 1 won!' if player1.lives > player2.lives else 'CPU won!'
            choice = _overlay_menu(screen, font, winner, joystick=joy)
            if choice == 'replay':
                continue
            if choice == 'menu':
                return 'menu'
            return 'quit'

    finally:
        # cleanup joystick and pygame with specific suppressed errors
        with suppress(AttributeError, OSError, serial.SerialException):
            if joy:
                joy.close()
        with suppress(pygame.error):
            pygame.quit()