import math
from copy import deepcopy
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



random.seed(0)
np.random.seed(0)
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

    def empty_memory(self):
        self.memory = None

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

            logger.debug(f"Model class variables from Base class: {pp.pformat(self.__dict__)}")

            self.memory = {"reward":[],
                            "cum_reward":[],
                           'eps_th':[],
                           'C1_temp':[],
                           'C2_power':[],
                           'best_reward':[],
                           'action_exp':[],
                           'action_opt': [],
                           'raw_actions':[],
                           'out_network':[]}


            self.actions = [-3,-2.8,-2.2,-1.8,-1.2,-0.8,-0.4,-0.2, -0.1, 0, 0.1, 0.2, 0.4, 0.8, 1.2, 1.8, 2.2, 2.8, 3.0] # todo should be generalized like for the observations
            self.action_space = Discrete(len(self.actions), start=0, seed=42)  # {-1, 0, 1 #todo should generalize from config using a class that based on a flag choose the right gym space
            self.n_actions = self.action_space.n # this only because we have discrete set of actions




            self.observation_space = {k:(self.obs_space[k]['range'],self.obs_space[k]['type']) for k in self.observation_vars}
            self.n_observations = len(self.observation_vars)
            self.observation = torch.tensor(np.array([0.0 for data in self.observation_vars])) # todo instead of 0.0 should use some initial values
            self.observation_ = torch.tensor(np.array([np.array([0.0]) for data in self.observation_vars])) # previous observations because we evaluate rewards at next time step
            self.observation_dict = {k:0.0 for k in self.observation_vars}
            self.observation_prev_dict = {k:0.0 for k in self.observation_vars}
            self.reward = None
            self.action = torch.tensor([0])

            logger.debug(f" Action_space number: {self.action_space.n}\n obs space number: ")

            #replay memory
            self.replay_memory = ReplayMemory(self.REPLAY_MEMORY)

            #instantiation neural networks
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
            self.best_model = None
            self.switch_tobestmodel = False # questo serve solo fino a che non ho embeddato tutti i trigger dovuti al cambio tra training e testing in una callback (non fa nulla che evitare che il best model sia fissato piiu di una volta)
            self.training = True
            self.best_reward = -10000000
            self.best_inst_rew = -10000000
            self.best_param = None
            self.cum_reward = []


    def get_observations(self, obs_vars):
        if self.steps_done!=0:
            self.observation_ = self.observation # the new observation self.observation must be used only in predict action, while for the reward we are calculating the previous one
            self.observation_prev_dict = self.observation_dict
        # obs_vars = {k:normalize(val,self.n_dict[k][0],self.n_dict[k][1]) for k,val in obs_vars.items()}
        self.observation_dict = {k:val for k,val in obs_vars.items()}
        obs_vars_norm = self.normalize_obs(obs_vars)
        #add day of the year in observation todo
        #need to tranform obsvars data into a proper format to feed the neural network
        self.observation = torch.tensor([obs_vars_norm[data] for data in obs_vars_norm])
        logger.debug(f"Observation now : {self.observation_dict}, {self.observation}")
        logger.debug(f"Observation t-1 : {self.observation_prev_dict}, {self.observation_}")

    def normalize_obs(self, obs_vars):
        normalized_obs = {}
        for k, data in obs_vars.items():
            min = self.observation_space[k][0][0]
            max = self.observation_space[k][0][1]
            space_type = self.observation_space[k][1]
            if space_type == 'continous' or space_type == 'discrete':
                normalized_obs[k] = normalize(data, min, max)
            else:
                normalized_obs[k] = data
        return normalized_obs


    def update_replay_memory(self):
        state = self.observation_.unsqueeze(0) #.reshape(1, -1).float()
        action = self.action.unsqueeze(0) #.reshape(1,-1) # to be properly defined this is the previous action thats why this update must always come before taking a new action (predict action
        next_state = self.observation.unsqueeze(0) #.reshape(1,-1).float()
        reward = self.reward.unsqueeze(0) #.reshape(1,-1).float() # all of these must be copy of torch tensor
        transition = (state, action, next_state, reward)

        logger.debug(f"\n Updating the replay memory with the following information:\n"
                     f"state: {state } &&\n"
                     f"action: {action} &&\n"
                     f"next_state: {next_state} &&\n"
                     f"reward: {reward}&&\n"
                     f"organized in the following transition: {transition}!!!\n")


        self.replay_memory.push(*transition)

    def predict_action(self):

        # if self.observation_dict['on_off'] == 0 :
        #     return self.observation_dict['setpoint']  # run the baseline

        # if self.observation_dict['t_zone'] > self.observation_dict['setpoint'] and self.observation_dict['on_off'] == 1: #heating
        #     return self.observation_dict['setpoint']  # run the baseline
        # if self.observation_dict['t_zone'] < self.observation_dict['setpoint'] and self.observation_dict['on_off'] == -1: #cooling
        #     return self.observation_dict['setpoint']  # run the baseline

        if self.steps_done==0:
            self.steps_done += 1
            return self.observation_dict['setpoint']  # run the baseline


        sample = random.random()
        eps_threshold = self.EPS_END + (self.EPS_START - self.EPS_END) * math.exp(-1 * self.steps_done / self.EPS_DECAY)
        self.memory['eps_th'].append(eps_threshold)

        if sample > eps_threshold or not self.training:
            with torch.no_grad():
                # state = torch.tensor(self.observation.reshape(1, -1))
                logger.debug(f"OBSERVATION state to be fed to NN: {self.observation}")

                #transform observation in a normalized tensor
                #norm_obs = self.normalize_obs()
                #obs= torch.tensor([norm_obs[data] for data in norm_obs])
                #the network return the q value for all the actions (3 in this case -1, 0, +1) we have to pick the highest q valued and the corresponding action ans sum it to the scheduled tset
                # Q = self.policy_model(self.observation) #working
                Q = self.policy_model(self.observation) #.max(1).indices.view(1, 1)
                logger.debug(f"output of NN network: {Q}, type: {type(Q)}, dimension {Q.shape}")
                # logger.debug(f"Q value from neural network: {Q}")
                action_index = torch.argmax(Q).item() #todo check maybe is missing something

                # logger.debug(f"Action index after agrmax: {action_index}")
                self.memory['raw_actions'].append(action_index) # todo remove
                action = self.actions[action_index]
                logger.debug(f"Action optimally chosen: {action}")
                self.memory['action_opt'].append(action)




        else:
            action_index = self.action_space.sample()
            action = self.actions[action_index]
            self.memory['action_exp'].append(action)

            logger.debug(f"Action casually chosen: {action}")


        # logger.debug(f"summing the observation set_point {self.observation[-1]} with the chosen action {action}")

        #this must be denormalized!!!! TODO
        self.action = torch.tensor(action_index)
        self.real_action = action
        self.steps_done += 1
        return action + self.observation_dict['setpoint'] # this must be done for the specific case we are treating
        # return self.observation_dict['setpoint']  # run the baseline

    def evaluate_agent(self, reward_vars):
        '''evaluate performs:
        - inst reward calculation of previous step
        - cumulative reward calculation
        - best model update
        - memory update during training '''

        # if self.observation_dict['on_off'] == 0 and self.observation_prev_dict['on_off'] == 0:
        # if self.observation_prev_dict['on_off']==0 or self.steps_done==0:
        #     return
        #
        # if self.observation_prev_dict['on_off'] == 1 and (self.observation_prev_dict['setpoint']- reward_vars['t_zone'])<0:  #not evaluating when heating and zone temperature already above setpoint
        #     return
        #
        # elif self.observation_prev_dict['on_off']==-1 and (self.observation_prev_dict['setpoint']- reward_vars['t_zone'])>0: #not evaluating when cooling and zone temperature already above setpoint
        #     return

        logger.debug(f"Agent Evaluation! steps_done = {self.steps_done}")
        inst_reward = self.estimate_reward(reward_vars) # calculating step reward
        self.reward = torch.tensor(inst_reward)
        self.memory['reward'].append(inst_reward)

        if len(self.cum_reward) < self.episode_ts:
            self.cum_reward.append(inst_reward)

        else:  # here an episode has been completed
            # self.memory['cum_reward'].append(sum(self.cum_reward)/len(self.cum_reward)) # todo MEAN
            self.memory['cum_reward'].append(sum(self.cum_reward)) # todo SUM

            self.cum_reward = []
            # self.steps_done += 1  # should be update for each episode, no need to explore too much

            #saving best model based on the best episopde reward todo e' giusto salvaree basandosi sullo score (aka cum reward per episode) piuttosto che sulla instantaneous reward?
            if self.best_reward < self.memory['cum_reward'][-1] and self.training: # todo how to get the best model
                self.best_reward = self.memory['cum_reward'][-1]
                self.memory['best_reward'].append(self.best_reward)
                torch.save(self.policy_model.state_dict(),
                           'best_model_%s' % self.GAMMA)  # saves into a file but we eant to keep becasue the testing happen without stopping the cosim
                self.best_model = self.policy_model.state_dict()


        # logger.debug(f"reward{self.reward}, reward type {type(self.reward)}")
        if self.training and not self.steps_done<2: # push in replay memory only during training
            self.update_replay_memory()  # in DQN we have to push inside the rapley memory
        else: # empty the memory when testing only first time
            if self.replay_memory.memory:
                self.replay_memory.empty_memory()



        #checking for the best reward for each step and saving the best one
        # if self.steps_done == 0:
        #     self.best_reward = inst_reward
        # if self.best_reward < inst_reward and self.training:
        #     self.best_reward = inst_reward
        #     torch.save(self.policy_model.state_dict(), 'best_model_%s' % self.GAMMA) # saves into a file but we eant to keep becasue the testing happen without stopping the cosim
        #     self.best_model = self.policy_model.state_dict()

        if not self.training and not self.switch_tobestmodel: # fix the params of best model for testing but ensure to do it only the first time # todo all the related trigger to switching from train to test should be done with a proper callback and not here NON MI VA ORA!
            self.policy_model.load_state_dict(self.best_model)
            self.switch_tobestmodel = True

    def estimate_reward(self, reward_vars):
        ''' This method estimate the instantaneours reward: the reward achieved by the previous action taken thus need to standardize what to use when calculating it.
        observation_ = previous step before action todo maybe do not need
        observation = current step' before action
        reward_vars = previous step after action
        '''

        tset = self.observation_prev_dict['setpoint']
        text = self.observation_prev_dict['drybulb']
        t_zone_prev = self.observation_prev_dict['t_zone']
        t_zone = reward_vars['t_zone']

        logger.debug(f"calculating rewards t_zone after action:{t_zone} ---- t_zone pre action :{t_zone_prev}")
        energy = reward_vars['load_s']

        # logger.debug(f"Calculate reward: tset = {tset}, t_ext = {text}, t_zone = {reward_vars['t_zone']}")
        on_off = self.observation_prev_dict['on_off']
        hour = self.observation_prev_dict['hour_of_day']

        penalty_comfort = -1
        penalty_energy = -0.00001


        if t_zone_prev>tset or 0<=hour<=6:
            Dt = 0
            if 0<=hour<=6:
                penalty_energy = -0.000001
        else:
            Dt = (t_zone-tset)**2
        # R_comfort = (1 / c) * (Dt)**4
        R_comfort = Dt
        R_power = energy #/ abs(tset - text) if abs(tset - text)!=0 else energy

        r = penalty_comfort * R_comfort + penalty_energy * R_power
        self.memory['C1_temp'].append(penalty_comfort*R_comfort)
        self.memory['C2_power'].append(penalty_energy*R_power)

        return r


    def update_agent(self, ts):
        # if self.observation_dict['on_off'] == 0 and self.observation_prev_dict['on_off']==0:
        #     return

        if ts%self.episode_ts==0: #todo parametrize
            self.learn()

        if ts%(self.episode_ts*2)==0: #todo parametrize

            #soft update of the target model todo what is a soft update
            target_net_state_dict = self.target_model.state_dict()
            policy_net_state_dict = self.policy_model.state_dict()
            for key in policy_net_state_dict:
                target_net_state_dict[key] = policy_net_state_dict[key] * self.TAU + target_net_state_dict[key] * (1 - self.TAU)
            self.target_model.load_state_dict(target_net_state_dict)



    def learn(self): # train the

        if len(self.replay_memory) < self.BATCH_SIZE:
            return

        logger.debug(f"TRAINING")
        transitions = self.replay_memory.sample(self.BATCH_SIZE) #get the batch from replay memory
        batch = Transition(*zip(*transitions))
        # logger.debug(f"training phase: batch : {pp.pformat(batch)}")

        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                                batch.observation)), device=self.device, dtype=torch.bool)
        non_final_next_states = torch.cat([s for s in batch.observation
                                           if s is not None])

        state_batch = torch.cat(batch.observation_)
        action_batch = torch.cat(batch.action).unsqueeze(1)
        reward_batch = torch.cat(batch.reward)

        logger.debug(f'action batch ({action_batch.shape}): {action_batch}\n')
        logger.debug(f"state batch ({state_batch.shape}): {state_batch}\n")
        logger.debug(f"output policy model ({self.policy_model(state_batch).shape}): {self.policy_model(state_batch)}\n")
        logger.debug(f'reward batch ({reward_batch.shape}): {reward_batch}\n')

        state_action_values = self.policy_model(state_batch).gather(1, action_batch)
        logger.debug(f'state action values ({state_action_values.shape}): {state_action_values}\n')

        next_state_values = torch.zeros(self.BATCH_SIZE, device=self.device)
        logger.debug(f'empty next state values ({next_state_values.shape}): {next_state_values}\n')

        with torch.no_grad():
            next_state_values[non_final_mask] = self.target_model(non_final_next_states).max(1).values

        logger.debug(f'full next state values ({next_state_values.shape}): {next_state_values}\n')

        expected_q = (next_state_values * self.GAMMA) + reward_batch
        logger.debug(f'expected_q ({expected_q.shape}): {expected_q}\n')

        # Compute Huber loss
        criterion = nn.SmoothL1Loss() # loss function
        # loss = criterion(state_action_values, expected_q.unsqueeze(1))
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





