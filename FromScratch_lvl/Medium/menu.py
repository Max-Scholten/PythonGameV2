import tkinter as tk
import time

# Hardcoded static colors for the menu (edit here to change menu colors)
MENU_COLORS = {
    # background for the whole window
    'bg': '#ffffff',
    # normal option foreground
    'fg': '#ffffff',
    # selected option background and foreground
    'selected_bg': '#ffffff',
    'selected_fg': '#ffffff',
    # window size and fonts
    'size': (840, 520),
    'title_font': ('Helvetica', 24),
    'option_font': ('Helvetica', 18),
}

# Hardcoded static colors for the loading screen (loader only)
LOADER_COLORS = {
    'bg': '#ffffff',
    'neon': ['#ffffff', '#ffffff', '#ffffff'],
}

class RetroLoadingScreen:
    """Simple loading screen using LOADER_COLORS (static)."""
    def __init__(self, parent=None, title="LOADING", size=(820,320), duration=1400, on_done=None):
        self.parent = parent
        self.duration = duration / 1000.0
        self.on_done = on_done
        self.w, self.h = size
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.window, width=self.w, height=self.h, highlightthickness=0)
        self.canvas.pack()
        self._center()
        self.start_time = None
        self.title = title
        self._setup_static()
        self._animate()

    def _center(self):
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - self.w) // 2
        y = (sh - self.h) // 2
        self.window.geometry(f"{self.w}x{self.h}+{x}+{y}")

    def _setup_static(self):
        mid_color = LOADER_COLORS.get('bg')
        neon = LOADER_COLORS.get('neon', ["#7fffd4", "#00f0ff", "#00bcd4"])
        self.bg_id = self.canvas.create_rectangle(0,0,self.w,self.h, fill=mid_color, outline="")
        self.progress_bg = self.canvas.create_rectangle(80, self.h - 80, self.w - 80, self.h - 50, fill="#111", outline="#333")
        prog_color = neon[1] if len(neon) > 1 else neon[0]
        self.progress_fg = self.canvas.create_rectangle(82, self.h - 78, 82, self.h - 52, fill=prog_color, outline="")
        self.percent_text = self.canvas.create_text(self.w - 90, self.h - 65, text="0%", anchor="e", fill="#fff", font=("Courier", 12, "bold"))
        self.scan_ids = []
        step = 4
        for y in range(0, self.h, step):
            if (y // step) % 4 == 0:
                id_ = self.canvas.create_rectangle(0, y, self.w, y+1, fill="#071020", outline="")
                self.scan_ids.append(id_)

    def _draw_text(self, text, x, y, color):
        self.canvas.create_text(x, y, text=text, fill=color, font=("Impact", 36, "bold"), anchor="n", tags="title")

    def _animate(self):
        if self.start_time is None:
            self.start_time = time.time()
        elapsed = time.time() - self.start_time
        t = min(1.0, elapsed / self.duration)

        mid_color = LOADER_COLORS.get('bg')
        neon = LOADER_COLORS.get('neon', ["#7fffd4", "#00f0ff", "#00bcd4"])
        self.canvas.itemconfig(self.bg_id, fill=mid_color)

        # minimal scanline animation for movement
        for i, id_ in enumerate(self.scan_ids):
            offset = (i * 3 + int(time.time() * 30)) % 20
            shade = 12 + (offset % 6) * 6
            col = f'#{shade:02x}{(shade+8):02x}{(shade+14):02x}'
            self.canvas.itemconfig(id_, fill=col)

        self.canvas.delete("title")
        self._draw_text(self.title, self.w//2, 28, "#ffffff")

        total_width = (self.w - 162)
        cur_width = 2 + int(total_width * t)
        prog_color = neon[1] if len(neon) > 1 else neon[0]
        self.canvas.coords(self.progress_fg, 82, self.h - 78, 82 + cur_width, self.h - 52)
        self.canvas.itemconfig(self.progress_fg, fill=prog_color)
        self.canvas.itemconfig(self.percent_text, text=f"{int(t*100)}%")

        if t >= 1.0:
            if self.on_done:
                try:
                    self.on_done()
                finally:
                    self.window.destroy()
            else:
                self.window.destroy()
            return
        self.window.after(30, self._animate)


class StartMenu:
    """Simple Tk menu that uses local MENU_COLORS and supports joystick control."""
    def __init__(self, joystick=None):
        self.joystick = joystick
        self.root = tk.Tk()
        self.root.title("Start Menu")
        self.palette = MENU_COLORS
        self.root.configure(bg=self.palette.get('bg', self.root.cget('bg')))

        self.selection = None
        self.options = [("one", "Singleplayer"), ("two", "Multiplayer"), ("quit", "Quit")]
        self.selected_index = 0

        # input debouncing
        self.last_move_time = 0.0
        self.last_button_time = 0.0
        self.move_cooldown = 0.18
        self.button_cooldown = 0.25

        title_fg = self.palette.get('selected_fg', '#ffd54f')
        title_font = self.palette.get('title_font', ("Helvetica", 24))
        option_font = self.palette.get('option_font', ("Helvetica", 18))

        self.title_lbl = tk.Label(self.root, text="ARENA", font=title_font, bg=self.root.cget('bg'), fg=title_fg)
        self.title_lbl.pack(pady=(20,8))

        self.option_vars = []
        for _, text in self.options:
            var = tk.StringVar(value=text)
            lbl = tk.Label(self.root, textvariable=var, font=option_font, width=24, anchor='w', padx=20,
                           bg=self.root.cget('bg'), fg=self.palette.get('fg', '#ffffff'))
            lbl.pack(pady=6)
            self.option_vars.append((var, lbl))

        self._update_visuals()
        self.root.bind('<Up>', lambda e: self._move(-1))
        self.root.bind('<Down>', lambda e: self._move(1))
        self.root.bind('<Return>', lambda e: self._confirm())
        self.root.after(50, self._poll_joystick)

    def _update_visuals(self):
        # refresh palette to local constants to ensure exact colors are used
        self.palette = MENU_COLORS
        selected_bg = self.palette.get('selected_bg', '#333')
        selected_fg = self.palette.get('selected_fg', '#ffd54f')
        default_fg = self.palette.get('fg', '#ffffff')
        default_bg = self.palette.get('bg', self.root.cget('bg'))
        self.root.configure(bg=default_bg)
        self.title_lbl.config(bg=default_bg, fg=selected_fg)
        for i, (_, lbl) in enumerate(self.option_vars):
            if i == self.selected_index:
                lbl.config(bg=selected_bg, fg=selected_fg)
            else:
                lbl.config(bg=default_bg, fg=default_fg)

    def _move(self, delta):
        now = time.time()
        if now - self.last_move_time < self.move_cooldown:
            return
        self.last_move_time = now
        self.selected_index = (self.selected_index + delta) % len(self.options)
        self._update_visuals()

    def _confirm(self):
        now = time.time()
        if now - self.last_button_time < self.button_cooldown:
            return
        self.last_button_time = now
        key = self.options[self.selected_index][0]
        if key == 'one':
            self.selection = {'mode': 'one', 'p1': {'character': 'Ryu', 'special': 'fireball', 'port': None}}
        elif key == 'two':
            self.selection = {'mode': 'two', 'p1': {'character': 'Ryu', 'special': 'fireball'}, 'p2': {'character': 'Ken', 'special': 'dash'}}
        else:
            self.selection = None
        self.root.quit()

    def _poll_joystick(self):
        if self.joystick:
            try:
                self.joystick.poll()
                dir = self.joystick.get_direction()
                d = self.joystick.last_data
                if dir == 'UP':
                    self._move(-1)
                elif dir == 'DOWN':
                    self._move(1)
                if d and d.get('a') == 1:
                    self._confirm()
            except Exception:
                pass
        self.root.after(50, self._poll_joystick)

    def show(self):
        self.root.update_idletasks()
        w, h = self.palette.get('size', (840, 520))
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.mainloop()
        sel = self.selection
        self.root.destroy()
        return sel
