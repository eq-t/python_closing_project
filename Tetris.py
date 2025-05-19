import pygame
import random
import math
import sys
from datetime import datetime
import json
import os

# Initialize configuration
pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 750
BLOCK_SIZE = 35
GAME_WIDTH = 12
GAME_HEIGHT = 24
INFO_WIDTH = 8
FPS = 60  # Frames per second

# Colors
COLORS = {
    'BACKGROUND': (30, 30, 30),
    'GRID': (50, 50, 50),
    'TEXT': (255, 255, 255),
    'TITLE': (255, 215, 0),
    'BUTTON': (60, 120, 216),
    'BUTTON_HOVER': (80, 140, 236),
    'GAME_OVER': (255, 100, 100),
    'PAUSED': (255, 255, 100),
    'TETROMINO': [
        (0, 0, 0),       # Background
        (255, 85, 85),   # I
        (100, 255, 100), # O
        (100, 100, 255), # T
        (255, 165, 50),  # L
        (255, 255, 100), # J
        (200, 100, 255), # S
        (50, 255, 255)   # Z
    ]
}

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[2, 2], [2, 2]],  # O
    [[3, 3, 3], [0, 3, 0]],  # T
    [[4, 4, 4], [4, 0, 0]],  # L
    [[5, 5, 5], [0, 0, 5]],  # J
    [[6, 6, 0], [0, 6, 6]],  # S
    [[0, 7, 7], [7, 7, 0]]  # Z
]

# Save file path
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tetris_history.json")  # 绝对路径



class Button:
    def __init__(self, x, y, width, height, text, font_size=36):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont('Arial', font_size, bold=True)
        self.is_hovered = False

    def draw(self, screen):
        color = COLORS['BUTTON_HOVER'] if self.is_hovered else COLORS['BUTTON']
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, COLORS['TEXT'], self.rect, 2, border_radius=10)

        text_surface = self.font.render(self.text, True, COLORS['TEXT'])
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class TetrisGame:
    def __init__(self, screen):
        self.VISIBLE_HEIGHT = 20  # 可视区域高度
        self.BUFFER_HEIGHT = 4  # 上方缓冲区域
        self.TOTAL_HEIGHT = self.VISIBLE_HEIGHT + self.BUFFER_HEIGHT

        # 修改初始化
        self.game_field = [[0] * GAME_WIDTH for _ in range(self.TOTAL_HEIGHT)]
        self.screen = screen
        self.reset_game()

    def reset_game(self):
        self.game_field = [[0] * GAME_WIDTH for _ in range(GAME_HEIGHT)]
        self.current_piece = None
        self.next_piece = random.choice(SHAPES)
        self.score = 0
        self.level = 1
        self.lines = 0
        self.start_time = datetime.now()
        self.game_over = False
        self.is_paused = False
        self.ghost_alpha = 80
        self.clear_effect = {'active': False, 'rows': [], 'frame': 0}
        self.particles = []
        self.create_new_piece()

    def create_new_piece(self):
        self.current_piece = {
            'shape': self.next_piece,
            'color': random.randint(1, 7),
            'x': GAME_WIDTH // 2 - len(self.next_piece[0]) // 2,
            'y': 0
        }
        self.next_piece = random.choice(SHAPES)
        if self.check_collision(self.current_piece['shape'], (0, 0)):
            self.game_over = True

    def check_collision(self, shape, offset):
        off_x, off_y = offset
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.current_piece['x'] + x + off_x
                    new_y = self.current_piece['y'] + y + off_y
                    if new_x < 0 or new_x >= GAME_WIDTH or new_y >= GAME_HEIGHT:
                        return True
                    if new_y >= 0 and self.game_field[new_y][new_x]:
                        return True
        return False

    def rotate_piece(self):
        rotated = [list(row) for row in zip(*self.current_piece['shape'][::-1])]
        if not self.check_collision(rotated, (0, 0)):
            self.current_piece['shape'] = rotated

    def merge_piece(self):
        shape = self.current_piece['shape']
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    pos_x = (self.current_piece['x'] + x) * BLOCK_SIZE + BLOCK_SIZE // 2
                    pos_y = (self.current_piece['y'] + y) * BLOCK_SIZE + BLOCK_SIZE // 2
                    self.add_particles((pos_x, pos_y))
                    self.game_field[y + self.current_piece['y']][x + self.current_piece['x']] = self.current_piece['color']

        lines_cleared = 0
        new_field = []
        for y in range(GAME_HEIGHT):
            if 0 not in self.game_field[y]:
                lines_cleared += 1
            else:
                new_field.append(self.game_field[y])
        self.game_field = [[0] * GAME_WIDTH for _ in range(lines_cleared)] + new_field

        if lines_cleared > 0:
            score_multiplier = {1: 100, 2: 300, 3: 500, 4: 800}.get(lines_cleared, 1000)
            self.score += score_multiplier * self.level
            self.lines += lines_cleared
            self.level = 1 + self.lines // 5

            self.clear_effect['active'] = True
            self.clear_effect['rows'] = list(range(len(new_field), len(new_field) + lines_cleared))
            self.clear_effect['frame'] = 0

        self.create_new_piece()

    def add_particles(self, pos):
        for _ in range(15):
            self.particles.append({
                'pos': [pos[0], pos[1]],
                'velocity': [random.uniform(-3, 3), random.uniform(-6, -2)],
                'timer': random.randint(10, 20),
                'color': random.choice([(255, 255, 255), (255, 255, 200), (255, 200, 200)])
            })

    def update_particles(self):
        for p in self.particles[:]:
            p['pos'][0] += p['velocity'][0]
            p['pos'][1] += p['velocity'][1]
            p['timer'] -= 1
            if p['timer'] <= 0:
                self.particles.remove(p)

    def draw_particles(self):
        for p in self.particles:
            alpha = int(255 * p['timer'] / 20)
            size = int(3 * p['timer'] / 20) + 1
            color = (*p['color'], alpha)
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (size, size), size)
            self.screen.blit(s, (int(p['pos'][0] - size), int(p['pos'][1] - size)))

    def get_fall_speed(self):
        return max(50, 800 - (self.level * 50))

    def draw_gradient_bg(self):
        for y in range(SCREEN_HEIGHT):
            color = (30 + y // 20, 30 + y // 20, 50 + y // 20)
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))

    def draw_block(self, x, y, color, alpha=255, size=BLOCK_SIZE - 1):
        # 调整绘制位置，只显示下方20行
        draw_y = y - self.BUFFER_HEIGHT
        if draw_y < 0:  # 不绘制缓冲区的方块
            return
        if x < 0 or x >= GAME_WIDTH or y < 0 or y >= GAME_HEIGHT:
            return
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        surface.set_alpha(alpha)

        # Main color
        pygame.draw.rect(surface, COLORS['TETROMINO'][color], (0, 0, size, size), 0, size // 5)

        # Highlight
        pygame.draw.rect(surface, (255, 255, 255, 80), (0, 0, size, 2), 0, 1)
        # Shadow
        pygame.draw.rect(surface, (0, 0, 0, 80), (0, size - 2, size, 2), 0, 1)

        self.screen.blit(surface, (x * BLOCK_SIZE + 150, draw_y * BLOCK_SIZE + 50))

    def draw_ghost_piece(self):
        if self.game_over or self.is_paused:
            return
        ghost_y = self.current_piece['y']
        max_falls = GAME_HEIGHT - self.current_piece['y']
        for _ in range(max_falls):
            if self.check_collision(self.current_piece['shape'], (0, 1)):
                break
            ghost_y += 1
        shape = self.current_piece['shape']
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(
                        self.current_piece['x'] + x,
                        ghost_y + y,
                        self.current_piece['color'],
                        self.ghost_alpha
                    )

    def draw_game_info(self):
        font = pygame.font.SysFont('Arial', 28, bold=True)
        small_font = pygame.font.SysFont('Arial', 24)

        # Score
        score_text = font.render(f'Score: {self.score}', True, COLORS['TEXT'])
        self.screen.blit(score_text, (GAME_WIDTH * BLOCK_SIZE + 200, 100))

        # Level
        level_text = font.render(f'Level: {self.level}', True, COLORS['TEXT'])
        self.screen.blit(level_text, (GAME_WIDTH * BLOCK_SIZE + 200, 150))

        # Lines cleared
        lines_text = font.render(f'Lines: {self.lines}', True, COLORS['TEXT'])
        self.screen.blit(lines_text, (GAME_WIDTH * BLOCK_SIZE + 200, 200))

        # Elapsed time
        if not self.game_over and not self.is_paused:
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
            minutes, seconds = divmod(int(elapsed_time), 60)
            time_text = font.render(f'Time: {minutes:02d}:{seconds:02d}', True, COLORS['TEXT'])
            self.screen.blit(time_text, (GAME_WIDTH * BLOCK_SIZE + 200, 250))

        # Next piece（修正位置和绘制逻辑）
        next_section_x = GAME_WIDTH * BLOCK_SIZE + 150  # 主区域右侧150像素
        next_section_y = 100  # 垂直起始位置

        # 绘制标题
        next_text = font.render('Next:', True, COLORS['TEXT'])
        self.screen.blit(next_text, (next_section_x, next_section_y - 30))

        # 绘制下一个方块的每个单元格
        for y, row in enumerate(self.next_piece):
            for x, cell in enumerate(row):
                if cell:
                    # 计算在右侧区域的坐标（每个方块间隔35像素）
                    x_pos = next_section_x + x * BLOCK_SIZE
                    y_pos = next_section_y + y * BLOCK_SIZE
                    self.draw_block(x, y, cell, 255, BLOCK_SIZE - 3)  # 直接使用cell作为颜色索引（与SHAPES定义一致）

        # Controls
        controls_y = 450
        controls = [
            'Left/Right Arrow: Move',
            'Down Arrow: Soft Drop',
            'Up Arrow: Rotate',
            'Space: Hard Drop',
            'P: Pause',
            'ESC: Menu'
        ]

        for i, text in enumerate(controls):
            control_text = small_font.render(text, True, COLORS['TEXT'])
            self.screen.blit(control_text, (GAME_WIDTH * BLOCK_SIZE + 180, controls_y + i * 30))

    def draw_game(self):
        self.draw_gradient_bg()

        # Game area border
        pygame.draw.rect(self.screen, (100, 100, 100),
                         (150, 50, BLOCK_SIZE * GAME_WIDTH, BLOCK_SIZE * GAME_HEIGHT), 3)

        # Grid lines
        for y in range(GAME_HEIGHT):
            for x in range(GAME_WIDTH):
                pygame.draw.rect(self.screen, COLORS['GRID'],
                                 (x * BLOCK_SIZE + 150, y * BLOCK_SIZE + 50,
                                  BLOCK_SIZE, BLOCK_SIZE), 1)

        # Drawn blocks
        for y in range(GAME_HEIGHT):
            for x in range(GAME_WIDTH):
                if self.game_field[y][x]:
                    self.draw_block(x, y, self.game_field[y][x])

        # Clear effect
        if self.clear_effect['active']:
            alpha = abs(math.sin(self.clear_effect['frame'] * 0.5)) * 255
            for row in self.clear_effect['rows']:
                if row < GAME_HEIGHT:
                    pygame.draw.rect(self.screen, (255, 255, 255, alpha),
                                    (150, row * BLOCK_SIZE + 50,
                                     BLOCK_SIZE * GAME_WIDTH, BLOCK_SIZE))
            self.clear_effect['frame'] += 1
            if self.clear_effect['frame'] > 10:
                self.clear_effect['active'] = False

        # Current piece and ghost
        if not self.game_over and not self.is_paused:
            self.draw_ghost_piece()
            shape = self.current_piece['shape']
            color = self.current_piece['color']
            for y, row in enumerate(shape):
                for x, cell in enumerate(row):
                    if cell:
                        self.draw_block(self.current_piece['x'] + x,
                                        self.current_piece['y'] + y, color)

        # Game info
        self.draw_game_info()

        # Particles
        self.draw_particles()

        # Overlay for game over or pause
        if self.game_over:
            self.draw_game_over()
        elif self.is_paused:
            self.draw_pause_overlay()

    def draw_pause_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        text = pygame.font.SysFont('Arial', 72, bold=True).render('PAUSED', True, COLORS['PAUSED'])
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(text, text_rect)

        prompt = pygame.font.SysFont('Arial', 36).render('Press P to Resume', True, COLORS['TEXT'])
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(prompt, prompt_rect)

        def draw_game_over(self):
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            text = pygame.font.SysFont('Arial', 72, bold=True).render('GAME OVER', True, COLORS['GAME_OVER'])
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(text, text_rect)

            score_text = pygame.font.SysFont('Arial', 48).render(f'Final Score: {self.score}', True, COLORS['TEXT'])
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
            self.screen.blit(score_text, score_rect)

            prompt = pygame.font.SysFont('Arial', 36).render('Press any key to return to menu', True, COLORS['TEXT'])
            prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
            self.screen.blit(prompt, prompt_rect)

        def get_fall_speed(self):
            return max(50, 800 - (self.level * 50))

        def save_game_record(self):
            end_time = datetime.now()
            elapsed_time = (end_time - self.start_time).total_seconds()

            record = {
                'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': f"{int(elapsed_time // 60):02d}:{int(elapsed_time % 60):02d}",
                'level': self.level,
                'score': self.score,
                'lines': self.lines
            }

            try:
                if os.path.exists(SAVE_FILE):
                    with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                else:
                    history = []

                history.append(record)
                # Keep only the last 100 records
                if len(history) > 100:
                    history = history[-100:]

                with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)

            except Exception as e:
                print(f"Failed to save game record: {e}")

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        text = pygame.font.SysFont('Arial', 72, bold=True).render('GAME OVER', True, COLORS['GAME_OVER'])
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(text, text_rect)

        score_text = pygame.font.SysFont('Arial', 48).render(f'Final Score: {self.score}', True, COLORS['TEXT'])
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(score_text, score_rect)

        prompt = pygame.font.SysFont('Arial', 36).render('Press any key to return to menu', True, COLORS['TEXT'])
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))  # 位置上移
        self.screen.blit(prompt, prompt_rect)

    def save_game_record(self):
        end_time = datetime.now()
        elapsed_time = (end_time - self.start_time).total_seconds()

        record = {
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': f"{int(elapsed_time // 60):02d}:{int(elapsed_time % 60):02d}",
            'level': self.level,
            'score': self.score,
            'lines': self.lines
        }

        try:
            os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)

            # 检查文件是否存在且非空
            if os.path.exists(SAVE_FILE) and os.path.getsize(SAVE_FILE) > 0:
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = []

            history.append(record)
            history = history[-100:]  # 保留最近100条记录

            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存记录失败: {e}")


class HistoryScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 24)
        self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
        self.back_button = Button(50, 650, 200, 60, "Back", 28)
        self.clear_button = Button(650, 650, 200, 60, "Clear History", 28)  # 新增清空按钮
        self.records = []
        self.load_history()
        self.scroll_offset = 0
        self.max_scroll = max(0, len(self.records) - 10)

    def load_history(self):
        try:
            if os.path.exists(SAVE_FILE) and os.path.getsize(SAVE_FILE) > 0:
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
            else:
                self.records = []

            self.records.sort(key=lambda x: x['start_time'], reverse=True)  # 按时间倒序
            self.max_scroll = max(0, len(self.records) - 10)
        except Exception as e:
            print(f"加载记录失败: {e}")
            self.records = []

    def save_history(self):
        """保存历史记录"""
        try:
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")

    def clear_history(self):
        """清空历史记录"""
        try:
            self.records = []
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            return True
        except Exception as e:
            print(f"Failed to clear history: {e}")
            return False

    def draw(self):
        self.screen.fill(COLORS['BACKGROUND'])

        # 绘制标题
        title = self.title_font.render("Game History", True, COLORS['TITLE'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)

        # 绘制表头
        headers = ["Start Time", "Duration", "Level", "Score", "Lines"]
        header_widths = [200, 100, 80, 100, 80]  # 各列宽度
        x_pos = 100
        for i, header in enumerate(headers):
            header_text = self.font.render(header, True, COLORS['TITLE'])
            self.screen.blit(header_text, (x_pos, 120))
            x_pos += header_widths[i]

        # 绘制分隔线
        pygame.draw.line(self.screen, COLORS['TEXT'], (100, 150), (800, 150), 2)

        # 绘制记录
        if not self.records:
            no_record_text = self.font.render("No game history found", True, COLORS['TEXT'])
            self.screen.blit(no_record_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        else:
            for i, record in enumerate(self.records[self.scroll_offset:self.scroll_offset + 10]):
                y = 170 + i * 40
                values = [
                    record['start_time'],
                    record['duration'],
                    f"{record['level']}",
                    f"{record['score']}",
                    f"{record['lines']}"
                ]

                x_pos = 100
                for j, value in enumerate(values):
                    text = self.font.render(value, True, COLORS['TEXT'])
                    self.screen.blit(text, (x_pos, y))
                    x_pos += header_widths[j]

        # 绘制滚动条
        if self.max_scroll > 0:
            scrollbar_height = 300
            scrollbar_width = 10
            scrollbar_x = 820

            # 滚动条背景
            pygame.draw.rect(self.screen, (80, 80, 80),
                             (scrollbar_x, 150, scrollbar_width, scrollbar_height),
                             border_radius=5)

            # 滚动条滑块
            scroll_ratio = min(1.0, self.scroll_offset / self.max_scroll)
            scroll_height = max(20, scrollbar_height * (10 / max(10, len(self.records))))
            scroll_pos = scroll_ratio * (scrollbar_height - scroll_height)
            pygame.draw.rect(self.screen, COLORS['BUTTON'],
                             (scrollbar_x, 150 + scroll_pos, scrollbar_width, scroll_height),
                             border_radius=5)

        # 绘制按钮
        self.back_button.draw(self.screen)
        self.clear_button.draw(self.screen)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEMOTION:
            self.back_button.check_hover(mouse_pos)
            self.clear_button.check_hover(mouse_pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                if self.back_button.is_clicked(mouse_pos):
                    return "main_menu"
                elif self.clear_button.is_clicked(mouse_pos):
                    if self.clear_history():
                        return "history"  # 清空后刷新界面

                # 滚动条点击处理
                if 820 <= mouse_pos[0] <= 830 and 150 <= mouse_pos[1] <= 450:
                    scrollbar_height = 300
                    scroll_height = max(20, scrollbar_height * (10 / max(10, len(self.records))))
                    available_height = scrollbar_height - scroll_height
                    scroll_ratio = (mouse_pos[1] - 150 - scroll_height / 2) / available_height
                    self.scroll_offset = int(scroll_ratio * self.max_scroll)
                    self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset))

            elif event.button == 4:  # 滚轮上滚
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.button == 5:  # 滚轮下滚
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 1)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.key == pygame.K_DOWN:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 1)
            elif event.key == pygame.K_ESCAPE:
                return "main_menu"

        return "history"

class HelpScreen:
        def __init__(self, screen):
            self.screen = screen
            self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
            self.header_font = pygame.font.SysFont('Arial', 32, bold=True)
            self.text_font = pygame.font.SysFont('Arial', 24)
            self.back_button = Button(50, 650, 200, 60, "Back to Menu", 28)

            self.controls = [
                ("Left/Right Arrow", "Move Block Horizontally"),
                ("Down Arrow", "Soft Drop"),
                ("Up Arrow", "Rotate Block"),
                ("Space Bar", "Hard Drop"),
                ("P Key", "Pause/Resume Game"),
                ("ESC Key", "Return to Main Menu")
            ]

            self.scoring = [
                "1 Line: 100 points × Level",
                "2 Lines: 300 points × Level",
                "3 Lines: 500 points × Level",
                "4 Lines: 800 points × Level",
                "Soft Drop: +1 point per cell"
            ]

        def draw(self):
            self.screen.fill(COLORS['BACKGROUND'])

            # Draw title
            title = self.title_font.render("Game Help", True, COLORS['TITLE'])
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(title, title_rect)

            # Draw controls section
            controls_header = self.header_font.render("Controls", True, COLORS['TITLE'])
            self.screen.blit(controls_header, (100, 120))

            for i, (key, desc) in enumerate(self.controls):
                key_text = self.text_font.render(key, True, COLORS['TEXT'])
                desc_text = self.text_font.render(desc, True, COLORS['TEXT'])

                y = 170 + i * 40
                self.screen.blit(key_text, (120, y))
                self.screen.blit(desc_text, (300, y))

            # Draw scoring section
            scoring_header = self.header_font.render("Scoring", True, COLORS['TITLE'])
            self.screen.blit(scoring_header, (100, 420))

            for i, rule in enumerate(self.scoring):
                rule_text = self.text_font.render(rule, True, COLORS['TEXT'])
                self.screen.blit(rule_text, (120, 470 + i * 35))

            # Draw back button
            self.back_button.draw(self.screen)

        def handle_event(self, event):
            mouse_pos = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEMOTION:
                self.back_button.check_hover(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.back_button.is_clicked(mouse_pos):
                    return "main_menu"

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "main_menu"

            return "help"

class MainMenu:
        def __init__(self, screen):
            self.screen = screen
            self.title_font = pygame.font.SysFont('Arial', 72, bold=True)
            self.button_font = pygame.font.SysFont('Arial', 36, bold=True)

            button_width = 300
            button_height = 70
            button_spacing = 20
            button_x = (SCREEN_WIDTH - button_width) // 2
            button_y = SCREEN_HEIGHT // 2 - (button_height * 4 + button_spacing * 3) // 2

            self.buttons = [
                Button(button_x, button_y, button_width, button_height, "Start Game"),
                Button(button_x, button_y + button_height + button_spacing, button_width, button_height, "Game History"),
                Button(button_x, button_y + (button_height + button_spacing) * 2, button_width, button_height, "Help"),
                Button(button_x, button_y + (button_height + button_spacing) * 3, button_width, button_height, "Quit")
            ]

        def draw(self):
            self.screen.fill(COLORS['BACKGROUND'])

            title = self.title_font.render("Tetris Pro", True, COLORS['TITLE'])
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
            self.screen.blit(title, title_rect)

            for button in self.buttons:
                button.draw(self.screen)

            footer_font = pygame.font.SysFont('Arial', 20)
            footer_text = footer_font.render('Press ESC to return to menu', True, COLORS['TEXT'])
            footer_rect = footer_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))  # 调整至底部50像素处
            self.screen.blit(footer_text, footer_rect)

        def handle_event(self, event):
            mouse_pos = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEMOTION:
                for button in self.buttons:
                    button.check_hover(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.buttons[0].is_clicked(mouse_pos):
                        return "game"
                    elif self.buttons[1].is_clicked(mouse_pos):
                        return "history"
                    elif self.buttons[2].is_clicked(mouse_pos):
                        return "help"
                    elif self.buttons[3].is_clicked(mouse_pos):
                        pygame.quit()
                        sys.exit()

            # 移除这里的ESC键处理
            return "main_menu"

class TetrisApp:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris Pro")
        self.clock = pygame.time.Clock()
        self.FPS = 60  # Frames per second

        # Create screens
        self.main_menu = MainMenu(self.screen)
        self.game = TetrisGame(self.screen)
        self.history_screen = HistoryScreen(self.screen)
        self.help_screen = HelpScreen(self.screen)

        # Current screen
        self.current_screen = "main_menu"

        # Game state timer
        self.fall_time = 0

    def run(self):
        while True:
            self.clock.tick(self.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Global ESC key to return to main menu
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.current_screen != "main_menu":  # 只要不在主菜单，按ESC都返回主菜单
                        self.current_screen = "main_menu"
                        continue  # 跳过后续处理

                # Handle events based on current screen
                if self.current_screen == "main_menu":
                    self.current_screen = self.main_menu.handle_event(event)

                elif self.current_screen == "game":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_p:
                            self.game.is_paused = not self.game.is_paused
                        elif not self.game.is_paused and not self.game.game_over:
                            if event.key == pygame.K_LEFT:
                                if not self.game.check_collision(self.game.current_piece['shape'], (-1, 0)):
                                    self.game.current_piece['x'] -= 1
                            elif event.key == pygame.K_RIGHT:
                                if not self.game.check_collision(self.game.current_piece['shape'], (1, 0)):
                                    self.game.current_piece['x'] += 1
                            elif event.key == pygame.K_DOWN:
                                if not self.game.check_collision(self.game.current_piece['shape'], (0, 1)):
                                    self.game.current_piece['y'] += 1
                            elif event.key == pygame.K_UP:
                                self.game.rotate_piece()
                            elif event.key == pygame.K_SPACE:
                                while not self.game.check_collision(self.game.current_piece['shape'], (0, 1)):
                                    self.game.current_piece['y'] += 1
                                    self.game.score += 1
                                self.game.merge_piece()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if self.game.game_over:
                            self.game.save_game_record()
                            self.game.reset_game()
                            self.current_screen = "main_menu"

                elif self.current_screen == "history":
                    self.current_screen = self.history_screen.handle_event(event)
                    if self.current_screen == "history":
                        self.history_screen.load_history()

                elif self.current_screen == "help":
                    self.current_screen = self.help_screen.handle_event(event)

            # Update game state (only in game screen and not paused)
            if self.current_screen == "game" and not self.game.is_paused and not self.game.game_over:
                self.fall_time += self.clock.get_rawtime()
                fall_speed = self.game.get_fall_speed()

                if self.fall_time >= fall_speed:
                    if not self.game.check_collision(self.game.current_piece['shape'], (0, 1)):
                        self.game.current_piece['y'] += 1
                    else:
                        self.game.merge_piece()
                    self.fall_time = 0

            # Update particles
            if self.current_screen == "game":
                self.game.update_particles()

            # Draw current screen
            if self.current_screen == "main_menu":
                self.main_menu.draw()
            elif self.current_screen == "game":
                self.game.draw_game()
            elif self.current_screen == "history":
                self.history_screen.draw()
            elif self.current_screen == "help":
                self.help_screen.draw()

            pygame.display.update()

if __name__ == "__main__":
    app = TetrisApp()
    app.run()