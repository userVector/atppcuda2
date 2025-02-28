# main.py
# runs the simulation

def debug():
    import os
    import sys
    current_file_path = os.path.abspath(__file__)
    current_directory = os.path.dirname(current_file_path)
    package_root_directory = os.path.dirname(os.path.dirname(current_directory))
    sys.path.append(package_root_directory)

try:
    import agent_torch
except:
    debug()
    import agent_torch

import argparse
from tqdm import trange

from agent_torch import Registry, Runner
from agent_torch.helpers import read_config, read_from_file, grid_network
from substeps import *
from helpers import *

from plot import Plot

import torch.optim as optim
import torch.nn.functional as F

print(':: execution started')

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help='path to yaml config file')
config_file = parser.parse_args().config

config = read_config(config_file)
metadata = config.get('simulation_metadata')
num_episodes = metadata.get('num_episodes')
num_steps_per_episode = metadata.get('num_steps_per_episode')
visualize = metadata.get('visualize')

registry = Registry()
registry.register(read_from_file, 'read_from_file', 'initialization')
registry.register(grid_network, 'grid', key='network')
registry.register(map_network, 'map', key='network')

runner = Runner(config, registry)
runner.init()

print(':: preparing simulation...')

#for name, param in runner.named_parameters():
#    if param.requires_grad:
#        print(f"Parameter '{name}' requires gradient and will be optimized.")

optimizer = optim.Adam(runner.parameters(), 
                lr=runner.config['simulation_metadata']['learning_params']['lr'], 
                betas=runner.config['simulation_metadata']['learning_params']['betas'])
scheduler = optim.lr_scheduler.ExponentialLR(optimizer, 
                runner.config['simulation_metadata']['learning_params']['lr_gamma'])

#visual = Plot(metadata.get('max_x'), metadata.get('max_y'))
for episode in trange(num_episodes, desc=':: running simulation'):
  #optimizer.zero_grad()
  runner.step(num_steps_per_episode)
  #visual.capture(runner.state)
  output = runner.state_trajectory[-1][-1]
  #x = output['agents']['prey']['nutritional_value'].to(metadata.get('device')) #['energy'] #
  #x = torch.tensor(output['agents']['prey']['nutritional_value'], requires_grad=True).to(metadata.get('device'))
  x = output['agents']['prey']['nutritional_value'].clone().detach().requires_grad_(True).to(metadata.get('device'))
  #print(x.shape)
  #print(x)
  #target = torch.from_numpy(np.full((x.shape), 32).astype(np.float32), requires_grad=True).to(metadata.get('device'))
  target = torch.full((x.shape), 32.0).to(metadata.get('device')) #, requires_grad=True
  loss = F.mse_loss(x, target)
  loss.backward()
  optimizer.step()
  scheduler.step()

print(':: execution completed')
