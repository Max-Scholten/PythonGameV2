# python
import pygame
import time
from serial.tools import list_ports
from shared.player import Player
from controller.joystick import ArduinoJoystick

BACKGROUND_IMAGE = r'assets\backgroundM.jpg'


# Try to open up to two Arduino-based joysticks, auto-detecting ports.
def open_joysticks(p1_conf, p2_conf):
    j1 = j2 = None
    try:
        if p1_conf and p1_conf.get('port'):
            j1 = ArduinoJoystick(port=p1_conf.get('port'))
    except Exception:
        j1 = None
    try:
        if p2_conf and p2_conf.get('port'):
            j2 = ArduinoJoystick(port=p2_conf.get('port'))
    except Exception:
        j2 = None

    if not j1 or not j2:
        try:
            ports = [p.device for p in list_ports.comports()]
            used = set()
            if j1 and getattr(j1, 'ser', None):
                used.add(j1.ser.port)
            if j2 and getattr(j2, 'ser', None):
                used.add(j2.ser.port)
            for p in ports:
                if p in used:
                    continue
                if not j1:
                    try:
                        j1 = ArduinoJoystick(port=p)
                        used.add(p)
                        continue
                    except Exception:
                        j1 = None
                if not j2:
                    try:
                        j2 = ArduinoJoystick(port=p)
                        used.add(p)
                        continue
                    except Exception:
                        j2 = None
                if j1 and j2:
                    break
        except Exception:
            pass
    return j1, j2


# Small overlay menu after a match. Works with keyboard or joystick.
def overlay_menu(screen, font, winner_text, joystick=None):
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
            except Exception:
                pass

        # draw overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        overlay.blit(font.render(winner_text, True, (255, 255, 255)), (20, 40))
        for i, o in enumerate(opts):
            color = (255, 200, 0) if i == sel else (200, 200, 200)
            overlay.blit(font.render(o, True, color), (60, 160 + i * 48))
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)


def run(p1_config=None, p2_config=None):
    pygame.init()
    try:
        info = pygame.display.Info()
        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    except Exception:
        screen = pygame.display.set_mode((800, 600))

    pygame.display.set_caption('Street Fighter - Two Player (Simple)')

    # load background and scale to window size
    bg = None
    bg_orig = None
    if BACKGROUND_IMAGE:
        try:
            bg_orig = pygame.image.load(BACKGROUND_IMAGE).convert()
            bg = pygame.transform.scale(bg_orig, screen.get_size())
        except Exception:
            bg = None

    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)

    def make_players():
        w, h = screen.get_size()
        size = 120
        p1 = Player(x=50, y=h // 2 - size // 2, character='Ryu', special='fireball', color=(0, 200, 80), sprite=r'assets\sp1.png', size=size)
        p2 = Player(x=w - 50 - size, y=h // 2 - size // 2, character='Chun', special='fireball', color=(200, 50, 50), bullet_speed=-10, sprite=r'assets\sp2.png', size=size)
        p1.bullet_sprite = r'assets\LasserP.png'
        p1.special_sprite = r'assets\FireBall.png'
        p2.bullet_sprite = r'assets\LasserTeal.png'
        p2.special_sprite = r'assets\FireBall.png'
        return p1, p2

    joy1, joy2 = open_joysticks(p1_config or {}, p2_config or {})

    try:
        p1, p2 = make_players()

        # simple countdown
        try:
            for n in range(3, 0, -1):
                screen.fill((8, 8, 16))
                txt = pygame.font.SysFont(None, 120).render(str(n), True, (255, 255, 0))
                screen.blit(txt, ((screen.get_width() - txt.get_width()) // 2, (screen.get_height() - txt.get_height()) // 2))
                pygame.display.flip()
                time.sleep(0.6)
        except Exception:
            pass

        while True:
            # draw background
            if bg:
                screen.blit(bg, (0, 0))
            else:
                screen.fill((2, 2, 18))

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return 'quit'
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return 'menu'

            # poll joysticks (keep logic intact)
            if joy1:
                try:
                    joy1.poll()
                except Exception:
                    pass
                dir1 = joy1.get_direction()
                data1 = joy1.last_data
            else:
                dir1 = None
                data1 = None

            if joy2:
                try:
                    joy2.poll()
                except Exception:
                    pass
                dir2 = joy2.get_direction()
                data2 = joy2.last_data
            else:
                dir2 = None
                data2 = None

            # keyboard fallback and actions
            keys = pygame.key.get_pressed()
            if dir1 == 'UP' or keys[pygame.K_w]:
                p1.move_up()
            if dir1 == 'DOWN' or keys[pygame.K_s]:
                p1.move_down()
            if keys[pygame.K_SPACE] or (data1 and data1.get('a') == 1):
                p1.shoot()
            if keys[pygame.K_LSHIFT] or (data1 and data1.get('b') == 1):
                p1.special_attack()

            if dir2 == 'UP' or keys[pygame.K_UP]:
                p2.move_up()
            if dir2 == 'DOWN' or keys[pygame.K_DOWN]:
                p2.move_down()
            if keys[pygame.K_RCTRL] or (data2 and data2.get('a') == 1):
                p2.shoot()
            if keys[pygame.K_RSHIFT] or (data2 and data2.get('b') == 1):
                p2.special_attack()

            # collisions
            for b in list(p1.bullets):
                if b.rect.colliderect(p2.rect):
                    p2.hit()
                    try:
                        p1.bullets.remove(b)
                    except ValueError:
                        pass
            for b in list(p2.bullets):
                if b.rect.colliderect(p1.rect):
                    p1.hit()
                    try:
                        p2.bullets.remove(b)
                    except ValueError:
                        pass

            # update and draw players
            p1.update(screen)
            p2.update(screen)
            p1.update_invulnerability()
            p2.update_invulnerability()

            # HUD
            screen.blit(font.render(f"Lives P1: {p1.lives}", True, (255, 255, 255)), (12, 12))
            screen.blit(font.render(f"Lives P2: {p2.lives}", True, (255, 255, 255)), (screen.get_width() - 180, 12))

            pygame.display.flip()
            clock.tick(60)

            # check end of match
            if p1.lives <= 0 or p2.lives <= 0:
                winner = 'Player 1 won!' if p1.lives > p2.lives else 'Player 2 won!'
                choice = overlay_menu(screen, font, winner, joystick=joy1 or joy2)
                if choice == 'replay':
                    p1, p2 = make_players()
                    continue
                if choice == 'menu':
                    return 'menu'
                return 'quit'

    finally:
        try:
            if joy1:
                joy1.close()
        except Exception:
            pass
        try:
            if joy2:
                joy2.close()
        except Exception:
            pass
        try:
            pygame.quit()
        except Exception:
            pass