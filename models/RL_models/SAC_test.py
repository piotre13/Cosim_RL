import os
import sys
sys.path.append("/home/pietrorm/Documents/CODE/Cosim_RL/models/RL_models")
import torch as T
import torch.nn.functional as F
import numpy as np
from buffer import ReplayBuffer
from networks import ActorNetwork, ValueNetwork, CriticNetwork
from models._baseModels.RL_Base import RL_Base
import random
import logging
import pprint
random.seed(0)
np.random.seed(0)
pp = pprint.PrettyPrinter(indent=4)


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


def normalize (x, min, max):
    return (x - min) / (max - min)
class SAC_agent(RL_Base):
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
                       'out_network':[],
                       'best_networks':[]}


        self.actions = np.linspace(self.act_space['low'], self.act_space['high'],self.act_space['n_slots'])#[-3,-2, -1, 0, 1, 2, 3] # todo should be generalized like for the observations
        self.action_space= {'min':self.act_space['low'],'max':self.act_space['high']} # todo passed from config files
        self.n_observations = len(self.observation_vars)
        self.n_actions = 1

        self.sac = Agent(input_dims=self.n_observations,n_actions=self.n_actions,batch_size=self.BATCH_SIZE, max_size=self.REPLAY_MEMORY, gamma=self.GAMMA, tau=self.TAU)

        # previous observations because we evaluate rewards at next time step
        self.observation_space = {k:(self.obs_space[k]['range'],self.obs_space[k]['type']) for k in self.observation_vars}
        self.observation_dict = {k:0.0 for k in self.observation_vars}
        self.observation_prev_dict = {k:0.0 for k in self.observation_vars}
        self.observation = np.array([0.0 for data in self.observation_vars])  # todo instead of 0.0 should use some initial values
        self.observation_ = np.array([np.array([0.0]) for data in
                                                   self.observation_vars])  # previous observations because we evaluate rewards at next time step
        self.reward = None
        self.action = 0.0
        logger.debug(f" Action_space number: {self.action_space}\n obs space number: ")

        self.steps_done = 0
        self.best_model = None
        self.switch_tobestmodel = False # questo serve solo fino a che non ho embeddato tutti i trigger dovuti al cambio tra training e testing in una callback (non fa nulla che evitare che il best model sia fissato piiu di una volta)
        self.training = True
        self.best_reward = -10000000000
        self.best_inst_rew = -10000000
        self.best_param = None
        self.cum_reward = [self.best_reward]
        self.set_point = 20
        self.real_action = 0


    def get_observations(self, obs_vars):
        if self.steps_done!=0:
            self.observation_ = self.observation # the new observation self.observation must be used only in predict action, while for the reward we are calculating the previous one
            self.observation_prev_dict = self.observation_dict
            self.set_point_prev = self.set_point
        # obs_vars = {k:normalize(val,self.n_dict[k][0],self.n_dict[k][1]) for k,val in obs_vars.items()}
        self.observation_dict = {k:val for k,val in obs_vars.items()}
        obs_vars_norm = self.normalize_obs(obs_vars)
        self.set_point = self.other_inputs['setpoint']
        #add day of the year in observation todo
        #need to tranform obsvars data into a proper format to feed the neural network
        # self.observation = T.tensor([obs_vars_norm[data] for data in obs_vars_norm])
        self.observation = np.array([obs_vars_norm[data] for data in obs_vars_norm])
        logger.debug(f"Observation now : {self.observation_dict}, {self.observation} type = {type(self.observation)}")
        logger.debug(f"Observation t-1 : {self.observation_prev_dict}, {self.observation_} type = {type(self.observation_)}")

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


    def update_replay_memory(self, done = False):
        # state = self.observation_.unsqueeze(0) #.reshape(1, -1).float()
        # action = self.action.unsqueeze(0) #.reshape(1,-1) # to be properly defined this is the previous action thats why this update must always come before taking a new action (predict action
        # next_state = self.observation.unsqueeze(0) #.reshape(1,-1).float()
        # reward = self.reward.unsqueeze(0) #.reshape(1,-1).float() # all of these must be copy of T tensor
        # transition = (state, action, next_state, reward)
        #

        state = self.observation_
        next_state = self.observation
        reward = self.reward
        action = self.real_action
        done = done# todo update the logic for the reset
        logger.debug("---------------- UPDATING MEMORY")
        logger.debug(f"\n Updating the replay memory with the following information:\n"
                     f"state: {state} type = {type(state)}&&\n"
                     f"action: {action} type = {type(action)} &&\n"
                     f"next_state: {next_state} type = {type(next_state)} &&\n"
                     f"reward: {reward} type = {type(reward)}&&\n")
        logger.debug("----------------------------------")

        self.sac.remember(state,action, reward, next_state, done)
    def predict_action(self):
        if self.steps_done<2:
            self.action = np.array([0.0])
            # logger.debug(f"Action optimally chosen: {self.action}, type = {type(self.action)}")

            self.real_action = 0.0
        else:
            action = self.sac.choose_action(self.observation)
            scaled_action = self.scaler(action)
            self.action = action
            self.real_action = scaled_action[0]

        self.memory['action_opt'].append(self.real_action)

        logger.debug(f"--------------- ACTION DECISION step = {self.steps_done}")
        logger.debug(f"State passed to the network: {self.observation} type = { type(self.observation)}")
        logger.debug(f"Real action = {self.real_action} type {type(self.real_action)}")
        logger.debug(f"Chosen action= {self.action} type {type(self.action)}")
        logger.debug(f"-------------------------------")
        self.steps_done += 1

        return self.real_action
    def scaler(self, action):
        #todo this caler only covers numbner in positive scale ranges that start from 0 must be generalized
        min = self.action_space['min']
        max = self.action_space['max']
        normalized_output = (action + 1) / 2

        # Scale the normalized output to the range 0 to 30000
        scaled_output = normalized_output * max

        return scaled_output

    def evaluate_agent(self, reward_vars):
        '''evaluate performs:
        - inst reward calculation of previous step
        - cumulative reward calculation
        - best model update
        - memory update during training '''
        done = False
        # if self.observation_dict['on_off'] == 0 and self.observation_prev_dict['on_off'] == 0:
        if self.steps_done < 2:
            return

        # if self.steps_done%720 == 0:


        inst_reward = self.estimate_reward(reward_vars) #*-1  # calculating step reward
        self.reward = inst_reward
        self.memory['reward'].append(inst_reward)
        self.cum_reward.append(inst_reward)


        if len(self.cum_reward) == self.episode_ts:  # here an episode has been completed
            done = True
            # self.memory['cum_reward'].append(sum(self.cum_reward)/len(self.cum_reward)) # todo MEAN
            self.memory['cum_reward'].append(sum(self.cum_reward))  # todo SUM
            self.cum_reward = []



            avg_score = np.mean(np.array(self.memory['cum_reward'][-100:]))

            # saving best model based on the best episopde reward
            # done = True # TODO should coincide with the reset?
            # if self.best_reward < self.memory['cum_reward'][-1] and self.training and self.steps_done > (
            # self.train_end_ts) * 0.6:  # todo how to get the best model
            logger.debug(f"average_score of cumulative reward: {avg_score}")
            if self.best_reward < avg_score and self.training and self.steps_done>0:# and self.steps_done > (self.train_end_ts) * 0.6:
                # self.best_reward = self.memory['cum_reward'][-1]
                self.best_reward = avg_score
                self.memory['best_reward'].append(self.best_reward)
                # best_networks = {'actor':self.sac.actor.state_dict(),
                #                  'critic1':self.sac.critic_1.state_dict(),
                #                  'critic2':self.sac.critic_2.state_dict(),
                #                  'value': self.sac.value.state_dict(),
                #                  'target':self.sac.target_value.state_dict()}
                # self.memory['best_networks'].append(best_networks)
                # torch.save(self.policy_model.state_dict(),
                #            'best_model_%s' % self.GAMMA)  # saves into a file but we eant to keep becasue the testing happen without stopping the cosim
                self.sac.save_models()
                logger.info("BEST MODEL SAVED")
                logger.debug(f"Best model saved with reward: {self.best_reward}")
                logger.debug(f"Switched to best model: {self.switch_tobestmodel}")
                logger.debug(f"Training phase: {self.training}")

        # logger.debug(f"reward{self.reward}, reward type {type(self.reward)}")
        if self.training and not self.steps_done < 2:  # push in replay memory only during training
            self.update_replay_memory(done = done)  # in DQN we have to push inside the rapley memory



        if not self.training and not self.switch_tobestmodel:  # fix the params of best model for testing but ensure to do it only the first time # todo all the related trigger to switching from train to test should be done with a proper callback and not here NON MI VA ORA!
            logger.info("USING BEST MODEL")
            self.sac.load_models()
            self.switch_tobestmodel = True

        logger.debug(f"--------------- EVALUATE AGENT")
        logger.debug(f"Instantaneous Reward = {self.reward} type={type(self.reward)}")
        logger.debug(f"cum_reward len:{len(self.cum_reward)}, cum_reward = {self.cum_reward}")
        logger.debug(f"------------------------------")

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
        energy = self.real_action
        # logger.debug(f"Calculate reward: tset = {tset}, t_ext = {text}, t_zone = {reward_vars['t_zone']}")
        # on_off = self.observation_prev_dict['on_off']
        hour = self.observation_prev_dict['hour_of_day']


        penalty_comfort = -1e-1
        penalty_energy = -1e-3
        #
        # if hour == 1:
        #     if t_zone>21:
        #         R_comfort = (t_zone-21)**2
        #     elif t_zone < 19 :
        #         R_comfort = (t_zone-19)**2
        #     else:
        #         R_comfort = 0
        # else:
        #     R_comfort = 0

        R_comfort = abs(t_zone-tset)
        R_energy = energy/3600
        # if hour !=1:
        #     R_comfort = 0

        r = penalty_comfort * R_comfort #+ penalty_energy * R_energy

        # r = penalty_comfort * (t_zone-20)**2

        logger.debug(f"REWARD components: {r}, C1temp = {penalty_comfort * R_comfort}, C2power = {penalty_energy * R_energy}")
        self.memory['C1_temp'].append(penalty_comfort * R_comfort)
        self.memory['C2_power'].append(penalty_energy * R_energy)

        # r = -1 * (t_zone - 20)**2
        return r


    def update_agent(self, ts):
        if self.steps_done % self.episode_ts == 0:
            self.sac.learn()



class Agent:
    def __init__(self, alpha=1e-4, beta=1e-4, input_dims=8, env=None, gamma=0.99, n_actions=1, max_size=1000000, tau=0.005,
                 layer1_size=64, layer2_size=64, batch_size=256, reward_scale=1, suffix=''):
        self.gamma = gamma
        self.tau = tau
        self.memory = ReplayBuffer(max_size, input_dims, n_actions)
        self.batch_size = batch_size
        self.n_actions = n_actions

        self.actor = ActorNetwork(alpha, input_dims, n_actions=n_actions, name=f'actor{suffix}' if suffix else 'actor', max_action=1)
        self.critic_1 = CriticNetwork(beta, input_dims, n_actions=n_actions, name=f'critic_1{suffix}' if suffix else 'critic_1')
        self.critic_2 = CriticNetwork(beta, input_dims, n_actions=n_actions, name=f'critic_2{suffix}' if suffix else 'critic_2')
        self.value = ValueNetwork(beta, input_dims, name=f'value{suffix}' if suffix else 'value')
        self.target_value = ValueNetwork(beta, input_dims, name=f'target_value{suffix}' if suffix else 'target_value')

        self.scale = reward_scale
        self.update_network_parameters(tau=tau)

    def choose_action(self, observation):
        state = T.tensor(observation.reshape(1, -1)).to(self.actor.device)
        actions, _ = self.actor.sample_normal(state, reparameterize=True)

        return actions.cpu().detach().numpy()[0]

    def remember(self, state, action, reward, new_state, done):
        self.memory.store_transition(state, action, reward, new_state, done)

    def update_network_parameters(self, tau=None):
        if tau is None:
            tau = self.tau

        target_value_params = self.target_value.named_parameters()
        value_params = self.value.named_parameters()

        target_value_state_dict = dict(target_value_params)
        value_state_dict = dict(value_params)

        # logger.debug(f"UPDATING target_value paramas= {target_value_params}, target value state dict = {target_value_state_dict}, value params = {value_params}, value state dict={value_state_dict}")

        for name in value_state_dict:
            value_state_dict[name] = tau*value_state_dict[name].clone() + (1-tau)*target_value_state_dict[name].clone()

        self.target_value.load_state_dict(value_state_dict)

    def save_models(self):
        # print('................saving models................')
        self.actor.save_checkpoint()
        self.value.save_checkpoint()
        self.target_value.save_checkpoint()
        self.critic_1.save_checkpoint()
        self.critic_2.save_checkpoint()

    def load_models(self):
        print('................loading models................')
        self.actor.load_checkpoint()
        self.value.load_checkpoint()
        self.target_value.load_checkpoint()
        self.critic_1.load_checkpoint()
        self.critic_2.load_checkpoint()

    def learn(self):
        if self.memory.mem_cntr < self.batch_size:
            return
        logger.info("UPDATE start")
        state, action, reward, new_state, done = self.memory.sample_buffer(self.batch_size)
        logger.debug(f"---------------- UPDATE")
        logger.debug(f"---------------- SAMPLING BUFFER")
        logger.debug(f"state = {state}, type={type(state)}")
        logger.debug(f"action = {action}, type={type(action)}")
        logger.debug(f"reward = {reward}, type={type(reward)}")
        logger.debug(f"new_state = {new_state}, type={type(new_state)}")
        logger.debug(f"done = {done}, type={type(done)}")
        logger.debug(f"---------------- ")

        reward = T.tensor(reward, dtype=T.float).to(self.actor.device)
        done = T.tensor(done).to(self.actor.device)
        state_ = T.tensor(new_state, dtype=T.float).to(self.actor.device)
        state = T.tensor(state, dtype=T.float).to(self.actor.device)
        action = T.tensor(action, dtype=T.float).to(self.actor.device)
        value = self.value(state).view(-1)
        value_ = self.target_value(state_).view(-1)
        value_[done] = 0
        # logger.debug(f"value= {value} and value_={value_}")

        # update state value network

        actions, log_probs = self.actor.sample_normal(state, reparameterize=False)
        log_probs = log_probs.view(-1)
        q1_new_policy = self.critic_1.forward(state, actions)
        q2_new_policy = self.critic_2.forward(state, actions)
        critic_value = T.min(q1_new_policy, q2_new_policy)
        critic_value = critic_value.view(-1)
        # logger.debug(f"actions= {actions} and logPorbs={log_probs}")

        self.value.optimizer.zero_grad()
        value_target = critic_value - log_probs  # entropy regularized value function: E{q} + H
        value_loss = F.mse_loss(value, value_target)
        value_loss.backward(retain_graph=True)
        T.nn.utils.clip_grad_norm_(self.value.parameters(), 0.1)
        self.value.optimizer.step()
        # self.value.scheduler.step()

        # update policy network
        actions, log_probs = self.actor.sample_normal(state, reparameterize=True)
        log_probs = log_probs.view(-1)
        q1_new_policy = self.critic_1.forward(state, actions)
        q2_new_policy = self.critic_2.forward(state, actions)
        critic_value = T.min(q1_new_policy, q2_new_policy)
        critic_value = critic_value.view(-1)

        actor_loss = log_probs - critic_value  # actor needs to maximize expected q value and entropy (for exploration)
        actor_loss = T.mean(actor_loss)
        self.actor.optimizer.zero_grad()
        actor_loss.backward(retain_graph=True)
        T.nn.utils.clip_grad_norm_(self.actor.parameters(), 0.1)
        self.actor.optimizer.step()

        # update action value network
        self.critic_1.optimizer.zero_grad()
        self.critic_2.optimizer.zero_grad()
        q_hat = self.scale*reward + self.gamma*value_
        q1_old_policy = self.critic_1.forward(state, action).view(-1)
        q2_old_policy = self.critic_2.forward(state, action).view(-1)
        critic_1_loss = 0.5*F.mse_loss(q1_old_policy, q_hat)
        critic_2_loss = 0.5*F.mse_loss(q2_old_policy, q_hat)

        critic_loss = critic_1_loss + critic_2_loss
        critic_loss.backward()
        T.nn.utils.clip_grad_norm_(self.critic_1.parameters(), 0.1)
        T.nn.utils.clip_grad_norm_(self.critic_2.parameters(), 0.1)
        self.critic_1.optimizer.step()
        self.critic_2.optimizer.step()

        self.update_network_parameters()
        logger.info("------------------UPDATE succeed")






