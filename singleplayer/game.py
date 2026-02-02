import pygame
import time
import random
from shared.player import Player
from controller.joystick import ArduinoJoystick
import ctypes

# Local static palette used by overlay menu (no shared/settings dependency)
MENU_COLORS = {
    'selected_bg': '#7b61ff',
    'selected_fg': '#ff4b81',
    'fg': '#00e5ff',
    'bg': '#05030a',
}

# Optional background image path (set to a file path string to enable)
BACKGROUND_IMAGE = r'assets\backgroundS.jpg'  # use assets/backgroundS.jpg for singleplayer

COUNTDOWN_START = 5


def _retro_countdown(screen, font):
    for n in range(COUNTDOWN_START, -1, -1):
        screen.fill((8, 8, 16))
        txt = font.render(str(n), True, (255, 255, 0))
        screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2,
                          screen.get_height() // 2 - txt.get_height() // 2))
        pygame.display.flip()
        time.sleep(0.8)


def _hex_to_rgb(hexstr):
    hexstr = hexstr.lstrip('#')
    return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))


def _overlay_menu(screen, font, winner_text, winner_lives, joystick=None):
    """Draw a translucent overlay on top of the current screen and handle input.

    Returns one of: 'replay', 'menu', 'quit'
    """
    options = ["Play Again (same mode)", "Back to Menu", "Quit (Power down)"]
    selected = 0
    clock = pygame.time.Clock()

    # debounce timers for joystick navigation / confirm
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

        # joystick input for menu navigation
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

        # draw translucent overlay on top of current screen (don't clear underlying frame)
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))  # semi-transparent dark overlay

        # Winner text and info
        wtxt = font.render(winner_text, True, fg)
        sub = font.render(f"Winner has {winner_lives} lives remaining", True, fg)
        overlay.blit(wtxt, (20, 40))
        overlay.blit(sub, (20, 80))

        # Options
        for i, opt in enumerate(options):
            if i == selected:
                # draw selected with background rectangle
                txt = font.render(opt, True, sel_fg)
                rect = txt.get_rect(topleft=(60, 160 + i * 48))
                pygame.draw.rect(overlay, sel_bg + (200,), rect)  # add alpha to bg
                overlay.blit(txt, rect)
            else:
                txt = font.render(opt, True, fg)
                overlay.blit(txt, (60, 160 + i * 48))

        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)


def _cleanup(joy=None):
    """Close joystick and ensure pygame display is closed."""
    if joy:
        try:
            joy.close()
        except Exception:
            pass
    try:
        pygame.event.pump()
    except Exception:
        pass
    try:
        pygame.display.quit()
    except Exception:
        pass
    try:
        time.sleep(0.06)
    except Exception:
        pass
    try:
        pygame.quit()
    except Exception:
        pass


def run(p1_config):
    pygame.init()
    # create a standard resizable window then ask the OS to maximize it (windowed-maximized)
    try:
        screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    except Exception:
        screen = pygame.display.set_mode((800, 600))
    # On Windows, maximize the window (keeps window decorations so user can still close it)
    try:
        wm = pygame.display.get_wm_info()
        hwnd = wm.get('window') or wm.get('hwnd')
        if hwnd:
            # SW_MAXIMIZE = 3
            try:
                ctypes.windll.user32.ShowWindow(hwnd, 3)
            except Exception:
                pass
            # attempt to update the pygame surface to the window's client size
            try:
                # pygame 2 provides get_window_size(); fallback to display.Info()
                try:
                    w, h = pygame.display.get_window_size()
                except Exception:
                    info = pygame.display.Info()
                    w, h = info.current_w, info.current_h
                screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
            except Exception:
                pass
    except Exception:
        pass
    pygame.display.set_caption("Street Fighter - Single Player")
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

    def make_players():
        # use the player sprite for player 1 so it looks like a real character
        p1_sprite_path = r'assets\sp1.png'
        # increase size so the image appears larger in-game; adjust y so center lines up with CPU
        # compute horizontal positions so players are always 50px from screen edges
        sw = screen.get_width()
        p_size = 120
        p1_x = 50
        p2_x = max(50, sw - 50 - p_size)
        p1 = Player(x=p1_x, y=280, character=p1_config.get("character","Ryu"),
                    special=p1_config.get("special","fireball"), color=(0,200,80), sprite=p1_sprite_path, size=p_size)
        # give player 2 a sprite and match size/vertical alignment with player1
        p2 = Player(x=p2_x, y=280, character="CPU", special="spread",
                    color=(200,50,50), bullet_speed=-10, sprite=r'assets\sp2.png', size=p_size)

        # assign projectile sprites (found in assets folder):
        # - Player 1 uses LasserP for standard shots and FireBall for the special
        # - Player 2 uses LasserTeal for standard shots and FireBall for the special
        p1.bullet_sprite = r'assets\LasserP.png'
        p1.special_sprite = r'assets\FireBall.png'
        p2.bullet_sprite = r'assets\LasserTeal.png'
        p2.special_sprite = r'assets\FireBall.png'

        return p1, p2

    # open joystick only if a port is provided in config (avoid hardcoded fallback)
    joy1 = None
    try:
        if p1_config.get("port"):
            try:
                joy1 = ArduinoJoystick(port=p1_config.get("port"))
            except Exception:
                joy1 = None

        font = pygame.font.SysFont(None, 36)

        while True:
                # start a fresh match
            player1, player2 = make_players()

            # show a retro countdown before the match begins
            try:
                _retro_countdown(screen, pygame.font.SysFont(None, 120))
            except Exception:
                # if countdown fails for any reason, continue without blocking
                pass

            # AI state
            ai_move_interval = 0.6
            last_ai_move = time.time()
            ai_dir = 0
            ai_shoot_cooldown = 0.9
            last_ai_shot = 0
            ai_special_cooldown = 5.0
            last_ai_special = 0

            game_over = False

            while not game_over:
                now = time.time()
                # draw background
                if bg_image:
                    screen.blit(bg_image, (0,0))
                else:
                    screen.fill((8,8,16))

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return "quit"
                    # handle window resize: recreate the screen surface and rescale background
                    elif event.type == pygame.VIDEORESIZE:
                        nw, nh = event.w, event.h
                        try:
                            screen = pygame.display.set_mode((nw, nh), pygame.RESIZABLE)
                        except Exception:
                            # fallback if set_mode fails
                            screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
                        if bg_image_orig:
                            try:
                                bg_image = pygame.transform.scale(bg_image_orig, (nw, nh))
                            except Exception:
                                bg_image = None
                        # if players exist (in the running match), clamp their positions to new size
                        try:
                            # if players exist (in the running match), clamp their positions to new size
                            # clamp their positions on resize; compute initial x based on current screen width instead of hardcoded values.
                            player1.rect.y = min(player1.rect.y, screen.get_height() - player1.rect.height)
                            player2.rect.y = min(player2.rect.y, screen.get_height() - player2.rect.height)
                            # horizontal clamp: keep both players at least 50px from edges
                            min_x = 50
                            player1.rect.x = max(min_x, min(player1.rect.x, screen.get_width() - player1.rect.width - min_x))
                            player2.rect.x = max(min_x, min(player2.rect.x, screen.get_width() - player2.rect.width - min_x))
                        except Exception:
                            pass

                # joystick poll once per frame
                if joy1:
                    joy1.poll()
                    dir1 = joy1.get_direction()
                    data1 = joy1.last_data
                else:
                    dir1 = None
                    data1 = None

                # player controls
                if dir1 == "UP":
                    player1.move_up()
                elif dir1 == "DOWN":
                    player1.move_down()
                else:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_w]: player1.move_up()
                    if keys[pygame.K_s]: player1.move_down()
                    if keys[pygame.K_SPACE]: player1.shoot()
                    if keys[pygame.K_LSHIFT]: player1.special_attack()

                if data1 and data1.get("a") == 1:
                    player1.shoot()
                if data1 and data1.get("b") == 1:
                    player1.special_attack()

                # CPU AI
                if now - last_ai_move > ai_move_interval:
                    last_ai_move = now
                    ai_move_interval = random.uniform(0.35, 1.2)
                    ai_dir = random.choice([-1, 0, 1])
                if ai_dir == -1:
                    player2.move_up()
                elif ai_dir == 1:
                    player2.move_down()
                if now - last_ai_shot > ai_shoot_cooldown and random.random() < 0.35:
                    player2.shoot()
                    last_ai_shot = now
                if now - last_ai_special > ai_special_cooldown and random.random() < 0.12:
                    player2.special_attack()
                    last_ai_special = now

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

                player1.update(screen)
                player2.update(screen)
                player1.update_invulnerability()
                player2.update_invulnerability()

                # HUD (positions adapt to current window size)
                screen.blit(font.render(f"Lives P1: {player1.lives}", True, (255,255,255)), (12,12))
                # place CPU lives anchored near the right edge
                cpu_x = max(200, screen.get_width() - 180)
                screen.blit(font.render(f"Lives CPU: {player2.lives}", True, (255,255,255)), (cpu_x, 12))

                pygame.display.flip()
                clock.tick(60)

                if player1.lives <= 0 or player2.lives <= 0:
                    game_over = True

            # decide winner and show end menu overlay
            if player1.lives > player2.lives:
                winner_text = "Player 1 won!"
                winner_lives = player1.lives
            else:
                winner_text = "CPU won!"
                winner_lives = player2.lives

            choice = _overlay_menu(screen, font, winner_text, winner_lives, joystick=joy1)
            if choice == "replay":
                # show retro countdown then restart match loop
                _retro_countdown(screen, pygame.font.SysFont(None, 120))
                continue
            elif choice == "menu":
                _cleanup(joy1)
                return "menu"
            else:
                _cleanup(joy1)
                return "quit"
    finally:
        # always close joystick to free COM port
        if joy1:
            try:
                joy1.close()
            except Exception:
                pass
        try:
            # ensure events are pumped and display is closed before quitting
            try:
                pygame.event.pump()
            except Exception:
                pass
            try:
                pygame.display.quit()
            except Exception:
                pass
            time.sleep(0.12)
            pygame.quit()
        except Exception:
            pass