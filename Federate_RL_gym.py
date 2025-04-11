from venv import logger

import gymnasium as gym
from sympy import false
import logging
from FedBaseClass import FederateBase
import numpy as np
import sys
import os
from definitions import *
import pprint
pp = pprint.PrettyPrinter(indent=4)

from utils import read_yaml, save_json
from stable_baselines3 import SAC
import helics as h
import ast
from utils import setup_logger
import importlib.util

logger= setup_logger(__name__)

def parse_space(space_config):
    """
    Create a Gym space from a configuration dictionary.
    Supports 'Box', 'Discrete', and 'Dict' types.
    """
    space_type = space_config.get("type", "Box")

    if space_type == "Box":
        low = np.array([space_config.get("low", -np.inf)])
        high = np.array([space_config.get("high", np.inf)])
        # If shape is provided, use it; otherwise, infer it from low.
        shape = tuple(space_config.get("shape", low.shape))
        dtype = np.dtype(space_config.get("dtype", "float32"))
        return gym.spaces.Box(low=low, high=high, shape=(1,), dtype=dtype)

    elif space_type == "Discrete":
        n = int(space_config["n"])
        return gym.spaces.Discrete(n)

    elif space_type == "Dict":
        # Build a dictionary of sub-spaces.
        subspaces = {}
        for key, sub_config in space_config.get("spaces", {}).items():
            subspaces[key] = parse_space(sub_config)
        return gym.spaces.Dict(subspaces)

    else:
        raise ValueError(f"Unsupported space type: {space_type}")

class Env_fed(gym.Env, FederateBase):
    def __init__(self, args):
        super(Env_fed,self).__init__(args)
        self.config = read_yaml(os.path.join(FEDERATIONS_dir, args[2], args[1]))
        self.granted_period = 0
        #register federate
        #self.fed = self.register_federate()
        #register connections
        #self.inp_ids, self.pub_ids, self.end_ids = self.register_connections()

        #training_vars =
        self.episode_duration = self.config['fed_conf']['episode_period']/self.config['fed_conf']['sim_params']['real_period'] #number of steps
        self.number_episodes = self.config['fed_conf']['training_episodes'] #number of episodes
        self.time_step = 0
        self.episode = 0

        #create spaces
        # observations
        self.observation_space = parse_space(self.config["observation_space"])

        # actions
        self.action_space = parse_space(self.config["action_space"])


        #buffer for observations and actions and rewards beacuse of co-simulation nature
        self.action_buffer = []
        self.observation_buffer = []
        self.reward_buffer = []

        logger.debug(f"Federate RL instance variables: {pp.pformat(self.__dict__)}")
        h.helicsFederateEnterExecutingMode(self._fed)
        logger.debug(f"Federate RL instance variables: {pp.pformat(self.__dict__)}")
        self.memory = {'action':[], 'reward':[]}

    def get_observation_dummy(self):
        #todo need to understand how to get initial state from the rest will require a first publish by the other federates
        #get the observation from the federate
        # obs_dict = {}
        # for k, val in self.in_values.items():
        #     if k in self.observation_space.spaces.keys():
        #         obs_dict[k] = val
        self.obs_dict = self.observation_space.sample()
        self.obs_dict['day_night']=np.array([self.obs_dict['day_night']])
        return self.obs_dict

    def get_observation(self):
        self.prev_obs_dict = self.obs_dict
        self.obs_dict = {}
        for k, val in self.in_values[0].items():
            if k in self.observation_space.spaces.keys():
                self.obs_dict[k] = val
        #obs_dict['day_night']=np.array([obs_dict['day_night']])
        return self.obs_dict


    def reset(self,seed=None, options = None):
        super().reset(seed=seed)
        observations = self.get_observation_dummy()
        info= {}
        logger.debug(f"Observation dict at reset: {observations}")
        return observations, info

    def bufferize(self,action,observation,reward):
        self.action_buffer.append(action)
        self.observation_buffer.append(observation)
        self.reward_buffer.append(reward)

    def step(self, action):
        # publish the action received from the algo #todo this is hardcoded must be done in automatic depending on the actions
        pubid = self.pub_ids[0]['vent_q']
        h.helicsPublicationPublishDouble(pubid, action)
        logger.debug(f"Action published: {action}")

        #request time
        requested_period = self.granted_period + self.sim_period
        self.granted_period = h.helicsFederateRequestTime(self._fed, requested_period)
        logger.debug(
            f"************* Requesting time {requested_period} -- Granted time {self.granted_period} **************")

        #get the next observation - subscribe
        self._receive_inputs()  # update self.in_values class variable
        next_observation = self.get_observation()

        #get the reward
        reward = self.reward()

        #update memory not for algorithm but for plotting:
        self.memory['action'].append(action)
        self.memory['reward'].append(reward)
        #get the done flag
        self.time_step+=1
        done = False #set True at episode end
        if self.episode == self.episode_duration:
            self.time_step = 0
            self.episode+=1
            done = True

        info = {}
        return next_observation, reward, done, False, info


    def reward(self):
        beta = -0.1
        if self.obs_dict['t_set']<20:
            beta = -0.01
        reward = beta * (self.obs_dict['t_zone']-self.obs_dict['t_set'])**2
        return reward

    def close(self):
        pass





# def main(args):
#     env = Env_fed(args)
#     model = SAC("MultiInputPolicy", env, learning_rate=0.0003, buffer_size=1000000, learning_starts=100, batch_size=256,
#                 tau=0.005, gamma=0.99, train_freq=1, gradient_steps=1, action_noise=None, replay_buffer_class=None, replay_buffer_kwargs=None,
#                 optimize_memory_usage=False, ent_coef='auto', target_update_interval=1, target_entropy='auto', use_sde=False, sde_sample_freq=-1,
#                 use_sde_at_warmup=False, stats_window_size=100, tensorboard_log=None, policy_kwargs=None, verbose=1, seed=None, device='auto',
#                 _init_setup_model=True)
#     model.learn(total_timesteps=17520, callback=None, log_interval=4, tb_log_name='SAC', reset_num_timesteps=True, progress_bar=False)
#     model.save("best_model")
#
#     vec_env = model.get_env()
#     obs = vec_env.reset()
#     for i in range(720):
#         action, _states = model.predict(obs, deterministic=True)
#         obs, reward, done, info = vec_env.step(action)
#         # if done:
#         #     obs, info = env.reset()
#
#     env.save_fed_memory()
#     env.finalize()

if __name__ == '__main__':
    args = sys.argv
    env = Env_fed(args)



    # Path or name of the script (without .py extension)
    script_path = 'rl_main/'+args[-1] +'.py'
    module_name = os.path.splitext(os.path.basename(script_path))[0]

    # Load the module dynamically
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "main"):
        module.main(env)
    else:
        print(f"No main() function found in {script_path}")
    # Call the function
