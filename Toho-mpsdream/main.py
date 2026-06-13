import json
import sys
import time
import argparse
from pathlib import Path

import pygame
from pygame.sprite import Group
import os

# 将工作目录切换到脚本所在目录，确保所有模块中的资源路径正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import game_functions as gf
from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from player import Player
from button import Button

from picture import Picture_before_all
from picture import Picture_before_game
from text import Text_before_game
from picture import Picture_before_boss1
from text import Text_before_boss1
from picture import Picture_after_boss1
from text import Text_after_boss1
from picture import Picture_before_boss2
from text import Text_before_boss2
from picture import Picture_after_boss2
from text import Text_after_boss2
from picture import Picture_before_boss3
from text import Text_before_boss3
from picture import Picture_after_boss3
from text import Text_after_boss3
from picture import Picture_after_game
from text import Text_after_game
from picture import Picture_end_game

# 全局答题状态（通过 ai_settings 传递）
_original_check_events = None
_original_update_screen = None


def _init_quiz(ai_settings, stats, quiz_file):
    """Load questions from JSON, set up quiz state on ai_settings."""
    with open(quiz_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    ai_settings.quiz_questions = data["questions"]
    ai_settings.quiz_duration = data.get("duration_minutes", 5) * 60
    ai_settings.quiz_start_time = time.time()
    ai_settings.quiz_stats = stats
    ai_settings.quiz_idx = 0
    ai_settings.quiz_phase = "question"  # question | options | result
    ai_settings.quiz_phase_start = time.time()
    ai_settings.quiz_option_index = 0
    ai_settings.quiz_result = ""  # "correct" | "wrong" | ""
    ai_settings._quiz_started = False  # first _quiz_render call resets timer
    ai_settings._quiz_handle_key = _quiz_handle_key  # for game_functions to use
    ai_settings._quiz_update = _quiz_update
    ai_settings._quiz_render = _quiz_render

    # Load game-over sound
    out_p = Path(__file__).resolve().parent.parent / "assets" / "out.mp3"
    ai_settings._sfx_out = pygame.mixer.Sound(str(out_p)) if out_p.exists() else None
    ai_settings._sfx_out_played = False


def _quiz_update(ai_settings):
    """Advance quiz phase timers."""
    q = ai_settings
    if not getattr(q, "_quiz_started", False):
        return
    elapsed = time.time() - q.quiz_phase_start
    cur = q.quiz_questions[q.quiz_idx] if q.quiz_idx < len(q.quiz_questions) else None

    if q.quiz_phase == "question" and elapsed >= 3.5:
        q.quiz_phase = "options"
        q.quiz_phase_start = time.time()
        q.quiz_option_index = 0
    elif q.quiz_phase == "options":
        # If all options shown and no answer → wrong
        if cur and q.quiz_option_index >= len(cur["options"]):
            q.quiz_result = "wrong"
            q.quiz_phase = "result"
            q.quiz_phase_start = time.time()
            q.quiz_stats.life_left = max(0, q.quiz_stats.life_left - 1)
        elif elapsed >= 2:
            q.quiz_option_index += 1
            q.quiz_phase_start = time.time()
    elif q.quiz_phase == "result" and elapsed >= 2:
        _quiz_next(q)


def _quiz_next(ai_settings):
    q = ai_settings
    q.quiz_idx += 1
    if q.quiz_idx >= len(q.quiz_questions):
        q.quiz_idx = 0
    q.quiz_phase = "question"
    q.quiz_phase_start = time.time()
    q.quiz_option_index = 0
    q.quiz_result = ""


def _quiz_handle_key(ai_settings, key):
    """Handle 1/2/3/4 keys for answers. Correct → +1 life."""
    q = ai_settings
    if q.quiz_phase != "options":
        return
    cur = q.quiz_questions[q.quiz_idx]
    idx_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}
    pressed_idx = idx_map.get(key)
    if pressed_idx is None or pressed_idx >= len(cur["options"]):
        return
    correct_letter = cur["answer"].strip().upper()
    option_letters = "ABCD"
    if option_letters[pressed_idx] == correct_letter:
        q.quiz_stats.life_left += 1
        q.quiz_result = "correct"
    else:
        q.quiz_result = "wrong"
        q.quiz_stats.life_left = max(0, q.quiz_stats.life_left - 1)
    q.quiz_phase = "result"
    q.quiz_phase_start = time.time()


def _quiz_render(ai_settings, screen):
    """Render quiz overlay — below the scoreboard area."""
    q = ai_settings
    remaining = max(0, q.quiz_duration - (time.time() - q.quiz_start_time))
    mins, secs = divmod(int(remaining), 60)

    font_sm = pygame.font.SysFont("simhei", 18)
    font_lg = pygame.font.SysFont("simhei", 22)

    # Countdown top-left
    timer_surf = font_sm.render(f"⏱ {mins:02d}:{secs:02d}", True, (255, 200, 100))
    screen.blit(timer_surf, (10, 10))

    if q.quiz_idx >= len(q.quiz_questions):
        return
    cur = q.quiz_questions[q.quiz_idx]

    # Hide during cutscenes / game over — play game-over sound once
    if not ai_settings.game_active:
        if not q._sfx_out_played and q._sfx_out:
            q._sfx_out_played = True
            q._sfx_out.play()
        return

    # Play game-over sound when timer expires
    if remaining <= 0 and not q._sfx_out_played and q._sfx_out:
        q._sfx_out_played = True
        q._sfx_out.play()

    # First render = actual gameplay starts, reset all timers
    if not ai_settings._quiz_started:
        ai_settings._quiz_started = True
        ai_settings.quiz_start_time = time.time()
        ai_settings.quiz_phase_start = time.time()

    # Text bar full-width at bottom, centered
    sh = screen.get_height()
    sw = screen.get_width()
    bar_h = 44
    bar_top = sh - bar_h - 12
    bar_w = sw - 28
    bar_x = 14
    pygame.draw.rect(screen, (20, 20, 60), (bar_x, bar_top, bar_w, bar_h))
    pygame.draw.rect(screen, (60, 60, 180), (bar_x, bar_top, bar_w, bar_h), 2)

    if q.quiz_phase == "question":
        text = cur["text"][:50]
        color = (255, 255, 255)
    elif q.quiz_phase == "options":
        idx = min(q.quiz_option_index, len(cur["options"]) - 1)
        text = f"{idx + 1}. {cur['options'][idx]}"
        color = (200, 200, 255)
    elif q.quiz_phase == "result":
        if q.quiz_result == "correct":
            text = "✓ Yes！生命 +1(≧∇≦)/"
            color = (100, 255, 100)
        else:
            text = "✗ 啊喔 (=ｘェｘ=)"
            color = (255, 100, 100)
    else:
        text = ""
        color = (255, 255, 255)

    text_surf = font_lg.render(text, True, color)
    tx = bar_x + (bar_w - text_surf.get_width()) // 2
    screen.blit(text_surf, (tx, bar_top + 10))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiz-file", type=str, default="")
    args = parser.parse_args()

    pygame.init()
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (50, 70)
    pygame.display.set_caption('东方×Python梦')
    pygame.mixer.init()

    try:
        with open('high_score.txt', 'r') as hs:
            high_score = hs.read().strip() or "0"
    except (FileNotFoundError, ValueError):
        high_score = "0"

    ai_settings = Settings()
    screen = pygame.display.set_mode((ai_settings.screen_width, ai_settings.screen_height))

    stats = GameStats(ai_settings, high_score)

    # Quiz init
    if args.quiz_file:
        _init_quiz(ai_settings, stats, args.quiz_file)
    sb = Scoreboard(ai_settings, screen, stats)

    continue_button = Button(ai_settings, screen, 'to be continue...')
    reimu = Player(ai_settings, screen)
    my_bullets = Group()

    p_ba = Picture_before_all(screen)
    p_b0 = Picture_before_game(screen)
    t_b0 = Text_before_game(screen)
    p_b1 = Picture_before_boss1(ai_settings, screen)
    t_b1 = Text_before_boss1(screen)
    p_a1 = Picture_after_boss1(ai_settings, screen)
    t_a1 = Text_after_boss1(screen)
    p_b2 = Picture_before_boss2(ai_settings, screen)
    t_b2 = Text_before_boss2(screen)
    p_a2 = Picture_after_boss2(ai_settings, screen)
    t_a2 = Text_after_boss2(screen)
    p_b3 = Picture_before_boss3(ai_settings, screen)
    t_b3 = Text_before_boss3(screen)
    p_a3 = Picture_after_boss3(ai_settings, screen)
    t_a3 = Text_after_boss3(screen)
    p_a0 = Picture_after_game(screen)
    t_a0 = Text_after_game(screen)
    p_00 = Picture_end_game(ai_settings, screen)

    # Star the quiz
    if args.quiz_file:
        ai_settings.quiz_start_time = time.time()

    # Patch game functions to inject quiz handling into their event loops
    import game_functions as _gf
    _gf.QUIZ_ACTIVE = bool(args.quiz_file)

    def _wrap_run(func):
        """Wrap a run_game_* function to add quiz logic."""
        def wrapper(*a, **kw):
            func(*a, **kw)
        return wrapper

    # 运行游戏
    gf.before_all(ai_settings, p_ba)
    gf.before_game(ai_settings, screen, t_b0, p_b0)
    pygame.mixer.music.stop()

    if args.quiz_file and time.time() - ai_settings.quiz_start_time >= ai_settings.quiz_duration:
        gf.end_game(ai_settings, screen, p_00, stats)
        return

    gf.run_game_1_first(ai_settings, screen, stats, sb, reimu, my_bullets, continue_button)
    pygame.mixer.music.stop()

    gf.before_boss1(ai_settings, screen, t_b1, p_b1)
    ai_settings.next_game = False
    gf.run_game_1_second(ai_settings, screen, stats, sb, reimu, my_bullets, continue_button)
    pygame.mixer.music.stop()

    gf.after_boss1(ai_settings, screen, t_a1, p_a1)
    ai_settings.next_game = False
    gf.run_game_2_first(ai_settings, screen, stats, sb, reimu, my_bullets, continue_button)
    pygame.mixer.music.stop()

    gf.before_boss2(ai_settings, screen, t_b2, p_b2)
    ai_settings.next_game = False
    gf.run_game_2_second(ai_settings, screen, stats, sb, reimu, my_bullets, continue_button)
    pygame.mixer.music.stop()

    gf.after_boss2(ai_settings, screen, t_a2, p_a2)
    ai_settings.next_game = False
    gf.run_game_3_first(ai_settings, screen, stats, sb, reimu, my_bullets, continue_button)
    pygame.mixer.music.stop()

    gf.before_boss3(ai_settings, screen, t_b3, p_b3)
    ai_settings.next_game = False
    gf.run_game_3_second(ai_settings, screen, stats, sb, reimu, my_bullets, continue_button)

    gf.after_boss3(ai_settings, screen, t_a3, p_a3)
    pygame.mixer.music.stop()

    gf.after_game(ai_settings, screen, t_a0, p_a0)
    pygame.mixer.music.stop()

    gf.end_game(ai_settings, screen, p_00, stats)
    pygame.mixer.music.stop()


if __name__ == '__main__':
    main()