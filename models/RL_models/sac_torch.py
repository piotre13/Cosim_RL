import os
import torch as T
import torch.nn.functional as F
import numpy as np
from buffer import ReplayBuffer
from networks import ActorNetwork, ValueNetwork, CriticNetwork


class Agent:
    def __init__(self, alpha=0.0003, beta=0.0003, input_dims=8, env=None, gamma=0.99, n_actions=3, max_size=1000000, tau=0.005,
                 layer1_size=256, layer2_size=256, batch_size=256, reward_scale=1, suffix=''):
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

        for name in value_state_dict:
            value_state_dict[name] = tau*value_state_dict[name].clone() + (1-tau)*target_value_state_dict[name].clone()

        self.target_value.load_state_dict(value_state_dict)

    def save_models(self):
        print('................saving models................')
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
        state, action, reward, new_state, done = self.memory.sample_buffer(self.batch_size)

        reward = T.tensor(reward, dtype=T.float).to(self.actor.device)
        done = T.tensor(done).to(self.actor.device)
        state_ = T.tensor(new_state, dtype=T.float).to(self.actor.device)
        state = T.tensor(state, dtype=T.float).to(self.actor.device)
        action = T.tensor(action, dtype=T.float).to(self.actor.device)

        value = self.value(state).view(-1)
        value_ = self.target_value(state_).view(-1)
        value_[done] = 0

        # update state value network
        actions, log_probs = self.actor.sample_normal(state, reparameterize=False)
        log_probs = log_probs.view(-1)
        q1_new_policy = self.critic_1.forward(state, actions)
        q2_new_policy = self.critic_2.forward(state, actions)
        critic_value = T.min(q1_new_policy, q2_new_policy)
        critic_value = critic_value.view(-1)

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





