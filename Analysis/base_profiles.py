import matplotlib.pyplot as plt
from utils import read_json
import numpy as np

from matplotlib.dates import MonthLocator, DateFormatter
import matplotlib.dates as mdates
from datetime import datetime

power_pv = np.array(read_json('FINAL_scenarios\\baseline20_16_nocapacity\\PV.json')["PV/0/PV"]['outputs']['Power_PV'])
radiation = np.array(read_json('FINAL_scenarios\\baseline20_16_nocapacity\\Weather.json')['Weather/0/CSV']['outputs']['glohorzrad'])
drybulb = np.array(read_json('FINAL_scenarios\\baseline20_16_nocapacity\\Weather.json')['Weather/0/CSV']['outputs']['drybulb'])






plt.plot(power_pv[1:25], label='powerPV', marker='o')
plt.legend()
plt.show()
plt.close()



plt.plot(radiation[:24], label='radiation', marker='o')
plt.legend()
plt.show()
plt.close()



plt.plot(drybulb, label='temperature')
plt.legend()
plt.show()
plt.close()










time = np.arange(0, len(power_pv))


fig, ax1 = plt.subplots()

# Plot entity1 using the first y-axis
color = 'tab:red'
ax1.set_xlabel('Time')
ax1.set_ylabel('Entity 1', color=color)
ax1.plot(time, power_pv, color=color, label='power PV', marker='o')
ax1.tick_params(axis='y', labelcolor=color)

# Create a second y-axis sharing the same x-axis
ax2 = ax1.twinx()
color = 'tab:blue'
ax2.set_ylabel('Entity 2', color=color)
ax2.plot(time, radiation, color=color, label='radiation', marker='o')
ax2.tick_params(axis='y', labelcolor=color)

# Create a separate y-axis for entity3
ax3 = ax1.twinx()
color = 'tab:green'
ax3.spines['right'].set_position(('outward', 60))  # Move the spine to the right
ax3.set_ylabel('Entity 3', color=color)
ax3.plot(time, drybulb, color=color, label='temperature', marker='o')
ax3.tick_params(axis='y', labelcolor=color)

# Set x-axis ticks to display months
ax1.xaxis.set_major_locator(MonthLocator())
ax1.xaxis.set_major_formatter(DateFormatter('%b'))

# Display the legend
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
lines3, labels3 = ax3.get_legend_handles_labels()
ax3.legend(lines + lines2 + lines3, labels + labels2 + labels3, loc='best')

plt.show()
