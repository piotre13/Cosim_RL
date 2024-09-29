import matplotlib.pyplot as plt
from utils import read_json
import numpy as np



d1 = np.array(read_json('FINAL_scenarios\\FMU_nolim_20_gamma090\\RLController.json')['DQN_agent']['cum_reward'][1:100])
d2 = np.array(read_json('FINAL_scenarios\\FMU_nolim_20_gamma095\\RLController.json')['DQN_agent']['cum_reward'][1:100])
d3 = np.array(read_json('FINAL_scenarios\\FMU_nolim_20_gamma099\\RLController.json')['DQN_agent']['cum_reward'][1:100])



data_list = [d1, d2, d3]
gamma = ['0.90', '0.95', '0.99']
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(15, 5))  # Adjust the figure size as needed

for i in range(len(data_list)):

	# Calculate the rolling average and standard deviation
	rolling_mean = np.convolve(data_list[i], np.ones(10) / 10, mode='same')  # 10-period rolling average
	rolling_std = np.zeros(len(data_list[i]))
	ax[i].plot(data_list[i], label='cum reward gamma=%s'%gamma[i])
	ax[i].plot(rolling_mean, label='rolling mean')
	for j in range(len(data_list[i])):
		if j < 5:
			rolling_std[j] = np.std(data_list[i][:j + 5])
		elif j > len(data_list[i]) - 6:
			rolling_std[j] = np.std(data_list[i][j - 5:])
		else:
			rolling_std[j] = np.std(data_list[i][j - 5:j + 5])
	ax[i].fill_between(range(len(data_list[i])), rolling_mean - 1.96 * rolling_std, rolling_mean + 1.96 * rolling_std,
					   color='gray', alpha=0.2)

	ax[1].set_xlabel('number of episodes', fontsize=15)  # Set x-axis label with increased font size
	ax[0].set_ylabel('cum reward value', fontsize=15)  # Set y-axis label with increased font size
	ax[i].legend(fontsize=15, loc='lower right')  # Show legend with increased font size
	ax[i].tick_params(axis='both', which='major', labelsize=15)  # Adjust tick label size to prevent overlapping
	ax[i].grid(color='lightgray', linestyle='-', linewidth=0.5)  # Add a less visible grid

plt.tight_layout()  # Adjust subplots to prevent overlapping
plt.show()