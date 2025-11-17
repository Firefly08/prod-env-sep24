# snake_game.py
# Snake with manual control option
# - Starts length 3
# - Grows on food, speeds up in auto mode
# - **Manual Step Mode**: the snake moves only when you press a key (arrow/WASD or SPACE)
#   Toggle manual/auto at runtime with **M**.
# - Windowed, resizable canvas

import random
import sys
import tkinter as tk

# ---------------- Settings ----------------
GRID_COLS = 32
GRID_ROWS = 24
CELL_SIZE = 24           # initial pixel size per cell; canvas rescales on resize
MARGIN = 10

BG_COLOR = "#121212"
GRID_COLOR = "#2a2a2a"
SNAKE_COLOR = "#36c"      # body
SNAKE_HEAD_COLOR = "#4db6ff"
FOOD_COLOR = "#f44336"
TEXT_COLOR = "#e0e0e0"

START_LEN = 3
START_SPEED_MS = 150      # auto mode speed (lower is faster)
SPEED_GAIN_MS = 4         # auto mode speedup per food (ms decrease)
MIN_SPEED_MS = 55

WRAP_AROUND = True        # if False, hitting wall = game over

# Start in Manual Step Mode so it's NOT autopilot.
MANUAL_STEP_MODE = True   # True = only moves on key presses; False = auto-loop


# -------------- Helpers -------------------
DIRS = {
    'Up': (0, -1),
    'Down': (0, 1),
    'Left': (-1, 0),
    'Right': (1, 0),
}

OPPOSITE = {
    'Up': 'Down',
    'Down': 'Up',
    'Left': 'Right',
    'Right': 'Left',
}


class SnakeGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Snake — Manual control ready (press M to toggle auto)")

        self.canvas = tk.Canvas(root, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # UI overlays
        self.hud = self.canvas.create_text(
            10, 10, anchor='nw', fill=TEXT_COLOR, font=("Segoe UI", 12), text=""
        )
        self.msg = None

        # Bindings
        root.bind('<Configure>', self._on_resize)
        for key in ("<Up>", "<Down>", "<Left>", "<Right>"):
            root.bind(key, self.on_arrow)
        for key in ("w","a","s","d","W","A","S","D"):
            root.bind(key, self.on_wasd)
        root.bind('<space>', self.on_step)
        root.bind('p', self.on_toggle_pause)
        root.bind('P', self.on_toggle_pause)
        root.bind('r', self.on_restart)
        root.bind('R', self.on_restart)
        root.bind('m', self.on_toggle_mode)
        root.bind('M', self.on_toggle_mode)
        root.bind('<Escape>', lambda e: root.destroy())

        self.running = False
        self.paused = False
        self.manual_mode = MANUAL_STEP_MODE
        self._reset_state()
        self._layout()
        self._draw_all()

        if not self.manual_mode:
            self._loop()

    # ---------- State ----------
    def _reset_state(self):
        self.cols = GRID_COLS
        self.rows = GRID_ROWS
        cx, cy = self.cols // 2, self.rows // 2
        # Initial snake of length START_LEN heading Right
        self.direction = 'Right'
        self.pending_dir = 'Right'
        # Head at the end of list
        self.snake = [(cx - i, cy) for i in range(START_LEN)][::-1]
        self.spawn_food()
        self.score = 0
        self.speed_ms = START_SPEED_MS
        self.tick_after = None
        self.running = True
        self.paused = False

    def spawn_food(self):
        free = {(x, y) for x in range(self.cols) for y in range(self.rows)} - set(self.snake)
        if not free:
            self.food = None
            return
        self.food = random.choice(tuple(free))

    # ---------- Layout & drawing ----------
    def _layout(self):
        w = max(200, self.canvas.winfo_width())
        h = max(200, self.canvas.winfo_height())
        # Compute cell size that fits grid with margins
        gw = w - 2*MARGIN
        gh = h - 2*MARGIN
        self.cell = max(8, min(gw / self.cols, gh / self.rows))
        self.x0 = (w - self.cols * self.cell) / 2
        self.y0 = (h - self.rows * self.cell) / 2

    def _cell_rect(self, x, y, pad=0.0):
        px = self.x0 + x * self.cell
        py = self.y0 + y * self.cell
        return (px + pad, py + pad, px + self.cell - pad, py + self.cell - pad)

    def _draw_grid(self):
        # Optional faint grid for aesthetics
        for c in range(self.cols + 1):
            x = self.x0 + c * self.cell
            self.canvas.create_line(x, self.y0, x, self.y0 + self.rows * self.cell, fill=GRID_COLOR)
        for r in range(self.rows + 1):
            y = self.y0 + r * self.cell
            self.canvas.create_line(self.x0, y, self.x0 + self.cols * self.cell, y, fill=GRID_COLOR)

    def _draw_all(self):
        self.canvas.delete('all')
        self._draw_grid()

        # Food
        if self.food is not None:
            fx, fy = self.food
            self.canvas.create_oval(*self._cell_rect(fx, fy, pad=self.cell*0.18), fill=FOOD_COLOR, outline="")

        # Snake body
        for i, (sx, sy) in enumerate(self.snake):
            pad = self.cell * 0.12
            color = SNAKE_HEAD_COLOR if i == len(self.snake) - 1 else SNAKE_COLOR
            self.canvas.create_rectangle(*self._cell_rect(sx, sy, pad=pad), fill=color, outline="")

        # HUD text
        mode = 'MANUAL' if self.manual_mode else 'AUTO'
        help_hint = 'Arrows/WASD to turn & step, SPACE=step' if self.manual_mode else 'Arrows/WASD to turn, P=pause'
        speed_info = '' if self.manual_mode else f"   Speed: {max(1, int(1000/self.speed_ms))} tps"
        self.canvas.itemconfigure(self.hud, text=f"Mode: {mode}   Score: {self.score}   Length: {len(self.snake)}{speed_info}   M=toggle mode   {help_hint}   R=restart")
        self.canvas.coords(self.hud, 10, 10)

        if not self.running:
            self._draw_message("Game Over — Press R to restart")
        elif self.paused and not self.manual_mode:
            self._draw_message("Paused — Press P to resume")

    def _draw_message(self, text):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        box = self.canvas.create_rectangle(w*0.2, h*0.4, w*0.8, h*0.6, fill="#000", outline="#444")
        lbl = self.canvas.create_text((w/2), (h/2), text=text, fill=TEXT_COLOR, font=("Segoe UI", 18, "bold"))
        self.msg = (box, lbl)

    # ---------- Input ----------
    def on_arrow(self, event):
        self._set_direction(event.keysym)
        if self.manual_mode:
            self._tick()  # move immediately in manual mode

    def on_wasd(self, event):
        k = event.keysym.lower()
        if k == 'w':
            self._set_direction('Up')
        elif k == 's':
            self._set_direction('Down')
        elif k == 'a':
            self._set_direction('Left')
        elif k == 'd':
            self._set_direction('Right')
        if self.manual_mode:
            self._tick()  # step once

    def on_step(self, event=None):
        # SPACE steps forward without changing direction (manual mode)
        if self.manual_mode and self.running:
            self._tick()

    def _set_direction(self, dir_name):
        if dir_name not in DIRS:
            return
        # Prevent reversing directly into yourself
        if OPPOSITE.get(dir_name) == self.direction and len(self.snake) > 1:
            return
        self.pending_dir = dir_name

    def on_toggle_pause(self, event=None):
        if self.manual_mode or not self.running:
            return
        self.paused = not self.paused
        self._draw_all()

    def on_restart(self, event=None):
        self._reset_state()
        self._draw_all()

    def on_toggle_mode(self, event=None):
        # Toggle Manual <-> Auto
        self.manual_mode = not self.manual_mode
        self.paused = False
        self._draw_all()
        if not self.manual_mode:
            # enter auto loop
            self._schedule_next_tick()
        else:
            # cancel any scheduled tick
            if hasattr(self, 'tick_after') and self.tick_after is not None:
                try:
                    self.root.after_cancel(self.tick_after)
                except Exception:
                    pass
                self.tick_after = None

    # ---------- Game loop ----------
    def _loop(self):
        # Only used for auto mode timing; manual mode steps on key events.
        if self.running and not self.paused and not self.manual_mode:
            self._tick()
        self.root.after(16, self._loop)  # UI refresh cadence

    def _schedule_next_tick(self):
        if self.manual_mode:
            return
        if hasattr(self, 'tick_after') and self.tick_after is not None:
            try:
                self.root.after_cancel(self.tick_after)
            except Exception:
                pass
        self.tick_after = self.root.after(self.speed_ms, self._tick)

    def _tick(self):
        if not self.running:
            return
        # Apply pending direction at tick boundary
        if self.pending_dir:
            self.direction = self.pending_dir

        dx, dy = DIRS[self.direction]
        hx, hy = self.snake[-1]
        nx, ny = hx + dx, hy + dy

        # Wrap or collide with walls
        if WRAP_AROUND:
            nx %= self.cols
            ny %= self.rows
        else:
            if not (0 <= nx < self.cols and 0 <= ny < self.rows):
                self._game_over(); return

        # Self-collision (allow moving into tail only if it will move this tick when not growing)
        growing = (self.food is not None and (nx, ny) == self.food)
        body_without_tail = set(self.snake if growing else self.snake[1:])
        if (nx, ny) in body_without_tail:
            self._game_over(); return

        # Move
        self.snake.append((nx, ny))
        if growing:
            self.score += 1
            self.spawn_food()
            if not self.manual_mode:  # speed only matters in auto mode
                self.speed_ms = max(MIN_SPEED_MS, self.speed_ms - SPEED_GAIN_MS)
        else:
            self.snake.pop(0)

        self._draw_all()

        # Schedule next tick if in auto mode
        if not self.manual_mode:
            self._schedule_next_tick()

    def _game_over(self):
        self.running = False
        self._draw_all()

    # ---------- Resize ----------
    def _on_resize(self, event):
        self._layout()
        self._draw_all()


# --------------- Main --------------------

def main():
    random.seed()
    root = tk.Tk()
    root.geometry(f"{int(GRID_COLS*CELL_SIZE + 2*MARGIN)}x{int(GRID_ROWS*CELL_SIZE + 2*MARGIN)}")
    root.minsize(480, 360)
    app = SnakeGame(root)
    root.mainloop()


if __name__ == '__main__':
    try:
        main()
    except tk.TclError as e:
        sys.stderr.write("\nUnable to start Tkinter GUI. Are you running in a headless environment?\n")
        sys.stderr.write(str(e) + "\n")
