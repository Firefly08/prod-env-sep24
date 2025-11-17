# ml_snake_qlearning.py
"""
Tabular Q-learning Snake (feature-based) — for learning purposes

We use a compact feature representation to keep the state space small:
  - danger_left, danger_straight, danger_right (relative to current heading)
  - food_left, food_ahead, food_right (relative to current heading)
  - current_heading in {Up,Right,Down,Left}
Actions are {turn_left, go_straight, turn_right} relative to heading.

Rewards:
  +10  for eating food
  -10  for death
  -0.01 per step to encourage efficiency

Run:
    python ml_snake_qlearning.py

This will train for several episodes and then demo one greedy episode.
Only numpy + stdlib are used.
"""
import random
import numpy as np

# Grid and game parameters
COLS, ROWS = 16, 12
WRAP = False  # walls are deadly
MAX_STEPS_PER_EP = 1000
EPISODES = 1000
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

ACTIONS = ["LEFT","STRAIGHT","RIGHT"]  # relative

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
        # Danger bits relative to current heading
        def danger_in_dir(test_dir):
            hx, hy = self.snake[-1]
            dx, dy = DIR_V[test_dir]
            nx, ny = hx+dx, hy+dy
            if not WRAP and not (0<=nx<COLS and 0<=ny<ROWS):
                return 1
            if WRAP:
                nx %= COLS; ny %= ROWS
            # collision with body (excluding tail cell that moves only if not growing is hard to estimate here; conservative)
            return 1 if (nx,ny) in set(self.snake[:-1]) else 0
        left_dir = LEFT_TURN[self.dir]
        right_dir = RIGHT_TURN[self.dir]
        straight_dir = self.dir
        danger_left = danger_in_dir(left_dir)
        danger_straight = danger_in_dir(straight_dir)
        danger_right = danger_in_dir(right_dir)

        # Food direction relative to heading
        hx, hy = self.snake[-1]
        fx, fy = self.food
        relx = fx - hx
        rely = fy - hy
        # Rotate frame so that 'ahead' is along current heading
        # Map vector into left/ahead/right indicators
        def rotate(vecx, vecy, dir_):
            if dir_ == UP:
                return vecx, vecy
            if dir_ == RIGHT:
                return vecy, -vecx
            if dir_ == DOWN:
                return -vecx, -vecy
            if dir_ == LEFT:
                return -vecy, vecx
        rx, ry = rotate(relx, rely, self.dir)
        food_left = 1 if rx < 0 else 0
        food_right = 1 if rx > 0 else 0
        food_ahead = 1 if ry < 0 else 0  # ahead is negative y in rotated UP frame

        # One-hot heading
        heading = [1 if self.dir==d else 0 for d in (UP,RIGHT,DOWN,LEFT)]

        return (danger_left, danger_straight, danger_right,
                food_left, food_ahead, food_right,
                *heading)

    def step(self, action):
        # action in {LEFT, STRAIGHT, RIGHT}
        if action == "LEFT":
            self.dir = LEFT_TURN[self.dir]
        elif action == "RIGHT":
            self.dir = RIGHT_TURN[self.dir]
        # else STRAIGHT keeps dir

        hx, hy = self.snake[-1]
        dx, dy = DIR_V[self.dir]
        nx, ny = hx+dx, hy+dy
        if WRAP:
            nx %= COLS; ny %= ROWS
        # Check collision
        if not (0<=nx<COLS and 0<=ny<ROWS):
            return self.state(), -10.0, True
        if (nx,ny) in set(self.snake[1:]):
            return self.state(), -10.0, True

        # Move
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

# Discretize state to table index
from collections import defaultdict

def state_key(s):
    return tuple(int(v) for v in s)

class QAgent:
    def __init__(self):
        self.Q = defaultdict(lambda: np.zeros(len(ACTIONS), dtype=np.float32))
        self.eps = EPS_START

    def act(self, s):
        if random.random() < self.eps:
            return random.choice(ACTIONS)
        q = self.Q[state_key(s)]
        return ACTIONS[int(np.argmax(q))]

    def update(self, s, a, r, s2):
        si = state_key(s)
        ai = ACTIONS.index(a)
        s2i = state_key(s2)
        best_next = np.max(self.Q[s2i])
        td = r + GAMMA * best_next - self.Q[si][ai]
        self.Q[si][ai] += ALPHA * td


def train():
    env = SnakeEnv()
    agent = QAgent()
    lengths = []
    rewards = []
    eps = agent.eps

    for ep in range(1, EPISODES+1):
        s = env.reset()
        total_r = 0.0
        steps = 0
        agent.eps = max(EPS_END, agent.eps * EPS_DECAY)
        while True:
            a = agent.act(s)
            s2, r, done = env.step(a)
            agent.update(s, a, r, s2)
            s = s2
            total_r += r
            steps += 1
            if done:
                break
        lengths.append(len(env.snake))
        rewards.append(total_r)
        if ep % 50 == 0:
            avg_len = np.mean(lengths[-50:])
            avg_r = np.mean(rewards[-50:])
            print(f"Ep {ep:4d} | eps={agent.eps:.3f} | avg_len(50)={avg_len:.2f} | avg_reward(50)={avg_r:.2f}")

    return agent


def demo(agent):
    env = SnakeEnv()
    agent.eps = 0.0
    s = env.reset()
    total_r = 0
    steps = 0
    while True:
        a = agent.act(s)
        s, r, done = env.step(a)
        total_r += r
        steps += 1
        if done:
            break
    print(f"Demo: steps={steps}, length={len(env.snake)}, total_reward={total_r:.2f}")


if __name__ == '__main__':
    agent = train()
    demo(agent)
