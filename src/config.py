WORLD_WIDTH = 128
WORLD_HEIGHT = 128
CELL_SIZE = 6

BIOME_COLORS = {
    0: (34, 85, 34),
    1: (194, 178, 128),
    2: (30, 60, 110),
    3: (90, 90, 90),
}

BIOME_FOOD_RATES = {
    0: 0.008,
    1: 0.002,
    2: 0.004,
    3: 0.001,
}

BIOME_VISION_MODIFIER = {
    0: 0.6,
    1: 1.4,
    2: 1.0,
    3: 1.6,
}

BIOME_SPEED_MODIFIER = {
    0: 1.0,
    1: 1.0,
    2: 0.5,
    3: 0.4,
}

BIOME_ENERGY_MODIFIER = {
    0: 1.0,   # forest: normal energy cost
    1: 1.2,   # desert: slightly harder
    2: 1.5,   # water: draining
    3: 2.0,   # mountain: very costly
}

INITIAL_POPULATION = 20
INITIAL_ENERGY = 80
REPRODUCTION_THRESHOLD = 70
REPRODUCTION_COST = 30
MUTATION_RATE = 0.1

TRAIT_RANGES = {
    "speed":      (0.5, 3.0),
    "vision":     (2.0, 8.0),
    "size":       (0.5, 3.0),
    "aggression": (0.0, 1.0),
    "metabolism":  (0.5, 2.0),
    "stamina":    (0.5, 2.0),
}

COMBAT_RANGE = 1.5
ENERGY_STEAL_RATIO = 0.5
COMBAT_COST = 2.0

FOOD_ENERGY = 15
MAX_FOOD = 600

FPS = 30
WINDOW_TITLE = "Life Simulation"
STATS_HEIGHT = 40
