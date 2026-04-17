import math
import collections
import numpy as np
import pygame
from src.config import *


class Renderer:
    def __init__(self):
        pygame.init()
        self.world_px_w = WORLD_WIDTH * CELL_SIZE
        self.world_px_h = WORLD_HEIGHT * CELL_SIZE
        self.win_w = self.world_px_w
        self.win_h = self.world_px_h + STATS_HEIGHT
        self.screen = pygame.display.set_mode((self.win_w, self.win_h))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.font_lbl = pygame.font.SysFont("menlo", 11)    # NEW: small label font
        self.font_val = pygame.font.SysFont("menlo", 15, bold=True)  # NEW: value font
        self.biome_surface = None                            # NEW: cached biome bg
        self.pop_history = collections.deque(maxlen=300)     # NEW: sparkline data

    # NEW: precompute biome texture once — avoids redrawing 16k rects per frame
    def _build_biome_surface(self, world):
        surf = pygame.Surface((self.world_px_w, self.world_px_h))
        rng = np.random.default_rng(42)
        for y in range(world.height):
            for x in range(world.width):
                biome = world.biome_map[y, x]
                base = BIOME_COLORS[biome]
                v = int(rng.integers(-10, 11))  # per-cell shade variation
                color = tuple(int(np.clip(c + v, 0, 255)) for c in base)
                rect = (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surf, color, rect)
        return surf

    def draw(self, world, creatures):
        # NEW: lazy-build biome texture on first frame
        if self.biome_surface is None:
            self.biome_surface = self._build_biome_surface(world)

        self.screen.blit(self.biome_surface, (0, 0))  # CHANGED: cached bg instead of loop

        # Food — small green dot
        for fx, fy in world.food:
            px = int(fx * CELL_SIZE + CELL_SIZE / 2)
            py = int(fy * CELL_SIZE + CELL_SIZE / 2)
            pygame.draw.circle(self.screen, (120, 230, 100), (px, py), 2)

        # NEW: pulsing mushrooms — two-layer glow + center dot
        pulse = 0.5 + 0.5 * math.sin(world.timestep * 0.15)
        for mx, my in world.mushrooms:
            px = int(mx * CELL_SIZE + CELL_SIZE / 2)
            py = int(my * CELL_SIZE + CELL_SIZE / 2)
            outer_r = int(14 + pulse * 4)
            inner_r = int(6 + pulse * 2)
            outer = pygame.Surface((outer_r * 2, outer_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(outer, (180, 60, 255, 50), (outer_r, outer_r), outer_r)
            self.screen.blit(outer, (px - outer_r, py - outer_r))
            inner = pygame.Surface((inner_r * 2, inner_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(inner, (220, 120, 255, 110), (inner_r, inner_r), inner_r)
            self.screen.blit(inner, (px - inner_r, py - inner_r))
            pygame.draw.circle(self.screen, (230, 180, 255), (px, py), 3)

        # Creatures — pro look: outlined, energy bar, IQ ring
        for c in creatures:
            if not c.alive:
                continue
            px = int(c.x * CELL_SIZE + CELL_SIZE / 2)
            py = int(c.y * CELL_SIZE + CELL_SIZE / 2)
            radius = max(3, int(c.size * 3))                      # CHANGED: bigger
            r = int(c.aggression * 220 + 30)
            b = int((1 - c.aggression) * 220 + 30)
            color = (r, 60, b)

            pygame.draw.circle(self.screen, color, (px, py), radius)
            pygame.draw.circle(self.screen, (0, 0, 0), (px, py), radius, 1)  # NEW: outline

            # IQ ring — white normal, orange when hallucinating
            if c.iq > 0:
                ring_color = (255, 150, 40) if c.hallucination_steps > 0 else (235, 235, 255)
                ring_width = max(1, int(c.iq * 3))
                pygame.draw.circle(self.screen, ring_color, (px, py),
                                   radius + 3, ring_width)

            # NEW: energy bar above creature
            bar_w = radius * 2
            bar_h = 2
            bar_x = px - radius
            bar_y = py - radius - 5
            pygame.draw.rect(self.screen, (25, 25, 30), (bar_x, bar_y, bar_w, bar_h))
            fill = int(bar_w * max(0.0, min(1.0, c.energy / 100.0)))
            if c.energy > 60:
                bar_color = (100, 220, 120)
            elif c.energy > 25:
                bar_color = (230, 190, 70)
            else:
                bar_color = (230, 80, 80)
            pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, fill, bar_h))

        # NEW: pro stats bar
        self._draw_stats_bar(world, creatures)

        pygame.display.flip()
        self.clock.tick(FPS)

    # NEW: separate method for stats bar
    def _draw_stats_bar(self, world, creatures):
        stats_y = self.world_px_h
        # dark bg
        pygame.draw.rect(self.screen, (16, 18, 24),
                         (0, stats_y, self.win_w, STATS_HEIGHT))
        # top accent line
        pygame.draw.rect(self.screen, (60, 90, 140),
                         (0, stats_y, self.win_w, 1))

        alive = sum(1 for c in creatures if c.alive)
        smart = sum(1 for c in creatures if c.alive and c.iq > 0)
        halluc = sum(1 for c in creatures if c.alive and c.hallucination_steps > 0)
        avg_iq = (sum(c.iq for c in creatures if c.alive and c.iq > 0) / smart
                  if smart else 0.0)

        self.pop_history.append(alive)

        metrics = [
            ("STEP",    f"{world.timestep}",          (180, 180, 190)),
            ("ALIVE",   f"{alive}",                    (120, 220, 140)),
            ("SMART",   f"{smart}",                    (170, 190, 255)),
            ("AVG IQ",  f"{avg_iq:.2f}",               (200, 160, 255)),
            ("HALLUC",  f"{halluc}",                   (255, 150, 40)),
            ("FOOD",    f"{len(world.food)}",          (130, 200, 110)),
            ("SHROOM",  f"{len(world.mushrooms)}",     (220, 120, 220)),
            ("BORN",    f"{len(creatures)}",           (200, 200, 200)),
        ]

        x = 12
        for label, value, color in metrics:
            lbl = self.font_lbl.render(label, True, (110, 115, 130))
            val = self.font_val.render(value, True, color)
            self.screen.blit(lbl, (x, stats_y + 8))
            self.screen.blit(val, (x, stats_y + 24))
            x += max(lbl.get_width(), val.get_width()) + 22

        # NEW: population sparkline on right side
        self._draw_sparkline(stats_y)

    # NEW: sparkline graph of alive count over last 300 steps
    def _draw_sparkline(self, stats_y):
        if len(self.pop_history) < 2:
            return
        graph_w = 220
        graph_h = STATS_HEIGHT - 20
        x0 = self.win_w - graph_w - 14
        y0 = stats_y + 10
        # faint backdrop
        pygame.draw.rect(self.screen, (24, 26, 34),
                         (x0, y0, graph_w, graph_h))
        max_v = max(self.pop_history) or 1
        n = len(self.pop_history)
        pts = []
        for i, v in enumerate(self.pop_history):
            px = x0 + int(i / max(n - 1, 1) * graph_w)
            py = y0 + graph_h - int(v / max_v * (graph_h - 4)) - 2
            pts.append((px, py))
        if len(pts) >= 2:
            pygame.draw.lines(self.screen, (100, 210, 140), False, pts, 2)
        # label
        lbl = self.font_lbl.render("POPULATION", True, (110, 115, 130))
        self.screen.blit(lbl, (x0, y0 - 9))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        return True

    def quit(self):
        pygame.quit()
