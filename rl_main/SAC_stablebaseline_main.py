from stable_baselines3 import SAC

def main(env):

    model = SAC("MultiInputPolicy", env, learning_rate=0.0003, buffer_size=1000000, learning_starts=100, batch_size=1000,
                tau=0.005, gamma=0.99, train_freq=10, gradient_steps=1, action_noise=None, replay_buffer_class=None, replay_buffer_kwargs=None,
                optimize_memory_usage=False, ent_coef='auto', target_update_interval=1, target_entropy='auto', use_sde=False, sde_sample_freq=-1,
                use_sde_at_warmup=False, stats_window_size=100, tensorboard_log=None, policy_kwargs=None, verbose=1, seed=None, device='auto',
                _init_setup_model=True)
    model.learn(total_timesteps=17520, callback=None, log_interval=4, tb_log_name='SAC', reset_num_timesteps=True, progress_bar=False)
    model.save("best_model")

    vec_env = model.get_env()
    obs = vec_env.reset()
    for i in range(720):
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, info = vec_env.step(action)
        # if done:
        #     obs, info = env.reset()

    env.save_fed_memory()
    env.finalize()