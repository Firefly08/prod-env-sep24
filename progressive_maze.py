# progressive_maze.py
# Keyboard maze with breadcrumbs, solver visualization, and a title credit.
# - Random maze each run
# - Gets more complex each time you open it (persisted level)
# - Arrow keys / WASD to move
# - Breadcrumbs trail of visited cells
# - Shows shortest path after you finish (animated)
# - Title includes your name
# - Opens in a resizable window (not fullscreen)

import json
import random
import sys
import tkinter as tk
from collections import deque
from pathlib import Path

# --------------------- Settings ---------------------
AUTHOR = "Horea Lazar"  # Name shown in title banner
INCREMENT_ON_LAUNCH = True  # Increase level every time the app launches
PROGRESS_FILE = ".maze_progress.json"  # stored next to this script

# Window / viewport
VIEWPORT_WIDTH = 1000
VIEWPORT_HEIGHT = 800
MARGIN = 24

# Level sizing policy
BASE_ROWS = 15
BASE_COLS = 21
STEP_PER_LEVEL = 2
MAX_ROWS = 65
MAX_COLS = 85

# Colors
PLAYER_COLOR = "#1f77b4"
GOAL_COLOR = "#2ca02c"
WALL_COLOR = "#111"
BG_COLOR = "#fafafa"
TEXT_COLOR = "#333"
BREADCRUMB_COLOR = "#cfe8ff"  # light blue
SOLUTION_COLOR = "#f1c40f"    # gold

# Animation
SOLUTION_DRAW_DELAY_MS = 18  # per segment


# --------------------- Utilities ---------------------
def script_dir() -> Path:
    try:
        return Path(__file__).resolve().parent
    except NameError:
        return Path.cwd()


def progress_path() -> Path:
    return script_dir() / PROGRESS_FILE


def load_level() -> int:
    p = progress_path()
    if p.exists():
        try:
            level = int(json.loads(p.read_text()).get("level", 1))
        except Exception:
            level = 1
    else:
        level = 1
    if INCREMENT_ON_LAUNCH:
        level += 1
        save_level(level)
    return max(1, level)


def save_level(level: int) -> None:
    try:
        progress_path().write_text(json.dumps({"level": int(level)}, indent=2))
    except Exception:
        pass


def level_to_size(level: int) -> tuple[int, int]:
    rows = min(BASE_ROWS + (level - 1) * STEP_PER_LEVEL, MAX_ROWS)
    cols = min(BASE_COLS + (level - 1) * STEP_PER_LEVEL, MAX_COLS)
    return rows, cols


# --------------------- Maze Generation ---------------------
class Maze:
    """Perfect maze generated via iterative DFS / recursive backtracker."""

    N, S, E, W = 1, 2, 4, 8
    DX = {E: 1, W: -1, N: 0, S: 0}
    DY = {E: 0, W: 0, N: -1, S: 1}
    OPP = {E: W, W: E, N: S, S: N}

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        # Each cell stores bitwise flags of open passages (N/S/E/W). 0 means walled on all sides.
        self.grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self._generate()

    def _generate(self) -> None:
        r0, c0 = random.randrange(self.rows), random.randrange(self.cols)
        stack = [(r0, c0)]
        visited = [[False] * self.cols for _ in range(self.rows)]
        visited[r0][c0] = True

        while stack:
            r, c = stack[-1]
            neighbors = []
            for d in (self.N, self.S, self.E, self.W):
                nr, nc = r + self.DY[d], c + self.DX[d]
                if 0 <= nr < self.rows and 0 <= nc < self.cols and not visited[nr][nc]:
                    neighbors.append((d, nr, nc))
            if neighbors:
                d, nr, nc = random.choice(neighbors)
                self.grid[r][c] |= d
                self.grid[nr][nc] |= self.OPP[d]
                visited[nr][nc] = True
                stack.append((nr, nc))
            else:
                stack.pop()

    def can_move(self, r: int, c: int, d: int) -> bool:
        return (self.grid[r][c] & d) != 0

    def neighbors(self, r: int, c: int):
        for d in (self.N, self.S, self.E, self.W):
            if self.grid[r][c] & d:
                nr, nc = r + self.DY[d], c + self.DX[d]
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc

    def shortest_path(self, start: tuple[int, int], goal: tuple[int, int]):
        """Unweighted BFS shortest path; returns list of (r,c) from start to goal inclusive, or [] if none."""
        sr, sc = start
        gr, gc = goal
        q = deque([(sr, sc)])
        parent = { (sr, sc): None }
        while q:
            r, c = q.popleft()
            if (r, c) == (gr, gc):
                break
            for nr, nc in self.neighbors(r, c):
                if (nr, nc) not in parent:
                    parent[(nr, nc)] = (r, c)
                    q.append((nr, nc))
        if (gr, gc) not in parent:
            return []
        # Reconstruct
        path = []
        cur = (gr, gc)
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path.reverse()
        return path


# --------------------- Game UI ---------------------
class Game:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"Progressive Maze — by {AUTHOR}")
        self.root.resizable(True, True)

        self.level = load_level()
        self.rows, self.cols = level_to_size(self.level)

        self.canvas = tk.Canvas(root, width=VIEWPORT_WIDTH, height=VIEWPORT_HEIGHT, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # State for breadcrumbs and solution
        self.visited_cells: set[tuple[int,int]] = set()
        self.breadcrumb_items: dict[tuple[int,int], int] = {}
        self.solution_items: list[int] = []
        self.solution_path: list[tuple[int,int]] = []
        self.breadcrumbs_enabled = True

        # Bindings
        root.bind("<Configure>", self._on_resize)
        for key in ("<Up>", "<Down>", "<Left>", "<Right>"):
            root.bind(key, self.on_arrow)
        for key in ("w", "a", "s", "d", "W", "A", "S", "D"):
            root.bind(key, self.on_wasd)
        root.bind("<space>", self.on_space)
        root.bind("r", self.on_reset)
        root.bind("R", self.on_reset)
        root.bind("n", self.on_next_level)
        root.bind("N", self.on_next_level)
        root.bind("b", self.on_toggle_breadcrumbs)
        root.bind("B", self.on_toggle_breadcrumbs)
        root.bind("p", self.on_show_path)
        root.bind("P", self.on_show_path)
        root.bind("<Escape>", lambda e: root.destroy())

        self._new_maze(self.level)

    # ----- Maze lifecycle -----
    def _new_maze(self, level: int):
        self.level = level
        save_level(self.level)
        self.rows, self.cols = level_to_size(level)
        self.maze = Maze(self.rows, self.cols)
        self.start = (0, 0)
        self.goal = (self.rows - 1, self.cols - 1)
        self.player = list(self.start)

        # Reset overlays
        self.visited_cells.clear()
        self.breadcrumb_items.clear()
        self._clear_solution()

        self._layout()
        self._draw_all()
        self._update_banner()

    def _layout(self):
        w = self.canvas.winfo_width() or VIEWPORT_WIDTH
        h = self.canvas.winfo_height() or VIEWPORT_HEIGHT
        gw = max(1, w - 2 * MARGIN)
        gh = max(1, h - 2 * MARGIN)
        self.cell = max(4, min(gw / self.cols, gh / self.rows))
        self.x0 = (w - self.cols * self.cell) / 2
        self.y0 = (h - self.rows * self.cell) / 2

    def _draw_all(self):
        self.canvas.delete("all")

        # Background
        self.canvas.create_rectangle(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height(), fill=BG_COLOR, outline="")

        # Maze walls
        for r in range(self.rows):
            for c in range(self.cols):
                x = self.x0 + c * self.cell
                y = self.y0 + r * self.cell
                if (self.maze.grid[r][c] & Maze.N) == 0:
                    self.canvas.create_line(x, y, x + self.cell, y, fill=WALL_COLOR)
                if (self.maze.grid[r][c] & Maze.W) == 0:
                    self.canvas.create_line(x, y, x, y + self.cell, fill=WALL_COLOR)
                if r == self.rows - 1:
                    self.canvas.create_line(x, y + self.cell, x + self.cell, y + self.cell, fill=WALL_COLOR)
                if c == self.cols - 1:
                    self.canvas.create_line(x + self.cell, y, x + self.cell, y + self.cell, fill=WALL_COLOR)

        # Breadcrumbs that existed
        if self.breadcrumbs_enabled:
            for (r, c) in self.visited_cells:
                self._draw_breadcrumb(r, c)

        # Goal
        gx, gy = self._cell_center(*self.goal)
        pad = self.cell * 0.3
        self.goal_item = self.canvas.create_rectangle(gx - pad, gy - pad, gx + pad, gy + pad, fill=GOAL_COLOR, outline="")

        # Player
        self.player_item = self._draw_player()

        # Banner / Info overlay
        self.banner_item = self.canvas.create_text(
            self.canvas.winfo_width() / 2,
            max(10, self.y0 - 14),
            text="",
            anchor="n",
            font=("Segoe UI", 14, "bold"),
            fill=TEXT_COLOR)

        self.info_text = self.canvas.create_text(
            self.x0 + 8,
            self.y0 + self.rows * self.cell + 10,
            text="",
            anchor="nw",
            font=("Segoe UI", 11),
            fill=TEXT_COLOR)

        # If a solution path is known (e.g., after resize), redraw it
        if self.solution_path:
            self._draw_solution_path_static(self.solution_path)

    def _draw_player(self):
        px, py = self._cell_center(*self.player)
        r = self.cell * 0.3
        return self.canvas.create_oval(px - r, py - r, px + r, py + r, fill=PLAYER_COLOR, outline="")

    def _update_player(self):
        px, py = self._cell_center(*self.player)
        r = self.cell * 0.3
        self.canvas.coords(self.player_item, px - r, py - r, px + r, py + r)

    def _update_banner(self, extra: str = ""):
        text = f"Progressive Maze — by {AUTHOR}  |  Level {self.level}  |  Size {self.rows}×{self.cols}"
        if extra:
            text += f"  |  {extra}"
        if hasattr(self, 'banner_item'):
            self.canvas.itemconfigure(self.banner_item, text=text)

    def _update_info(self, text: str):
        if hasattr(self, 'info_text') and self.info_text:
            self.canvas.itemconfigure(self.info_text, text=text)

    def _cell_center(self, r: int, c: int) -> tuple[float, float]:
        x = self.x0 + c * self.cell + self.cell / 2
        y = self.y0 + r * self.cell + self.cell / 2
        return x, y

    # ----- Breadcrumbs -----
    def _draw_breadcrumb(self, r: int, c: int):
        if (r, c) in self.breadcrumb_items:
            return
        cx, cy = self._cell_center(r, c)
        size = self.cell * 0.18
        item = self.canvas.create_rectangle(cx - size, cy - size, cx + size, cy + size,
                                            fill=BREADCRUMB_COLOR, outline="")
        self.breadcrumb_items[(r, c)] = item

    def on_toggle_breadcrumbs(self, event=None):
        self.breadcrumbs_enabled = not self.breadcrumbs_enabled
        if not self.breadcrumbs_enabled:
            # Hide breadcrumb items
            for itm in self.breadcrumb_items.values():
                self.canvas.itemconfigure(itm, state='hidden')
            self._update_banner("breadcrumbs OFF (press B to toggle)")
        else:
            for itm in self.breadcrumb_items.values():
                self.canvas.itemconfigure(itm, state='normal')
            self._update_banner("breadcrumbs ON")

    # ----- Solution Path -----
    def _clear_solution(self):
        for itm in self.solution_items:
            try:
                self.canvas.delete(itm)
            except Exception:
                pass
        self.solution_items.clear()
        self.solution_path = []

    def _draw_solution_path_static(self, path: list[tuple[int,int]]):
        # Draw as a polyline connecting centers
        if len(path) < 2:
            return
        coords = []
        for r, c in path:
            x, y = self._cell_center(r, c)
            coords.extend([x, y])
        line = self.canvas.create_line(*coords, fill=SOLUTION_COLOR, width=max(2, int(self.cell*0.15)))
        self.solution_items.append(line)

    def _animate_solution(self, path: list[tuple[int,int]]):
        # Animate segment-by-segment
        self._clear_solution()
        if len(path) < 2:
            return
        idx = 1
        prevx, prevy = self._cell_center(*path[0])
        line = None

        def step():
            nonlocal idx, prevx, prevy, line
            if idx >= len(path):
                return
            x, y = self._cell_center(*path[idx])
            if line is None:
                line = self.canvas.create_line(prevx, prevy, x, y, fill=SOLUTION_COLOR,
                                               width=max(2, int(self.cell*0.15)))
                self.solution_items.append(line)
            else:
                # extend line by adding segment
                coords = self.canvas.coords(line) + [x, y]
                self.canvas.coords(line, *coords)
            prevx, prevy = x, y
            idx += 1
            self.root.after(SOLUTION_DRAW_DELAY_MS, step)

        step()

    def on_show_path(self, event=None):
        # Compute and (re)draw the shortest path from start to goal
        path = self.maze.shortest_path(self.start, self.goal)
        if path:
            self.solution_path = path
            self._animate_solution(path)
            self._update_info("Shortest path shown (gold). Press SPACE for new maze, N for next level.")
        else:
            self._update_info("No path found (unexpected for a perfect maze).")

    # ----- Events -----
    def _on_resize(self, event):
        self._layout()
        self._draw_all()
        self._update_banner()

    def on_arrow(self, event):
        key = event.keysym
        if key == "Up":
            self._try_move(Maze.N)
        elif key == "Down":
            self._try_move(Maze.S)
        elif key == "Left":
            self._try_move(Maze.W)
        elif key == "Right":
            self._try_move(Maze.E)

    def on_wasd(self, event):
        k = event.keysym.lower()
        if k == 'w':
            self._try_move(Maze.N)
        elif k == 's':
            self._try_move(Maze.S)
        elif k == 'a':
            self._try_move(Maze.W)
        elif k == 'd':
            self._try_move(Maze.E)

    def on_space(self, event):
        self._new_maze(self.level)

    def on_next_level(self, event=None):
        self._new_maze(self.level + 1)

    def on_reset(self, event=None):
        save_level(1)
        self._new_maze(1)

    # ----- Movement / Win check -----
    def _try_move(self, direction: int):
        r, c = self.player
        if self.maze.can_move(r, c, direction):
            nr = r + Maze.DY[direction]
            nc = c + Maze.DX[direction]
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                # Breadcrumb at current cell before moving
                if self.breadcrumbs_enabled:
                    self.visited_cells.add((r, c))
                    self._draw_breadcrumb(r, c)

                self.player = [nr, nc]
                self._update_player()

                if (nr, nc) == self.goal:
                    self._update_info("✔ Goal reached! Showing shortest path…")
                    # Compute and animate solution path
                    path = self.maze.shortest_path(self.start, self.goal)
                    self.solution_path = path
                    self._animate_solution(path)
                    # After a short pause, level up automatically
                    self.root.after(max(800, SOLUTION_DRAW_DELAY_MS * len(path) + 250),
                                    lambda: self._new_maze(self.level + 1))
        else:
            # Brief feedback color flash
            self.canvas.after(0, lambda: self.canvas.itemconfigure(self.player_item, fill="#ff7f0e"))
            self.canvas.after(120, lambda: self.canvas.itemconfigure(self.player_item, fill=PLAYER_COLOR))


# --------------------- Main ---------------------
def main():
    random.seed()
    root = tk.Tk()
    app = Game(root)

    # Open in a centered window (not fullscreen)
    root.update_idletasks()
    w, h = VIEWPORT_WIDTH, VIEWPORT_HEIGHT
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except tk.TclError as e:
        sys.stderr.write("\nUnable to start Tkinter GUI. Are you running in a headless environment?\n")
        sys.stderr.write(str(e) + "\n")
