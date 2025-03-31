import gymnasium as gym
from sympy import false

from FedBaseClass import FederateBase
import numpy as np
import sys
import os
from definitions import *

from utils import read_yaml, save_json
from stable_baselines3 import SAC
import helics as h


def parse_space(space_config):
    """
    Create a Gym space from a configuration dictionary.
    Supports 'Box', 'Discrete', and 'Dict' types.
    """
    space_type = space_config.get("type", "Box")

    if space_type == "Box":
        low = np.array(space_config.get("low", -np.inf))
        high = np.array(space_config.get("high", np.inf))
        # If shape is provided, use it; otherwise, infer it from low.
        shape = tuple(space_config.get("shape", low.shape))
        dtype = np.dtype(space_config.get("dtype", "float32"))
        return gym.spaces.Box(low=low, high=high, shape=shape, dtype=dtype)

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
        self.config = read_yaml(os.path.join(FEDERATIONS_dir, args[-1], args[-2]))

        #register federate
        #self.fed = self.register_federate()
        #register connections
        #self.inp_ids, self.pub_ids, self.end_ids = self.register_connections()

        #create spaces
        # observations
        self.observation_space = parse_space(self.config["observation_space"])

        # actions
        self.action_space = parse_space(self.config["action_space"])


        #buffer for observations and actions and rewards beacuse of co-simulation nature
        self.action_buffer = []
        self.observation_buffer = []
        self.reward_buffer = []


    def get_observation(self):
        #get the observation from the federate
        obs_dict = {}
        for k, val in self.in_values.items():
            if k in self.observation_space.spaces.keys():
                obs_dict[k] = val
        return obs_dict

    def reset(self):
        pass

    def bufferize(self,action,observation,reward):
        self.action_buffer.append(action)
        self.observation_buffer.append(observation)
        self.reward_buffer.append(reward)

    def step(self, action):
        # publish the action received from the algo
        h.helicsPublicationPublishDouble(self.action_pub, action)  # todo self.action_pub does not exist

        #request time
        requested_period = self.granted_period + self.sim_period
        self.granted_period = h.helicsFederateRequestTime(self._fed, requested_period)

        #get the next observation - subscribe
        self._receive_inputs()  # update self.in_values class variable
        next_observation = self.get_observation() #todo

        #get the reward
        reward = self.reward()

        #get the done flag
        done = False

        return next_observation, reward, done


    def reward(self):
        #TODO
        return 0
    def close(self):
        pass





def main(args):
    env = Env_fed(args)
    model = SAC("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=10000, log_interval=4)



    model.save("best_model")

    obs, info = env.reset()
    while True:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        if done:
            obs, info = env.reset()


if __name__ == '__main__':
    args = sys.argv
    main(args)