
import logging
from copy import deepcopy
from gymnasium.spaces import Space
from abc import ABC,  abstractmethod
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class RL_Base(ABC):
    def __init__(self, **kwargs):

        # self.training = True
        # self.spaces = Space()
        # self.action_space = None
        # self.observation_space = None
        # self.observations = []
        # self.actions = []
        # self.reward = []
        pass


    def get_observations(self):
        pass


    def predict_actions(self):
        pass


    def estimate_reward(self):
        pass


    def update_agent(self):
        pass


    def update_replay_memory(self):
        pass

    def check_training(self):
        pass


    def memory_buffer(self):
        pass

    def train(self):
        pass