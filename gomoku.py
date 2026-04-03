import pygame
import sys
import math
import json
import array
import random
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum, auto
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from pathlib import Path

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    SETTINGS = auto()
    STATS = auto()


class GameMode(Enum):
    PVP = auto()
    PVE = auto()


class Difficulty(Enum):
    EASY = auto()
    MEDIUM = auto()
    HARD = auto()


class ThemeType(Enum):
    CLASSIC = "classic"
    MODERN = "modern"
    DARK = "dark"


THEMES = {
    ThemeType.CLASSIC: {
        'name': '经典木纹',
        'primary': (139, 90, 43),
        'secondary': (222, 184, 135),
        'background': (245, 222, 179),
        'text': (60, 40, 20),
        'highlight': (255, 215, 0),
        'board_bg': (222, 184, 135),
        'board_line': (80, 60, 40),
        'button_normal': (139, 90, 43),
        'button_hover': (160, 110, 60),
    },
    ThemeType.MODERN: {
        'name': '现代简约',
        'primary': (70, 130, 180),
        'secondary': (176, 224, 230),
        'background': (240, 248, 255),
        'text': (25, 25, 112),
        'highlight': (0, 191, 255),
        'board_bg': (176, 224, 230),
        'board_line': (70, 130, 180),
        'button_normal': (70, 130, 180),
        'button_hover': (100, 149, 237),
    },
    ThemeType.DARK: {
        'name': '暗黑风格',
        'primary': (75, 0, 130),
        'secondary': (48, 25, 52),
        'background': (25, 25, 35),
        'text': (200, 200, 220),
        'highlight': (255, 0, 255),
        'board_bg': (48, 25, 52),
        'board_line': (100, 50, 100),
        'button_normal': (75, 0, 130),
        'button_hover': (138, 43, 226),
    },
}


class GomokuAI:
    def __init__(self, difficulty: Difficulty):
        self.difficulty = difficulty
        self.depth_map = {
            Difficulty.EASY: 2,
            Difficulty.MEDIUM: 3,
            Difficulty.HARD: 4,
        }
        self.random_factor = {
            Difficulty.EASY: 0.3,
            Difficulty.MEDIUM: 0.1,
            Difficulty.HARD: 0.0,
        }
    
    def get_best_move(self, board: List[List[int]], player: int) -> Tuple[int, int]:
        import random
        
        depth = self.depth_map[self.difficulty]
        candidates = self._get_candidate_moves(board)
        
        if not candidates:
            size = len(board)
            return size // 2, size // 2
        
        if random.random() < self.random_factor[self.difficulty]:
            return random.choice(candidates)
        
        best_score = float('-inf')
        best_move = candidates[0]
        
        for row, col in candidates:
            board[row][col] = player
            score = self._minimax(board, depth - 1, float('-inf'), float('inf'), False, player)
            board[row][col] = 0
            
            if score > best_score:
                best_score = score
                best_move = (row, col)
        
        return best_move
    
    def _minimax(self, board: List[List[int]], depth: int, alpha: float, beta: float,
                 is_maximizing: bool, player: int) -> float:
        if depth == 0:
            return self._evaluate_board(board, player)
        
        candidates = self._get_candidate_moves(board)
        if not candidates:
            return self._evaluate_board(board, player)
        
        if is_maximizing:
            max_eval = float('-inf')
            for row, col in candidates:
                board[row][col] = player
                eval_score = self._minimax(board, depth - 1, alpha, beta, False, player)
                board[row][col] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            opponent = 3 - player
            for row, col in candidates:
                board[row][col] = opponent
                eval_score = self._minimax(board, depth - 1, alpha, beta, True, player)
                board[row][col] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def _get_candidate_moves(self, board: List[List[int]]) -> List[Tuple[int, int]]:
        size = len(board)
        candidates = set()
        has_pieces = False
        
        for i in range(size):
            for j in range(size):
                if board[i][j] != 0:
                    has_pieces = True
                    for di in range(-2, 3):
                        for dj in range(-2, 3):
                            ni, nj = i + di, j + dj
                            if 0 <= ni < size and 0 <= nj < size and board[ni][nj] == 0:
                                candidates.add((ni, nj))
        
        if not has_pieces:
            return [(size // 2, size // 2)]
        
        return list(candidates)
    
    def _evaluate_board(self, board: List[List[int]], player: int) -> float:
        score = 0
        size = len(board)
        opponent = 3 - player
        
        for i in range(size):
            for j in range(size):
                if board[i][j] == player:
                    score += self._evaluate_position(board, i, j, player)
                elif board[i][j] == opponent:
                    score -= self._evaluate_position(board, i, j, opponent)
        
        return score
    
    def _evaluate_position(self, board: List[List[int]], row: int, col: int, player: int) -> float:
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        total_score = 0
        
        for dr, dc in directions:
            count = 1
            open_ends = 0
            
            r, c = row + dr, col + dc
            while 0 <= r < len(board) and 0 <= c < len(board) and board[r][c] == player:
                count += 1
                r += dr
                c += dc
            if 0 <= r < len(board) and 0 <= c < len(board) and board[r][c] == 0:
                open_ends += 1
            
            r, c = row - dr, col - dc
            while 0 <= r < len(board) and 0 <= c < len(board) and board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if 0 <= r < len(board) and 0 <= c < len(board) and board[r][c] == 0:
                open_ends += 1
            
            total_score += self._get_pattern_score(count, open_ends)
        
        return total_score
    
    def _get_pattern_score(self, count: int, open_ends: int) -> float:
        if count >= 5:
            return 100000
        elif count == 4:
            if open_ends == 2:
                return 10000
            elif open_ends == 1:
                return 1000
        elif count == 3:
            if open_ends == 2:
                return 1000
            elif open_ends == 1:
                return 100
        elif count == 2:
            if open_ends == 2:
                return 100
            elif open_ends == 1:
                return 10
        return 0


@dataclass
class GameConfig:
    window_width: int = 900
    window_height: int = 700
    window_title: str = "五子棋 - Gomoku"
    
    board_size: int = 15
    cell_size: int = 40
    board_margin: int = 50
    
    fps: int = 60
    
    master_volume: float = 1.0
    music_volume: float = 0.8
    sfx_volume: float = 1.0
    
    theme_type: str = "classic"
    
    theme_primary: Tuple[int, int, int] = (139, 90, 43)
    theme_secondary: Tuple[int, int, int] = (222, 184, 135)
    theme_background: Tuple[int, int, int] = (245, 222, 179)
    theme_text: Tuple[int, int, int] = (60, 40, 20)
    theme_highlight: Tuple[int, int, int] = (255, 215, 0)
    theme_board_bg: Tuple[int, int, int] = (222, 184, 135)
    theme_board_line: Tuple[int, int, int] = (80, 60, 40)
    theme_button_normal: Tuple[int, int, int] = (139, 90, 43)
    theme_button_hover: Tuple[int, int, int] = (160, 110, 60)
    
    @property
    def board_area_size(self) -> int:
        return (self.board_size - 1) * self.cell_size + self.board_margin * 2
    
    def apply_theme(self, theme_type: ThemeType) -> None:
        self.theme_type = theme_type.value
        theme = THEMES[theme_type]
        self.theme_primary = theme['primary']
        self.theme_secondary = theme['secondary']
        self.theme_background = theme['background']
        self.theme_text = theme['text']
        self.theme_highlight = theme['highlight']
        self.theme_board_bg = theme['board_bg']
        self.theme_board_line = theme['board_line']
        self.theme_button_normal = theme['button_normal']
        self.theme_button_hover = theme['button_hover']
    
    def get_current_theme(self) -> ThemeType:
        for tt in ThemeType:
            if tt.value == self.theme_type:
                return tt
        return ThemeType.CLASSIC
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'window_width': self.window_width,
            'window_height': self.window_height,
            'board_size': self.board_size,
            'cell_size': self.cell_size,
            'board_margin': self.board_margin,
            'master_volume': self.master_volume,
            'music_volume': self.music_volume,
            'sfx_volume': self.sfx_volume,
            'theme_type': self.theme_type,
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        if 'theme_type' in data:
            try:
                theme_type = ThemeType(data['theme_type'])
                self.apply_theme(theme_type)
            except:
                pass


@dataclass
class GameStats:
    total_games: int = 0
    black_wins: int = 0
    white_wins: int = 0
    draws: int = 0
    pvp_games: int = 0
    pvp_black_wins: int = 0
    pvp_white_wins: int = 0
    pve_games: int = 0
    pve_easy_games: int = 0
    pve_easy_wins: int = 0
    pve_medium_games: int = 0
    pve_medium_wins: int = 0
    pve_hard_games: int = 0
    pve_hard_wins: int = 0
    pve_wins: int = 0
    pve_losses: int = 0
    longest_win_streak: int = 0
    current_win_streak: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_games': self.total_games,
            'black_wins': self.black_wins,
            'white_wins': self.white_wins,
            'draws': self.draws,
            'pvp_games': self.pvp_games,
            'pvp_black_wins': self.pvp_black_wins,
            'pvp_white_wins': self.pvp_white_wins,
            'pve_games': self.pve_games,
            'pve_easy_games': self.pve_easy_games,
            'pve_easy_wins': self.pve_easy_wins,
            'pve_medium_games': self.pve_medium_games,
            'pve_medium_wins': self.pve_medium_wins,
            'pve_hard_games': self.pve_hard_games,
            'pve_hard_wins': self.pve_hard_wins,
            'pve_wins': self.pve_wins,
            'pve_losses': self.pve_losses,
            'longest_win_streak': self.longest_win_streak,
            'current_win_streak': self.current_win_streak,
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def record_game(self, winner: int, mode: GameMode, difficulty: Difficulty = Difficulty.MEDIUM) -> None:
        self.total_games += 1
        
        if mode == GameMode.PVP:
            self.pvp_games += 1
            if winner == 1:
                self.pvp_black_wins += 1
            elif winner == 2:
                self.pvp_white_wins += 1
        else:
            self.pve_games += 1
            if difficulty == Difficulty.EASY:
                self.pve_easy_games += 1
                if winner == 1:
                    self.pve_easy_wins += 1
            elif difficulty == Difficulty.MEDIUM:
                self.pve_medium_games += 1
                if winner == 1:
                    self.pve_medium_wins += 1
            elif difficulty == Difficulty.HARD:
                self.pve_hard_games += 1
                if winner == 1:
                    self.pve_hard_wins += 1
        
        if winner == 1:
            self.black_wins += 1
            if mode == GameMode.PVE:
                self.pve_wins += 1
                self.current_win_streak += 1
                self.longest_win_streak = max(self.longest_win_streak, self.current_win_streak)
        elif winner == 2:
            self.white_wins += 1
            if mode == GameMode.PVE:
                self.pve_losses += 1
                self.current_win_streak = 0
        else:
            self.draws += 1
    
    def get_win_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return (self.black_wins + self.white_wins) / self.total_games * 100
    
    def get_pve_win_rate(self) -> float:
        if self.pve_games == 0:
            return 0.0
        return self.pve_wins / self.pve_games * 100
    
    def reset(self) -> None:
        self.total_games = 0
        self.black_wins = 0
        self.white_wins = 0
        self.draws = 0
        self.pvp_games = 0
        self.pvp_black_wins = 0
        self.pvp_white_wins = 0
        self.pve_games = 0
        self.pve_easy_games = 0
        self.pve_easy_wins = 0
        self.pve_medium_games = 0
        self.pve_medium_wins = 0
        self.pve_hard_games = 0
        self.pve_hard_wins = 0
        self.pve_wins = 0
        self.pve_losses = 0
        self.longest_win_streak = 0
        self.current_win_streak = 0


class SaveManager:
    SAVE_PATH = Path("d:/news-map-app/gomoku_save.json")
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
    
    def save(self, config: GameConfig, stats: GameStats) -> bool:
        try:
            self._data = {
                'config': config.to_dict(),
                'stats': stats.to_dict(),
            }
            
            self.SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.SAVE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False
    
    def load(self) -> Optional[Dict[str, Any]]:
        try:
            if not self.SAVE_PATH.exists():
                return None
            
            with open(self.SAVE_PATH, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            return self._data
        except Exception as e:
            print(f"加载失败: {e}")
            return None
    
    def apply_loaded_data(self, config: GameConfig, stats: GameStats) -> None:
        data = self.load()
        if data:
            if 'config' in data:
                config.from_dict(data['config'])
            if 'stats' in data:
                stats.from_dict(data['stats'])


class ResourceManager:
    _instance: Optional['ResourceManager'] = None
    
    def __new__(cls) -> 'ResourceManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._fonts: Dict[str, pygame.font.Font] = {}
        self._images: Dict[str, pygame.Surface] = {}
        self._sounds: Dict[str, Any] = {}
        self._loaded: bool = False
    
    def load_fonts(self) -> None:
        font_path = self._find_chinese_font()
        
        if font_path:
            try:
                self._fonts['title'] = pygame.font.Font(font_path, 48)
                self._fonts['large'] = pygame.font.Font(font_path, 36)
                self._fonts['medium'] = pygame.font.Font(font_path, 24)
                self._fonts['small'] = pygame.font.Font(font_path, 18)
                self._fonts['tiny'] = pygame.font.Font(font_path, 14)
                
                test_surface = self._fonts['medium'].render('测试', True, (255, 255, 255))
                if test_surface.get_width() > 10:
                    return
            except Exception as e:
                pass
        
        font_name = self._find_chinese_font_by_name()
        
        if font_name:
            try:
                self._fonts['title'] = pygame.font.SysFont(font_name, 48)
                self._fonts['large'] = pygame.font.SysFont(font_name, 36)
                self._fonts['medium'] = pygame.font.SysFont(font_name, 24)
                self._fonts['small'] = pygame.font.SysFont(font_name, 18)
                self._fonts['tiny'] = pygame.font.SysFont(font_name, 14)
                
                test_surface = self._fonts['medium'].render('测试', True, (255, 255, 255))
                if test_surface.get_width() > 10:
                    return
            except Exception as e:
                pass
        
        self._load_default_fonts()
    
    def _find_chinese_font(self) -> Optional[str]:
        import os
        import platform
        
        system = platform.system()
        font_dirs = []
        
        if system == 'Windows':
            windows_font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
            font_dirs.append(windows_font_dir)
            
            chinese_fonts = [
                'msyh.ttc',
                'msyhbd.ttc',
                'simhei.ttf',
                'simsun.ttc',
                'simkai.ttf',
                'simfang.ttf',
                'msyhl.ttc'
            ]
            
            for font_dir in font_dirs:
                if not os.path.exists(font_dir):
                    continue
                    
                for font_file in chinese_fonts:
                    font_path = os.path.join(font_dir, font_file)
                    if os.path.exists(font_path):
                        return font_path
            
            for font_dir in font_dirs:
                if not os.path.exists(font_dir):
                    continue
                    
                try:
                    for file in os.listdir(font_dir):
                        if file.lower().endswith(('.ttf', '.ttc')):
                            full_path = os.path.join(font_dir, file)
                            try:
                                test_font = pygame.font.Font(full_path, 20)
                                test_surface = test_font.render('测试', True, (255, 255, 255))
                                if test_surface.get_width() > 20:
                                    return full_path
                            except:
                                continue
                except:
                    continue
        
        return None
    
    def _find_chinese_font_by_name(self) -> Optional[str]:
        font_names_to_try = [
            ('microsoftyahei', 'Microsoft YaHei'),
            ('simhei', 'SimHei'),
            ('simsun', 'SimSun'),
            ('kaiti', 'KaiTi'),
            ('fangsong', 'FangSong'),
            ('arialunicodems', 'Arial Unicode MS'),
        ]
        
        for name_key, display_name in font_names_to_try:
            try:
                matched = pygame.font.match_font(name_key)
                if matched and matched != '':
                    test_font = pygame.font.SysFont(matched, 20)
                    test_surface = test_font.render('测试', True, (255, 255, 255))
                    if test_surface.get_width() > 10:
                        return matched
            except:
                continue
            
            try:
                test_font = pygame.font.SysFont(display_name, 20)
                test_surface = test_font.render('测试', True, (255, 255, 255))
                if test_surface.get_width() > 10:
                    return display_name
            except:
                continue
        
        return None
    
    def _load_default_fonts(self) -> None:
        try:
            default_font = pygame.font.get_default_font()
            self._fonts['title'] = pygame.font.SysFont(default_font, 48)
            self._fonts['large'] = pygame.font.SysFont(default_font, 36)
            self._fonts['medium'] = pygame.font.SysFont(default_font, 24)
            self._fonts['small'] = pygame.font.SysFont(default_font, 18)
            self._fonts['tiny'] = pygame.font.SysFont(default_font, 14)
            
            test_surface = self._fonts['medium'].render('Test', True, (255, 255, 255))
        except:
            self._fonts['title'] = pygame.font.Font(None, 48)
            self._fonts['large'] = pygame.font.Font(None, 36)
            self._fonts['medium'] = pygame.font.Font(None, 24)
            self._fonts['small'] = pygame.font.Font(None, 18)
            self._fonts['tiny'] = pygame.font.Font(None, 14)
    
    def load_resources(self) -> None:
        if self._loaded:
            return
        
        self.load_fonts()
        self._loaded = True
    
    def get_font(self, name: str) -> pygame.font.Font:
        if name not in self._fonts:
            return self._fonts.get('medium', pygame.font.Font(None, 24))
        return self._fonts[name]
    
    def load_image(self, name: str, path: str) -> None:
        try:
            image = pygame.image.load(path)
            self._images[name] = image
        except:
            pass
    
    def get_image(self, name: str) -> Optional[pygame.Surface]:
        return self._images.get(name)
    
    def load_sound(self, name: str, path: str) -> None:
        try:
            sound = pygame.mixer.Sound(path)
            self._sounds[name] = sound
        except:
            pass
    
    def play_sound(self, name: str, volume: float = 1.0) -> None:
        if name in self._sounds:
            sound = self._sounds[name]
            sound.set_volume(volume)
            sound.play()
    
    def cleanup(self) -> None:
        self._fonts.clear()
        self._images.clear()
        self._sounds.clear()
        self._loaded = False


class Particle:
    def __init__(self, x: float, y: float, particle_type: str = 'background'):
        self.x = x
        self.y = y
        self.particle_type = particle_type
        self.vx = 0.0
        self.vy = 0.0
        self.life = 1.0
        self.max_life = 1.0
        self.size = 3.0
        self.color = (255, 255, 255)
        self.alpha = 255
        
        import random
        
        if particle_type == 'background':
            self.vx = random.uniform(-0.5, 0.5)
            self.vy = random.uniform(-0.5, 0.5)
            self.life = random.uniform(3.0, 6.0)
            self.max_life = self.life
            self.size = random.uniform(1.0, 3.0)
            self.color = (255, 255, 255)
            self.alpha = random.randint(50, 150)
        elif particle_type == 'ripple':
            self.life = 1.0
            self.max_life = 1.0
            self.size = 5.0
            self.color = (255, 215, 0)
            self.alpha = 200
        elif particle_type == 'celebration':
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.life = random.uniform(2.0, 4.0)
            self.max_life = self.life
            self.size = random.uniform(3.0, 8.0)
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), 
                     (255, 255, 0), (255, 0, 255), (0, 255, 255)]
            self.color = random.choice(colors)
            self.alpha = 255
        elif particle_type == 'sparkle':
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(-3, -1)
            self.life = random.uniform(1.0, 2.0)
            self.max_life = self.life
            self.size = random.uniform(2.0, 4.0)
            self.color = (255, 215, 0)
            self.alpha = 255
    
    def update(self, dt: float) -> bool:
        self.life -= dt
        
        if self.particle_type == 'background':
            self.x += self.vx
            self.y += self.vy
        elif self.particle_type == 'ripple':
            self.size += 100 * dt
            self.alpha = int(200 * (self.life / self.max_life))
        elif self.particle_type == 'celebration':
            self.x += self.vx
            self.y += self.vy
            self.vy += 0.2
            self.alpha = int(255 * (self.life / self.max_life))
        elif self.particle_type == 'sparkle':
            self.x += self.vx
            self.y += self.vy
            self.alpha = int(255 * (self.life / self.max_life))
        
        return self.life > 0
    
    def render(self, screen: pygame.Surface) -> None:
        if self.alpha <= 0:
            return
        
        if self.particle_type == 'ripple':
            surf = pygame.Surface((int(self.size * 2 + 4), int(self.size * 2 + 4)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, self.alpha), 
                             (int(self.size + 2), int(self.size + 2)), int(self.size), 2)
            screen.blit(surf, (int(self.x - self.size - 2), int(self.y - self.size - 2)))
        else:
            surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, self.alpha), 
                             (int(self.size), int(self.size)), int(self.size))
            screen.blit(surf, (int(self.x - self.size), int(self.y - self.size)))


class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []
        self.max_particles = 500
    
    def emit_background(self, width: int, height: int, count: int = 1) -> None:
        import random
        for _ in range(count):
            if len(self.particles) < self.max_particles:
                x = random.uniform(0, width)
                y = random.uniform(0, height)
                self.particles.append(Particle(x, y, 'background'))
    
    def emit_ripple(self, x: float, y: float, count: int = 3) -> None:
        for i in range(count):
            if len(self.particles) < self.max_particles:
                particle = Particle(x, y, 'ripple')
                particle.life = 1.0 - i * 0.2
                particle.max_life = 1.0
                self.particles.append(particle)
    
    def emit_celebration(self, x: float, y: float, count: int = 50) -> None:
        for _ in range(count):
            if len(self.particles) < self.max_particles:
                self.particles.append(Particle(x, y, 'celebration'))
    
    def emit_sparkle(self, x: float, y: float, count: int = 10) -> None:
        import random
        for _ in range(count):
            if len(self.particles) < self.max_particles:
                px = x + random.uniform(-20, 20)
                py = y + random.uniform(-20, 20)
                self.particles.append(Particle(px, py, 'sparkle'))
    
    def update(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def render(self, screen: pygame.Surface) -> None:
        for particle in self.particles:
            particle.render(screen)
    
    def clear(self) -> None:
        self.particles.clear()


class SoundManager:
    _instance: Optional['SoundManager'] = None
    
    def __new__(cls) -> 'SoundManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._music_playing: bool = False
        self._music_data: Optional[bytes] = None
        
        self.master_volume: float = 1.0
        self.music_volume: float = 0.8
        self.sfx_volume: float = 1.0
        
        self._sample_rate: int = 44100
        self._generate_all_sounds()
    
    def _generate_wave(self, frequency: float, duration: float, 
                       wave_type: str = 'sine', volume: float = 1.0,
                       fade_in: float = 0.0, fade_out: float = 0.0) -> bytes:
        sample_count = int(self._sample_rate * duration)
        
        if HAS_NUMPY:
            t = np.linspace(0, duration, sample_count, False)
            
            if wave_type == 'sine':
                wave = np.sin(2 * np.pi * frequency * t)
            elif wave_type == 'square':
                wave = np.sign(np.sin(2 * np.pi * frequency * t))
            elif wave_type == 'triangle':
                wave = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
            elif wave_type == 'sawtooth':
                wave = 2 * (t * frequency - np.floor(t * frequency + 0.5))
            else:
                wave = np.sin(2 * np.pi * frequency * t)
            
            if fade_in > 0:
                fade_samples = int(self._sample_rate * fade_in)
                fade_curve = np.linspace(0, 1, fade_samples)
                wave[:fade_samples] *= fade_curve
            
            if fade_out > 0:
                fade_samples = int(self._sample_rate * fade_out)
                fade_curve = np.linspace(1, 0, fade_samples)
                wave[-fade_samples:] *= fade_curve
            
            wave = (wave * volume * 32767 * 0.5).astype(np.int16)
            
            stereo_wave = np.column_stack((wave, wave))
            return stereo_wave.tobytes()
        else:
            samples = array.array('h')
            for i in range(sample_count):
                t = i / self._sample_rate
                
                if wave_type == 'sine':
                    value = math.sin(2 * math.pi * frequency * t)
                elif wave_type == 'square':
                    value = 1.0 if math.sin(2 * math.pi * frequency * t) >= 0 else -1.0
                elif wave_type == 'triangle':
                    phase = (t * frequency) % 1.0
                    value = 4 * abs(phase - 0.5) - 1
                elif wave_type == 'sawtooth':
                    phase = (t * frequency) % 1.0
                    value = 2 * phase - 1
                else:
                    value = math.sin(2 * math.pi * frequency * t)
                
                envelope = 1.0
                if fade_in > 0 and t < fade_in:
                    envelope *= t / fade_in
                if fade_out > 0 and t > duration - fade_out:
                    envelope *= (duration - t) / fade_out
                
                sample_value = int(value * volume * envelope * 32767 * 0.5)
                samples.append(sample_value)
                samples.append(sample_value)
            
            return samples.tobytes()
    
    def _generate_chord(self, frequencies: List[float], duration: float,
                        wave_type: str = 'sine', volume: float = 1.0) -> bytes:
        sample_count = int(self._sample_rate * duration)
        
        if HAS_NUMPY:
            t = np.linspace(0, duration, sample_count, False)
            wave = np.zeros(sample_count)
            
            for freq in frequencies:
                if wave_type == 'sine':
                    wave += np.sin(2 * np.pi * freq * t)
                elif wave_type == 'triangle':
                    phase = (t * freq) % 1.0
                    wave += 2 * np.abs(2 * (phase - 0.5)) - 1
                else:
                    wave += np.sin(2 * np.pi * freq * t)
            
            wave /= len(frequencies)
            
            fade_samples = int(self._sample_rate * 0.05)
            wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            wave = (wave * volume * 32767 * 0.5).astype(np.int16)
            stereo_wave = np.column_stack((wave, wave))
            return stereo_wave.tobytes()
        else:
            samples = array.array('h')
            for i in range(sample_count):
                t = i / self._sample_rate
                value = 0.0
                
                for freq in frequencies:
                    if wave_type == 'sine':
                        value += math.sin(2 * math.pi * freq * t)
                    elif wave_type == 'triangle':
                        phase = (t * freq) % 1.0
                        value += 2 * abs(phase - 0.5) - 1
                    else:
                        value += math.sin(2 * math.pi * freq * t)
                
                value /= len(frequencies)
                
                if t > duration - 0.05:
                    value *= (duration - t) / 0.05
                
                sample_value = int(value * volume * 32767 * 0.5)
                samples.append(sample_value)
                samples.append(sample_value)
            
            return samples.tobytes()
    
    def _generate_all_sounds(self) -> None:
        self._generate_place_sound()
        self._generate_win_sound()
        self._generate_lose_sound()
        self._generate_click_sound()
        self._generate_background_music()
    
    def _generate_place_sound(self) -> None:
        data = self._generate_wave(800, 0.08, 'sine', 0.6, fade_out=0.05)
        self._sounds['place'] = pygame.mixer.Sound(buffer=data)
    
    def _generate_win_sound(self) -> None:
        samples = array.array('h')
        
        notes = [
            (523.25, 0.15),
            (659.25, 0.15),
            (783.99, 0.15),
            (1046.50, 0.3),
        ]
        
        for freq, dur in notes:
            data = self._generate_wave(freq, dur, 'sine', 0.5, fade_out=0.05)
            samples.extend(array.array('h', data))
        
        chord_data = self._generate_chord([523.25, 659.25, 783.99, 1046.50], 0.5, 'sine', 0.4)
        samples.extend(array.array('h', chord_data))
        
        self._sounds['win'] = pygame.mixer.Sound(buffer=samples.tobytes())
    
    def _generate_lose_sound(self) -> None:
        samples = array.array('h')
        
        notes = [
            (392.00, 0.2),
            (349.23, 0.2),
            (311.13, 0.2),
            (261.63, 0.4),
        ]
        
        for freq, dur in notes:
            data = self._generate_wave(freq, dur, 'triangle', 0.4, fade_out=0.1)
            samples.extend(array.array('h', data))
        
        self._sounds['lose'] = pygame.mixer.Sound(buffer=samples.tobytes())
    
    def _generate_click_sound(self) -> None:
        data = self._generate_wave(1200, 0.03, 'sine', 0.4, fade_out=0.02)
        self._sounds['click'] = pygame.mixer.Sound(buffer=data)
    
    def _generate_background_music(self) -> None:
        samples = array.array('h')
        
        melody = [
            (523.25, 0.3), (587.33, 0.3), (659.25, 0.3), (698.46, 0.3),
            (783.99, 0.3), (698.46, 0.3), (659.25, 0.3), (587.33, 0.3),
            (523.25, 0.3), (493.88, 0.3), (523.25, 0.3), (587.33, 0.3),
            (659.25, 0.6), (587.33, 0.6),
        ]
        
        for i in range(2):
            for freq, dur in melody:
                data = self._generate_wave(freq, dur, 'triangle', 0.25, fade_out=0.05)
                samples.extend(array.array('h', data))
        
        self._music_data = samples.tobytes()
    
    def play_sound(self, name: str) -> None:
        if name in self._sounds:
            effective_volume = self.master_volume * self.sfx_volume
            self._sounds[name].set_volume(effective_volume)
            self._sounds[name].play()
    
    def play_place_sound(self) -> None:
        self.play_sound('place')
    
    def play_win_sound(self) -> None:
        self.play_sound('win')
    
    def play_lose_sound(self) -> None:
        self.play_sound('lose')
    
    def play_click_sound(self) -> None:
        self.play_sound('click')
    
    def start_background_music(self) -> None:
        if self._music_data and not self._music_playing:
            try:
                pygame.mixer.music.load(
                    pygame.mixer.Sound(buffer=self._music_data)
                )
                effective_volume = self.master_volume * self.music_volume
                pygame.mixer.music.set_volume(effective_volume)
                pygame.mixer.music.play(-1)
                self._music_playing = True
            except:
                pass
    
    def stop_background_music(self) -> None:
        if self._music_playing:
            pygame.mixer.music.stop()
            self._music_playing = False
    
    def toggle_background_music(self) -> bool:
        if self._music_playing:
            self.stop_background_music()
            return False
        else:
            self.start_background_music()
            return True
    
    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))
        self._update_music_volume()
    
    def set_music_volume(self, volume: float) -> None:
        self.music_volume = max(0.0, min(1.0, volume))
        self._update_music_volume()
    
    def set_sfx_volume(self, volume: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, volume))
    
    def _update_music_volume(self) -> None:
        if self._music_playing:
            effective_volume = self.master_volume * self.music_volume
            pygame.mixer.music.set_volume(effective_volume)
    
    def is_music_playing(self) -> bool:
        return self._music_playing
    
    def cleanup(self) -> None:
        self.stop_background_music()
        self._sounds.clear()


class GameStateManager:
    def __init__(self):
        self._state: GameState = GameState.MENU
        self._previous_state: Optional[GameState] = None
        self._state_data: Dict[str, Any] = {}
    
    @property
    def state(self) -> GameState:
        return self._state
    
    @property
    def previous_state(self) -> Optional[GameState]:
        return self._previous_state
    
    def change_state(self, new_state: GameState, data: Optional[Dict[str, Any]] = None) -> None:
        self._previous_state = self._state
        self._state = new_state
        if data:
            self._state_data.update(data)
    
    def get_state_data(self, key: str, default: Any = None) -> Any:
        return self._state_data.get(key, default)
    
    def set_state_data(self, key: str, value: Any) -> None:
        self._state_data[key] = value
    
    def clear_state_data(self) -> None:
        self._state_data.clear()
    
    def is_playing(self) -> bool:
        return self._state == GameState.PLAYING
    
    def is_paused(self) -> bool:
        return self._state == GameState.PAUSED
    
    def is_game_over(self) -> bool:
        return self._state == GameState.GAME_OVER


class BaseScene(ABC):
    def __init__(self, screen: pygame.Surface, config: GameConfig, 
                 resource_manager: ResourceManager, state_manager: GameStateManager,
                 sound_manager: Optional['SoundManager'] = None):
        self.screen = screen
        self.config = config
        self.resource_manager = resource_manager
        self.state_manager = state_manager
        self.sound_manager = sound_manager
        self.animation_offset: int = 0
        self.transition_alpha: int = 255
        self.is_entering: bool = False
        self.is_exiting: bool = False
    
    @abstractmethod
    def enter(self, data: Optional[Dict[str, Any]] = None) -> None:
        pass
    
    @abstractmethod
    def exit(self) -> None:
        pass
    
    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        pass
    
    @abstractmethod
    def update(self, dt: float) -> None:
        pass
    
    @abstractmethod
    def render(self) -> None:
        pass
    
    def update_animation(self) -> None:
        self.animation_offset += 1
    
    def render_transition(self) -> None:
        if self.is_entering or self.is_exiting:
            overlay = pygame.Surface((self.config.window_width, self.config.window_height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self.transition_alpha)
            self.screen.blit(overlay, (0, 0))


class Slider:
    def __init__(self, rect: pygame.Rect, min_val: float, max_val: float, 
                 initial_val: float, label: str, font: pygame.font.Font,
                 config: GameConfig):
        self.rect = rect
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.font = font
        self.config = config
        self.dragging = False
        self.knob_radius = 10
        self.track_height = 8
    
    @property
    def knob_x(self) -> int:
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return int(self.rect.left + ratio * self.rect.width)
    
    @property
    def knob_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.knob_x - self.knob_radius,
            self.rect.centery - self.knob_radius,
            self.knob_radius * 2,
            self.knob_radius * 2
        )
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.knob_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self._update_value(event.pos[0])
                return True
        return False
    
    def _update_value(self, x: int) -> None:
        x = max(self.rect.left, min(x, self.rect.right))
        ratio = (x - self.rect.left) / self.rect.width
        self.value = self.min_val + ratio * (self.max_val - self.min_val)
    
    def render(self, screen: pygame.Surface) -> None:
        label_surface = self.font.render(self.label, True, self.config.theme_text)
        label_rect = label_surface.get_rect(midleft=(self.rect.left, self.rect.top - 15))
        screen.blit(label_surface, label_rect)
        
        track_rect = pygame.Rect(
            self.rect.left,
            self.rect.centery - self.track_height // 2,
            self.rect.width,
            self.track_height
        )
        pygame.draw.rect(screen, self.config.theme_secondary, track_rect, border_radius=4)
        
        filled_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        filled_rect = pygame.Rect(
            self.rect.left,
            self.rect.centery - self.track_height // 2,
            filled_width,
            self.track_height
        )
        pygame.draw.rect(screen, self.config.theme_primary, filled_rect, border_radius=4)
        
        knob_color = self.config.theme_highlight if self.dragging else self.config.theme_primary
        pygame.draw.circle(screen, knob_color, (self.knob_x, self.rect.centery), self.knob_radius)
        pygame.draw.circle(screen, (255, 255, 255), (self.knob_x, self.rect.centery), self.knob_radius - 3)
        
        value_text = f"{int(self.value * 100)}%"
        value_surface = self.font.render(value_text, True, self.config.theme_text)
        value_rect = value_surface.get_rect(midright=(self.rect.right + 50, self.rect.centery))
        screen.blit(value_surface, value_rect)


class OptionSelector:
    def __init__(self, rect: pygame.Rect, options: List[str], selected_index: int,
                 label: str, font: pygame.font.Font, config: GameConfig):
        self.rect = rect
        self.options = options
        self.selected_index = selected_index
        self.label = label
        self.font = font
        self.config = config
        self.option_width = 80
        self.option_spacing = 10
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(len(self.options)):
                option_rect = self._get_option_rect(i)
                if option_rect.collidepoint(event.pos):
                    self.selected_index = i
                    return True
        return False
    
    def _get_option_rect(self, index: int) -> pygame.Rect:
        total_width = len(self.options) * self.option_width + (len(self.options) - 1) * self.option_spacing
        start_x = self.rect.centerx - total_width // 2
        
        return pygame.Rect(
            start_x + index * (self.option_width + self.option_spacing),
            self.rect.y,
            self.option_width,
            self.rect.height
        )
    
    def render(self, screen: pygame.Surface) -> None:
        label_surface = self.font.render(self.label, True, self.config.theme_text)
        label_rect = label_surface.get_rect(midleft=(self.rect.left, self.rect.y - 15))
        screen.blit(label_surface, label_rect)
        
        for i, option in enumerate(self.options):
            option_rect = self._get_option_rect(i)
            is_selected = i == self.selected_index
            
            if is_selected:
                bg_color = self.config.theme_primary
                text_color = (255, 255, 255)
            else:
                bg_color = self.config.theme_secondary
                text_color = self.config.theme_text
            
            pygame.draw.rect(screen, bg_color, option_rect, border_radius=5)
            pygame.draw.rect(screen, self.config.theme_primary, option_rect, 2, border_radius=5)
            
            option_surface = self.font.render(option, True, text_color)
            option_text_rect = option_surface.get_rect(center=option_rect.center)
            screen.blit(option_surface, option_text_rect)


class Button:
    def __init__(self, rect: pygame.Rect, text: str, 
                 font: pygame.font.Font,
                 color: Tuple[int, int, int] = None,
                 hover_color: Tuple[int, int, int] = None,
                 text_color: Tuple[int, int, int] = (255, 255, 255),
                 config: GameConfig = None):
        self.rect = rect
        self.text = text
        self.font = font
        self.color = color if color else (config.theme_button_normal if config else (139, 90, 43))
        self.hover_color = hover_color if hover_color else (config.theme_button_hover if config else (160, 110, 60))
        self.text_color = text_color
        self.is_hovered: bool = False
        self.is_pressed: bool = False
        self.animation_scale: float = 1.0
    
    def update(self, mouse_pos: Tuple[int, int]) -> None:
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        target_scale = 1.05 if self.is_hovered else 1.0
        self.animation_scale += (target_scale - self.animation_scale) * 0.2
    
    def render(self, screen: pygame.Surface, config: GameConfig = None) -> None:
        color = self.hover_color if self.is_hovered else self.color
        
        scaled_rect = self.rect.copy()
        if self.animation_scale != 1.0:
            center = self.rect.center
            scaled_rect.width = int(self.rect.width * self.animation_scale)
            scaled_rect.height = int(self.rect.height * self.animation_scale)
            scaled_rect.center = center
        
        pygame.draw.rect(screen, color, scaled_rect, border_radius=10)
        border_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.rect(screen, border_color, scaled_rect, 2, border_radius=10)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=scaled_rect.center)
        screen.blit(text_surface, text_rect)
    
    def is_clicked(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


class ConfirmDialog:
    def __init__(self, screen: pygame.Surface, config: GameConfig,
                 resource_manager: ResourceManager, title: str, message: str):
        self.screen = screen
        self.config = config
        self.resource_manager = resource_manager
        self.title = title
        self.message = message
        self.visible = False
        self.result: Optional[bool] = None
        
        dialog_width = 400
        dialog_height = 200
        self.rect = pygame.Rect(
            (config.window_width - dialog_width) // 2,
            (config.window_height - dialog_height) // 2,
            dialog_width,
            dialog_height
        )
        
        font = resource_manager.get_font('medium')
        self.yes_button = Button(
            pygame.Rect(self.rect.x + 60, self.rect.bottom - 60, 100, 40),
            "确认", font, color=(180, 80, 80), hover_color=(200, 100, 100)
        )
        self.no_button = Button(
            pygame.Rect(self.rect.right - 160, self.rect.bottom - 60, 100, 40),
            "取消", font
        )
    
    def show(self) -> None:
        self.visible = True
        self.result = None
    
    def hide(self) -> None:
        self.visible = False
    
    def handle_event(self, event: pygame.event.Event) -> Optional[bool]:
        if not self.visible:
            return None
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.yes_button.is_clicked(event.pos):
                self.result = True
                self.hide()
                return True
            elif self.no_button.is_clicked(event.pos):
                self.result = False
                self.hide()
                return False
        
        return None
    
    def update(self) -> None:
        if self.visible:
            mouse_pos = pygame.mouse.get_pos()
            self.yes_button.update(mouse_pos)
            self.no_button.update(mouse_pos)
    
    def render(self) -> None:
        if not self.visible:
            return
        
        overlay = pygame.Surface((self.config.window_width, self.config.window_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(self.screen, self.config.theme_background, self.rect, border_radius=15)
        pygame.draw.rect(self.screen, self.config.theme_primary, self.rect, 3, border_radius=15)
        
        title_font = self.resource_manager.get_font('large')
        title_surface = title_font.render(self.title, True, self.config.theme_text)
        title_rect = title_surface.get_rect(centerx=self.rect.centerx, y=self.rect.y + 30)
        self.screen.blit(title_surface, title_rect)
        
        font = self.resource_manager.get_font('medium')
        message_surface = font.render(self.message, True, self.config.theme_text)
        message_rect = message_surface.get_rect(centerx=self.rect.centerx, y=self.rect.y + 80)
        self.screen.blit(message_surface, message_rect)
        
        self.yes_button.render(self.screen, self.config)
        self.no_button.render(self.screen, self.config)


class MenuScene(BaseScene):
    def __init__(self, screen: pygame.Surface, config: GameConfig,
                 resource_manager: ResourceManager, state_manager: GameStateManager,
                 sound_manager: Optional['SoundManager'] = None):
        super().__init__(screen, config, resource_manager, state_manager, sound_manager)
        self.buttons: List[Button] = []
        self.difficulty_buttons: List[Button] = []
        self.title_offset: float = 0
        self.show_difficulty_menu: bool = False
        self.menu_transition: float = 0.0
        self.selected_difficulty: Difficulty = Difficulty.MEDIUM
        self.board_pattern_phase: float = 0.0
        self._create_buttons()
        self._create_difficulty_buttons()
    
    def _create_buttons(self) -> None:
        font = self.resource_manager.get_font('medium')
        button_width = 200
        button_height = 50
        start_y = 280
        spacing = 70
        
        button_data = [
            ("双人对战", "pvp"),
            ("人机对战", "pve"),
            ("游戏设置", "settings"),
            ("游戏统计", "stats"),
            ("退出游戏", "quit"),
        ]
        
        self.buttons = []
        for i, (text, action) in enumerate(button_data):
            rect = pygame.Rect(
                (self.config.window_width - button_width) // 2,
                start_y + i * spacing,
                button_width,
                button_height
            )
            button = Button(rect, text, font)
            button.action = action
            self.buttons.append(button)
    
    def _create_difficulty_buttons(self) -> None:
        font = self.resource_manager.get_font('medium')
        button_width = 150
        button_height = 45
        start_y = 300
        spacing = 60
        
        difficulty_data = [
            ("简 单", Difficulty.EASY),
            ("中 等", Difficulty.MEDIUM),
            ("困 难", Difficulty.HARD),
        ]
        
        self.difficulty_buttons = []
        for i, (text, difficulty) in enumerate(difficulty_data):
            rect = pygame.Rect(
                (self.config.window_width - button_width) // 2,
                start_y + i * spacing,
                button_width,
                button_height
            )
            button = Button(rect, text, font, color=(100, 140, 100), hover_color=(120, 160, 120))
            button.difficulty = difficulty
            self.difficulty_buttons.append(button)
        
        back_rect = pygame.Rect(
            (self.config.window_width - 120) // 2,
            start_y + 3 * spacing + 20,
            120,
            40
        )
        back_button = Button(back_rect, "返回", font, color=(140, 100, 100), hover_color=(160, 120, 120))
        back_button.action = "back"
        self.difficulty_buttons.append(back_button)
    
    def enter(self, data: Optional[Dict[str, Any]] = None) -> None:
        self.is_entering = True
        self.transition_alpha = 255
        self.show_difficulty_menu = False
        self.menu_transition = 0.0
    
    def exit(self) -> None:
        self.is_exiting = True
        self.transition_alpha = 0
    
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.show_difficulty_menu:
                for button in self.difficulty_buttons:
                    if button.is_clicked(event.pos):
                        if self.sound_manager:
                            self.sound_manager.play_click_sound()
                        self._handle_difficulty_click(button)
                        break
            else:
                for button in self.buttons:
                    if button.is_clicked(event.pos):
                        if self.sound_manager:
                            self.sound_manager.play_click_sound()
                        self._handle_button_click(button)
                        break
    
    def _handle_difficulty_click(self, button: Button) -> None:
        if hasattr(button, 'difficulty'):
            self.selected_difficulty = button.difficulty
            self.state_manager.change_state(GameState.PLAYING, {
                'mode': GameMode.PVE,
                'difficulty': self.selected_difficulty
            })
        elif getattr(button, 'action', '') == "back":
            self.show_difficulty_menu = False
            self.menu_transition = 0.0
    
    def _handle_button_click(self, button: Button) -> None:
        action = getattr(button, 'action', '')
        
        if action == "pvp":
            self.state_manager.change_state(GameState.PLAYING, {'mode': GameMode.PVP})
        elif action == "pve":
            self.show_difficulty_menu = True
            self.menu_transition = 0.0
        elif action == "settings":
            self.state_manager.change_state(GameState.SETTINGS)
        elif action == "stats":
            self.state_manager.change_state(GameState.STATS)
        elif action == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))
    
    def update(self, dt: float) -> None:
        self.update_animation()
        self.title_offset = math.sin(self.animation_offset * 0.05) * 5
        self.board_pattern_phase += dt * 0.5
        
        if self.show_difficulty_menu and self.menu_transition < 1.0:
            self.menu_transition = min(1.0, self.menu_transition + 0.05)
        elif not self.show_difficulty_menu and self.menu_transition > 0.0:
            self.menu_transition = max(0.0, self.menu_transition - 0.05)
        
        if self.is_entering:
            self.transition_alpha = max(0, self.transition_alpha - 10)
            if self.transition_alpha == 0:
                self.is_entering = False
        
        mouse_pos = pygame.mouse.get_pos()
        if self.show_difficulty_menu:
            for button in self.difficulty_buttons:
                button.update(mouse_pos)
        for button in self.buttons:
            button.update(mouse_pos)
    
    def render(self) -> None:
        self._render_gradient_background()
        self._render_board_pattern()
        
        self._render_decorations()
        self._render_title()
        
        if self.show_difficulty_menu:
            self._render_difficulty_menu()
        else:
            for button in self.buttons:
                button.render(self.screen)
        
        self._render_footer()
        self.render_transition()
    
    def _render_gradient_background(self) -> None:
        for y in range(self.config.window_height):
            ratio = y / self.config.window_height
            r = int(245 - ratio * 30)
            g = int(222 - ratio * 40)
            b = int(179 - ratio * 50)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.config.window_width, y))
    
    def _render_board_pattern(self) -> None:
        pattern_surf = pygame.Surface((self.config.window_width, self.config.window_height), pygame.SRCALPHA)
        cell_size = 40
        line_color = (200, 180, 150, 30)
        
        for x in range(0, self.config.window_width, cell_size):
            wave = int(5 * math.sin(self.board_pattern_phase + x * 0.01))
            pygame.draw.line(pattern_surf, line_color, (x, 0), (x + wave, self.config.window_height), 1)
        
        for y in range(0, self.config.window_height, cell_size):
            wave = int(5 * math.sin(self.board_pattern_phase + y * 0.01))
            pygame.draw.line(pattern_surf, line_color, (0, y), (self.config.window_width, y + wave), 1)
        
        self.screen.blit(pattern_surf, (0, 0))
    
    def _render_difficulty_menu(self) -> None:
        overlay = pygame.Surface((self.config.window_width, self.config.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(100 * self.menu_transition)))
        self.screen.blit(overlay, (0, 0))
        
        menu_width = 280
        menu_height = 350
        menu_x = (self.config.window_width - menu_width) // 2
        menu_y = (self.config.window_height - menu_height) // 2 - 30
        
        menu_surf = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        pygame.draw.rect(menu_surf, (245, 222, 179, int(240 * self.menu_transition)), 
                        (0, 0, menu_width, menu_height), border_radius=15)
        pygame.draw.rect(menu_surf, (139, 90, 43, int(255 * self.menu_transition)), 
                        (0, 0, menu_width, menu_height), 3, border_radius=15)
        
        title_font = self.resource_manager.get_font('large')
        title_text = "选择难度"
        title_surface = title_font.render(title_text, True, self.config.theme_text)
        title_rect = title_surface.get_rect(centerx=menu_width // 2, y=20)
        menu_surf.blit(title_surface, title_rect)
        
        self.screen.blit(menu_surf, (menu_x, menu_y))
        
        if self.menu_transition > 0.5:
            for button in self.difficulty_buttons:
                button.render(self.screen)
    
    def _render_decorations(self) -> None:
        for i in range(5):
            x = 50 + i * 180
            y = 100 + math.sin(self.animation_offset * 0.03 + i) * 10
            radius = 15
            
            glow_alpha = int(50 + 30 * math.sin(self.animation_offset * 0.08 + i * 0.5))
            if glow_alpha > 60:
                glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (100, 100, 100, glow_alpha), (radius * 2, radius * 2), radius * 2)
                self.screen.blit(glow_surf, (x - radius * 2, int(y) - radius * 2))
            
            for j in range(radius, 0, -1):
                ratio = j / radius
                gray = int(20 + 50 * (1 - ratio))
                pygame.draw.circle(self.screen, (gray, gray, gray), (x, int(y)), j)
            
            highlight_pos = (x - radius // 3, int(y) - radius // 3)
            pygame.draw.circle(self.screen, (80, 80, 80), highlight_pos, radius // 4)
        
        for i in range(5):
            x = self.config.window_width - 50 - i * 180
            y = self.config.window_height - 100 + math.sin(self.animation_offset * 0.03 + i + 2) * 10
            radius = 15
            
            glow_alpha = int(50 + 30 * math.sin(self.animation_offset * 0.08 + i * 0.5 + 2))
            if glow_alpha > 60:
                glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (200, 200, 200, glow_alpha), (radius * 2, radius * 2), radius * 2)
                self.screen.blit(glow_surf, (x - radius * 2, int(y) - radius * 2))
            
            for j in range(radius, 0, -1):
                ratio = j / radius
                gray = int(250 - 30 * (1 - ratio))
                pygame.draw.circle(self.screen, (gray, gray, gray), (x, int(y)), j)
            
            pygame.draw.circle(self.screen, (200, 200, 200), (x, int(y)), radius, 1)
            
            highlight_pos = (x - radius // 3, int(y) - radius // 3)
            pygame.draw.circle(self.screen, (255, 255, 255), highlight_pos, radius // 4)
        
        self._render_corner_decorations()
    
    def _render_corner_decorations(self) -> None:
        corner_size = 60
        corners = [
            (40, 40), (self.config.window_width - 40, 40),
            (40, self.config.window_height - 40), (self.config.window_width - 40, self.config.window_height - 40)
        ]
        
        for i, (cx, cy) in enumerate(corners):
            angle = self.animation_offset * 0.02 + i * math.pi / 2
            for j in range(2):
                offset = j * 10
                alpha = int(60 - j * 20)
                
                surf = pygame.Surface((corner_size, corner_size), pygame.SRCALPHA)
                line_len = 20
                x1 = corner_size // 2 + int(offset * math.cos(angle))
                y1 = corner_size // 2 + int(offset * math.sin(angle))
                x2 = x1 + int(line_len * math.cos(angle + 0.5))
                y2 = y1 + int(line_len * math.sin(angle + 0.5))
                pygame.draw.line(surf, (180, 150, 120, alpha), (x1, y1), (x2, y2), 2)
                self.screen.blit(surf, (cx - corner_size // 2, cy - corner_size // 2))
    
    def _render_title(self) -> None:
        title_font = self.resource_manager.get_font('title')
        title_text = "五子棋"
        
        glow_surf = pygame.Surface((300, 80), pygame.SRCALPHA)
        glow_alpha = int(50 + 30 * math.sin(self.animation_offset * 0.08))
        pygame.draw.ellipse(glow_surf, (255, 215, 0, glow_alpha), (0, 0, 300, 80))
        self.screen.blit(glow_surf, (self.config.window_width // 2 - 150, 110 + self.title_offset))
        
        shadow_surface = title_font.render(title_text, True, (180, 160, 140))
        shadow_rect = shadow_surface.get_rect(
            center=(self.config.window_width // 2 + 3, 153 + self.title_offset)
        )
        self.screen.blit(shadow_surface, shadow_rect)
        
        title_surface = title_font.render(title_text, True, self.config.theme_text)
        title_rect = title_surface.get_rect(
            center=(self.config.window_width // 2, 150 + self.title_offset)
        )
        self.screen.blit(title_surface, title_rect)
        
        subtitle_font = self.resource_manager.get_font('small')
        subtitle_text = "Gomoku Game"
        subtitle_surface = subtitle_font.render(subtitle_text, True, (120, 100, 80))
        subtitle_rect = subtitle_surface.get_rect(
            center=(self.config.window_width // 2, 200 + self.title_offset)
        )
        self.screen.blit(subtitle_surface, subtitle_rect)
    
    def _render_footer(self) -> None:
        footer_font = self.resource_manager.get_font('tiny')
        footer_text = "按 ESC 键退出 | 版本 1.0"
        footer_surface = footer_font.render(footer_text, True, self.config.theme_primary)
        footer_rect = footer_surface.get_rect(
            center=(self.config.window_width // 2, self.config.window_height - 30)
        )
        self.screen.blit(footer_surface, footer_rect)


class GameScene(BaseScene):
    STAR_POINTS_15 = [(3, 3), (3, 7), (3, 11), (7, 3), (7, 7), (7, 11), (11, 3), (11, 7), (11, 11)]
    STAR_POINTS_13 = [(3, 3), (3, 6), (3, 9), (6, 3), (6, 6), (6, 9), (9, 3), (9, 6), (9, 9)]
    STAR_POINTS_19 = [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9), (9, 15), (15, 3), (15, 9), (15, 15)]
    
    def __init__(self, screen: pygame.Surface, config: GameConfig,
                 resource_manager: ResourceManager, state_manager: GameStateManager,
                 stats: GameStats, save_manager: SaveManager,
                 sound_manager: Optional['SoundManager'] = None):
        super().__init__(screen, config, resource_manager, state_manager, sound_manager)
        self.stats = stats
        self.save_manager = save_manager
        
        self.board: List[List[int]] = []
        self.current_player: int = 1
        self.game_mode: GameMode = GameMode.PVP
        self.difficulty: Difficulty = Difficulty.MEDIUM
        self.move_history: List[Tuple[int, int]] = []
        self.win_line: List[Tuple[int, int]] = []
        self.hover_pos: Optional[Tuple[int, int]] = None
        self.winner: int = 0
        self.win_animation_frame: int = 0
        
        self.board_offset_x: int = 0
        self.board_offset_y: int = 0
        
        self.ai: Optional[GomokuAI] = None
        self.ai_thinking: bool = False
        self.ai_think_timer: float = 0
        self.ai_think_duration: float = 0.5
        self.ai_move: Optional[Tuple[int, int]] = None
        self.ai_animation_angle: float = 0
        
        self.particle_system: Optional[ParticleSystem] = None
        self.animation_offset: int = 0
        
        self.buttons: List[Button] = []
        self._calculate_board_position()
        self._create_buttons()
    
    def _get_star_points(self) -> List[Tuple[int, int]]:
        if self.config.board_size == 13:
            return self.STAR_POINTS_13
        elif self.config.board_size == 19:
            return self.STAR_POINTS_19
        return self.STAR_POINTS_15
    
    def _calculate_board_position(self) -> None:
        board_size_px = (self.config.board_size - 1) * self.config.cell_size
        self.board_offset_x = (self.config.window_width - board_size_px) // 2
        self.board_offset_y = (self.config.window_height - board_size_px) // 2 - 30
    
    def _create_buttons(self) -> None:
        font = self.resource_manager.get_font('small')
        button_width = 80
        button_height = 35
        button_y = self.config.window_height - 50
        
        button_data = [
            ("悔棋", "undo", 50),
            ("重开", "restart", 150),
            ("菜单", "menu", 250),
        ]
        
        self.buttons = []
        for text, action, x in button_data:
            rect = pygame.Rect(x, button_y, button_width, button_height)
            button = Button(rect, text, font, config=self.config)
            button.action = action
            self.buttons.append(button)
    
    def enter(self, data: Optional[Dict[str, Any]] = None) -> None:
        self.is_entering = True
        self.transition_alpha = 255
        
        if data:
            self.game_mode = data.get('mode', GameMode.PVP)
            self.difficulty = data.get('difficulty', Difficulty.MEDIUM)
        
        if self.game_mode == GameMode.PVE:
            self.ai = GomokuAI(self.difficulty)
        else:
            self.ai = None
        
        self.particle_system = ParticleSystem()
        self.animation_offset = 0
        
        self._calculate_board_position()
        self._create_buttons()
        self._reset_game()
    
    def exit(self) -> None:
        self.is_exiting = True
        self.transition_alpha = 0
    
    def _reset_game(self) -> None:
        self.board = [[0] * self.config.board_size for _ in range(self.config.board_size)]
        self.current_player = 1
        self.move_history = []
        self.win_line = []
        self.winner = 0
        self.win_animation_frame = 0
        self.ai_thinking = False
        self.ai_think_timer = 0
        self.ai_move = None
        if self.particle_system:
            self.particle_system.clear()
    
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.ai_thinking:
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.is_clicked(event.pos):
                    if self.sound_manager:
                        self.sound_manager.play_click_sound()
                    self._handle_button_click(button)
                    return
            
            if self.state_manager.state == GameState.PLAYING:
                board_pos = self._screen_to_board(event.pos)
                if board_pos:
                    self._make_move(*board_pos)
        
        elif event.type == pygame.MOUSEMOTION:
            self.hover_pos = self._screen_to_board(event.pos)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state_manager.change_state(GameState.MENU)
            elif event.key == pygame.K_r:
                self._reset_game()
            elif event.key == pygame.K_u:
                self._undo_move()
    
    def _handle_button_click(self, button: Button) -> None:
        action = getattr(button, 'action', '')
        
        if action == "undo":
            self._undo_move()
        elif action == "restart":
            self._reset_game()
        elif action == "menu":
            self.state_manager.change_state(GameState.MENU)
    
    def _screen_to_board(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        x, y = pos
        col = round((x - self.board_offset_x) / self.config.cell_size)
        row = round((y - self.board_offset_y) / self.config.cell_size)
        
        if 0 <= row < self.config.board_size and 0 <= col < self.config.board_size:
            screen_x, screen_y = self._board_to_screen(row, col)
            distance = math.sqrt((x - screen_x) ** 2 + (y - screen_y) ** 2)
            if distance < self.config.cell_size // 2:
                return row, col
        return None
    
    def _board_to_screen(self, row: int, col: int) -> Tuple[int, int]:
        x = self.board_offset_x + col * self.config.cell_size
        y = self.board_offset_y + row * self.config.cell_size
        return x, y
    
    def _make_move(self, row: int, col: int) -> bool:
        if self.board[row][col] == 0 and self.state_manager.state == GameState.PLAYING:
            self.board[row][col] = self.current_player
            self.move_history.append((row, col))
            
            screen_x, screen_y = self._board_to_screen(row, col)
            if self.particle_system:
                self.particle_system.emit_ripple(screen_x, screen_y, 3)
            
            if self.sound_manager:
                self.sound_manager.play_place_sound()
            
            win_line = self._check_win(row, col)
            if win_line:
                self.win_line = win_line
                self.winner = self.current_player
                self.state_manager.change_state(GameState.GAME_OVER)
                self.stats.record_game(self.winner, self.game_mode, self.difficulty)
                self.save_manager.save(self.config, self.stats)
                
                if self.particle_system:
                    center_x = self.config.window_width // 2
                    center_y = self.config.window_height // 2
                    self.particle_system.emit_celebration(center_x, center_y, 100)
                    for r, c in win_line:
                        x, y = self._board_to_screen(r, c)
                        self.particle_system.emit_sparkle(x, y, 5)
                
                if self.sound_manager:
                    if self.game_mode == GameMode.PVE and self.winner == 1:
                        self.sound_manager.play_win_sound()
                    elif self.game_mode == GameMode.PVE and self.winner == 2:
                        self.sound_manager.play_lose_sound()
                    else:
                        self.sound_manager.play_win_sound()
            elif len(self.move_history) == self.config.board_size * self.config.board_size:
                self.winner = 0
                self.state_manager.change_state(GameState.GAME_OVER)
                self.stats.record_game(0, self.game_mode, self.difficulty)
                self.save_manager.save(self.config, self.stats)
            else:
                self.current_player = 3 - self.current_player
                if self.game_mode == GameMode.PVE and self.ai and self.current_player == 2:
                    self._start_ai_thinking()
            
            return True
        return False
    
    def _start_ai_thinking(self) -> None:
        self.ai_thinking = True
        self.ai_think_timer = 0
        self.ai_move = self.ai.get_best_move(self.board, self.config.board_size)
    
    def _execute_ai_move(self, row: int, col: int) -> None:
        if self.board[row][col] == 0 and self.state_manager.state == GameState.PLAYING:
            self.board[row][col] = self.current_player
            self.move_history.append((row, col))
            
            if self.sound_manager:
                self.sound_manager.play_place_sound()
            
            win_line = self._check_win(row, col)
            if win_line:
                self.win_line = win_line
                self.winner = self.current_player
                self.state_manager.change_state(GameState.GAME_OVER)
                self.stats.record_game(self.winner, self.game_mode, self.difficulty)
                self.save_manager.save(self.config, self.stats)
                if self.sound_manager:
                    if self.winner == 2:
                        self.sound_manager.play_lose_sound()
                    else:
                        self.sound_manager.play_win_sound()
            elif len(self.move_history) == self.config.board_size * self.config.board_size:
                self.winner = 0
                self.state_manager.change_state(GameState.GAME_OVER)
                self.stats.record_game(0, self.game_mode, self.difficulty)
                self.save_manager.save(self.config, self.stats)
            else:
                self.current_player = 3 - self.current_player
    
    def _undo_move(self) -> None:
        if self.move_history and self.state_manager.state == GameState.PLAYING:
            row, col = self.move_history.pop()
            self.board[row][col] = 0
            self.current_player = 3 - self.current_player
            
            if self.game_mode == GameMode.PVE and self.move_history and self.current_player == 2:
                row, col = self.move_history.pop()
                self.board[row][col] = 0
                self.current_player = 3 - self.current_player
    
    def _check_win(self, row: int, col: int) -> List[Tuple[int, int]]:
        player = self.board[row][col]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            line = [(row, col)]
            
            r, c = row + dr, col + dc
            while 0 <= r < self.config.board_size and 0 <= c < self.config.board_size and self.board[r][c] == player:
                line.append((r, c))
                r += dr
                c += dc
            
            r, c = row - dr, col - dc
            while 0 <= r < self.config.board_size and 0 <= c < self.config.board_size and self.board[r][c] == player:
                line.append((r, c))
                r -= dr
                c -= dc
            
            if len(line) >= 5:
                return line
        
        return []
    
    def update(self, dt: float) -> None:
        self.update_animation()
        
        self.animation_offset += 1
        
        if self.particle_system:
            self.particle_system.update(dt)
            if random.random() < 0.1:
                self.particle_system.emit_background(self.config.window_width, self.config.window_height, 1)
        
        if self.state_manager.state == GameState.GAME_OVER:
            self.win_animation_frame += 1
        
        if self.ai_thinking:
            self.ai_think_timer += dt
            self.ai_animation_angle += 5
            
            if self.ai_think_timer >= self.ai_think_duration and self.ai_move:
                self.ai_thinking = False
                row, col = self.ai_move
                self._execute_ai_move(row, col)
        
        if self.is_entering:
            self.transition_alpha = max(0, self.transition_alpha - 10)
            if self.transition_alpha == 0:
                self.is_entering = False
        
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
    
    def render(self) -> None:
        self.screen.fill(self.config.theme_background)
        
        if self.particle_system:
            self.particle_system.render(self.screen)
        
        self._render_board()
        self._render_pieces()
        self._render_hover()
        self._render_win_line()
        self._render_status()
        self._render_ai_thinking()
        
        for button in self.buttons:
            button.render(self.screen, self.config)
        
        self.render_transition()
    
    def _render_ai_thinking(self) -> None:
        if self.ai_thinking:
            font = self.resource_manager.get_font('medium')
            text = "AI思考中..."
            text_surface = font.render(text, True, (100, 100, 100))
            text_rect = text_surface.get_rect(center=(self.config.window_width // 2, 60))
            self.screen.blit(text_surface, text_rect)
            
            center_x = text_rect.right + 20
            center_y = 60
            
            for i in range(3):
                angle = math.radians(self.ai_animation_angle + i * 120)
                x = center_x + math.cos(angle) * 12
                y = center_y + math.sin(angle) * 12
                
                alpha = int(150 + 100 * math.sin(self.ai_animation_angle * 0.1 + i))
                radius = 5
                
                surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(surf, (100, 100, 100, alpha), (radius + 2, radius + 2), radius)
                self.screen.blit(surf, (int(x - radius - 2), int(y - radius - 2)))
    
    def _render_board(self) -> None:
        board_size_px = (self.config.board_size - 1) * self.config.cell_size
        board_rect = pygame.Rect(
            self.board_offset_x - self.config.cell_size // 2,
            self.board_offset_y - self.config.cell_size // 2,
            board_size_px + self.config.cell_size,
            board_size_px + self.config.cell_size
        )
        pygame.draw.rect(self.screen, self.config.theme_board_bg, board_rect)
        
        for i in range(self.config.board_size):
            start_x = self.board_offset_x
            end_x = self.board_offset_x + board_size_px
            y = self.board_offset_y + i * self.config.cell_size
            pygame.draw.line(self.screen, self.config.theme_board_line, (start_x, y), (end_x, y), 1)
            
            start_y = self.board_offset_y
            end_y = self.board_offset_y + board_size_px
            x = self.board_offset_x + i * self.config.cell_size
            pygame.draw.line(self.screen, self.config.theme_board_line, (x, start_y), (x, end_y), 1)
        
        for row, col in self._get_star_points():
            if row < self.config.board_size and col < self.config.board_size:
                x, y = self._board_to_screen(row, col)
                pygame.draw.circle(self.screen, self.config.theme_board_line, (x, y), 4)
    
    def _render_pieces(self) -> None:
        for row in range(self.config.board_size):
            for col in range(self.config.board_size):
                if self.board[row][col] != 0:
                    self._render_piece(row, col, self.board[row][col])
        
        self._render_last_move()
    
    def _render_piece(self, row: int, col: int, player: int) -> None:
        x, y = self._board_to_screen(row, col)
        radius = self.config.cell_size // 2 - 3
        
        if player == 1:
            for i in range(radius, 0, -1):
                ratio = i / radius
                gray = int(20 + 60 * (1 - ratio))
                color = (gray, gray, gray)
                pygame.draw.circle(self.screen, color, (x, y), i)
            
            highlight_pos = (x - radius // 3, y - radius // 3)
            highlight_radius = radius // 4
            pygame.draw.circle(self.screen, (100, 100, 100), highlight_pos, highlight_radius)
        else:
            for i in range(radius, 0, -1):
                ratio = i / radius
                gray = int(250 - 30 * (1 - ratio))
                color = (gray, gray, gray)
                pygame.draw.circle(self.screen, color, (x, y), i)
            
            pygame.draw.circle(self.screen, (200, 200, 200), (x, y), radius, 1)
            
            highlight_pos = (x - radius // 3, y - radius // 3)
            highlight_radius = radius // 4
            pygame.draw.circle(self.screen, (255, 255, 255), highlight_pos, highlight_radius)
    
    def _render_last_move(self) -> None:
        if self.move_history:
            row, col = self.move_history[-1]
            x, y = self._board_to_screen(row, col)
            
            size = 8 + int(2 * math.sin(self.animation_offset * 0.15))
            pygame.draw.rect(self.screen, (255, 100, 100), 
                           (x - size // 2, y - size // 2, size, size), 2)
    
    def _render_hover(self) -> None:
        if self.hover_pos and self.state_manager.state == GameState.PLAYING:
            row, col = self.hover_pos
            if self.board[row][col] == 0:
                x, y = self._board_to_screen(row, col)
                radius = self.config.cell_size // 2 - 3
                
                alpha = 100 + int(50 * math.sin(self.animation_offset * 0.1))
                
                if self.current_player == 1:
                    color = (50, 50, 50)
                else:
                    color = (200, 200, 200)
                
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*color, alpha), (radius, radius), radius)
                self.screen.blit(surf, (x - radius, y - radius))
    
    def _render_win_line(self) -> None:
        if self.win_line and self.state_manager.state == GameState.GAME_OVER:
            alpha = int(150 + 100 * math.sin(self.win_animation_frame * 0.2))
            
            for row, col in self.win_line:
                x, y = self._board_to_screen(row, col)
                radius = self.config.cell_size // 2 + 3
                
                surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*self.config.theme_highlight, alpha), (radius + 5, radius + 5), radius, 4)
                self.screen.blit(surf, (x - radius - 5, y - radius - 5))
    
    def _render_status(self) -> None:
        font = self.resource_manager.get_font('medium')
        
        if self.state_manager.state == GameState.GAME_OVER:
            if self.winner == 1:
                text = "黑棋胜利！"
                color = (20, 20, 20)
            elif self.winner == 2:
                text = "白棋胜利！"
                color = (100, 100, 100)
            else:
                text = "平局！"
                color = (100, 100, 100)
        else:
            if self.current_player == 1:
                text = "黑棋回合"
                color = (20, 20, 20)
            else:
                text = "白棋回合"
                color = (100, 100, 100)
        
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(self.config.window_width // 2, 30))
        self.screen.blit(text_surface, text_rect)
        
        piece_x = text_rect.left - 25
        piece_y = 30
        pygame.draw.circle(self.screen, (20, 20, 20) if self.current_player == 1 else (250, 250, 250), 
                          (piece_x, piece_y), 12)
        pygame.draw.circle(self.screen, (150, 150, 150), (piece_x, piece_y), 12, 1)


class SettingsScene(BaseScene):
    BOARD_SIZES = [13, 15, 19]
    BOARD_SIZE_LABELS = ["13x13", "15x15", "19x19"]
    
    def __init__(self, screen: pygame.Surface, config: GameConfig,
                 resource_manager: ResourceManager, state_manager: GameStateManager,
                 save_manager: SaveManager, sound_manager: Optional['SoundManager'] = None):
        super().__init__(screen, config, resource_manager, state_manager, sound_manager)
        self.save_manager = save_manager
        self.buttons: List[Button] = []
        self.sliders: List[Slider] = []
        self.selectors: List[OptionSelector] = []
        self._create_ui()
    
    def _create_ui(self) -> None:
        font = self.resource_manager.get_font('medium')
        
        slider_width = 250
        slider_x = self.config.window_width // 2 - slider_width // 2
        
        self.sliders = []
        self.master_slider = Slider(
            pygame.Rect(slider_x, 170, slider_width, 20),
            0.0, 1.0, self.config.master_volume,
            "主音量", font, self.config
        )
        self.sliders.append(self.master_slider)
        
        self.music_slider = Slider(
            pygame.Rect(slider_x, 250, slider_width, 20),
            0.0, 1.0, self.config.music_volume,
            "音乐音量", font, self.config
        )
        self.sliders.append(self.music_slider)
        
        self.sfx_slider = Slider(
            pygame.Rect(slider_x, 330, slider_width, 20),
            0.0, 1.0, self.config.sfx_volume,
            "音效音量", font, self.config
        )
        self.sliders.append(self.sfx_slider)
        
        self.selectors = []
        current_size_index = self.BOARD_SIZES.index(self.config.board_size) if self.config.board_size in self.BOARD_SIZES else 1
        self.board_selector = OptionSelector(
            pygame.Rect(0, 420, self.config.window_width, 35),
            self.BOARD_SIZE_LABELS, current_size_index,
            "棋盘大小", font, self.config
        )
        self.selectors.append(self.board_selector)
        
        theme_labels = [THEMES[t]['name'] for t in ThemeType]
        current_theme = self.config.get_current_theme()
        theme_index = list(ThemeType).index(current_theme)
        self.theme_selector = OptionSelector(
            pygame.Rect(0, 500, self.config.window_width, 35),
            theme_labels, theme_index,
            "主题风格", font, self.config
        )
        self.selectors.append(self.theme_selector)
        
        button_width = 120
        button_height = 40
        button_y = self.config.window_height - 80
        
        self.buttons = []
        back_button = Button(
            pygame.Rect((self.config.window_width - button_width) // 2, button_y, button_width, button_height),
            "返回", font, config=self.config
        )
        back_button.action = "back"
        self.buttons.append(back_button)
    
    def enter(self, data: Optional[Dict[str, Any]] = None) -> None:
        self.is_entering = True
        self.transition_alpha = 255
        self._create_ui()
    
    def exit(self) -> None:
        self.is_exiting = True
        self.transition_alpha = 0
    
    def handle_event(self, event: pygame.event.Event) -> None:
        for slider in self.sliders:
            if slider.handle_event(event):
                self._apply_settings()
                return
        
        for selector in self.selectors:
            if selector.handle_event(event):
                self._apply_settings()
                return
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.is_clicked(event.pos):
                    self._handle_button_click(button)
                    break
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state_manager.change_state(GameState.MENU)
    
    def _apply_settings(self) -> None:
        self.config.master_volume = self.master_slider.value
        self.config.music_volume = self.music_slider.value
        self.config.sfx_volume = self.sfx_slider.value
        
        if self.sound_manager:
            self.sound_manager.set_master_volume(self.config.master_volume)
            self.sound_manager.set_music_volume(self.config.music_volume)
            self.sound_manager.set_sfx_volume(self.config.sfx_volume)
        
        new_board_size = self.BOARD_SIZES[self.board_selector.selected_index]
        if new_board_size != self.config.board_size:
            self.config.board_size = new_board_size
        
        new_theme = list(ThemeType)[self.theme_selector.selected_index]
        self.config.apply_theme(new_theme)
        
        self._create_ui()
        
        self.save_manager.save(self.config, GameStats())
    
    def _handle_button_click(self, button: Button) -> None:
        action = getattr(button, 'action', '')
        if action == "back":
            self.state_manager.change_state(GameState.MENU)
    
    def update(self, dt: float) -> None:
        self.update_animation()
        
        if self.is_entering:
            self.transition_alpha = max(0, self.transition_alpha - 10)
            if self.transition_alpha == 0:
                self.is_entering = False
        
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
    
    def render(self) -> None:
        self.screen.fill(self.config.theme_background)
        
        self._render_title()
        
        for slider in self.sliders:
            slider.render(self.screen)
        
        for selector in self.selectors:
            selector.render(self.screen)
        
        for button in self.buttons:
            button.render(self.screen, self.config)
        
        self.render_transition()
    
    def _render_title(self) -> None:
        title_font = self.resource_manager.get_font('large')
        title_text = "游戏设置"
        title_surface = title_font.render(title_text, True, self.config.theme_text)
        title_rect = title_surface.get_rect(center=(self.config.window_width // 2, 80))
        self.screen.blit(title_surface, title_rect)
        
        small_font = self.resource_manager.get_font('tiny')
        hint_text = "拖动滑块或点击选项进行设置"
        hint_surface = small_font.render(hint_text, True, self.config.theme_primary)
        hint_rect = hint_surface.get_rect(center=(self.config.window_width // 2, 115))
        self.screen.blit(hint_surface, hint_rect)


class StatsScene(BaseScene):
    def __init__(self, screen: pygame.Surface, config: GameConfig,
                 resource_manager: ResourceManager, state_manager: GameStateManager,
                 stats: GameStats, save_manager: SaveManager,
                 sound_manager: Optional['SoundManager'] = None):
        super().__init__(screen, config, resource_manager, state_manager, sound_manager)
        self.stats = stats
        self.save_manager = save_manager
        self.buttons: List[Button] = []
        self.confirm_dialog = ConfirmDialog(
            screen, config, resource_manager,
            "确认重置", "确定要清除所有统计数据吗？"
        )
        self._create_ui()
    
    def _create_ui(self) -> None:
        font = self.resource_manager.get_font('medium')
        
        button_width = 120
        button_height = 40
        button_y = self.config.window_height - 80
        
        self.buttons = []
        
        reset_button = Button(
            pygame.Rect((self.config.window_width - button_width) // 2, button_y - 60, button_width, button_height),
            "重置统计", font, color=(180, 80, 80), hover_color=(200, 100, 100)
        )
        reset_button.action = "reset"
        self.buttons.append(reset_button)
        
        back_button = Button(
            pygame.Rect((self.config.window_width - button_width) // 2, button_y, button_width, button_height),
            "返回", font, config=self.config
        )
        back_button.action = "back"
        self.buttons.append(back_button)
    
    def enter(self, data: Optional[Dict[str, Any]] = None) -> None:
        self.is_entering = True
        self.transition_alpha = 255
        self._create_ui()
    
    def exit(self) -> None:
        self.is_exiting = True
        self.transition_alpha = 0
    
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.confirm_dialog.visible:
            result = self.confirm_dialog.handle_event(event)
            if result is True:
                self.stats.reset()
                self.save_manager.save(self.config, self.stats)
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.is_clicked(event.pos):
                    if self.sound_manager:
                        self.sound_manager.play_click_sound()
                    self._handle_button_click(button)
                    break
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state_manager.change_state(GameState.MENU)
    
    def _handle_button_click(self, button: Button) -> None:
        action = getattr(button, 'action', '')
        if action == "back":
            self.state_manager.change_state(GameState.MENU)
        elif action == "reset":
            self.confirm_dialog.show()
    
    def update(self, dt: float) -> None:
        self.update_animation()
        
        if self.is_entering:
            self.transition_alpha = max(0, self.transition_alpha - 10)
            if self.transition_alpha == 0:
                self.is_entering = False
        
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
        
        self.confirm_dialog.update()
    
    def render(self) -> None:
        self.screen.fill(self.config.theme_background)
        
        self._render_title()
        self._render_stats()
        
        for button in self.buttons:
            button.render(self.screen, self.config)
        
        self.confirm_dialog.render()
        self.render_transition()
    
    def _render_title(self) -> None:
        title_font = self.resource_manager.get_font('large')
        title_text = "游戏统计"
        title_surface = title_font.render(title_text, True, self.config.theme_text)
        title_rect = title_surface.get_rect(center=(self.config.window_width // 2, 45))
        self.screen.blit(title_surface, title_rect)
    
    def _render_stats(self) -> None:
        font = self.resource_manager.get_font('medium')
        small_font = self.resource_manager.get_font('small')
        tiny_font = self.resource_manager.get_font('tiny')
        
        left_x = 100
        right_x = self.config.window_width - 100
        center_x = self.config.window_width // 2
        
        pygame.draw.line(self.screen, self.config.theme_primary, 
                        (center_x, 80), (center_x, self.config.window_height - 150), 2)
        
        self._render_section_title(small_font, "总体统计", left_x + 20, 85)
        self._render_stat_item(font, small_font, "总对局数", str(self.stats.total_games), left_x + 30, 115)
        self._render_stat_item(font, small_font, "黑棋胜场", str(self.stats.black_wins), left_x + 30, 145)
        self._render_stat_item(font, small_font, "白棋胜场", str(self.stats.white_wins), left_x + 30, 175)
        self._render_stat_item(font, small_font, "平局数", str(self.stats.draws), left_x + 30, 205)
        
        win_rate = self.stats.get_win_rate()
        win_rate_color = (50, 150, 50) if win_rate >= 50 else (150, 50, 50)
        self._render_stat_item(font, small_font, "总体胜率", f"{win_rate:.1f}%", left_x + 30, 235, win_rate_color)
        
        self._render_section_title(small_font, "连胜记录", left_x + 20, 275)
        self._render_stat_item(font, small_font, "最长连胜", str(self.stats.longest_win_streak), left_x + 30, 305)
        self._render_stat_item(font, small_font, "当前连胜", str(self.stats.current_win_streak), left_x + 30, 335)
        
        self._render_section_title(small_font, "双人对战", right_x - 180, 85)
        self._render_stat_item(font, small_font, "总对局", str(self.stats.pvp_games), right_x - 170, 115)
        self._render_stat_item(font, small_font, "黑棋胜", str(self.stats.pvp_black_wins), right_x - 170, 145)
        self._render_stat_item(font, small_font, "白棋胜", str(self.stats.pvp_white_wins), right_x - 170, 175)
        
        self._render_section_title(small_font, "人机对战", right_x - 180, 215)
        self._render_stat_item(font, small_font, "总对局", str(self.stats.pve_games), right_x - 170, 245)
        
        pve_win_rate = self.stats.get_pve_win_rate()
        pve_rate_color = (50, 150, 50) if pve_win_rate >= 50 else (150, 50, 50)
        self._render_stat_item(font, small_font, "胜率", f"{pve_win_rate:.1f}%", right_x - 170, 275, pve_rate_color)
        
        self._render_section_title(small_font, "难度统计", right_x - 180, 315)
        
        easy_rate = (self.stats.pve_easy_wins / self.stats.pve_easy_games * 100) if self.stats.pve_easy_games > 0 else 0
        self._render_stat_item(tiny_font, tiny_font, f"简单 {self.stats.pve_easy_games}局 胜{self.stats.pve_easy_wins}", 
                              f"{easy_rate:.0f}%", right_x - 170, 345, (100, 180, 100))
        
        medium_rate = (self.stats.pve_medium_wins / self.stats.pve_medium_games * 100) if self.stats.pve_medium_games > 0 else 0
        self._render_stat_item(tiny_font, tiny_font, f"中等 {self.stats.pve_medium_games}局 胜{self.stats.pve_medium_wins}", 
                              f"{medium_rate:.0f}%", right_x - 170, 370, (180, 150, 50))
        
        hard_rate = (self.stats.pve_hard_wins / self.stats.pve_hard_games * 100) if self.stats.pve_hard_games > 0 else 0
        self._render_stat_item(tiny_font, tiny_font, f"困难 {self.stats.pve_hard_games}局 胜{self.stats.pve_hard_wins}", 
                              f"{hard_rate:.0f}%", right_x - 170, 395, (180, 80, 80))
    
    def _render_section_title(self, font: pygame.font.Font, title: str, x: int, y: int) -> None:
        title_surface = font.render(title, True, self.config.theme_primary)
        self.screen.blit(title_surface, (x, y))
        
        pygame.draw.line(self.screen, self.config.theme_secondary,
                        (x, y + 22), (x + 150, y + 22), 1)
    
    def _render_stat_item(self, value_font: pygame.font.Font, label_font: pygame.font.Font,
                          label: str, value: str, x: int, y: int, 
                          value_color: Tuple[int, int, int] = None) -> None:
        label_surface = label_font.render(label, True, self.config.theme_text)
        self.screen.blit(label_surface, (x, y))
        
        color = value_color if value_color else self.config.theme_primary
        value_surface = value_font.render(value, True, color)
        self.screen.blit(value_surface, (x + 100, y))


class SceneManager:
    def __init__(self, screen: pygame.Surface, config: GameConfig,
                 resource_manager: ResourceManager, state_manager: GameStateManager,
                 stats: GameStats, save_manager: SaveManager, sound_manager: 'SoundManager'):
        self.screen = screen
        self.config = config
        self.resource_manager = resource_manager
        self.state_manager = state_manager
        self.stats = stats
        self.save_manager = save_manager
        self.sound_manager = sound_manager
        
        self._scenes: Dict[GameState, BaseScene] = {}
        self._current_scene: Optional[BaseScene] = None
        
        self._create_scenes()
    
    def _create_scenes(self) -> None:
        self._scenes[GameState.MENU] = MenuScene(
            self.screen, self.config, self.resource_manager, self.state_manager,
            self.sound_manager
        )
        
        self._scenes[GameState.PLAYING] = GameScene(
            self.screen, self.config, self.resource_manager, self.state_manager,
            self.stats, self.save_manager, self.sound_manager
        )
        
        self._scenes[GameState.SETTINGS] = SettingsScene(
            self.screen, self.config, self.resource_manager, self.state_manager,
            self.save_manager, self.sound_manager
        )
        
        self._scenes[GameState.STATS] = StatsScene(
            self.screen, self.config, self.resource_manager, self.state_manager,
            self.stats, self.save_manager, self.sound_manager
        )
        
        self._scenes[GameState.GAME_OVER] = self._scenes[GameState.PLAYING]
    
    def get_current_scene(self) -> Optional[BaseScene]:
        current_state = self.state_manager.state
        if current_state in self._scenes:
            return self._scenes[current_state]
        return None
    
    def change_scene(self, new_state: GameState, data: Optional[Dict[str, Any]] = None) -> None:
        if self._current_scene:
            self._current_scene.exit()
        
        self.state_manager.change_state(new_state, data)
        
        self._current_scene = self.get_current_scene()
        if self._current_scene:
            self._current_scene.enter(data)
    
    def handle_event(self, event: pygame.event.Event) -> None:
        if self._current_scene:
            self._current_scene.handle_event(event)
    
    def update(self, dt: float) -> None:
        current_state = self.state_manager.state
        
        if self._current_scene and isinstance(self._current_scene, MenuScene):
            if current_state != GameState.MENU:
                self._current_scene = self.get_current_scene()
                if self._current_scene:
                    self._current_scene.enter(self.state_manager._state_data)
        
        if self._current_scene:
            self._current_scene.update(dt)
    
    def render(self) -> None:
        if self._current_scene:
            self._current_scene.render()


class GomokuGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        self.config = GameConfig()
        self.stats = GameStats()
        self.save_manager = SaveManager()
        
        self.save_manager.apply_loaded_data(self.config, self.stats)
        
        self.screen = pygame.display.set_mode(
            (self.config.window_width, self.config.window_height)
        )
        pygame.display.set_caption(self.config.window_title)
        
        self.resource_manager = ResourceManager()
        self.resource_manager.load_resources()
        
        self.sound_manager = SoundManager()
        self.sound_manager.set_master_volume(self.config.master_volume)
        self.sound_manager.set_music_volume(self.config.music_volume)
        self.sound_manager.set_sfx_volume(self.config.sfx_volume)
        
        self.state_manager = GameStateManager()
        self.scene_manager = SceneManager(
            self.screen, self.config, self.resource_manager, self.state_manager,
            self.stats, self.save_manager, self.sound_manager
        )
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.scene_manager.change_scene(GameState.MENU)
    
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(self.config.fps) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene_manager.handle_event(event)
            
            self.scene_manager.update(dt)
            self.scene_manager.render()
            
            pygame.display.flip()
        
        self._cleanup()
    
    def _cleanup(self) -> None:
        self.save_manager.save(self.config, self.stats)
        self.resource_manager.cleanup()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = GomokuGame()
    game.run()
