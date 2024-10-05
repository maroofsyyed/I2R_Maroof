Initiatives: Explored Brain-Inspired learning methods, specifically Hebbian learning, as an alternatives to Stochastic Gradient Descent (SGD) in state-of-the-art reinforcement learning algorithms like DQN, DDPG, A2C and PPO

Approach: Tested Hebbian learning algorithms on some custom built Maze Exploration Tasks and Gymnasium environments like CartPole-v0, MountainCar-v0, AntBulletEnv-v0 comparing results with non-Hebbian counterparts

Results: Ran several batches of hyperparameter tuning, concluding that Hebbian-DDPG learned faster than the Stable Baselines3(SB3)-DDPG on AntBullet-V0, and Hebbian-DQN outperformed non-Hebbian DQN on some maze task
