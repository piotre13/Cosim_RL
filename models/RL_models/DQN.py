import gymnasium as gym

from stable_baselines3 import DQN
from models._baseModels.Model import Model


class DQN(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def step(self, ts, **kwargs):
        pass

    def finalize(self):
        pass
#
#
# env = gym.make("CartPole-v1", render_mode="human")
#
# model = DQN("MlpPolicy", env, verbose=1)
# model.learn(total_timesteps=10000, log_interval=4)
# model.save("dqn_cartpole")
#
# del model # remove to demonstrate saving and loading
#
# model = DQN.load("dqn_cartpole")
#
# obs, info = env.reset()
# while True:
#     action, _states = model.predict(obs, deterministic=True)
#     obs, reward, terminated, truncated, info = env.step(action)
#     if terminated or truncated:
#         obs, info = env.reset()
