# ml_maze_supervised.py
"""
Supervised learning on mazes (for learning purposes)

Goal
----
Given a random maze and the agent's local view (walls around + relative goal
vector), learn to predict the *next move* that follows the shortest path.

What it does
------------
1) Generates many random mazes (DFS backtracker) and builds a dataset.
   For each cell, it computes the BFS distance-to-goal and labels the action
   that moves to a neighbor with smaller distance.
2) Trains a simple multinomial logistic regression (softmax) with NumPy.
3) Evaluates on held-out mazes by rolling out the learned policy from start to goal.

Run
---
    python ml_maze_supervised.py

This prints dataset size, training loss, accuracy, and success rate on new mazes.

Dependencies: only numpy (and standard library).
"""

import math
import random
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

# ---------------- Maze generator ----------------
N, S, E, W = 1, 2, 4, 8
DX = {E: 1, W: -1, N: 0, S: 0}
DY = {E: 0, W: 0, N: -1, S: 1}
OPP = {E: W, W: E, N: S, S: N}
DIRS = [N, S, E, W]
DIR_IDX = {N:0, S:1, E:2, W:3}

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

# --------------- Dataset builder ---------------

def features_for_cell(maze: Maze, r:int, c:int, goal:Tuple[int,int]):
    gr, gc = goal
    # Walls one-hot: [noN, noS, noE, noW]
    noN = 1.0 if (maze.grid[r][c] & N)==0 else 0.0
    noS = 1.0 if (maze.grid[r][c] & S)==0 else 0.0
    noE = 1.0 if (maze.grid[r][c] & E)==0 else 0.0
    noW = 1.0 if (maze.grid[r][c] & W)==0 else 0.0
    # Relative goal vector normalized to [-1,1]
    dx = (gc - c) / max(1, maze.cols-1)
    dy = (gr - r) / max(1, maze.rows-1)
    # Distance to goal (approx) normalized
    dman = (abs(gr - r) + abs(gc - c)) / (maze.rows + maze.cols)
    return np.array([noN,noS,noE,noW, dx,dy, dman], dtype=np.float32)


def build_dataset(n_mazes:int=150, rows:int=15, cols:int=21, seed:int=0):
    rng = random.Random(seed)
    X, y = [], []
    for i in range(n_mazes):
        maze = Maze.generate(rows, cols)
        start = (0,0)
        goal = (rows-1, cols-1)
        dist = maze.distance_to_goal(goal)
        # For each cell, if not infinity, label the action that goes to smaller distance
        for r in range(rows):
            for c in range(cols):
                if dist[r][c] is math.inf:
                    continue
                # find best action (tie-break randomly for variety)
                best_dirs = []
                best_val = dist[r][c]
                for d,nr,nc in maze.neighbors(r,c):
                    if dist[nr][nc] < best_val:
                        best_dirs = [d]
                        best_val = dist[nr][nc]
                    elif dist[nr][nc] == best_val:
                        best_dirs.append(d)
                if not best_dirs:
                    continue
                d = rng.choice(best_dirs)
                X.append(features_for_cell(maze, r,c, goal))
                y.append(DIR_IDX[d])
    X = np.stack(X)
    y = np.array(y, dtype=np.int64)
    return X, y

# --------------- Softmax regression ---------------
class Softmax:
    def __init__(self, in_dim:int, n_classes:int):
        self.W = np.zeros((in_dim, n_classes), dtype=np.float32)
        self.b = np.zeros((n_classes,), dtype=np.float32)

    def logits(self, X):
        return X @ self.W + self.b

    def predict(self, X):
        lg = self.logits(X)
        return lg.argmax(axis=1)

    def fit(self, X, y, lr=0.3, epochs=40, reg=1e-4, batch_size=2048):
        n, d = X.shape
        k = self.b.shape[0]
        for ep in range(epochs):
            # minibatch SGD
            perm = np.random.permutation(n)
            total_loss = 0.0
            for i in range(0, n, batch_size):
                idx = perm[i:i+batch_size]
                xb, yb = X[idx], y[idx]
                lg = xb @ self.W + self.b  # (B,K)
                lg -= lg.max(axis=1, keepdims=True)
                exp = np.exp(lg)
                probs = exp / exp.sum(axis=1, keepdims=True)
                # loss: -log p(y)
                y_onehot = np.eye(k)[yb]
                loss = -np.log((probs * y_onehot).sum(axis=1) + 1e-9).mean()
                # L2
                loss += reg * (self.W**2).sum()
                total_loss += loss * len(idx)
                # grads
                grad = (probs - y_onehot)/len(idx)  # (B,K)
                gW = xb.T @ grad + 2*reg*self.W
                gb = grad.sum(axis=0)
                self.W -= lr * gW
                self.b -= lr * gb
            print(f"epoch {ep+1:02d}: loss={total_loss/n:.4f}")

# --------------- Evaluation / rollout ---------------

def policy_move(model:Softmax, maze:Maze, r:int, c:int, goal:Tuple[int,int]):
    x = features_for_cell(maze, r,c, goal)[None, :]
    a = int(model.predict(x)[0])  # 0..3 -> N,S,E,W
    return [N,S,E,W][a]


def rollout_success_rate(model:Softmax, n_mazes:int=50, rows:int=15, cols:int=21, max_steps_factor:float=4.0):
    success = 0
    for _ in range(n_mazes):
        maze = Maze.generate(rows, cols)
        start = (0,0)
        goal = (rows-1, cols-1)
        r,c = start
        max_steps = int(max_steps_factor * rows * cols)
        for t in range(max_steps):
            if (r,c) == goal:
                success += 1
                break
            d = policy_move(model, maze, r,c, goal)
            # if chosen dir isn't available (model mistake), pick any valid neighbor as fallback
            moved = False
            if maze.grid[r][c] & d:
                r, c = r+DY[d], c+DX[d]
                moved = True
            else:
                for dd, nr, nc in maze.neighbors(r,c):
                    r,c = nr,nc
                    moved = True
                    break
            if not moved:
                break
    return success / n_mazes


def main():
    # Build dataset
    X, y = build_dataset(n_mazes=120, rows=15, cols=21, seed=42)
    n = len(X)
    print(f"Dataset: {n} samples, dim={X.shape[1]}")
    # Train/val split
    idx = np.random.permutation(n)
    train_idx = idx[: int(0.85*n)]
    val_idx = idx[int(0.85*n):]
    Xtr, ytr = X[train_idx], y[train_idx]
    Xva, yva = X[val_idx], y[val_idx]

    model = Softmax(in_dim=X.shape[1], n_classes=4)
    model.fit(Xtr, ytr, lr=0.4, epochs=35, reg=1e-4, batch_size=4096)

    # Accuracy on validation set
    pred = model.predict(Xva)
    acc = (pred == yva).mean()
    print(f"Validation accuracy: {acc*100:.2f}%")

    # Rollout success on unseen mazes
    sr = rollout_success_rate(model, n_mazes=30, rows=15, cols=21)
    print(f"Rollout success rate to reach goal: {sr*100:.1f}%")


if __name__ == '__main__':
    main()
