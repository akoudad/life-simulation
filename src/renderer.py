import pygame
from src.config import *


class Renderer:
    def __init__(self):
        pygame.init()
        self.win_w = WORLD_WIDTH * CELL_SIZE
        self.win_h = WORLD_HEIGHT * CELL_SIZE + STATS_HEIGHT
        self.screen = pygame.display.set_mode((self.win_w, self.win_h))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 14)

    def draw(self, world, creatures):
        self.screen.fill((0, 0, 0))

        for y in range(world.height):
            for x in range(world.width):
                biome = world.biome_map[y, x]
                color = BIOME_COLORS[biome]
                rect = (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, color, rect)

        for fx, fy in world.food:
            px = int(fx * CELL_SIZE + CELL_SIZE / 2)
            py = int(fy * CELL_SIZE + CELL_SIZE / 2)
            pygame.draw.circle(self.screen, (100, 220, 80), (px, py), 2)


        for mx, my in world.mushrooms:
            px = int(mx*CELL_SIZE + CELL_SIZE / 2)
            py = int(my*CELL_SIZE + CELL_SIZE / 2)
            glow = pygame.Surface((20,20),pygame.SRCALPHA)
            pygame.draw.circle(glow,(180,0,255,60),(10,10),10)
            self.screen.blit(glow,(px-10,py-10))
            pygame.draw.circle(self.screen,(200,0,255),(px,py),3)



        for c in creatures:
            if not c.alive:
                continue
            px = int(c.x * CELL_SIZE + CELL_SIZE / 2)
            py = int(c.y * CELL_SIZE + CELL_SIZE / 2)
            radius = max(2, int(c.size * 2.5))
            r = int(c.aggression * 255)
            b = int((1 - c.aggression) * 255)
            g = 50
            color = (r, g, b)
            pygame.draw.circle(self.screen, color, (px, py), radius)
            if c.iq>0:
                ring_color= (255,165,0) if c.hallucination_steps>0 else(255,255,255)
                ring_width=max(1,int(c.iq*3))
                pygame.draw.circle(self.screen,ring_color,(px,py),radius+3,ring_width)
            elif c.energy > 50:
                glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255,255,200,40), (radius * 2, radius * 2), radius * 2)
                self.screen.blit(glow_surf, (px - radius * 2, py - radius * 2))

        stats_y = WORLD_HEIGHT * CELL_SIZE
        pygame.draw.rect(self.screen, (15, 15, 15), (0, stats_y, self.win_w, STATS_HEIGHT))
        alive = sum(1 for c in creatures if c.alive)
        smart = sum(1 for c in creatures if c.alive and c.iq>0)
        avg_iq=(sum(c.iq for c in creatures if c.alive and c.iq>0)/smart if smart>0 else 0.0)
        food_count = len(world.food)
        mushroom_count= len(world.mushrooms)
        text = (f"Step: {world.timestep}  |  "
                f"Alive: {alive}  |  "
                f"Smart: {smart}  |  "
                f"Avg IQ: {avg_iq:.2f}  |  "
                f"Food: {len(world.food)}  |  "
                f"Shrooms: {len(world.mushrooms)}  |  "
                f"Born: {len(creatures)}")
        surf = self.font.render(text, True, (180, 180, 180))
        self.screen.blit(surf, (10, stats_y + 12))
        pygame.display.flip()
        self.clock.tick(FPS)

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
