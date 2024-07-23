import math

from gymnasium.spaces import Discrete, Box, Dict

from models._baseModels.RL_Base import RL_Base
import random
import torch
import torch.nn.functional as F
import torch.nn as nn
import torch.optim as optim
from torch.distributions.normal import Normal
from collections import namedtuple, deque
import numpy as np
import logging
import pprint

pp = pprint.PrettyPrinter(indent=4)


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def normalize (x, min, max):
    return (x - min) / (max - min)
def denormalize (y, min, max):
    return (y *(max-min)) + min


# class ReplayMemory():
#     def __init__(self, memory_size: int) -> None:
#         self.memory_size = memory_size
#         self.buffer = deque([],maxlen=self.memory_size)
#
#     def add(self, experience) -> None:
#         self.buffer.append(experience)
#
#     def size(self):
#         return len(self.buffer)
#
#     def sample(self, batch_size: int, continuous: bool = True):
#         if batch_size > len(self.buffer):
#             batch_size = len(self.buffer)
#         if continuous:
#             rand = random.randint(0, len(self.buffer) - batch_size)
#             return [self.buffer[i] for i in range(rand, rand + batch_size)]
#         else:
#             indexes = np.random.choice(np.arange(len(self.buffer)), size=batch_size, replace=False)
#             return [self.buffer[i] for i in indexes]
#
#     def clear(self):
#         self.buffer.clear()





Transition = namedtuple('Transition',
                        ('observation_', 'action', 'observation', 'reward'))


class ReplayMemory(object):

    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        """Save a transition"""
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)



class QNetwork(nn.Module):
    def __init__(self, n_observations, n_actions):
        super(QNetwork, self).__init__()
        #todo define checkpoint file and understand for what is for
        self.create_model(n_observations, n_actions)

    def create_model(self, n_observations, n_actions):
        self.layer1 = nn.Linear(n_observations, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, n_actions)

    def forward(self, state):
        x = F.relu(self.layer1(state))
        x = F.relu(self.layer2(x))
        return self.layer3(x)


    # def chose_action(self, state):
    #     with torch.no_grad():
    #         Q = self.forward(state)
    #         action_index = torch.argmax(Q, dim=1)
    #     return action_index.item()

    # def fit(self,x,y):
    #
    #
    #     loss = F.mse_loss(onlineQNetwork(batch_state).gather(1, batch_action.long()), y)
    #     optimizer.zero_grad()
    #     loss.backward()
    #     optimizer.step()
    #
    # def save_checkpoint(self):
    #     torch.save(self.state_dict(), self.checkpoint_file)
    #
    # def load_checkpoint(self):
    #     self.load_state_dict(torch.load(self.checkpoint_file, map_location=torch.device('cpu')))



class DQN_Agent(RL_Base):
    # training vars
    # TRAIN = True  # flag to see if we are in training or testing phase
    # MAX_EPISODES = 365  # maximum number of update steps
    # UPDATE_STEPS = 24  # update target network every 24 hours
    # REPLAY_MEMORY = 15000  # size of the replay memory
    # BATCH = 32  # size of the batch used for training
    #
    # EXPLORE = 150000
    # INITIAL_EPSILON = 1
    # FINAL_EPSILON = 0.1
    # BATCH_SIZE = 24
    # GAMMA = 0.99
    #
    # # fore epsilon greedy exploration
    # EPS_START = 0.08 # initial value of epsilon # should be 0.9
    # EPS_END = 0.05 #final value of epsilon
    # EPS_DECAY = 1000 #decay rate of epsilon
    #
    # TAU = 0.005
    # LR = 1e-4


    def __init__(self, **kwargs):
            super().__init__(**kwargs)
            for k, val in kwargs.items():
                setattr(self,k,val)

            self.best_reward = 0
            self.best_param = None



            logger.debug(f"Model class variables from Base class: {pp.pformat(self.__dict__)}")

            self.memory = {"reward":[],
                            "cum_reward":[],
                           'eps_th':[]}

            self.cum_reward = []


            self.action_space = Discrete(7, start=0, seed=42)  # {-1, 0, 1 #todo should generalize from config using a class that based on a flag choose the right gym space
            self.actions = [-3,-2, -1, 0, 1, 2, 3]
            self.observation_space =  None #for now not using an observation space too complex Todo
            # define state space: 1-6. 6 indoor air temperature, 7-12. temperature setpoint, 13. 398C air temperature, 14. outdoor air temperature, 15. solar radiation, 16. time cos, 17. time sin
            # self.observation_space = Box(
            #     low=np.array([5, 5, 5, 5, 5, 5, 15, 15, 15, 15, 15, 15, 5, -20, 0, -1, -1], dtype=np.float32),
            #     high=np.array([35, 35, 35, 35, 35, 35, 25, 25, 25, 25, 25, 25, 35, 20, 400, 1, 1], dtype=np.float32),
            #     shape=(17,),
            #     dtype=np.float32
            # )

            logger.debug(f" Action_space number: {self.action_space.n}\n obs space number: ")

            self.n_actions = self.action_space.n # this only because we have discrete set of actions
            self.n_observations = len(self.observation_vars)

            self.observation = torch.tensor(np.array([0.0 for data in self.observation_vars])) # todo instead of 0.0 should use some initial values
            self.observation_ = torch.tensor(np.array([np.array([0.0]) for data in self.observation_vars]))
            self.reward = None
            self.action = torch.tensor([0])

            #replay memory
            self.replay_memory = ReplayMemory(self.REPLAY_MEMORY)

            self.policy_model = QNetwork(self.n_observations,self.n_actions)  # instance of Qnetwork
            self.target_model = QNetwork(self.n_observations,self.n_actions)  # insctance of Q network
            self.target_model.load_state_dict(self.policy_model.state_dict())


            # #use best_model
            # best= 'best_model_0.9'
            # self.policy_model.load_state_dict(torch.load(best))


            self.optimizer = optim.Adam(self.policy_model.parameters(), lr=float(self.LR), amsgrad=True)
            # self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=int(1e4), gamma=0.1)
            self.device = torch.device('cuda:1' if torch.cuda.is_available() else 'cpu')
            self.steps_done = 0


    def get_observations(self, obs_vars):
        self.observation_ = self.observation
        self.n_dict = {'drybulb':[-30,50], 'glohorzrad':[0,2000],'wind_speed':[0,100], 'setpoint':[15,26]} # todo generalize this normalization process
        obs_vars = {k:normalize(val,self.n_dict[k][0],self.n_dict[k][1]) for k,val in obs_vars.items()}
        #need to tranform obsvars data into a proper format to feed the neural network
        self.observation = torch.tensor([obs_vars[data] for data in obs_vars])
        logger.debug(f"OBSERVATION: {self.observation}")

    def update_replay_memory(self):
        state = self.observation_.reshape(1, -1).float()
        action = self.action.reshape(1,-1) # to be properly defined
        next_state = self.observation.reshape(1,-1).float()
        reward = self.reward.reshape(1,-1).float() # all of these must be copy of torch tensor
        transition = (state, action, next_state, reward)

        logger.debug(f"Updating the replay memory with the following information:\n"
                     f"state: {state } &&\n"
                     f"action: {action} &&\n"
                     f"next_state: {next_state} &&\n"
                     f"reward: {reward}&&\n"
                     f"organized in the following transition: {transition}!!!")


        self.replay_memory.push(*transition)

    def predict_action(self):
        sample = random.random()
        eps_threshold = self.EPS_END + (self.EPS_START - self.EPS_END) * math.exp(-1 * self.steps_done / self.EPS_DECAY)
        self.memory['eps_th'].append(eps_threshold)

        self.steps_done += 1 #should be reset at the end of every training episodes todo
        if sample > eps_threshold:
            with torch.no_grad():
                # state = torch.tensor(self.observation.reshape(1, -1))
                logger.debug(f"OBSERVATION state to be fed to NN: {self.observation}")

                #the network return the q value for all the actions (3 in this case -1, 0, +1) we have to pick the highest q valued and the corresponding action ans sum it to the scheduled tset
                Q = self.policy_model(self.observation)
                logger.debug(f"output of NN network: {Q}, type: {type(Q)}, dimension {Q.shape}")
                # logger.debug(f"Q value from neural network: {Q}")
                action_index = torch.argmax(Q).item() #todo check maybe is missing something
                # logger.debug(f"Action index after agrmax: {action_index}")
                action = self.actions[action_index]
                logger.debug(f"Action optimally chosen: {action}")


        else:
            action_index = self.action_space.sample()
            action = self.actions[action_index]

            logger.debug(f"Action casually chosen: {action}")


        # logger.debug(f"summing the observation set_point {self.observation[-1]} with the chosen action {action}")

        #this must be denormalized!!!! TODO
        self.action = torch.tensor(action_index)
        # return action + denormalize(self.observation[-1], self.n_dict['setpoint'][0], self.n_dict['setpoint'][1]) # this must be done for the specific case we are treating
        return denormalize(self.observation[-1], self.n_dict['setpoint'][0], self.n_dict['setpoint'][1]) # run the baseline

    def estimate_reward(self, reward_vars):
        # logger.debug(f"reward vars: {reward_vars}")
        self.penalty_Dt = -1e-1
        self.penalty_power = -1e-3
        #todo normalize
        tset = denormalize(self.observation_[-1].item(),self.n_dict['setpoint'][0],self.n_dict['setpoint'][1])
        text = denormalize(self.observation_[0].item(),self.n_dict['drybulb'][0],self.n_dict['drybulb'][1])
        max_diff = abs(text-tset)
        alpha = 1
        beta = 0.0

        C1 = alpha * abs(reward_vars['t_zone'] - tset) # + beta * abs(reward_vars['t_zone'] - 20.0) # souldh be normnalized over the difference of external temperature and setpoint
        # C1 = normalize(C1,0, max_diff)

        # C1 = abs(reward_vars['t_zone'] - tset) # temperature component
        C2 = abs(reward_vars['load_s'])
        #C2 = normalize(C2,0,max_diff)
        # logger.debug(f"C1: {C1}... C2: {C2}")
        r = C1 * self.penalty_Dt  + C2 * self.penalty_power  #/ abs(reward_vars['t_zone'] - denormalize(self.observation_[0].item(),self.n_dict['setpoint'][0],self.n_dict['setpoint'][1]))
        self.memory['reward'].append(r)
        if len(self.cum_reward)<48:
            self.cum_reward.append(r)
        else:
            self.memory['cum_reward'].append(sum(self.cum_reward))

            # self.memory['policy_state_dict'] = self.policy_model.state_dict()
            # self.memory['target_state_dict'] = self.target_model.state_dict()
            self.cum_reward=[]
        self.reward = torch.tensor(r)
        # logger.debug(f"reward{self.reward}, reward type {type(self.reward)}")
        self.update_replay_memory() # in DQN we have to push inside the rapley memory
        if self.steps_done == 0:
            self.best_reward=r
        if self.best_reward<r:
            self.best_reward=r
            torch.save(self.policy_model.state_dict(),'best_model_%s'%self.GAMMA)


    def update_agent(self, ts):
        logger.debug(f"TRAINING")
        if ts%24==0: #todo parametrize
            self.learn()

        if ts%48==0: #todo parametrize

            #soft update of the target model todo what is a soft update
            target_net_state_dict = self.target_model.state_dict()
            policy_net_state_dict = self.policy_model.state_dict()
            for key in policy_net_state_dict:
                target_net_state_dict[key] = policy_net_state_dict[key] * self.TAU + target_net_state_dict[key] * (1 - self.TAU)
            self.target_model.load_state_dict(target_net_state_dict)



    def learn(self): # train the
        if len(self.replay_memory) < self.BATCH_SIZE:
            return

        transitions = self.replay_memory.sample(self.BATCH_SIZE) #get the batch from replay memory
        batch = Transition(*zip(*transitions))
        logger.debug(f"training phase: batch : {pp.pformat(batch)}")

        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                                batch.observation)), device=self.device, dtype=torch.bool)
        non_final_next_states = torch.cat([s for s in batch.observation
                                           if s is not None])

        state_batch = torch.cat(batch.observation_)
        action_batch = torch.cat(batch.action)
        reward_batch = torch.cat(batch.reward)

        logger.debug(f'action batch: {action_batch}\n')
        state_action_values = self.policy_model(state_batch).gather(1, action_batch)
        logger.debug(f"%%%% state_action no action = {state_action_values}")

        next_state_values = torch.zeros(self.BATCH_SIZE, device=self.device)

        with torch.no_grad():
            next_state_values[non_final_mask] = self.target_model(non_final_next_states).max(1).values

        expected_q = (next_state_values * self.GAMMA) + reward_batch

        # Compute Huber loss
        criterion = nn.SmoothL1Loss() # loss function
        logger.debug(f"calculating loss: state_action_values {state_action_values},\n expected q {expected_q.unsqueeze(1)}")
        loss = criterion(state_action_values, expected_q.unsqueeze(1))

        #Optimize model
        self.optimizer.zero_grad()
        loss.backward()

        torch.nn.utils.clip_grad_value_(self.policy_model.parameters(), 100)
        self.optimizer.step()






    # def check_training(self):
    #     pass
    #
    # def memory_buffer(self):
    #     pass
    #
    # def update_replay_memory(self):
    #     transition = (self.observation_, self.action, self.reward, self.observation )
    #     self.replay_memory.append(transition)
    #
    # def finalize(self):
    #     pass
    #
    # def update_network_parameters(self, tau=None):
    #     if tau is None:
    #         tau = self.tau
    #
    #     target_value_params = self.target_value.named_parameters()
    #     value_params = self.value.named_parameters()
    #
    #     target_value_state_dict = dict(target_value_params)
    #     value_state_dict = dict(value_params)
    #
    #     for name in value_state_dict:
    #         value_state_dict[name] = tau * value_state_dict[name].clone() + (1 - tau) * target_value_state_dict[
    #             name].clone()
    #
    #     self.target_value.load_state_dict(value_state_dict)
    # def learn (self):
    #     if len(self.replay_memory) < MIN_REPLAY_MEMORY_SIZE:
    #         return
    #
    #     state, action, reward, new_state, done = self.memory.sample_buffer(self.batch_size)
    #
    #     reward = T.tensor(reward, dtype=T.float).to(self.actor.device)
    #     done = T.tensor(done).to(self.actor.device)
    #     state_ = T.tensor(new_state, dtype=T.float).to(self.actor.device)
    #     state = T.tensor(state, dtype=T.float).to(self.actor.device)
    #     action = T.tensor(action, dtype=T.float).to(self.actor.device)
    #
    #     value = self.value(state).view(-1)
    #     value_ = self.target_value(state_).view(-1)
    #     value_[done] = 0
    #
    #     actions, log_probs = self.actor.sample_normal(state, reparameterize=False)
    #     log_probs = log_probs.view(-1)
    #     q1_new_policy = self.critic_1.forward(state, actions)
    #     q2_new_policy = self.critic_2.forward(state, actions)
    #     critic_value = T.min(q1_new_policy, q2_new_policy)
    #     critic_value = critic_value.view(-1)
    #
    #     self.value.optimizer.zero_grad()
    #     value_target = critic_value - log_probs  # entropy regularized value function: E{q} + H
    #     value_loss = F.mse_loss(value, value_target)
    #     value_loss.backward(retain_graph=True)
    #     T.nn.utils.clip_grad_norm_(self.value.parameters(), 0.1)
    #     self.value.optimizer.step()
    #
    #     self.update_network_parameters()
    #
    #
    #
    # def train(self, terminal_state, step):
    #
    #     # Start training only if certain number of samples is already saved
    #     if len(self.replay_memory) < MIN_REPLAY_MEMORY_SIZE:
    #         return
    #
    #     # Get a minibatch of random samples from memory replay table
    #     minibatch = random.sample(self.replay_memory, MINIBATCH_SIZE)
    #
    #     # Get current states from minibatch, then query NN model for Q values
    #     current_states = np.array([transition[0] for transition in minibatch]) / #normvalue
    #     current_qs_list = self.model.forward(current_states)
    #
    #     # Get future states from minibatch, then query NN model for Q values
    #     # When using target network, query it, otherwise main network should be queried
    #     new_current_states = np.array([transition[3] for transition in minibatch]) / #normvalue
    #     future_qs_list = self.target_model.forward(new_current_states)
    #
    #     X = []
    #     y = []
    #
    #     # Now we need to enumerate our batches
    #     for index, (current_state, action, reward, new_current_state, done) in enumerate(minibatch):
    #
    #         # If not a terminal state, get new q from future states, otherwise set it to 0
    #         # almost like with Q Learning, but we use just part of equation here
    #         if not done:
    #             max_future_q = np.max(future_qs_list[index])
    #             new_q = reward + DISCOUNT * max_future_q
    #         else:
    #             new_q = reward
    #
    #         # Update Q value for given state
    #         current_qs = current_qs_list[index]
    #         current_qs[action] = new_q
    #
    #         # And append to our training data
    #         X.append(current_state)
    #         y.append(current_qs)
    #
    #     # Fit on all samples as one batch, log only on terminal state
    #     self.model.fit(np.array(X) / 255, np.array(y), batch_size=MINIBATCH_SIZE, verbose=0, shuffle=False,
    #                    callbacks=[self.tensorboard] if terminal_state else None)
    #
    #     # Update target network counter every episode
    #     if terminal_state:
    #         self.target_update_counter += 1
    #
    #     # If counter reaches set value, update target network with weights of main network
    #     if self.target_update_counter > UPDATE_TARGET_EVERY:
    #         self.target_model.set_weights(self.model.get_weights())
    #         self.target_update_counter = 0





