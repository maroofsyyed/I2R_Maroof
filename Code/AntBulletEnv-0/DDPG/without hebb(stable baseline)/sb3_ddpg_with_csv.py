# -*- coding: utf-8 -*-
"""sb3_ddpg_with_csv.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1zlSPYLpbmHhPzLXCWuHUBR0AYbjw_GlQ
"""

import gym
from stable_baselines3 import DDPG
from stable_baselines3.common.noise import NormalActionNoise
from stable_baselines3.common.vec_env import DummyVecEnv
import numpy as np
import csv

# Hyperparameters
hidden_dim = 256
buffer_size = 1000000
batch_size = 1024  # Reduced batch size to fit in memory
actor_lr = 1e-4
critic_lr = 1e-3
tau = 4e-3
gamma = 0.96
episodes = 1000
max_steps = 1000

# Create environment
env = gym.make('AntBulletEnv-v0')
env = DummyVecEnv([lambda: env])

# Create action noise
n_actions = env.action_space.shape[-1]
action_noise = NormalActionNoise(mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions))

# Define DDPG policy architecture
policy_kwargs = dict(
    net_arch=dict(pi=[hidden_dim, hidden_dim], qf=[hidden_dim, hidden_dim])
)

# Custom learning rate function
def custom_lr_fn(progress_remaining):
    param_name = str(progress_remaining)
    if "actor" in param_name:
        return actor_lr
    elif "critic" in param_name:
        return critic_lr
    else:
        return 1e-3  # default learning rate

# Create the DDPG agent
model = DDPG(
    "MlpPolicy",
    env,
    buffer_size=buffer_size,
    batch_size=batch_size,
    action_noise=action_noise,
    learning_rate=custom_lr_fn,
    gamma=gamma,
    tau=tau,
    verbose=1,
    policy_kwargs=policy_kwargs,
    device='cuda:7'  # Ensure the model is using CUDA
)

# Train the model and print rewards
episode_rewards = []

# Create CSV file
with open('training_results.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['Episode', 'Reward', 'Average Reward (Last 100)'])

    # Inside the training loop:
    for episode in range(episodes):
        obs = env.reset()
        total_reward = 0
        for step in range(max_steps):
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, done, _ = env.step(action)
            total_reward += reward.item() if isinstance(reward, np.ndarray) else reward
            if done:
                break

        episode_rewards.append(total_reward)

        # Calculate average reward for the last 100 episodes
        avg_reward = np.mean(episode_rewards[-100:]) if len(episode_rewards) >= 100 else np.nan

        # Print results
        print(f"Episode {episode + 1}: Total Reward = {float(total_reward):.2f}, Average Reward (Last 100) = {float(avg_reward):.2f}")

        # Write to CSV
        csvwriter.writerow([episode + 1, float(total_reward), float(avg_reward)])

        # Learn from the experience
        model.learn(total_timesteps=max_steps, log_interval=10)

# Save the model
model.save("ddpg_antbullet")

# Test the trained agent
obs = env.reset()
for _ in range(max_steps):
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, done, _ = env.step(action)
    env.render()
    if done:
        obs = env.reset()
env.close()

# Print final results
print("\nTraining completed!")
print(f"Final Average Reward (Last 100 Episodes): {np.mean(episode_rewards[-100:]):.2f}")

