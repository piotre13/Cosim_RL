import matplotlib.pyplot as plt
from utils import read_json
import numpy as np

from matplotlib.dates import MonthLocator, DateFormatter
import matplotlib.dates as mdates
from datetime import datetime

run1_RL = np.array(read_json('FINAL_scenarios\\baseline20_16_nocapacity\\RLController.json')["DQN_agent"])
run1_envelope = np.array(read_json('FINAL_scenarios\\baseline20_16_nocapacity\\Envelope.json')["Envelope/0/Envelope"])

run2_RL = np.array(read_json('FINAL_scenarios\\baseline20_16_nocapacity\\RLController.json')["DQN_agent"])
run2_envelope = np.array(read_json('FINAL_scenarios\\baseline20_16_nocapacity\\Envelope.json')["Envelope/0/Envelope"])

run3_RL = np.array(read_json('FINAL_scenarios\\baseline20_16_nocapacity\\RLController.json')["DQN_agent"])
run3_envelope = np.array(read_json('FINAL_scenarios\\baseline20_16_nocapacity\\Envelope.json')["Envelope/0/Envelope"])

#plot convergency curves


#plot result of temperature and consumption