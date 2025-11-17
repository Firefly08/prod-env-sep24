# ml_maze_visual.py
"""
Visual ML for Mazes — Supervised Model + Animated Viewer

- Trains a small softmax (logistic regression) to imitate shortest-path moves on
  random mazes using simple features (walls + relative goal vector).
- Then opens a Tk window to **visualize**:
    * The maze
    * Optional **distance heatmap** (BFS distance to goal)
    * **Model path** animation (gold)
    * **Oracle (BFS) path** (green)

Controls (in the viewer):
  Space : generate a new maze and animate the model
  H     : toggle heatmap on/off
  G     : toggle showing oracle (green) path
  P     : animate model path (again)
  O     : show one-step model **arrows** from every cell
  Esc   : quit

Requires: numpy (and standard library + tkinter)
Run:  python ml_maze_visual.py
"""

import math
import random
import tkinter as tk
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

# ---------- Maze primitives ----------
N, S, E, W = 1, 2, 4, 8
DX = {E: 1, W: -1, N: 0, S: 0}
DY = {E: 0, W: 0, N: -1, S: 1}
OPP = {E: W, W: E, N: S, S: N}
DIRS = [N, S, E, W]
DIR_IDX = {N:0, S:1, E:2, W:3}
IDX_DIR = {0:N, 1:S, 2:E, 3:W}

@dataclass
class Maze:
    rows: int
    cols: int
    grid: List[List[int]]

    @staticmethod
    def generate(rows: int, cols: int) -> 'Maze':
        g = [[0 for _ in range(cols)] for _ in range(rows)]
        r0, c0 = random.randrange(rows), random.randrange(cols)
        stack = [(r0, c0)]
        visited = [[False]*cols for _ in range(rows)]
        visited[r0][c0]=True
        while stack:
            r,c = stack[-1]
            neighbors = []
            for d in DIRS:
                nr, nc = r+DY[d], c+DX[d]
                if 0<=nr<rows and 0<=nc<cols and not visited[nr][nc]:
                    neighbors.append((d,nr,nc))
            if neighbors:
                d,nr,nc = random.choice(neighbors)
                g[r][c] |= d
                g[nr][nc] |= OPP[d]
                visited[nr][nc]=True
                stack.append((nr,nc))
            else:
                stack.pop()
        return Maze(rows, cols, g)

    def neighbors(self, r:int, c:int):
        for d in DIRS:
            if self.grid[r][c] & d:
                nr, nc = r+DY[d], c+DX[d]
                if 0<=nr<self.rows and 0<=nc<self.cols:
                    yield d, nr, nc

    def distance_to_goal(self, goal:Tuple[int,int]):
        gr, gc = goal
        dist = [[math.inf]*self.cols for _ in range(self.rows)]
        q = deque([(gr,gc)])
        dist[gr][gc]=0
        while q:
            r,c = q.popleft()
            for d, nr, nc in self.neighbors(r,c):
                if dist[nr][nc] is math.inf:
                    dist[nr][nc] = dist[r][c] + 1
                    q.append((nr,nc))
        return dist

# ---------- Features & dataset ----------

def features_for_cell(maze: Maze, r:int, c:int, goal:Tuple[int,int]):
    gr, gc = goal
    # Walls one-hot: [noN, noS, noE, noW]
    noN = 1.0 if (maze.grid[r][c] & N)==0 else 0.0
    noS = 1.0 if (maze.grid[r][c] & S)==0 else 0.0
    noE = 1.0 if (maze.grid[r][c] & E)==0 else 0.0
    noW = 1.0 if (maze.grid[r][c] & W)==0 else 0.0
    # Relative goal vector normalized
    dx = (gc - c) / max(1, maze.cols-1)
    dy = (gr - r) / max(1, maze.rows-1)
    dman = (abs(gr - r) + abs(gc - c)) / (maze.rows + maze.cols)
    return np.array([noN,noS,noE,noW, dx,dy, dman], dtype=np.float32)


def build_dataset(n_mazes:int=80, rows:int=15, cols:int=21, seed:int=0):
    rng = random.Random(seed)
    X, y = [], []
    for _ in range(n_mazes):
        maze = Maze.generate(rows, cols)
        goal = (rows-1, cols-1)
        dist = maze.distance_to_goal(goal)
        for r in range(rows):
            for c in range(cols):
                if dist[r][c] is math.inf:
                    continue
                best_dirs, best_val = [], dist[r][c]
                for d, nr, nc in maze.neighbors(r,c):
                    if dist[nr][nc] < best_val:
                        best_dirs = [d]; best_val = dist[nr][nc]
                    elif dist[nr][nc] == best_val:
                        best_dirs.append(d)
                if not best_dirs:
                    continue
                d = rng.choice(best_dirs)
                X.append(features_for_cell(maze, r,c, goal)); y.append(DIR_IDX[d])
    X = np.stack(X)
    y = np.array(y, dtype=np.int64)
    return X, y

# ---------- Softmax model ----------
class Softmax:
    def __init__(self, in_dim:int, n_classes:int):
        self.W = np.zeros((in_dim, n_classes), dtype=np.float32)
        self.b = np.zeros((n_classes,), dtype=np.float32)

    def predict(self, X):
        lg = X @ self.W + self.b
        return lg.argmax(axis=1)

    def fit(self, X, y, lr=0.4, epochs=25, reg=1e-4, batch_size=4096):
        n, d = X.shape
        k = self.b.shape[0]
        for ep in range(epochs):
            perm = np.random.permutation(n)
            for i in range(0, n, batch_size):
                idx = perm[i:i+batch_size]
                xb, yb = X[idx], y[idx]
                lg = xb @ self.W + self.b
                lg -= lg.max(axis=1, keepdims=True)
                exp = np.exp(lg)
                probs = exp / exp.sum(axis=1, keepdims=True)
                yoh = np.eye(k)[yb]
                grad = (probs - yoh)/len(idx)
                gW = xb.T @ grad + 2*reg*self.W
                gb = grad.sum(axis=0)
                self.W -= lr * gW
                self.b -= lr * gb

# ---------- Train once ----------
print("Building dataset…")
X, y = build_dataset(n_mazes=80, rows=15, cols=21, seed=7)
idx = np.random.permutation(len(X))
train = idx[: int(0.85*len(X))]
val = idx[int(0.85*len(X)):]
model = Softmax(in_dim=X.shape[1], n_classes=4)
print("Training…")
model.fit(X[train], y[train], epochs=30)
val_acc = (model.predict(X[val]) == y[val]).mean()
print(f"Validation accuracy: {val_acc*100:.2f}%")

# ---------- Viewer ----------
class MazeViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("ML Maze Viewer — Model (gold) vs Oracle (green)")
        self.canvas = tk.Canvas(master, width=1000, height=700, bg="#fafafa", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.rows, self.cols = 15, 21
        self.heatmap_on = True
        self.show_oracle_path = True
        self.show_model_arrows = False

        master.bind('<Configure>', self.on_resize)
        master.bind('<space>', self.on_space)
        master.bind('h', self.on_heatmap)
        master.bind('H', self.on_heatmap)
        master.bind('g', self.on_toggle_oracle)
        master.bind('G', self.on_toggle_oracle)
        master.bind('o', self.on_toggle_arrows)
        master.bind('O', self.on_toggle_arrows)
        master.bind('p', self.on_play_model)
        master.bind('P', self.on_play_model)
        master.bind('<Escape>', lambda e: master.destroy())

        self.new_maze()

    def new_maze(self):
        self.maze = Maze.generate(self.rows, self.cols)
        self.start = (0,0)
        self.goal = (self.rows-1, self.cols-1)
        self.dist = self.maze.distance_to_goal(self.goal)
        self.model_path = self.compute_model_path()
        self.oracle_path = self.compute_oracle_path()
        self._layout(); self.draw_all()
        self.play_path(self.model_path, color="#f1c40f")

    def compute_oracle_path(self):
        # Reconstruct shortest path by greedily stepping to lower distance
        r,c = self.start
        path=[(r,c)]
        seen=set([(r,c)])
        for _ in range(self.rows*self.cols*2):
            if (r,c)==self.goal:
                break
            best = None
            bv = self.dist[r][c]
            for _, nr, nc in self.maze.neighbors(r,c):
                if self.dist[nr][nc] < bv:
                    bv = self.dist[nr][nc]
                    best = (nr,nc)
            if best is None:
                break
            r,c = best
            if (r,c) in seen:
                break
            seen.add((r,c))
            path.append((r,c))
        return path

    def compute_model_path(self):
        r,c = self.start
        path=[(r,c)]
        seen=set([(r,c)])
        for _ in range(self.rows*self.cols*2):
            if (r,c)==self.goal:
                break
            x = features_for_cell(self.maze, r,c, self.goal)[None,:]
            a = int(model.predict(x)[0])  # 0..3
            d = IDX_DIR[a]
            if self.maze.grid[r][c] & d:
                r, c = r+DY[d], c+DX[d]
            else:
                # fall back to any neighbor (model mistake)
                moved=False
                for _,nr,nc in self.maze.neighbors(r,c):
                    r,c = nr,nc; moved=True; break
                if not moved:
                    break
            if (r,c) in seen:
                break
            seen.add((r,c))
            path.append((r,c))
        return path

    def on_resize(self, event):
        self._layout(); self.draw_all()

    def _layout(self):
        w = self.canvas.winfo_width(); h = self.canvas.winfo_height()
        gw = w - 40; gh = h - 60
        self.cell = max(8, min(gw/self.cols, gh/self.rows))
        self.x0 = (w - self.cols*self.cell)/2
        self.y0 = (h - self.rows*self.cell)/2

    def cell_rect(self, r,c, pad=0.0):
        x = self.x0 + c*self.cell
        y = self.y0 + r*self.cell
        return x+pad, y+pad, x+self.cell-pad, y+self.cell-pad

    def cell_center(self, r,c):
        x = self.x0 + c*self.cell + self.cell/2
        y = self.y0 + r*self.cell + self.cell/2
        return x,y

    def draw_all(self):
        self.canvas.delete('all')
        # Heatmap background
        if self.heatmap_on:
            maxd = max([d for row in self.dist for d in row if d is not math.inf] or [1])
            for r in range(self.rows):
                for c in range(self.cols):
                    d = self.dist[r][c]
                    if d is math.inf:
                        color = '#ffffff'
                    else:
                        t = d / max(1, maxd)
                        # blue -> white -> red
                        rcol = int(255 * t)
                        bcol = int(255 * (1-t))
                        color = f"#{rcol:02x}{int(220):02x}{bcol:02x}"
                    self.canvas.create_rectangle(*self.cell_rect(r,c), fill=color, outline='')
        # Walls
        wall='#111'
        for r in range(self.rows):
            for c in range(self.cols):
                x = self.x0 + c*self.cell
                y = self.y0 + r*self.cell
                if (self.maze.grid[r][c] & N)==0:
                    self.canvas.create_line(x,y,x+self.cell,y, fill=wall)
                if (self.maze.grid[r][c] & W)==0:
                    self.canvas.create_line(x,y,x,y+self.cell, fill=wall)
                if r==self.rows-1:
                    self.canvas.create_line(x,y+self.cell,x+self.cell,y+self.cell, fill=wall)
                if c==self.cols-1:
                    self.canvas.create_line(x+self.cell,y,x+self.cell,y+self.cell, fill=wall)
        # Start/Goal
        sx,sy = self.cell_center(*self.start)
        gx,gy = self.cell_center(*self.goal)
        rad = self.cell*0.28
        self.canvas.create_oval(sx-rad, sy-rad, sx+rad, sy+rad, fill="#1f77b4", outline='')
        self.canvas.create_rectangle(gx-rad, gy-rad, gx+rad, gy+rad, fill="#2ca02c", outline='')

        # Oracle path (static)
        if self.show_oracle_path and len(self.oracle_path)>1:
            coords=[]
            for r,c in self.oracle_path:
                x,y = self.cell_center(r,c); coords.extend([x,y])
            self.canvas.create_line(*coords, fill="#2ecc71", width=max(2,int(self.cell*0.15)))

        # Model arrows from each cell (optional)
        if self.show_model_arrows:
            for r in range(self.rows):
                for c in range(self.cols):
                    x = features_for_cell(self.maze, r,c, self.goal)[None,:]
                    a = int(model.predict(x)[0])
                    d = IDX_DIR[a]
                    cx,cy = self.cell_center(r,c)
                    lenv = self.cell*0.32
                    dx = DY[d]*(-lenv)  # note: N/S map to y axis
                    dy = DX[d]*(lenv)
                    self.canvas.create_line(cx,cy, cx+dy, cy+dx, arrow=tk.LAST, fill="#8e44ad")

        # HUD
        self.canvas.create_text(self.x0, self.y0-12, anchor='sw',
                                text=f"Val Acc: {val_acc*100:.1f}%   (Space=new maze & animate, H=heatmap, G=oracle, P=play, O=arrows)",
                                fill="#333", font=("Segoe UI", 12))

    def play_path(self, path, color="#f1c40f"):
        if len(path)<2: return
        rad = self.cell*0.22
        # animate moving dot along path
        x,y = self.cell_center(*path[0])
        dot = self.canvas.create_oval(x-rad,y-rad,x+rad,y+rad, fill=color, outline='')
        i=1
        def step():
            nonlocal i
            if i>=len(path): return
            x,y = self.cell_center(*path[i])
            self.canvas.coords(dot, x-rad,y-rad,x+rad,y+rad)
            i+=1
            self.master.after(30, step)
        step()

    # ---- Key handlers ----
    def on_space(self, event):
        self.new_maze()

    def on_heatmap(self, event):
        self.heatmap_on = not self.heatmap_on
        self.draw_all()

    def on_toggle_oracle(self, event):
        self.show_oracle_path = not self.show_oracle_path
        self.draw_all()

    def on_toggle_arrows(self, event):
        self.show_model_arrows = not self.show_model_arrows
        self.draw_all()

    def on_play_model(self, event):
        self.model_path = self.compute_model_path()
        self.draw_all()
        self.play_path(self.model_path, color="#f1c40f")


if __name__ == '__main__':
    root = tk.Tk()
    app = MazeViewer(root)
    root.geometry('1000x700+80+60')
    root.mainloop()
