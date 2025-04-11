import json
import matplotlib.pyplot as plt
import numpy as np

# Path to the JSON file
json_file_path = '../federations/SAC_stablebaseline_main/results/RLController.json'



def moving_average(x, w):

    # Define the kernel for the moving average
    kernel = np.ones(w) / w

    return np.convolve(x, kernel, 'same')


# Load the JSON data
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Extract the reward data
rewards = data['reward']
avg = moving_average(np.array(rewards), 100)

# Plot the reward data
#plt.plot(rewards)
plt.plot(avg, label='Moving Average', color='red')
plt.xlabel('Episode')
plt.ylabel('Reward')
plt.title('Reward per Episode')
plt.show()