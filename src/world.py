import numpy as np
from src.config import *


class World:
    def __init__(self):
        self.width = WORLD_WIDTH
        self.height = WORLD_HEIGHT
        self.biome_map = self._generate_biomes()
        self.food = []
        self.timestep = 0

    def _generate_biomes(self):
        grid = np.zeros((self.height, self.width), dtype=int)
        mid_x = self.width // 2
        mid_y = self.height // 2
        grid[:mid_y, :mid_x] = 0
        grid[:mid_y, mid_x:] = 1
        grid[mid_y:, :mid_x] = 2
        grid[mid_y:, mid_x:] = 3
        return grid

    def get_biome(self, x, y):
        gx = int(np.clip(x, 0, self.width - 1))
        gy = int(np.clip(y, 0, self.height - 1))
        return self.biome_map[gy, gx]

    def spawn_food(self):
        if len(self.food) >= MAX_FOOD:
            return
        for y in range(self.height):
            for x in range(self.width):
                biome = self.biome_map[y, x]
                rate = BIOME_FOOD_RATES[biome]
                if np.random.random() < rate * 0.01:
                    self.food.append((float(x), float(y)))
                    if len(self.food) >= MAX_FOOD:
                        return

    def remove_food(self, x, y, radius=1.0):
        for i, (fx, fy) in enumerate(self.food):
            if abs(fx - x) < radius and abs(fy - y) < radius:
                self.food.pop(i)
                return True
        return False

    def step(self):
        self.spawn_food()
        self.timestep += 1
