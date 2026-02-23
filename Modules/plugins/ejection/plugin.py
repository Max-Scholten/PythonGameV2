"""Ejection mini-game plugin.
Hook: on_all_lives_lost(player, joystick, screen)
Behavior: when called, shows a short overlay instructing the player to "shake" the joystick left-right quickly
or alternately press left/right arrow keys. If successful within time limit, restore 1 life and return True.
Otherwise return False.
"""
import time
import pygame

def on_all_lives_lost(player, joystick=None, screen=None):
    # basic safety: require a pygame surface and player
    if screen is None or player is None:
        return False

    font = pygame.font.SysFont(None, 36)
    clock = pygame.time.Clock()

    # require an alternating LEFT/RIGHT sequence of this length within time_limit seconds
    required_alternations = 6
    time_limit = 6.0

    start = time.time()
    last_dir = None
    alternations = 0

    # draw instruction once then loop until success or timeout
    while True:
        now = time.time()
        elapsed = now - start
        if elapsed > time_limit:
            # failed
            return False

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False

        # poll joystick if present
        dir = None
        if joystick:
            try:
                joystick.poll()
                dir = joystick.get_direction()
            except Exception:
                dir = None

        # keyboard fallback
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            dir = "LEFT"
        elif keys[pygame.K_RIGHT]:
            dir = "RIGHT"

        if dir and last_dir and dir != last_dir and ((last_dir in ("LEFT","RIGHT") and dir in ("LEFT","RIGHT"))):
            alternations += 1
            last_dir = dir
        elif dir and last_dir is None:
            last_dir = dir

        # draw translucent overlay
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        title = font.render("EJECTION LOCKED!", True, (255,180,50))
        msg = font.render("Shake the joystick LEFT <-> RIGHT rapidly to free the ejection system", True, (220,220,220))
        progress = font.render(f"Progress: {alternations}/{required_alternations}", True, (160,255,160))
        timer = font.render(f"Time left: {int(time_limit - elapsed)}", True, (255,120,120))
        overlay.blit(title, (20, 20))
        overlay.blit(msg, (20, 80))
        overlay.blit(progress, (20, 140))
        overlay.blit(timer, (20, 200))

        screen.blit(overlay, (0,0))
        pygame.display.flip()
        clock.tick(60)

        if alternations >= required_alternations:
            # success: restore one life and give short feedback
            player.lives = max(1, player.lives)
            # small success flash
            for i in range(6):
                screen.fill((0,0,0) if i % 2 == 0 else (0,80,0))
                s = font.render("EJECTION SUCCESSFUL! Lives restored", True, (255,255,255))
                screen.blit(s, (20, 60))
                pygame.display.flip()
                time.sleep(0.08)
            return True

        # small sleep to avoid busy loop
        time.sleep(0.01)

