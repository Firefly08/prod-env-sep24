# ml_snake_qlearning_visual.py
"""
Visual RL for Snake — Tabular Q-Learning + Animated Viewer

- Trains a compact tabular Q-learner with features:
    danger_left / straight / right, food_left / ahead / right, heading one-hot
- Live **Tk** window shows the grid, snake, and food.
- You can train for chunks of episodes and then **demo** the greedy policy.

Controls:
  T : train 200 episodes (repeat as you like)
  D : demo greedy policy (animated)
  A : toggle auto-demo loop
  R : reset agent & environment
  V : show current Q-values (LEFT, STRAIGHT, RIGHT) in the HUD
  Esc : quit

Requires: numpy (and stdlib + tkinter)
Run:  python ml_snake_qlearning_visual.py
"""
import random
import tkinter as tk
import numpy as np

# ---- Env params ----
COLS, ROWS = 20, 15
WRAP = False
MAX_STEPS_PER_EP = 600

# ---- Q-learning params ----
EPISODES_PER_TRAIN = 200
GAMMA = 0.95
ALPHA = 0.1
EPS_START = 1.0
EPS_END = 0.05
EPS_DECAY = 0.995

# Directions
UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3
DIR_V = {UP:(0,-1), RIGHT:(1,0), DOWN:(0,1), LEFT:(-1,0)}
LEFT_TURN = {UP:LEFT, LEFT:DOWN, DOWN:RIGHT, RIGHT:UP}
RIGHT_TURN = {UP:RIGHT, RIGHT:DOWN, DOWN:LEFT, LEFT:UP}

ACTIONS = ["LEFT","STRAIGHT","RIGHT"]

class SnakeEnv:
    def __init__(self):
        self.reset()

    def reset(self):
        cx, cy = COLS//2, ROWS//2
        self.dir = RIGHT
        self.snake = [(cx-2,cy),(cx-1,cy),(cx,cy)]  # head last
        self.spawn_food()
        self.steps = 0
        return self.state()

    def spawn_food(self):
        free = {(x,y) for x in range(COLS) for y in range(ROWS)} - set(self.snake)
        self.food = random.choice(tuple(free))

    def state(self):
        # danger flags
        def danger_in_dir(test_dir):
            hx, hy = self.snake[-1]
            dx, dy = DIR_V[test_dir]
            nx, ny = hx+dx, hy+dy
            if not WRAP and not (0<=nx<COLS and 0<=ny<ROWS):
                return 1
            if WRAP:
                nx %= COLS; ny %= ROWS
            return 1 if (nx,ny) in set(self.snake[:-1]) else 0
        left_dir = LEFT_TURN[self.dir]
        right_dir = RIGHT_TURN[self.dir]
        straight_dir = self.dir
        danger_left = danger_in_dir(left_dir)
        danger_straight = danger_in_dir(straight_dir)
        danger_right = danger_in_dir(right_dir)
        # food direction (relative)
        hx, hy = self.snake[-1]
        fx, fy = self.food
        relx, rely = fx - hx, fy - hy
        def rotate(x,y,dir):
            if dir == UP: return x,y
            if dir == RIGHT: return y, -x
            if dir == DOWN: return -x, -y
            if dir == LEFT: return -y, x
        rx, ry = rotate(relx,rely,self.dir)
        food_left = 1 if rx < 0 else 0
        food_right = 1 if rx > 0 else 0
        food_ahead = 1 if ry < 0 else 0
        heading = [1 if self.dir==d else 0 for d in (UP,RIGHT,DOWN,LEFT)]
        return (danger_left, danger_straight, danger_right,
                food_left, food_ahead, food_right,
                *heading)

    def step(self, action):
        if action == "LEFT":
            self.dir = LEFT_TURN[self.dir]
        elif action == "RIGHT":
            self.dir = RIGHT_TURN[self.dir]
        hx, hy = self.snake[-1]
        dx, dy = DIR_V[self.dir]
        nx, ny = hx+dx, hy+dy
        if WRAP:
            nx %= COLS; ny %= ROWS
        if not (0<=nx<COLS and 0<=ny<ROWS):
            return self.state(), -10.0, True
        if (nx,ny) in set(self.snake[1:]):
            return self.state(), -10.0, True
        self.snake.append((nx,ny))
        reward = -0.01
        done = False
        if (nx,ny) == self.food:
            reward = 10.0
            self.spawn_food()
        else:
            self.snake.pop(0)
        self.steps += 1
        if self.steps >= MAX_STEPS_PER_EP:
            done = True
        return self.state(), reward, done

# ---- Q agent ----
from collections import defaultdict

def skey(s):
    return tuple(int(v) for v in s)

class QAgent:
    def __init__(self):
        self.Q = defaultdict(lambda: np.zeros(len(ACTIONS), dtype=np.float32))
        self.eps = EPS_START

    def act(self, s):
        if random.random() < self.eps:
            return random.choice(ACTIONS)
        q = self.Q[skey(s)]
        return ACTIONS[int(np.argmax(q))]

    def update(self, s, a, r, s2):
        si = skey(s)
        ai = ACTIONS.index(a)
        s2i = skey(s2)
        best_next = np.max(self.Q[s2i])
        td = r + 0.0 + GAMMA * best_next - self.Q[si][ai]
        self.Q[si][ai] += ALPHA * td

# ---- Viewer ----
class SnakeViewer:
    def __init__(self, root):
        self.root = root
        root.title("Snake RL — Q-learning Visual")
        self.canvas = tk.Canvas(root, width=900, height=700, bg="#111", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.env = SnakeEnv()
        self.agent = QAgent()
        self.auto_demo = False
        self.show_qvals = True

        root.bind('<Configure>', self.on_resize)
        root.bind('t', self.on_train)
        root.bind('T', self.on_train)
        root.bind('d', self.on_demo)
        root.bind('D', self.on_demo)
        root.bind('a', self.on_toggle_auto)
        root.bind('A', self.on_toggle_auto)
        root.bind('r', self.on_reset)
        root.bind('R', self.on_reset)
        root.bind('v', self.on_toggle_qvals)
        root.bind('V', self.on_toggle_qvals)
        root.bind('<Escape>', lambda e: root.destroy())

        self.ep_counter = 0
        self.len_hist = []
        self.reward_hist = []

        self._layout()
        self.draw_all()

    # ---- Layout & drawing ----
    def _layout(self):
        w = self.canvas.winfo_width() or 900
        h = self.canvas.winfo_height() or 700
        gw = w - 260
        gh = h - 80
        self.cell = max(14, min(gw/COLS, gh/ROWS))
        self.x0 = (w - 260 - COLS*self.cell)/2 + 20
        self.y0 = (h - ROWS*self.cell)/2
        self.side_x = w - 230
        self.side_y = 40

    def rect(self, x,y,pad=0.0):
        px = self.x0 + x*self.cell
        py = self.y0 + y*self.cell
        return (px+pad, py+pad, px+self.cell-pad, py+self.cell-pad)

    def draw_grid(self):
        for c in range(COLS+1):
            x = self.x0 + c*self.cell
            self.canvas.create_line(x, self.y0, x, self.y0+ROWS*self.cell, fill="#2a2a2a")
        for r in range(ROWS+1):
            y = self.y0 + r*self.cell
            self.canvas.create_line(self.x0, y, self.x0+COLS*self.cell, y, fill="#2a2a2a")

    def draw_side_panel(self):
        # Panel background
        self.canvas.create_rectangle(self.side_x-20, 20, self.side_x+200, 660, fill="#181818", outline="#333")
        # Stats
        avgL = np.mean(self.len_hist[-50:]) if self.len_hist else 0
        avgR = np.mean(self.reward_hist[-50:]) if self.reward_hist else 0
        self.canvas.create_text(self.side_x, self.side_y, anchor='nw', fill="#ddd",
                                text=f"Episodes: {self.ep_counter}\nAvg length (last 50): {avgL:.2f}\nAvg reward (last 50): {avgR:.2f}\n\nKeys:\nT=train 200\nD=demo\nA=auto demo\nR=reset\nV=Q-values on/off",
                                font=("Segoe UI", 12))
        # Q-values
        if self.show_qvals:
            s = self.env.state()
            q = self.agent.Q[skey(s)]
            mx = max(1.0, float(np.max(np.abs(q))))
            labels = ["LEFT","STRAIGHT","RIGHT"]
            for i,lab in enumerate(labels):
                v = float(q[i])
                barw = 150 * (0.5 + 0.5 * (v/mx))  # normalized around half
                y = self.side_y + 200 + i*40
                self.canvas.create_text(self.side_x, y, anchor='w', fill="#bbb", text=f"{lab:>8}: {v:6.2f}", font=("Segoe UI", 12))
                self.canvas.create_rectangle(self.side_x, y+18, self.side_x+barw, y+30, fill="#3498db", outline="")

    def draw_all(self):
        self.canvas.delete('all')
        self.draw_grid()
        # Food
        fx, fy = self.env.food
        self.canvas.create_oval(*self.rect(fx,fy,pad=self.cell*0.18), fill="#e74c3c", outline="")
        # Snake
        for i,(sx,sy) in enumerate(self.env.snake):
            pad = self.cell*0.12
            color = "#4db6ff" if i==len(self.env.snake)-1 else "#36c"
            self.canvas.create_rectangle(*self.rect(sx,sy,pad=pad), fill=color, outline="")
        # Side panel
        self.draw_side_panel()

    # ---- Interaction ----
    def on_resize(self, e):
        self._layout(); self.draw_all()

    def train_chunk(self, episodes=EPISODES_PER_TRAIN):
        for _ in range(episodes):
            s = self.env.reset()
            total_r = 0.0
            self.agent.eps = max(EPS_END, self.agent.eps * EPS_DECAY)
            while True:
                a = self.agent.act(s)
                s2, r, done = self.env.step(a)
                self.agent.update(s, a, r, s2)
                s = s2
                total_r += r
                if done:
                    break
            self.ep_counter += 1
            self.len_hist.append(len(self.env.snake))
            self.reward_hist.append(total_r)
        self.draw_all()

    def on_train(self, e=None):
        self.train_chunk()

    def on_demo(self, e=None):
        self.auto_demo = False
        self.demo_step(reset=True)

    def on_toggle_auto(self, e=None):
        self.auto_demo = not self.auto_demo
        if self.auto_demo:
            self.demo_step(reset=True)

    def on_reset(self, e=None):
        self.env.reset(); self.draw_all()

    def on_toggle_qvals(self, e=None):
        self.show_qvals = not self.show_qvals
        self.draw_all()

    # ---- Demo animation ----
    def demo_step(self, reset=False):
        if reset:
            self.env.reset()
        # run until done, animating
        def step():
            s = self.env.state()
            # greedy
            q = self.agent.Q[skey(s)]
            a = ACTIONS[int(np.argmax(q))]
            s2, r, done = self.env.step(a)
            self.draw_all()
            if not done and (self.auto_demo):
                self.root.after(80, step)
        step()


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('1000x720+80+60')
    app = SnakeViewer(root)
    root.mainloop()
