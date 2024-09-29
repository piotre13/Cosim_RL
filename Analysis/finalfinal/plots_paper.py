import matplotlib.pyplot as plt
from utils import read_json
import numpy as np
import os


def moving_average(x, w):

    # Define the kernel for the moving average
    kernel = np.ones(w) / w

    return np.convolve(x, kernel, 'same')


casestudy = "dest_setpoint_myrew_gamma0.95"

weather = read_json(os.path.join(casestudy,'Weather.json'))['Weather/0/CSV']
env_data =read_json(os.path.join(casestudy,'Envelope.json'))['Envelope/0/Envelope']
rlagent =read_json(os.path.join(casestudy,'RLController.json'))['DQN_agent']
baseline = read_json("baselineDest\\Envelope.json")['Envelope/0/Envelope']
t1B = baseline['outputs']['zone.ac_t 8674']
t2B = baseline['outputs']['zone.ac_t 8677']
t3B = baseline['outputs']['zone.ac_t 8680']
t4B = baseline['outputs']['zone.ac_t 8692']
t5B = baseline['outputs']['zone.ac_t 73086']
q1B = baseline['outputs']['zone.vent_q 8674']
q2B = baseline['outputs']['zone.vent_q 8677']
q3B = baseline['outputs']['zone.vent_q 8680']
q4B = baseline['outputs']['zone.vent_q 8692']
q5B = baseline['outputs']['zone.vent_q 73086']

q_totB = [sum(x) for x in zip(*[q1B,q2B,q3B,q4B,q5B])]



#learning curves

cum_reward = rlagent['cum_reward']
cum_rew_avg = moving_average(cum_reward,300)



#******************************Learning******************************************************************************************************
fig, ax = plt.subplots()
fig.set_size_inches(6, 4)  # Set the figure size
# Plotting the data with customizations
ax.plot(cum_reward[:-300], color='grey', label='cumulative reward')
ax.plot(cum_rew_avg[:-300], color='orange', linestyle='--', label='rolling mean')
# Adding labels and legend
ax.set_xlabel('number episodes', fontsize=12)
ax.set_ylabel('cumulative reward value', fontsize=12)
ax.legend()
# Set grid and ticks
ax.grid(True, linestyle='--', alpha=0.6)
ax.tick_params(axis='both', which='major', labelsize=10)
# Save the plot as a high-quality image for publication
plt.tight_layout()
# plt.show()
plt.savefig(f'cum_reward_{casestudy}.png', dpi=300)  # Save the plot as a PNG with high resolution
plt.clf()
plt.close()
#************************************************************************************************************************************




#physical results
text = weather['outputs']['drybulb']
t1 = env_data['outputs']['zone.ac_t 8674']
t2 = env_data['outputs']['zone.ac_t 8677']
t3 = env_data['outputs']['zone.ac_t 8680']
t4 = env_data['outputs']['zone.ac_t 8692']
t5 = env_data['outputs']['zone.ac_t 73086']


q1 = env_data['outputs']['zone.vent_q 8674']
q2 = env_data['outputs']['zone.vent_q 8677']
q3 = env_data['outputs']['zone.vent_q 8680']
q4 = env_data['outputs']['zone.vent_q 8692']
q5 = env_data['outputs']['zone.vent_q 73086']

q_tot = [sum(x) for x in zip(*[q1,q2,q3,q4,q5])]



#plot temperatures
room_temps=[t1,t2,t3,t4,t5]

num_days = 2
start = 2
start_hour = start * 24
hours_per_day = 24
total_hours = num_days * hours_per_day
x = np.arange(total_hours)  # Create x-axis values for total hours




#******************************TEMP ENERGY******************************************************************************************************
fig, (ax, ax3) = plt.subplots(2, 1, figsize=(10, 8))
cmap = plt.get_cmap('inferno')  # Choose a colormap (e.g., 'viridis')
# Plotting the first temperature profile
i=0
for t in room_temps:
    color = cmap(i / len(room_temps))  # Choose color based on the colormap
    ax.plot(x, t[start_hour:start_hour+num_days*24], color = color,label='room %s (°C)'%i)
    i+=1
ax2 = ax.twinx()
color = (79/255, 148/255, 205/255)
ax2.set_ylabel('Outdoor temperature (°C)', color=color)
ax2.plot(x, text[start_hour:start_hour+num_days*24], color=color)
ax2.tick_params(axis='y', labelcolor=color)
# Shrink the scale of the right y-axis to avoid overlap
ax2.set_ylim(-15, 50)  # Adjust the limits as needed
# Adding labels and legend
ax.set_xlabel('Time (hours)')
ax.set_ylabel('Temperature (°C)')
# plt.title('Temperature Profiles')
# Define the subset of hours to display on the x-axis
hour_subset = [0, 3, 6, 9, 12, 15, 18, 21]  # Adjust as needed
hour_ticks = [hour + day * hours_per_day for day in range(num_days) for hour in hour_subset]
hour_labels = [f'{hour % hours_per_day:02d}:00' for hour in hour_subset]
ax.grid(True, linestyle='--', alpha=0.6)
for n in range(num_days):
    if n ==0:
        ax.axvspan(6+(n)*24, 19+(n)*24, color='yellow', alpha=0.2, label='working hours')
    else:
        ax.axvspan(6+(n)*24, 19+(n)*24, color='yellow', alpha=0.2)
ax.legend(ncol = num_days, loc='upper left')
# Set the xticks locations
ax.set_xticks(hour_ticks)
# Set the xtick labels
ax.set_xticklabels(hour_labels * num_days, rotation=45)
ax3.plot(q_tot[start_hour:start_hour+num_days*24], color='red', label='Energy RL')
ax3.plot(q_totB[start_hour:start_hour+num_days*24], color='blue', label='Energy baseline')
ax3.set_xlabel('Time (hours)')
ax3.set_ylabel('Energy (W/h)')
# ax3.set_title('Energy consumption profile')
# ax.legend(ncol = num_days, loc='upper left')
ax3.grid(True, linestyle='--', alpha=0.6)
for n in range(num_days):
    ax3.axvspan(7+(n)*24, 20+(n)*24, color='yellow', alpha=0.2)
# Set the xticks locations
ax3.set_xticks(hour_ticks)
ax3.set_xticklabels(hour_labels * num_days, rotation=45)
ax3.legend()
# Adjusting the layout
fig.tight_layout()
# plt.show()
plt.savefig(f'Temp_Energy_{casestudy}.png')  # Save the plot as a PNG with high resolution
plt.clf()
plt.close()
#************************************************************************************************************************************

#******************************1 ROOM VS BASELINE ******************************************************************************************************
fig, (ax, ax3) = plt.subplots(2, 1, figsize=(10, 8))
cmap = plt.get_cmap('inferno')  # Choose a colormap (e.g., 'viridis')
# Plotting the first temperature profile
ax.plot(x, t1B[start_hour:start_hour+num_days*24], color = 'blue',label='room 3 -  baseline')
ax.plot(x, t1[start_hour:start_hour+num_days*24], color = 'red',label='room 3 -  RL')
ax.axhspan(19, 21.0, color='orange', alpha=0.5, label = "acceptable range")

ax2 = ax.twinx()
color = (79/255, 148/255, 205/255)
ax2.set_ylabel('Outdoor temperature (°C)', color=color)
ax2.plot(x, text[start_hour:start_hour+num_days*24], color=color)
ax2.tick_params(axis='y', labelcolor=color)
# Shrink the scale of the right y-axis to avoid overlap
ax2.set_ylim(-15, 50)  # Adjust the limits as needed
# Adding labels and legend
ax.set_xlabel('Time (hours)')
ax.set_ylabel('Temperature (°C)')
# plt.title('Temperature Profiles')
# Define the subset of hours to display on the x-axis
hour_subset = [0, 3, 6, 9, 12, 15, 18, 21]  # Adjust as needed
hour_ticks = [hour + day * hours_per_day for day in range(num_days) for hour in hour_subset]
hour_labels = [f'{hour % hours_per_day:02d}:00' for hour in hour_subset]
ax.grid(True, linestyle='--', alpha=0.6)
for n in range(num_days):
    if n ==0:
        ax.axvspan(7+(n)*24, 20+(n)*24, color='yellow', alpha=0.2, label='working hours')
    else:
        ax.axvspan(7+(n)*24, 20+(n)*24, color='yellow', alpha=0.2)
ax.legend(ncol = 4, loc='upper center', bbox_to_anchor=(0.5, 1.15))
# Set the xticks locations
ax.set_xticks(hour_ticks)
# Set the xtick labels
ax.set_xticklabels(hour_labels * num_days, rotation=45)
ax3.plot(q1[start_hour:start_hour+num_days*24], color='red', label='Energy RL room 1')
ax3.plot(q1B[start_hour:start_hour+num_days*24], color='blue', label='Energy baseline room 1')
ax3.set_xlabel('Time (hours)')
ax3.set_ylabel('Energy (W/h)')
# ax3.set_title('Energy consumption profile')
# ax.legend(ncol = num_days, loc='upper left')
ax3.grid(True, linestyle='--', alpha=0.6)
for n in range(num_days):
    ax3.axvspan(7+(n)*24, 20+(n)*24, color='yellow', alpha=0.2)
# Set the xticks locations
ax3.set_xticks(hour_ticks)
ax3.set_xticklabels(hour_labels * num_days, rotation=45)
ax3.legend()
# Adjusting the layout
fig.tight_layout()

plt.savefig(f'ROOMvsBase_{casestudy}.png')  # Save the plot as a PNG with high resolution
plt.clf()
plt.close()
#************************************************************************************************************************************



#******************************TEMP ENERGY TOTAL******************************************************************************************************

avg_temp_tot = [sum(x)/5 for x in zip(*[t1,t2,t3,t4,t5])]



fig, (ax, ax3) = plt.subplots(2, 1, figsize=(10, 8))
# Plotting the first temperature profile
ax.plot(avg_temp_tot,color='black',label='Average temperature 5 rooms (°C)')

ax2 = ax.twinx()
color = (79/255, 148/255, 205/255)
ax2.set_ylabel('Outdoor temperature (°C)', color=color)
ax2.plot(text, color=color)
ax2.tick_params(axis='y', labelcolor=color)
# Shrink the scale of the right y-axis to avoid overlap
ax2.set_ylim(-15, 50)  # Adjust the limits as needed
# Adding labels and legend
ax.set_xlabel('Time (hours)')
ax.set_ylabel('Temperature (°C)')
# plt.title('Temperature Profiles')
# Define the subset of hours to display on the x-axis
ax.grid(True, linestyle='--', alpha=0.6)

ax.axvspan(0, 31*24, color='yellow', alpha=0.1, label='January')
ax.axvspan(31*24, (31+28)*24, color='orange', alpha=0.1, label='February')
ax.axvspan((31+28)*24, (31+28+31)*24, color='red', alpha=0.1, label='March')

ax.legend(ncol=4, loc='upper left',framealpha=1)
# Set the xticks locations
# hour_subset = [0, 3, 6, 9, 12, 15, 18, 21]  # Adjust as needed
# hour_ticks = [hour + day * hours_per_day for day in range(num_days) for hour in hour_subset]
# hour_labels = [f'{hour % hours_per_day:02d}:00' for hour in hour_subset]
# ax.set_xticks(hour_ticks)
# ax.set_xticklabels(hour_labels * num_days, rotation=45)



ax3.plot(q_tot, color='red', label='Energy RL')
ax3.set_xlabel('Time (hours)')
ax3.set_ylabel('Energy (W/h)')
# ax3.set_title('Energy consumption profile')
# ax.legend(ncol = num_days, loc='upper left')
ax3.grid(True, linestyle='--', alpha=0.6)
ax3.axvspan(0, 31*24, color='yellow', alpha=0.1, label='January')
ax3.axvspan(31*24, (31+28)*24, color='orange', alpha=0.1, label='February')
ax3.axvspan((31+28)*24, (31+28+31)*24, color='red', alpha=0.1, label='March')
# Set the xticks locations
# ax3.set_xticks(hour_ticks)
# ax3.set_xticklabels(hour_labels * num_days, rotation=45)
ax3.legend(framealpha=1,facecolor='lightgrey')
# Adjusting the layout
fig.tight_layout()
# plt.show()
plt.savefig(f'Totals_{casestudy}.png', dpi=300)  # Save the plot as a PNG with high resolution
plt.clf()
plt.close()