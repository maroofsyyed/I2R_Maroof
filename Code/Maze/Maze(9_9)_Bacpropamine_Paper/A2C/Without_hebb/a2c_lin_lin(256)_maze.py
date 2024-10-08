# -*- coding: utf-8 -*-
"""a2c_lin_lin(256)_maze.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1zlSPYLpbmHhPzLXCWuHUBR0AYbjw_GlQ
"""

import numpy as np
import random
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import csv

# ANSI color codes
BLUE = "\033[44m"
RED = "\033[41m"
GREEN = "\033[42m"
CYAN = "\033[46m"
WHITE = "\033[37m"
RESET = "\033[0m"

# Check if CUDA is available and set the device
device = torch.device("cuda:5" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

class MazeEnvironment:
    def __init__(self, size=11):
        self.size = size
        self.maze = self.create_maze()
        self.agent_position = None
        self.reward_position = None
        self.steps = 0
        self.max_steps = 200
        self.reset()

    def create_maze(self):
        maze = np.ones((self.size, self.size))
        maze[1:self.size-1, 1:self.size-1] = 0
        for row in range(1, self.size - 1):
            for col in range(1, self.size - 1):
                if row % 2 == 0 and col % 2 == 0:
                    maze[row, col] = 1
        maze[self.size//2, self.size//2] = 0
        return maze

    def reset(self):
        self.steps = 0
        self.agent_position = self.get_random_empty_position()
        self.reward_position = self.get_random_empty_position()
        return self.get_observation()

    def get_random_empty_position(self):
        empty_positions = np.argwhere(self.maze == 0)
        return tuple(random.choice(empty_positions))

    def get_observation(self):
        i, j = self.agent_position
        neighborhood = self.maze[max(0, i-1):i+2, max(0, j-1):j+2]
        if neighborhood.shape != (3, 3):
            padding = [(0, 3 - neighborhood.shape[0]), (0, 3 - neighborhood.shape[1])]
            neighborhood = np.pad(neighborhood, padding, mode='constant', constant_values=1)
        return neighborhood.flatten()

    def step(self, action):
        self.steps += 1
        i, j = self.agent_position

        if action == 0:  # up
            new_position = (max(0, i - 1), j)
        elif action == 1:  # right
            new_position = (i, min(self.size - 1, j + 1))
        elif action == 2:  # down
            new_position = (min(self.size - 1, i + 1), j)
        elif action == 3:  # left
            new_position = (i, max(0, j - 1))

        if self.maze[new_position] == 0:
            self.agent_position = new_position

        reward = 0
        done = False

        if self.agent_position == self.reward_position:
            reward = 10.0
            self.agent_position = self.get_random_empty_position()
        elif self.maze[new_position] == 1:
            reward = -0.1

        if self.steps >= self.max_steps:
            done = True

        return self.get_observation(), reward, done

    def render(self):
        render_maze = self.maze.copy()
        i, j = self.agent_position
        ri, rj = self.reward_position
        render_maze[i, j] = 2  # Agent
        render_maze[ri, rj] = 3  # Reward

        print(WHITE + "+" + "---+" * self.size + RESET)
        for row in render_maze:
            print(WHITE + "|", end="")
            for cell in row:
                if cell == 1:
                    print(BLUE + "   " + RESET, end=WHITE + "|")
                elif cell == 2:
                    print(RED + " A " + RESET, end=WHITE + "|")
                elif cell == 3:
                    print(GREEN + " R " + RESET, end=WHITE + "|")
                else:
                    print(CYAN + "   " + RESET, end=WHITE + "|")
            print("\n" + WHITE + "+" + "---+" * self.size + RESET)


class ActorCritic(nn.Module):
    def __init__(self, input_size, n_actions):
        super(ActorCritic, self).__init__()
        self.shared = nn.Linear(input_size, 128)
        self.actor = nn.Linear(128, n_actions)
        self.critic = nn.Linear(128, 1)

    def forward(self, x):
        shared = torch.relu(self.shared(x))
        return self.actor(shared), self.critic(shared)


class A2CAgent:
    def __init__(self, input_size, n_actions, learning_rate=0.0005, gamma=0.99):
        self.device = device
        self.gamma = gamma
        self.model = ActorCritic(input_size, n_actions).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)

    def get_action(self, state):
        state = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        logits, _ = self.model(state)
        action_probs = torch.softmax(logits, dim=-1)
        action = torch.multinomial(action_probs, 1).item()
        return action

    def update(self, states, actions, rewards, next_states, dones):
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)

        # Compute advantages
        logits, values = self.model(states)
        _, next_values = self.model(next_states)

        delta = rewards + self.gamma * next_values * (1 - dones) - values
        advantages = delta.detach()

        # Compute losses
        action_probs = torch.softmax(logits, dim=-1)
        log_probs = torch.log(action_probs.gather(1, actions.unsqueeze(1)).squeeze(1))
        actor_loss = -(log_probs * advantages).mean()

        critic_loss = delta.pow(2).mean()

        # Compute entropy bonus
        entropy = -(action_probs * torch.log(action_probs)).sum(1).mean()

        # Total loss
        loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy

        # Update the model
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()


def train(env, agent, n_episodes=10000, max_steps=200):
    rewards_history = []
    csv_data = []

    for episode in range(n_episodes):
        state = env.reset()
        total_reward = 0
        done = False
        step = 0

        states, actions, rewards, next_states, dones = [], [], [], [], []

        while not done and step < max_steps:
            action = agent.get_action(state)
            next_state, reward, done = env.step(action)

            states.append(state)
            actions.append(action)
            rewards.append(reward)
            next_states.append(next_state)
            dones.append(done)

            state = next_state
            total_reward += reward
            step += 1

            if len(states) == 32 or done:  # Update every 32 steps or at the end of episode
                loss = agent.update(states, actions, rewards, next_states, dones)
                states, actions, rewards, next_states, dones = [], [], [], [], []

        rewards_history.append(total_reward)
        avg_reward = np.mean(rewards_history[-100:]) if len(rewards_history) >= 100 else np.mean(rewards_history)

        # Add data for CSV
        csv_data.append([episode, total_reward, avg_reward])

        # Print episodic reward and average reward over last 100 episodes
        print(f"Episode {episode}, Reward: {total_reward:.2f}, Average Reward (last 100): {avg_reward:.2f}")



if __name__ == "__main__":
    # Create environment and agent
    env = MazeEnvironment(size=11)
    input_size = 9  # 3x3 neighborhood
    n_actions = 4  # up, right, down, left
    agent = A2CAgent(input_size, n_actions)

    # Train the agent
    rewards_history = train(env, agent)

    # Test the trained agent
    state = env.reset()
    done = False
    total_reward = 0
    step = 0

    while not done and step < 200:
        env.render()
        action = agent.get_action(state)
        state, reward, done = env.step(action)
        total_reward += reward
        step += 1

    print(f"Test episode finished. Total reward: {total_reward}")



