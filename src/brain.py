import torch
import torch.nn as nn
import numpy as np 
from src.config import *

class BrainNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(BRAIN_INPUT_DIM,BRAIN_HIDDEN_DIM),
            nn.Tanh(),
            nn.Linear(BRAIN_HIDDEN_DIM, BRAIN_OUTPUT_DIM),
            nn.Tanh(),
        )
    def forward(self,x):
        return self.net(x)
    
class SharedBrain:
    def __init__(self):
        self.network = BrainNetwork()
        self.optimizer = torch.optim.Adam(
            self.network.parameters(), lr=BRAIN_LEARNING_RATE
        )
        self.log_probs =[]
        self.rewards =[]
    def act(self,obs):
        x= torch.tensor(obs,dtype=torch.float32)
        raw= self.network(x)
        noise=torch.randn_like(raw)*0.1
        action=torch.clamp(raw + noise, -1.0, 1.0)
        log_prob=-0.5 * ((action - raw)**2).sum()
        return action.detach().numpy(), log_prob
    
    def record(self,log_prob,reward):
        if log_prob is not None:
            self.log_probs.append(log_prob)
            self.rewards.append(reward)
    
    def update(self):
        if len(self.rewards) ==0:
            return
        returns = []
        R = 0 
        for r in reversed(self.rewards):
            R = r + BRAIN_GAMMA * R
            returns.insert(0,R)
        returns = torch.tensor(returns, dtype=torch.float32)
        if returns.std() > 1e-5:
            returns=(returns-returns.mean())/(returns.std()+1e-8)
        loss = sum(-lp * R for lp, R in zip(self.log_probs, returns))
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        self.log_probs=[]
        self.rewards=[]

    def save(self):
        return {
            "weights": {k: v.tolist() for k, v in self.network.state_dict().items()}
        }
    def load(self,data):
        state_dict = {k:torch.tensor(v) for k , v in data ["weights"].items()}
        self.network.load_state_dict(state_dict)
    
def build_observation(creature, world , creatures):
    food_dx, food_dy, food_dist= 0.0,0.0,1.0
    if world.food:
        dist= sorted(
            (np.sqrt((fx - creature.x)**2 + (fy-creature.y)**2), fx,fy)
            for fx , fy in world.food
        )
        dist, fx , fy = dist[0]
        dist = max(dist,1e-5)
        food_dx = (fx - creature.x)/ dist
        food_dy = (fy - creature.y)/ dist
        food_dist = min(dist/max(creature.vision, 1e-5),1.0)

    biome = world.get_biome(creature.x, creature.y)
    biome_oh = [0.0,0.0,0.0,0.0]
    biome_oh[biome]= 1.0

    cx_dir,cy_dir, nearby_count = 0.0,0.0,0.0
    alive_others= [c for c in creatures if c.alive and c.id != creature.id]
    if alive_others:
        cdists = sorted(
            (np.sqrt((c.x -creature.x)**2+(c.y-creature.y)**2),c)
            for c in alive_others
        )
        nearest_d,nearest = cdists[0]
        nearest_d = max(nearest_d,1e-5)
        cx_dir=(nearest.x - creature.x)/ nearest_d
        cy_dir = (nearest.y-creature.y)/ nearest_d
        nearby_count = sum(1 for d, _ in cdists if d < creature.vision)/10.0
    
    obs = [
        food_dx, food_dy,food_dist,
        creature.energy/100.0,
        biome_oh[0], biome_oh[1], biome_oh[2], biome_oh[3],
        cx_dir, cy_dir,
        nearby_count,
    ]
    return np.array(obs, dtype=np.float32)



    