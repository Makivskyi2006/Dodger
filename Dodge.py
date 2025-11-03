import random
import time
import tkinter as tk

WIDTH, HEIGHT = 480, 640
PLAYER_W, PLAYER_H = 40, 16
PLAYER_SPEED = 7

BLOCK_W_RANGE = (20, 80)     # min/max width of falling blocks
BLOCK_H = 14
BLOCK_SPEED_START = 3
BLOCK_SPEED_MAX = 14
SPAWN_EVERY_MS_START = 650   # how often to spawn at the beginning
SPAWN_EVERY_MS_MIN = 220

DIFFICULTY_STEP_SEC = 6      # every N seconds, increase difficulty
SCORE_PER_SECOND = 10

COLOR_BG = "#0f1117"
COLOR_PLAYER = "#26c281"
COLOR_BLOCK = "#ff6655"
COLOR_TEXT = "#e6e6e6"
COLOR_OVERLAY = "#000000"

class Dodger:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Dodger — Python/tkinter demo")
        root.resizable(False, False)

        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT, bg=COLOR_BG, highlightthickness=0
        )
        self.canvas.pack()

        self.hud = tk.Label(
            root,
            text="Score: 0   Pause: [Space]   Restart: [R]",
            fg=COLOR_TEXT,
            bg=COLOR_BG,
            font=("Segoe UI", 12),
        )
        self.hud.place(x=8, y=8)

        # input state
        self.key_left = False
        self.key_right = False

        root.bind("<KeyPress-Left>", lambda e: self._set_key("left", True))
        root.bind("<KeyRelease-Left>", lambda e: self._set_key("left", False))
        root.bind("<KeyPress-Right>", lambda e: self._set_key("right", True))
        root.bind("<KeyRelease-Right>", lambda e: self._set_key("right", False))
        root.bind("<KeyPress-a>", lambda e: self._set_key("left", True))
        root.bind("<KeyRelease-a>", lambda e: self._set_key("left", False))
        root.bind("<KeyPress-d>", lambda e: self._set_key("right", True))
        root.bind("<KeyRelease-d>", lambda e: self._set_key("right", False))
        root.bind("<space>", self.toggle_pause)
        root.bind("<Key-r>", self.restart)

        self.reset_game()
        self.loop()

    def reset_game(self):
        self.canvas.delete("all")
        self.game_over = False
        self.paused = False

        # player rect (x is centered)
        self.player_x = WIDTH // 2
        self.player_y = HEIGHT - 60


        self.blocks = []

        self.block_speed = BLOCK_SPEED_START
        self.spawn_every_ms = SPAWN_EVERY_MS_START
        self.last_spawn_ts = time.time()
        self.start_ts = time.time()
        self.last_step_ts = time.time()
        self.last_difficulty_ts = time.time()
        self.score = 0

        # draw once
        self._draw_player()
        self._update_hud()

    def restart(self, _=None):
        self.reset_game()

    def toggle_pause(self, _=None):
        if self.game_over:
            return
        self.paused = not self.paused
        self._update_hud()
        if self.paused:
            self._overlay("PAUSED")
        else:
            self.canvas.delete("overlay")


    def _set_key(self, which: str, down: bool):
        if which == "left":
            self.key_left = down
        elif which == "right":
            self.key_right = down


    def loop(self):
        self._step()
        # use a modest fixed step; visual speed comes from object speeds
        self.root.after(16, self.loop)  # ~60 FPS

    def _step(self):
        now = time.time()
        dt = now - self.last_step_ts
        self.last_step_ts = now

        if self.game_over or self.paused:
            return

        if now - self.last_difficulty_ts >= DIFFICULTY_STEP_SEC:
            self.last_difficulty_ts = now
            self.block_speed = min(BLOCK_SPEED_MAX, self.block_speed + 1)
            self.spawn_every_ms = max(SPAWN_EVERY_MS_MIN, self.spawn_every_ms - 40)

        self.score += int(SCORE_PER_SECOND * dt)

        # movement
        vx = 0
        if self.key_left:
            vx -= PLAYER_SPEED
        if self.key_right:
            vx += PLAYER_SPEED
        self.player_x = max(PLAYER_W // 2, min(WIDTH - PLAYER_W // 2, self.player_x + vx))

        # spawn logic
        if (now - self.last_spawn_ts) * 1000 >= self.spawn_every_ms:
            self._spawn_block()
            self.last_spawn_ts = now

        # update blocks
        for b in self.blocks:
            b["y"] += b["speed"]

        # remove off-screen blocks
        self.blocks = [b for b in self.blocks if b["y"] < HEIGHT + BLOCK_H]

        # collisions
        if self._collides_any():
            self._end_game()
            return

        self._redraw()

    def _draw_player(self):
        self.canvas.delete("player")
        x1 = self.player_x - PLAYER_W // 2
        y1 = self.player_y - PLAYER_H // 2
        x2 = self.player_x + PLAYER_W // 2
        y2 = self.player_y + PLAYER_H // 2
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_PLAYER, outline="", tags="player")

    def _draw_blocks(self):
        self.canvas.delete("block")
        for b in self.blocks:
            x1 = b["x"] - b["w"] // 2
            y1 = b["y"] - BLOCK_H // 2
            x2 = b["x"] + b["w"] // 2
            y2 = b["y"] + BLOCK_H // 2
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_BLOCK, outline="", tags="block")

    def _redraw(self):
        self._draw_player()
        self._draw_blocks()
        self._update_hud()

    def _overlay(self, text: str):
        self.canvas.delete("overlay")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=COLOR_OVERLAY, stipple="gray50",
                                     outline="", tags="overlay")
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 - 10, text=text, fill=COLOR_TEXT,
            font=("Segoe UI", 28, "bold"), tags="overlay"
        )
        if text == "GAME OVER":
            self.canvas.create_text(
                WIDTH // 2, HEIGHT // 2 + 24, text="Press R to restart",
                fill="#dddddd", font=("Segoe UI", 13), tags="overlay"
            )

    def _update_hud(self):
        status = ""
        if self.paused:
            status = "Paused"
        if self.game_over:
            status = "Game Over — press [R] to restart"
        self.hud.config(text=f"Score: {self.score}   {status}")

    def _spawn_block(self):
        w = random.randint(*BLOCK_W_RANGE)
        x = random.randint(w // 2, WIDTH - w // 2)
        speed = self.block_speed + random.uniform(-0.8, 0.8)
        self.blocks.append({"x": x, "y": -BLOCK_H, "w": w, "speed": speed})

    def _collides_any(self) -> bool:
        px1 = self.player_x - PLAYER_W // 2
        py1 = self.player_y - PLAYER_H // 2
        px2 = self.player_x + PLAYER_W // 2
        py2 = self.player_y + PLAYER_H // 2
        for b in self.blocks:
            bx1 = b["x"] - b["w"] // 2
            by1 = b["y"] - BLOCK_H // 2
            bx2 = b["x"] + b["w"] // 2
            by2 = b["y"] + BLOCK_H // 2
            if not (px2 < bx1 or px1 > bx2 or py2 < by1 or py1 > by2):
                return True
        return False

    def _end_game(self):
        self.game_over = True
        self._update_hud()
        self._overlay("GAME OVER")

def main():
    root = tk.Tk()
    Dodger(root)
    root.mainloop()

if __name__ == "__main__":
    main()
