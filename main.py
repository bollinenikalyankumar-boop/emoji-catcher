import pygame
import random
import sys
import math
import array

# ============================================================
# EMOJI CATCHER - ANDROID READY PYGAME VERSION
# Works with mouse on PC and touch/drag on Android.
# ============================================================

pygame.init()

# Audio may fail on some Android devices, so keep it optional.
sound_enabled = True
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    AUDIO_AVAILABLE = True
except pygame.error:
    AUDIO_AVAILABLE = False
    sound_enabled = False

# ------------------------------------------------------------
# Display
# ------------------------------------------------------------
BASE_WIDTH = 800
BASE_HEIGHT = 600

# Use a resizable window on PC and the Android screen size when available.
try:
    screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE)
except pygame.error:
    screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT))

pygame.display.set_caption("Emoji Catcher")
clock = pygame.time.Clock()

# ------------------------------------------------------------
# Colors
# ------------------------------------------------------------
BG_COLOR = (240, 242, 245)
TEXT_COLOR = (30, 30, 30)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
PURPLE = (155, 89, 182)
YELLOW = (255, 210, 55)
BLUE = (70, 130, 220)
WHITE = (255, 255, 255)
BLACK = (25, 25, 25)

# ------------------------------------------------------------
# Game settings
# ------------------------------------------------------------
sound_enabled = True
base_difficulty_speed = 3.0
MAX_LIVES = 5
GAME_TIME = 20.0

# ------------------------------------------------------------
# Scaling helpers
# ------------------------------------------------------------
def get_scale():
    width, height = screen.get_size()
    scale = min(width / BASE_WIDTH, height / BASE_HEIGHT)
    offset_x = (width - BASE_WIDTH * scale) / 2
    offset_y = (height - BASE_HEIGHT * scale) / 2
    return scale, offset_x, offset_y


def to_screen(x, y):
    scale, ox, oy = get_scale()
    return int(ox + x * scale), int(oy + y * scale)


def screen_to_game(x, y):
    scale, ox, oy = get_scale()
    if scale <= 0:
        return 0, 0
    return (x - ox) / scale, (y - oy) / scale


def draw_game_surface():
    screen.fill((15, 15, 20))


# ------------------------------------------------------------
# Fonts
# ------------------------------------------------------------
def make_font(size, bold=False):
    return pygame.font.SysFont("arial", size, bold=bold)


font_title = make_font(48, True)
font_ui = make_font(26, True)
font_small = make_font(20, False)


# ------------------------------------------------------------
# Sound generator
# ------------------------------------------------------------
def generate_sound(freq=440, duration=0.1, wave_type="square"):
    if not AUDIO_AVAILABLE:
        return None

    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array("h")
    amplitude = 14000

    for i in range(n_samples):
        t = i / sample_rate

        if wave_type == "square":
            wave = amplitude if (int(2 * freq * t) % 2) == 0 else -amplitude
        else:
            wave = int(
                amplitude
                * (2 * (t * freq - math.floor(t * freq + 0.5)))
            )

        # Small fade prevents clicks at the beginning/end.
        fade = min(1.0, i / max(1, sample_rate * 0.01),
                   (n_samples - i) / max(1, sample_rate * 0.01))
        buf.append(int(wave * max(0.0, fade)))

    try:
        return pygame.mixer.Sound(buffer=buf)
    except pygame.error:
        return None


sound_catch = generate_sound(880, 0.08)
sound_bomb = generate_sound(110, 0.40)
sound_mine = generate_sound(220, 0.20)
sound_lose = generate_sound(160, 0.25)


def play_sfx(sound):
    if sound_enabled and AUDIO_AVAILABLE and sound is not None:
        try:
            sound.play()
        except pygame.error:
            pass


# ------------------------------------------------------------
# Drawing icons
# Android-safe: no PIL, no external emoji fonts required.
# ------------------------------------------------------------
def draw_icon(surface, kind, center, size):
    x, y = center
    s = size

    if kind == "player":
        pygame.draw.circle(surface, YELLOW, (x, y), int(s * 0.48))
        pygame.draw.circle(surface, BLACK, (x - s * 0.16, y - s * 0.10),
                           max(2, int(s * 0.055)))
        pygame.draw.circle(surface, BLACK, (x + s * 0.16, y - s * 0.10),
                           max(2, int(s * 0.055)))
        pygame.draw.arc(
            surface,
            BLACK,
            (x - s * 0.23, y - s * 0.05, s * 0.46, s * 0.30),
            math.radians(20),
            math.radians(160),
            max(2, int(s * 0.055)),
        )

    elif kind == "shoe":
        points = [
            (x - s * 0.45, y - s * 0.10),
            (x - s * 0.05, y - s * 0.10),
            (x + s * 0.10, y + s * 0.20),
            (x + s * 0.42, y + s * 0.25),
            (x + s * 0.45, y + s * 0.42),
            (x - s * 0.45, y + s * 0.42),
        ]
        pygame.draw.polygon(surface, BLUE, points)
        pygame.draw.line(surface, WHITE,
                         (x - s * 0.15, y - s * 0.02),
                         (x + s * 0.12, y + s * 0.22), 3)

    elif kind == "donut":
        pygame.draw.circle(surface, (205, 130, 75), (x, y), int(s * 0.45))
        pygame.draw.circle(surface, (255, 175, 190), (x, y), int(s * 0.32))
        pygame.draw.circle(surface, BG_COLOR, (x, y), int(s * 0.12))

    elif kind == "banana":
        rect = pygame.Rect(
            x - s * 0.42, y - s * 0.38, s * 0.84, s * 0.76
        )
        pygame.draw.arc(surface, YELLOW, rect, math.radians(210),
                        math.radians(330), max(5, int(s * 0.15)))
        pygame.draw.circle(surface, (120, 80, 30),
                           (int(x - s * 0.38), int(y - s * 0.15)),
                           max(2, int(s * 0.06)))

    elif kind == "heart":
        r = s * 0.22
        pygame.draw.circle(surface, RED,
                           (int(x - r), int(y - r * 0.15)), int(r))
        pygame.draw.circle(surface, RED,
                           (int(x + r), int(y - r * 0.15)), int(r))
        pygame.draw.polygon(
            surface,
            RED,
            [
                (x - s * 0.42, y - s * 0.02),
                (x + s * 0.42, y - s * 0.02),
                (x, y + s * 0.45),
            ],
        )

    elif kind == "book":
        rect = pygame.Rect(x - s * 0.38, y - s * 0.42,
                           s * 0.76, s * 0.84)
        pygame.draw.rect(surface, (75, 110, 190), rect, border_radius=5)
        pygame.draw.line(surface, WHITE,
                         (x, y - s * 0.35),
                         (x, y + s * 0.35), max(2, int(s * 0.04)))
        pygame.draw.line(surface, WHITE,
                         (x - s * 0.27, y - s * 0.20),
                         (x - s * 0.06, y - s * 0.20), 2)

    elif kind == "mine":
        pygame.draw.circle(surface, BLACK, (x, y), int(s * 0.32))
        for angle in range(0, 360, 45):
            a = math.radians(angle)
            x1 = x + math.cos(a) * s * 0.30
            y1 = y + math.sin(a) * s * 0.30
            x2 = x + math.cos(a) * s * 0.48
            y2 = y + math.sin(a) * s * 0.48
            pygame.draw.line(surface, BLACK, (x1, y1), (x2, y2),
                             max(3, int(s * 0.08)))
        pygame.draw.circle(surface, RED, (x, y), int(s * 0.10))

    elif kind == "bomb":
        pygame.draw.circle(surface, BLACK, (x, y + s * 0.05),
                           int(s * 0.34))
        pygame.draw.line(surface, BLACK,
                         (x + s * 0.18, y - s * 0.25),
                         (x + s * 0.35, y - s * 0.43),
                         max(3, int(s * 0.07)))
        pygame.draw.circle(surface, RED,
                           (int(x + s * 0.40), int(y - s * 0.47)),
                           max(3, int(s * 0.08)))


# ------------------------------------------------------------
# Text
# ------------------------------------------------------------
def render_text(text, font, color, x, y, center=True):
    surf = font.render(text, True, color)
    rect = surf.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    # Scale from 800x600 coordinate system.
    scale, ox, oy = get_scale()
    scaled = pygame.transform.smoothscale(
        surf,
        (max(1, int(surf.get_width() * scale)),
         max(1, int(surf.get_height() * scale)))
    )

    if center:
        draw_rect = scaled.get_rect(
            center=(int(ox + x * scale), int(oy + y * scale))
        )
    else:
        draw_rect = scaled.get_rect(
            topleft=(int(ox + x * scale), int(oy + y * scale))
        )

    screen.blit(scaled, draw_rect)
    return pygame.Rect(x - rect.width / 2 if center else x,
                       y - rect.height / 2 if center else y,
                       rect.width, rect.height)


# ------------------------------------------------------------
# Buttons
# ------------------------------------------------------------
def draw_button(text, x, y, width, height, color):
    scale, ox, oy = get_scale()

    rect = pygame.Rect(x - width / 2, y - height / 2, width, height)

    screen_rect = pygame.Rect(
        int(ox + rect.x * scale),
        int(oy + rect.y * scale),
        int(rect.width * scale),
        int(rect.height * scale),
    )

    pygame.draw.rect(screen, color, screen_rect, border_radius=max(8, int(12 * scale)))
    pygame.draw.rect(screen, WHITE, screen_rect, 2, border_radius=max(8, int(12 * scale)))

    text_surf = font_ui.render(text, True, WHITE)
    text_surf = pygame.transform.smoothscale(
        text_surf,
        (max(1, int(text_surf.get_width() * scale)),
         max(1, int(text_surf.get_height() * scale)))
    )
    text_rect = text_surf.get_rect(center=screen_rect.center)
    screen.blit(text_surf, text_rect)

    return rect


def get_input_position(event):
    if event.type == pygame.MOUSEBUTTONDOWN:
        return screen_to_game(*event.pos)

    if event.type == pygame.FINGERDOWN:
        return screen_to_game(
            event.x * screen.get_width(),
            event.y * screen.get_height()
        )

    return None


# ------------------------------------------------------------
# Falling objects
# ------------------------------------------------------------
class FallingObject:
    TYPES = [
        {"kind": "shoe", "name": "Shoe", "time": 2, "points": 10, "type": "item"},
        {"kind": "donut", "name": "Donut", "time": 3, "points": 15, "type": "item"},
        {"kind": "banana", "name": "Banana", "time": 4, "points": 20, "type": "item"},
        {"kind": "heart", "name": "Heart", "time": 1, "points": 25, "type": "life"},
        {"kind": "book", "name": "Book", "time": 0, "points": -5, "type": "book"},
        {"kind": "mine", "name": "Mine", "time": -3, "points": -10, "type": "mine"},
        {"kind": "bomb", "name": "Bomb", "time": 0, "points": 0, "type": "bomb"},
    ]

    def __init__(self, current_speed):
        weights = [20, 20, 20, 10, 15, 10, 5]
        self.data = random.choices(self.TYPES, weights=weights)[0]
        self.x = random.randint(50, BASE_WIDTH - 50)
        self.y = -40
        self.speed = random.uniform(current_speed, current_speed + 1.5)
        self.size = 48
        self.rect = pygame.Rect(
            self.x - self.size / 2,
            self.y - self.size / 2,
            self.size,
            self.size,
        )

    def update(self):
        self.y += self.speed
        self.rect.center = (int(self.x), int(self.y))

    def draw(self):
        scale, ox, oy = get_scale()
        sx = int(ox + self.x * scale)
        sy = int(oy + self.y * scale)
        draw_icon(screen, self.data["kind"], (sx, sy), int(self.size * scale))


# ------------------------------------------------------------
# Pause menu
# ------------------------------------------------------------
def pause_menu():
    while True:
        scale, ox, oy = get_scale()

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        render_text("GAME PAUSED", font_title, WHITE, 400, 170)

        btn_resume = draw_button("RESUME", 400, 270, 250, 60, GREEN)
        btn_menu = draw_button("MAIN MENU", 400, 350, 250, 60, PURPLE)
        btn_exit = draw_button("EXIT GAME", 400, 430, 250, 60, RED)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_p, pygame.K_ESCAPE):
                    return "resume"

            pos = get_input_position(event)
            if pos is not None:
                if btn_resume.collidepoint(pos):
                    return "resume"
                if btn_menu.collidepoint(pos):
                    return "menu"
                if btn_exit.collidepoint(pos):
                    pygame.quit()
                    sys.exit()

        clock.tick(60)


# ------------------------------------------------------------
# Game over
# ------------------------------------------------------------
def game_over_screen(score):
    while True:
        screen.fill(BG_COLOR)

        render_text("GAME OVER!", font_title, RED, 400, 170)
        render_text(f"Final Score: {score}", font_ui, TEXT_COLOR, 400, 250)

        btn_retry = draw_button("PLAY AGAIN", 400, 350, 260, 65, GREEN)
        btn_exit = draw_button("EXIT GAME", 400, 440, 260, 65, RED)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            pos = get_input_position(event)
            if pos is not None:
                if btn_retry.collidepoint(pos):
                    return "retry"
                if btn_exit.collidepoint(pos):
                    pygame.quit()
                    sys.exit()

        clock.tick(60)


# ------------------------------------------------------------
# Main game
# ------------------------------------------------------------
def game_loop():
    player_x = BASE_WIDTH // 2
    player_y = BASE_HEIGHT - 65
    player_size = 58

    score = 0
    lives = MAX_LIVES
    time_remaining = GAME_TIME
    current_speed = base_difficulty_speed
    items = []
    spawn_timer = 0
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        time_remaining -= dt
        current_speed += 0.15 * dt

        if time_remaining <= 0 or lives <= 0:
            time_remaining = max(0, time_remaining)
            play_sfx(sound_lose)
            running = False
            break

        # ----------------------------------------------------
        # Events / touch control
        # ----------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_p, pygame.K_ESCAPE):
                    result = pause_menu()
                    if result == "menu":
                        return

            if event.type == pygame.FINGERDOWN:
                player_x, _ = screen_to_game(
                    event.x * screen.get_width(),
                    event.y * screen.get_height()
                )

            elif event.type == pygame.FINGERMOTION:
                player_x, _ = screen_to_game(
                    event.x * screen.get_width(),
                    event.y * screen.get_height()
                )

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = screen_to_game(*event.pos)

                if pause_button.collidepoint((mx, my)):
                    result = pause_menu()
                    if result == "menu":
                        return
                else:
                    player_x = mx

            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    player_x, _ = screen_to_game(*event.pos)

        # PC mouse control
        if pygame.mouse.get_pressed()[0]:
            mx, _ = screen_to_game(*pygame.mouse.get_pos())
            player_x = mx

        player_x = max(35, min(BASE_WIDTH - 35, player_x))

        # ----------------------------------------------------
        # Spawn objects
        # ----------------------------------------------------
        spawn_timer += 1
        spawn_rate = max(15, int(40 - current_speed * 2))

        if spawn_timer > spawn_rate:
            items.append(FallingObject(current_speed))
            spawn_timer = 0

        # ----------------------------------------------------
        # Player collision rectangle
        # ----------------------------------------------------
        player_rect = pygame.Rect(
            player_x - player_size / 2,
            player_y - player_size / 2,
            player_size,
            player_size,
        )

        # ----------------------------------------------------
        # Update objects
        # ----------------------------------------------------
        for item in items[:]:
            item.update()

            if player_rect.colliderect(item.rect):
                item_type = item.data["type"]

                if item_type == "bomb":
                    play_sfx(sound_bomb)
                    running = False
                    break

                elif item_type == "book":
                    lives -= 1
                    score += item.data["points"]
                    play_sfx(sound_lose)

                elif item_type == "mine":
                    current_speed = max(
                        base_difficulty_speed,
                        current_speed - 2.0
                    )
                    time_remaining = max(
                        0,
                        time_remaining + item.data["time"]
                    )
                    score += item.data["points"]
                    play_sfx(sound_mine)

                elif item_type == "life":
                    lives = min(MAX_LIVES, lives + 1)
                    time_remaining += item.data["time"]
                    score += item.data["points"]
                    play_sfx(sound_catch)

                else:
                    time_remaining += item.data["time"]
                    score += item.data["points"]
                    play_sfx(sound_catch)

                items.remove(item)

            elif item.y > BASE_HEIGHT + 30:
                if item.data["type"] == "item":
                    lives -= 1
                    play_sfx(sound_lose)

                items.remove(item)

        # ----------------------------------------------------
        # Draw
        # ----------------------------------------------------
        screen.fill(BG_COLOR)

        render_text(
            f"Score: {score}",
            font_ui,
            TEXT_COLOR,
            20,
            20,
            center=False,
        )

        render_text(
            f"Lives: {lives} / {MAX_LIVES}",
            font_ui,
            RED,
            20,
            55,
            center=False,
        )

        timer_color = GREEN if time_remaining > 5 else RED

        render_text(
            f"Time: {time_remaining:.1f}s",
            font_ui,
            timer_color,
            BASE_WIDTH - 220,
            20,
            center=False,
        )

        pause_button = draw_button(
            "PAUSE",
            BASE_WIDTH - 75,
            70,
            125,
            48,
            PURPLE,
        )

        # Player
        scale, ox, oy = get_scale()
        player_screen_pos = (
            int(ox + player_x * scale),
            int(oy + player_y * scale),
        )
        draw_icon(
            screen,
            "player",
            player_screen_pos,
            int(player_size * scale),
        )

        for item in items:
            item.draw()

        pygame.display.flip()

    result = game_over_screen(score)

    if result == "retry":
        game_loop()


# ------------------------------------------------------------
# Main menu
# ------------------------------------------------------------
def main_menu():
    global sound_enabled

    while True:
        screen.fill(BG_COLOR)

        render_text(
            "EMOJI CATCHER",
            font_title,
            TEXT_COLOR,
            BASE_WIDTH // 2,
            80,
        )

        render_text(
            "Touch and drag to control the player",
            font_small,
            TEXT_COLOR,
            BASE_WIDTH // 2,
            145,
        )

        render_text(
            "Catch items for time and points!",
            font_small,
            GREEN,
            BASE_WIDTH // 2,
            180,
        )

        # Small visual guide
        scale, ox, oy = get_scale()
        guide_y = int(oy + 240 * scale)

        guide_items = [
            ("shoe", 270),
            ("donut", 330),
            ("banana", 390),
            ("heart", 450),
        ]

        for kind, x in guide_items:
            draw_icon(
                screen,
                kind,
                (int(ox + x * scale), guide_y),
                int(48 * scale),
            )

        render_text(
            "Avoid books and mines.",
            font_small,
            RED,
            BASE_WIDTH // 2,
            310,
        )

        render_text(
            "Bomb = instant game over!",
            font_small,
            PURPLE,
            BASE_WIDTH // 2,
            340,
        )

        btn_play = draw_button(
            "START GAME",
            BASE_WIDTH // 2,
            420,
            270,
            65,
            GREEN,
        )

        btn_sound = draw_button(
            "SOUND: ON" if sound_enabled else "SOUND: OFF",
            BASE_WIDTH // 2,
            495,
            270,
            55,
            BLUE,
        )

        btn_exit = draw_button(
            "EXIT GAME",
            BASE_WIDTH // 2,
            560,
            270,
            55,
            RED,
        )

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            pos = get_input_position(event)

            if pos is not None:
                if btn_play.collidepoint(pos):
                    game_loop()

                elif btn_sound.collidepoint(pos):
                    sound_enabled = not sound_enabled

                elif btn_exit.collidepoint(pos):
                    pygame.quit()
                    sys.exit()

        clock.tick(60)


# ------------------------------------------------------------
# Start
# ------------------------------------------------------------
if __name__ == "__main__":
    main_menu()
