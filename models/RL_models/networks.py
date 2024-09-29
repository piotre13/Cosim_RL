import os
import torch as T
import torch.nn.functional as F
import torch.nn as nn
import torch.optim as optim
from torch.distributions.normal import Normal
import numpy as np

class CriticNetwork(nn.Module):  # q neural network
    def __init__(self, beta, input_dims, n_actions, fc1_dims=256, fc2_dims=256, name='critic', chkpt_dir='./chkpt'):
        super(CriticNetwork, self).__init__()
        self.input_dims = input_dims
        self.fc1_dims = fc1_dims
        self.fc2_dims = fc2_dims
        self.n_actions = n_actions
        self.name = name
        self.checkpoint_dir = chkpt_dir
        if not os.path.isdir(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
        self.checkpoint_file = os.path.join(self.checkpoint_dir, name+'_sac')

        self.fc1 = nn.Linear(self.input_dims+n_actions, self.fc1_dims)
        self.fc2 = nn.Linear(self.fc1_dims, self.fc2_dims)
        self.fc3 = nn.Linear(self.fc2_dims, self.fc2_dims)
        self.fc4 = nn.Linear(self.fc2_dims, self.fc2_dims)
        self.q = nn.Linear(self.fc2_dims, 1)

        self.optimizer = optim.Adam(self.parameters(), lr=beta)
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=int(1e4), gamma=0.1)
        self.device = T.device('cuda:1' if T.cuda.is_available() else 'cpu')
        self.to(self.device)

    def forward(self, state, action):
        action_value = self.fc1(T.cat([state, action], dim=1))
        action_value = F.leaky_relu(action_value)
        action_value = self.fc2(action_value)
        action_value = F.leaky_relu(action_value)
        action_value = self.fc3(action_value)
        action_value = F.leaky_relu(action_value)
        action_value = self.fc4(action_value)
        action_value = F.leaky_relu(action_value)

        q = self.q(action_value)

        return q

    def save_checkpoint(self):
        T.save(self.state_dict(), self.checkpoint_file)

    def load_checkpoint(self):
        self.load_state_dict(T.load(self.checkpoint_file,map_location=T.device('cpu')))


class ValueNetwork(nn.Module):  # v neural network
    def __init__(self, beta, input_dims, fc1_dims=256, fc2_dims=256, name='value', chkpt_dir='./chkpt'):
        super(ValueNetwork, self).__init__()
        self.input_dims = input_dims
        self.fc1_dims = fc1_dims
        self.fc2_dims = fc2_dims
        self.name = name
        self.checkpoint_dir = chkpt_dir
        if not os.path.isdir(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
        self.checkpoint_file = os.path.join(self.checkpoint_dir, name + '_sac')

        self.fc1 = nn.Linear(self.input_dims, self.fc1_dims)
        self.fc2 = nn.Linear(self.fc1_dims, self.fc2_dims)
        self.fc3 = nn.Linear(self.fc2_dims, self.fc2_dims)
        self.fc4 = nn.Linear(self.fc2_dims, self.fc2_dims)
        self.v = nn.Linear(self.fc2_dims, 1)

        self.optimizer = optim.Adam(self.parameters(), lr=beta)
        self.device = T.device('cuda:1' if T.cuda.is_available() else 'cpu')
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=int(1e4), gamma=0.1)
        self.to(self.device)

    def forward(self, state):
        state_value = self.fc1(state)
        state_value = F.leaky_relu(state_value)
        state_value = self.fc2(state_value)
        state_value = F.leaky_relu(state_value)
        state_value = self.fc3(state_value)
        state_value = F.leaky_relu(state_value)
        state_value = self.fc4(state_value)
        state_value = F.leaky_relu(state_value)

        v = self.v(state_value)

        return v

    def save_checkpoint(self):
        T.save(self.state_dict(), self.checkpoint_file)

    def load_checkpoint(self):
        self.load_state_dict(T.load(self.checkpoint_file,map_location=T.device('cpu')))


class ActorNetwork(nn.Module):  # policy neural network
    def __init__(self, alpha, input_dims, max_action, fc1_dims=256, fc2_dims=256, n_actions=2, name='actor', chkpt_dir='./chkpt'):
        super(ActorNetwork, self).__init__()
        self.input_dims = input_dims
        self.fc1_dims = fc1_dims
        self.fc2_dims = fc2_dims
        self.n_actions = n_actions
        self.name = name
        self.checkpoint_dir = chkpt_dir
        if not os.path.isdir(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
        self.checkpoint_file = os.path.join(self.checkpoint_dir, name + '_sac')
        self.max_action = max_action
        self.reparam_noise = 1e-6

        # multi-head neural network for means and standard deviations
        self.fc1 = nn.Linear(self.input_dims, self.fc1_dims)
        self.fc2 = nn.Linear(self.fc1_dims, self.fc2_dims)
        self.fc3 = nn.Linear(self.fc2_dims, self.fc2_dims)
        self.fc4 = nn.Linear(self.fc2_dims, self.fc2_dims)

        self.mu = nn.Linear(self.fc2_dims, self.n_actions)
        self.log_sigma = nn.Linear(self.fc2_dims, self.n_actions)

        self.optimizer = optim.AdamW(self.parameters(), lr=alpha)
        self.device = T.device('cuda:1' if T.cuda.is_available() else 'cpu')
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=int(1e6), gamma=0.1)
        self.to(self.device)

    def forward(self, state):
        prob = self.fc1(state)
        prob = F.leaky_relu(prob)
        prob = self.fc2(prob)
        prob = F.leaky_relu(prob)
        prob = self.fc3(prob)
        prob = F.leaky_relu(prob)
        prob = self.fc4(prob)
        prob = F.leaky_relu(prob)

        mu = self.mu(prob)
        log_sigma = self.log_sigma(prob)

        log_sigma = T.clamp(log_sigma, min=-10, max=3)  # todo: min and max are hyperparameters, if training is under expectation, change them as inputs and tune.

        return mu, log_sigma

    def sample_normal(self, state, reparameterize=True):
        mu, log_sigma = self.forward(state.float())
        probabilities = Normal(mu, log_sigma.exp())
        if reparameterize:
            actions = probabilities.rsample()
        else:
            actions = probabilities.sample()

        action = T.tanh(actions)*T.tensor(self.max_action).to(self.device)
        log_probs = probabilities.log_prob(actions)
        log_probs -= T.log(1 - T.tanh(actions).pow(2) + self.reparam_noise)
        log_probs = log_probs.sum(1, keepdim=True)

        return action, log_probs

    def save_checkpoint(self):
        T.save(self.state_dict(), self.checkpoint_file)

    def load_checkpoint(self):
        self.load_state_dict(T.load(self.checkpoint_file,map_location=T.device('cpu')))
