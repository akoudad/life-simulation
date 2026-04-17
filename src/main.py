import json
import os
import numpy as np
from src.config import *
from src.world import World
from src.creature import Creature
from src.renderer import Renderer
from src.brain import SharedBrain

SAVE_FILE = "save.json"


def spawn_initial_population(world):
    creatures = []
    for _ in range(INITIAL_POPULATION):
        x = np.random.uniform(0, world.width - 1)
        y = np.random.uniform(0, world.height - 1)
        creatures.append(Creature(x, y))
    return creatures


def try_reproduction(creatures,brain):
    alive = [c for c in creatures if c.alive]
    new_children = []
    for i, c1 in enumerate(alive):
        if c1.energy < REPRODUCTION_THRESHOLD or c1.reproduction_cooldown > 0:
            continue
        for c2 in alive[i + 1:]:
            if c2.energy < REPRODUCTION_THRESHOLD or c2.reproduction_cooldown > 0:
                continue
            dist = np.sqrt((c1.x - c2.x) ** 2 + (c1.y - c2.y) ** 2)
            if dist < 2.0:
                if np.random.random() < 0.02:
                    child = Creature.reproduce(c1, c2)
                    if child:
                        if c1.iq >0:
                            brain.record(c1.brain_log_prob, REWARD_REPRODUCE)
                        if c2.iq >0:
                            brain.record(c2.brain_log_prob, REWARD_REPRODUCE)
                        new_children.append(child)
                        break
    return new_children


def save_state(world, creatures, brain):
    state = {
        "timestep": world.timestep,
        "food": world.food,
        "mushrooms": world.mushrooms,
        "next_id": Creature._next_id,
        "brain": brain.save(),
        "creatures": [],
    }
    for c in creatures:
        state["creatures"].append({
            "id": c.id,
            "x": c.x,
            "y": c.y,
            "energy": c.energy,
            "age": c.age,
            "alive": c.alive,
            "traits": c.traits,
            "parent1_id": c.parent1_id,
            "parent2_id": c.parent2_id,
            "reproduction_cooldown": c.reproduction_cooldown,
            "iq": c.iq,
            "hallucination_steps": c.hallucination_steps,
            "mushroom_cooldown": c.mushroom_cooldown,   # NEW
        })

    with open(SAVE_FILE, "w") as f:
        json.dump(state, f)
    print(f"Saved at step {world.timestep} ({sum(1 for c in creatures if c.alive)} alive)")


def load_state(brain):
    if not os.path.exists(SAVE_FILE):
        return None, None
    with open(SAVE_FILE, "r") as f:
        state = json.load(f)
    world = World()
    world.timestep = state["timestep"]
    world.food = [tuple(f) for f in state["food"]]
    world.mushrooms = [tuple(m) for m in state.get("mushrooms", [])]
    Creature._next_id = state["next_id"]
    if "brain" in state:
        brain.load(state["brain"])
    creatures = []
    for cd in state["creatures"]:
        c = Creature(cd["x"], cd["y"], traits=cd["traits"],
                     parent1_id=cd["parent1_id"], parent2_id=cd["parent2_id"],iq=cd.get("iq",0.0))
        c.hallucination_steps = cd.get("hallucination_steps", 0)
        c.mushroom_cooldown = cd.get("mushroom_cooldown", 0)   # NEW
        c.id = cd["id"]
        c.energy = cd["energy"]
        c.age = cd["age"]
        c.alive = cd["alive"]
        c.reproduction_cooldown = cd.get("reproduction_cooldown", 0)
        creatures.append(c)
    print(f"Loaded step {world.timestep} ({sum(1 for c in creatures if c.alive)} alive)")
    return world, creatures

def save_history(world,creatures):
    import datetime
    alive = [c for c in creatures if c.alive]
    smart = [c for c in creatures if c.iq>0]
    alive_smart=[c for c in alive if c.iq>0]
    entry ={
        "extinct_step": world.timestep if not alive else None,
        "total_born": len(creatures),
        "max_iq": round(max((c.iq for c in creatures), default=0.0),3),
        "avg_iq_smart":round(
            sum(c.iq for c in smart)/ len(smart)if smart else 0.0,3),
        "brained_born":len(smart),
        "alive_at_end": len(alive),
        "date":str(datetime.date.today()),
    }
    with open(HISTORY_FILE,"a")as f:
        import json
        f.write(json.dumps(entry)+ "\n")
    print(f"History saved:{entry}")

def main():
    brain = SharedBrain()
    world, creatures = load_state(brain)
    if world is None:
        world = World()
        creatures = spawn_initial_population(world)
        for _ in range(50):
            world.spawn_food()

    renderer = Renderer()
    running = True
    extinct = False

    while running:
        running = renderer.handle_events()

        if extinct:
            renderer.draw(world, creatures)
            continue

        world.step()
        for creature in creatures:
            creature.step(world, brain=brain, creatures=creatures)
        children = try_reproduction(creatures,brain)
        creatures.extend(children)

        if world.timestep % BRAIN_UPDATE_INTERVAL ==0:
            brain.update()

        alive_count = sum(1 for c in creatures if c.alive)
        renderer.draw(world, creatures)

        if alive_count == 0:
            print(f"EXTINCTION at step {world.timestep}. Total born: {len(creatures)}.")
            save_history(world,creatures)
            extinct = True

    if not extinct:
        save_state(world, creatures, brain)
        save_history(world,creatures)

    renderer.quit()


if __name__ == "__main__":
    main()
