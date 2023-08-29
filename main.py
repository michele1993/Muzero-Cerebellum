import torch
import numpy as np
import logging
import gym
from env.hanoi import TowersOfHanoi
from Muzero import Muzero
from utils import setup_logger

def get_env(env_name):
    if env_name == 'Hanoi':
        N = 3 
        env = TowersOfHanoi(N)
        max_steps=200
        s_space_size = env.oneH_s_size 
        n_action = 6 # n. of action available in each state for Tower of Hanoi (including illegal ones)
        max_steps= max_steps
    else: # Use for gym env with discrete 1d action space        
        env = gym.make(env_name)
        assert isinstance(env.action_space,gym.spaces.discrete.Discrete), "Must be discrete action space"
        s_space_size = env.observation_space.shape[0]
        n_action = env.action_space.n
        max_steps = env.spec.max_episode_steps
    return env, s_space_size, n_action,  max_steps


## ======= Set seeds for debugging =======
s = 11 # seed
torch.manual_seed(s)
np.random.seed(s)
setup_logger(s)
## =======================

## ========= Useful variables: ===========
episodes = 10000
pre_training = 100
discount = 0.8
dirichlet_alpha = 0.25
n_ep_x_loop = 1#20
n_mcts_simulations = 25 #11 during acting n. of mcts passes for each step
n_update_x_loop = 1 #20
unroll_n_steps = 5
batch_s = 2000 #512
buffer_size = 50000 #int(1e6)
priority_replay = True
lr = 0.002
dev = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

env_n = 0
if env_n ==0:
    env_name = 'Hanoi' 
elif env_n == 1:
    env_name = "CartPole-v1" 

logging.info(f'Env: {env_name}, Episodes: {episodes}, Pretrain eps: {pre_training}, lr: {lr}, discount: {discount}, n. MCTS: {n_mcts_simulations}, batch size: {batch_s}, Priority Buff: {priority_replay}')

## ========= Initialise env ========
env, s_space_size, n_action, max_steps = get_env(env_name)
## ======== Initialise alg. ========
muzero = Muzero(env=env, s_space_size=s_space_size, n_action=n_action, max_steps=max_steps, discount=discount, dirichlet_alpha=dirichlet_alpha, n_mcts_simulations=n_mcts_simulations, unroll_n_steps=unroll_n_steps, batch_s=batch_s, lr=lr, buffer_size=buffer_size, priority_replay=priority_replay, device=dev, n_ep_x_loop=n_ep_x_loop, n_update_x_loop=n_update_x_loop)

## ======== Run training ==========
tot_acc = muzero.training_loop(episodes, pre_training)
