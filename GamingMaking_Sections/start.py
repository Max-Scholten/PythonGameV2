from menu import StartMenu, RetroLoadingScreen
from controller.joystick import ArduinoJoystick
import singleplayer.game as sp_game
import multiplayer.game as dp_game
from serial.tools import list_ports
import pygame
import time

def detect_com_ports():
    return [p.device for p in list_ports.comports()]

def powering_down_screen(duration=2.5):
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    start = time.time()
    while True:
        t = (time.time() - start) / duration
        if t > 1:
            t = 1
        screen.fill((40, 40, 48))  # space gray
        # red loading bar background
        bar_w, bar_h = 600, 36
        x = (800 - bar_w) // 2
        y = (600 - bar_h) // 2
        pygame.draw.rect(screen, (80, 80, 80), (x, y, bar_w, bar_h))
        # progress
        pygame.draw.rect(screen, (200, 30, 30), (x, y, int(bar_w * t), bar_h))
        txt = pygame.font.SysFont(None, 36).render("Powering down...", True, (220,220,220))
        screen.blit(txt, (x, y - 48))
        pygame.display.flip()
        clock.tick(60)
        if t >= 1:
            break
    time.sleep(0.6)
    pygame.quit()

if __name__ == "__main__":
    while True:
        ports = detect_com_ports()

        # open joystick for menu navigation (do this before StartMenu)
        menu_joystick = None
        if ports:
            try:
                menu_joystick = ArduinoJoystick(port=ports[0])
            except Exception:
                menu_joystick = None

        # quick auto-select when exactly one COM is present
        if len(ports) == 1:
            selection = {
                "mode": "one",
                "p1": {"character": "Ryu", "special": "fireball", "port": ports[0]}
            }
        else:
            # ensure any leftover pygame windows are closed before opening the Tk menu
            try:
                try:
                    pygame.event.pump()
                except Exception:
                    pass
                try:
                    pygame.display.quit()
                except Exception:
                    pass
                try:
                    pygame.quit()
                except Exception:
                    pass
                time.sleep(0.06)
            except Exception:
                pass
            menu = StartMenu(joystick=menu_joystick)
            selection = menu.show()
            if selection is None:
                # clean up joystick and show powering down screen then exit
                if menu_joystick:
                    try:
                        menu_joystick.close()
                    except Exception:
                        pass
                powering_down_screen()
                raise SystemExit(0)

        # free menu joystick immediately so game can open the same port (always do this)
        if menu_joystick:
            try:
                menu_joystick.close()
            except Exception:
                pass
            menu_joystick = None

        # loader UI
        loader = RetroLoadingScreen(parent=None, title="LOADING - ARENA", duration=1400, on_done=lambda: None)
        loader.window.mainloop()

        # ensure p1 port is set if possible
        mode = selection.get("mode")
        if mode == "one":
            if not selection["p1"].get("port") and ports:
                selection["p1"]["port"] = ports[0]
            result = sp_game.run(selection["p1"])
        else:
            # for multiplayer, pass ports into p1/p2 if you want similar auto wiring
            result = dp_game.run(selection["p1"], selection.get("p2"))

        if result == "menu":
            continue
        elif result == "replay":
            continue
        else:
            powering_down_screen()
            raise SystemExit(0)
