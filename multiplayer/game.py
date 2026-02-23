# python
import pygame
import random
import time
import ctypes
from shared.player import Player
from controller.joystick import ArduinoJoystick
from serial.tools import list_ports

# Debug flag: set to True to print joystick open/poll events
DEBUG = False

# Local static palette used by overlay menu
MENU_COLORS = {
    'selected_bg': '#7b61ff',
    'selected_fg': '#ff4b81',
    'fg': '#00e5ff',
    'bg': '#05030a',
}

# Optional background image path
BACKGROUND_IMAGE = r'assets\backgroundM.jpg'  # use assets/backgroundS.jpg for singleplayer


def _hex_to_rgb(hexstr):
    hexstr = hexstr.lstrip('#')
    return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))


def _overlay_menu(screen, font, winner_text, winner_lives, joystick=None):
    options = ["Play Again (same mode)", "Back to Menu", "Quit (Power down)"]
    selected = 0
    clock = pygame.time.Clock()

    last_move_time = 0.0
    last_button_time = 0.0
    move_cooldown = 0.18
    button_cooldown = 0.25

    palette = MENU_COLORS
    sel_bg = _hex_to_rgb(palette.get('selected_bg', '#333333'))
    sel_fg = _hex_to_rgb(palette.get('selected_fg', '#ffd54f'))
    fg = _hex_to_rgb(palette.get('fg', '#ffffff'))

    while True:
        now = time.time()
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

        if joystick:
            try:
                joystick.poll()
                dir = joystick.get_direction()
                data = joystick.last_data
                if dir == "UP" and (now - last_move_time) >= move_cooldown:
                    selected = (selected - 1) % len(options)
                    last_move_time = now
                elif dir == "DOWN" and (now - last_move_time) >= move_cooldown:
                    selected = (selected + 1) % len(options)
                    last_move_time = now
                if data and data.get("a") == 1 and (now - last_button_time) >= button_cooldown:
                    last_button_time = now
                    return ["replay", "menu", "quit"][selected]
            except Exception:
                pass

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))

        wtxt = font.render(winner_text, True, fg)
        sub = font.render(f"Winner: {winner_lives}", True, fg)
        overlay.blit(wtxt, (20,40))
        overlay.blit(sub, (20,80))

        for i, opt in enumerate(options):
            if i == selected:
                txt = font.render(opt, True, sel_fg)
                rect = txt.get_rect(topleft=(60, 160 + i * 48))
                pygame.draw.rect(overlay, sel_bg + (200,), rect)
                overlay.blit(txt, rect)
            else:
                txt = font.render(opt, True, fg)
                overlay.blit(txt, (60, 160 + i * 48))

        screen.blit(overlay, (0,0))
        pygame.display.flip()
        clock.tick(60)


def run(p1_config, p2_config):
    pygame.init()
    # create a standard resizable window then ask the OS to maximize it (windowed-maximized)
    try:
        screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    except Exception:
        screen = pygame.display.set_mode((800, 600))
    # On Windows, try to maximize the window while keeping decorations
    try:
        wm = pygame.display.get_wm_info()
        hwnd = wm.get('window') or wm.get('hwnd')
        if hwnd:
            try:
                ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
            except Exception:
                pass
            try:
                w, h = pygame.display.get_window_size()
            except Exception:
                info = pygame.display.Info()
                w, h = info.current_w, info.current_h
            try:
                screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
            except Exception:
                pass
    except Exception:
        pass
    pygame.display.set_caption("Street Fighter - Two Player")
    clock = pygame.time.Clock()

    # background image support - keep original image so we can rescale on resize
    bg_image = None
    bg_image_orig = None
    if BACKGROUND_IMAGE:
        try:
            bg_image_orig = pygame.image.load(BACKGROUND_IMAGE).convert()
            bg_image = pygame.transform.scale(bg_image_orig, screen.get_size())
        except Exception:
            bg_image = None
            bg_image_orig = None

    # factory to create players positioned 50px from edges
    def make_players():
        sw = screen.get_width()
        p_size = 120
        p1_x = 50
        p2_x = max(50, sw - 50 - p_size)
        p1 = Player(x=p1_x, y=screen.get_height() // 2 - p_size // 2,
                    character=(p1_config or {}).get("character", "Ryu"),
                    special=(p1_config or {}).get("special", "fireball"),
                    color=(0,200,80), sprite=r'assets\sp1.png', size=p_size)
        p2 = Player(x=p2_x, y=screen.get_height() // 2 - p_size // 2,
                    character=(p2_config or {}).get("character", "Chun"),
                    special=(p2_config or {}).get("special", "fireball"),
                    color=(200,50,50), bullet_speed=-10, sprite=r'assets\sp2.png', size=p_size)
        # assign projectile sprites
        p1.bullet_sprite = r'assets\LasserP.png'
        p1.special_sprite = r'assets\FireBall.png'
        p2.bullet_sprite = r'assets\LasserTeal.png'
        p2.special_sprite = r'assets\FireBall.png'
        return p1, p2

    # attempt to open joysticks from provided config ports (unchanged behavior)
    joy1 = None
    joy2 = None
    try:
        if p1_config and p1_config.get('port'):
            try:
                joy1 = ArduinoJoystick(port=p1_config.get('port'))
            except Exception:
                joy1 = None
    except Exception:
        joy1 = None
    try:
        if p2_config and p2_config.get('port'):
            try:
                joy2 = ArduinoJoystick(port=p2_config.get('port'))
            except Exception:
                joy2 = None
    except Exception:
        joy2 = None

    # auto-detect COM ports if needed (keep original logic)
    if not joy1 or not joy2:
        try:
            available = [p.device for p in list_ports.comports()]
            used = set()
            if joy1 and getattr(joy1, 'ser', None):
                try:
                    used.add(joy1.ser.port)
                except Exception:
                    pass
            if joy2 and getattr(joy2, 'ser', None):
                try:
                    used.add(joy2.ser.port)
                except Exception:
                    pass
            for port in available:
                if port in used:
                    continue
                if not joy1:
                    try:
                        joy1 = ArduinoJoystick(port=port)
                        if DEBUG:
                            print(f"[multiplayer] opened joy1 on {port}")
                        used.add(port)
                        continue
                    except Exception:
                        joy1 = None
                if not joy2:
                    try:
                        joy2 = ArduinoJoystick(port=port)
                        if DEBUG:
                            print(f"[multiplayer] opened joy2 on {port}")
                        used.add(port)
                        continue
                    except Exception:
                        joy2 = None
                if joy1 and joy2:
                    break
        except Exception:
            pass

    font = pygame.font.SysFont(None, 36)

    try:
        # start a fresh match
        player1, player2 = make_players()

        # show countdown before match
        try:
            # reuse singleplayer countdown
            for n in range(5, -1, -1):
                screen.fill((8,8,16))
                txt = pygame.font.SysFont(None, 120).render(str(n), True, (255,255,0))
                screen.blit(txt, (screen.get_width()//2 - txt.get_width()//2, screen.get_height()//2 - txt.get_height()//2))
                pygame.display.flip()
                time.sleep(0.8)
        except Exception:
            pass

        # lazy import plugin manager so Modules remains optional
        try:
            from Modules import plugin_manager
        except Exception:
            plugin_manager = None

        game_over = False
        while not game_over:
            now = time.time()
            # draw background
            if bg_image:
                screen.blit(bg_image, (0,0))
            else:
                screen.fill((2,2,18))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.VIDEORESIZE:
                    nw, nh = event.w, event.h
                    try:
                        screen = pygame.display.set_mode((nw, nh), pygame.RESIZABLE)
                    except Exception:
                        screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
                    if bg_image_orig:
                        try:
                            bg_image = pygame.transform.scale(bg_image_orig, (nw, nh))
                        except Exception:
                            bg_image = None
                    # clamp players to 50px margins
                    try:
                        min_x = 50
                        player1.rect.y = min(player1.rect.y, screen.get_height() - player1.rect.height)
                        player2.rect.y = min(player2.rect.y, screen.get_height() - player2.rect.height)
                        player1.rect.x = max(min_x, min(player1.rect.x, screen.get_width() - player1.rect.width - min_x))
                        player2.rect.x = max(min_x, min(player2.rect.x, screen.get_width() - player2.rect.width - min_x))
                    except Exception:
                        pass

            # joystick input and movement (maintain original mapping)
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

            # keyboard fallback controls for player1
            keys = pygame.key.get_pressed()
            if dir1 == "UP" or keys[pygame.K_w]:
                player1.move_up()
            if dir1 == "DOWN" or keys[pygame.K_s]:
                player1.move_down()
            if keys[pygame.K_SPACE] or (data1 and data1.get('a') == 1):
                player1.shoot()
            if keys[pygame.K_LSHIFT] or (data1 and data1.get('b') == 1):
                player1.special_attack()

            # player2 controls (joystick or arrow keys)
            if dir2 == "UP" or keys[pygame.K_UP]:
                player2.move_up()
            if dir2 == "DOWN" or keys[pygame.K_DOWN]:
                player2.move_down()
            if data2 and data2.get('a') == 1 or keys[pygame.K_RCTRL]:
                player2.shoot()
            if data2 and data2.get('b') == 1 or keys[pygame.K_RSHIFT]:
                player2.special_attack()

            # collisions
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

            # update and render players
            player1.update(screen)
            player2.update(screen)
            player1.update_invulnerability()
            player2.update_invulnerability()

            # HUD
            screen.blit(font.render(f"Lives P1: {player1.lives}", True, (255,255,255)), (12,12))
            cpu_x = max(200, screen.get_width() - 180)
            screen.blit(font.render(f"Lives P2: {player2.lives}", True, (255,255,255)), (cpu_x,12))

            pygame.display.flip()
            clock.tick(60)

            # give plugins a chance to handle a player's last life (e.g. ejection minigame)
            if player1.lives <= 0:
                handled = False
                if plugin_manager:
                    try:
                        handled = plugin_manager.run_hook('on_all_lives_lost', player1, joy1, screen)
                    except Exception:
                        handled = False
                if not handled:
                    game_over = True
                else:
                    # plugin restored a life; clamp positions and continue
                    try:
                        # ensure player1 stays on screen
                        player1.rect.y = max(0, min(player1.rect.y, screen.get_height() - player1.rect.height))
                    except Exception:
                        pass
            elif player2.lives <= 0:
                handled = False
                if plugin_manager:
                    try:
                        handled = plugin_manager.run_hook('on_all_lives_lost', player2, joy2, screen)
                    except Exception:
                        handled = False
                if not handled:
                    game_over = True
                else:
                    try:
                        player2.rect.y = max(0, min(player2.rect.y, screen.get_height() - player2.rect.height))
                    except Exception:
                        pass

            # decide winner and show overlay menu
            if player1.lives > player2.lives:
                winner_text = "Player 1 won!"
                winner_lives = player1.lives
            else:
                winner_text = "Player 2 won!"
                winner_lives = player2.lives

            choice = _overlay_menu(screen, font, winner_text, winner_lives, joystick=joy1 or joy2)
            if choice == "replay":
                # show retro countdown then restart match loop
                try:
                    for n in range(5, -1, -1):
                        screen.fill((8,8,16))
                        txt = pygame.font.SysFont(None, 120).render(str(n), True, (255,255,0))
                        screen.blit(txt, (screen.get_width()//2 - txt.get_width()//2, screen.get_height()//2 - txt.get_height()//2))
                        pygame.display.flip()
                        time.sleep(0.8)
                except Exception:
                    pass
                return "replay"
            elif choice == "menu":
                return "menu"
            else:
                return "quit"
    finally:
        if 'joy1' in locals() and joy1:
            try:
                joy1.close()
            except Exception:
                pass
        if 'joy2' in locals() and joy2:
            try:
                joy2.close()
            except Exception:
                pass
        try:
            pygame.quit()
        except Exception:
            pass