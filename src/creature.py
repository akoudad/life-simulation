import numpy as np
from src.config import *


class Creature:
    _next_id = 0

    def __init__(self, x, y, traits=None, parent1_id=None, parent2_id=None, iq=0.0):
        self.id = Creature._next_id
        Creature._next_id += 1
        self.x = float(x)
        self.y = float(y)
        self.energy = INITIAL_ENERGY
        self.age = 0
        self.alive = True
        self.parent1_id = parent1_id
        self.parent2_id = parent2_id
        self.reproduction_cooldown = 0
        self.iq = float(np.clip(iq, 0.0, 1.0))
        self.hallucination_steps = 0
        self.mushroom_cooldown = 0   # NEW: safe-dose cooldown
        self.brain_log_prob = None
        if traits is None:
            self.traits = self._random_traits()
        else:
            self.traits = traits

    def _random_traits(self):
        return {
            name: np.random.uniform(low, high)
            for name, (low, high) in TRAIT_RANGES.items()
        }

    @property
    def speed(self):
        return self.traits["speed"]

    @property
    def vision(self):
        return self.traits["vision"]

    @property
    def size(self):
        return self.traits["size"]

    @property
    def aggression(self):
        return self.traits["aggression"]

    @property
    def metabolism(self):
        return self.traits["metabolism"]

    @property
    def stamina(self):
        return self.traits["stamina"]

    def move_random(self, world):
        biome = world.get_biome(self.x, self.y)
        effective_speed = self.speed * BIOME_SPEED_MODIFIER[biome]
        dx = np.random.uniform(-1, 1) * effective_speed
        dy = np.random.uniform(-1, 1) * effective_speed
        self.x = np.clip(self.x + dx, 0, world.width - 1)
        self.y = np.clip(self.y + dy, 0, world.height - 1)
        distance = np.sqrt(dx**2 + dy**2)
        # Movement cost: distance * speed factor * biome difficulty
        biome_cost = BIOME_ENERGY_MODIFIER[biome]
        self.energy -= distance * 0.3 * biome_cost

    def move_smart(self, world, brain, creatures):
        from src.brain import build_observation
        obs = build_observation(self, world, creatures)
        action, log_prob = brain.act(obs)
        self.brain_log_prob = log_prob
        biome = world.get_biome(self.x, self.y)
        effective_speed = self.speed * BIOME_SPEED_MODIFIER[biome]
        dx = float(action[0]) * effective_speed
        dy = float(action[1]) * effective_speed
        self.x = np.clip(self.x + dx, 0, world.width - 1)
        self.y = np.clip(self.y + dy, 0, world.height - 1)
        distance = np.sqrt(dx**2 + dy**2)
        biome_cost = BIOME_ENERGY_MODIFIER[biome]
        self.energy -= distance * 0.3 * biome_cost

    def eat(self, world):
        if world.remove_food(self.x, self.y, radius=1.0):
            self.energy = min(100, self.energy + FOOD_ENERGY * self.metabolism)
            return True
        return False
    
    def eat_mushroom(self, world):
        if world.remove_mushroom(self.x, self.y):
            # CHANGED: overdose model — safe if cooldown passed AND iq<1.0
            if self.mushroom_cooldown == 0 and self.iq < 1.0:
                self.iq = min(1.0, self.iq + MUSHROOM_IQ_BOOST)
                self.mushroom_cooldown = MUSHROOM_COOLDOWN
            else:
                # overdose: too soon OR already maxed
                self.hallucination_steps += HALLUCINATION_STEPS
            return True
        return False

    def burn_energy(self, world):
        biome = world.get_biome(self.x, self.y)
        biome_cost = BIOME_ENERGY_MODIFIER[biome]
        base_cost = (0.2 * self.stamina + 0.1 * self.size + 0.05 * self.speed) * biome_cost
        if self.hallucination_steps > 0:          # NEW: hallucination extra drain
            base_cost += HALLUCINATION_ENERGY_DRAIN
        self.energy -= base_cost

    def step(self, world, brain=None, creatures=None):
        if not self.alive:
            return

        hallucinating = self.hallucination_steps > 0
        use_brain = (self.iq > 0 and brain is not None
                     and creatures is not None and not hallucinating)

        # NEW: iq is probability of using smart move vs random
        if use_brain and np.random.random() < self.iq:
            self.move_smart(world, brain, creatures)
        else:
            self.move_random(world)

        ate = self.eat(world)
        self.eat_mushroom(world)
        self.burn_energy(world)
        self.age += 1

        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1
        if self.hallucination_steps > 0:           # count down hallucination
            self.hallucination_steps -= 1
        if self.mushroom_cooldown > 0:             # NEW: tick mushroom cooldown
            self.mushroom_cooldown -= 1

        # NEW: richer reward signal replacing simple energy delta
        if self.iq > 0 and brain is not None:
            reward = REWARD_SURVIVE
            if ate:
                reward += REWARD_EAT
            if self.energy > 70:
                reward += REWARD_ENERGY_HIGH
            elif self.energy < 20:
                reward += PENALTY_LOW_ENERGY
            brain.record(self.brain_log_prob, reward)

        if self.energy <= 0:
            self.alive = False
            if self.iq > 0 and brain is not None:  # NEW: death penalty
                brain.record(self.brain_log_prob, PENALTY_DEATH)

    @staticmethod
    def reproduce(parent1, parent2):
        if (parent1.energy < REPRODUCTION_THRESHOLD or
                parent2.energy < REPRODUCTION_THRESHOLD):
            return None
        if parent1.reproduction_cooldown > 0 or parent2.reproduction_cooldown > 0:
            return None
        child_traits = {}
        for name in TRAIT_RANGES:
            if np.random.random() < 0.5:
                val = parent1.traits[name]
            else:
                val = parent2.traits[name]
            val += np.random.normal(0, MUTATION_RATE)
            low, high = TRAIT_RANGES[name]
            val = np.clip(val, low, high)
            child_traits[name] = val
        cx = (parent1.x + parent2.x) / 2
        cy = (parent1.y + parent2.y) / 2
        parent1.energy -= REPRODUCTION_COST
        parent2.energy -= REPRODUCTION_COST
        parent1.reproduction_cooldown = 50
        parent2.reproduction_cooldown = 50
        # CHANGED: child inherits avg iq of parents + small mutation (was has_brain)
        child_iq = float(np.clip(
            (parent1.iq + parent2.iq) / 2 + np.random.normal(0, IQ_MUTATION_STD),
            0.0, 1.0
        ))
        return Creature(cx, cy, traits=child_traits,
                        parent1_id=parent1.id, parent2_id=parent2.id,
                        iq=child_iq)