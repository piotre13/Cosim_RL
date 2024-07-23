import matplotlib.pyplot as plt
from utils import read_json
import numpy as np


data = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\RLController.json")

# data = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\RLController_gamma09.json")
data1 = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\RLController_gamma08.json")
data2 = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\RLController_gamma07.json")
data3 = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\RLController_base.json")



data_env = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\Envelope.json")

data_con = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\Controller.json")


pos_max = np.argmax(data["DQN_agent"]['cum_reward'])
# pos_max1 = np.argmax(data1["DQN_agent"]['cum_reward'])
# pos_max2 = np.argmax(data2["DQN_agent"]['cum_reward'])
# pos_max3 = np.argmax(data3["DQN_agent"]['cum_reward'])

#
# plt.plot(data['DQN_agent']['reward'][1:])
# plt.show()

# plt.plot(data_env['Envelope/0/Envelope']['outputs']["zone.ac_t 8674"][])
# plt.plot(data_env['Envelope/0/Envelope']['outputs']["zone.ac_t 8677"][])
# plt.plot(data_env['Envelope/0/Envelope']['outputs']["zone.ac_t 8680"][])
# plt.plot(data_env['Envelope/0/Envelope']['outputs']["zone.ac_t 8692"][])
# plt.plot(data_env['Envelope/0/Envelope']['outputs']["zone.ac_t 73086"][1:])
# plt.plot(data_con['Controller/0/Controller']['outputs']["tSetMax"][1:])


plt.plot(data['DQN_agent']['cum_reward'][1:1440])
plt.show()

plt.plot(data_env['Envelope/0/Envelope']['outputs']["zone.ac_t 8674"][1:1440])
plt.show()


reward = data["DQN_agent"]['cum_reward'][1:]
reward1 = data1["DQN_agent"]['cum_reward'][1:]
reward2 = data2["DQN_agent"]['cum_reward'][1:]
reward3 = data3["DQN_agent"]['cum_reward'][1:]

ep_reward = np.array(reward)
ep_reward1 = np.array(reward1)
ep_reward2 = np.array(reward2)
ep_reward3 = np.array(reward3)


def moving_average_1(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

avg_reward = moving_average(ep_reward, 48)
avg_reward1 = moving_average(ep_reward1, 48)
avg_reward2 = moving_average(ep_reward2, 48)
avg_reward3 = moving_average(ep_reward3, 48)

print(f"max reward episode : {pos_max},max avg reward using  24 window:{np.argmax(avg_reward)}, over tot number of episode: {len(data['DQN_agent']['cum_reward'])}!")


# plt.plot(avg_reward)

plt.plot(avg_reward,label='0.9')
# plt.plot(avg_reward1, label='0.8')
# plt.plot(avg_reward2,label='0.7')
# plt.plot(avg_reward3,label='base')
plt.legend()
plt.show()
plt.close()
#
# data = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\Hvac_09.json")
# data1 = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\Hvac_08.json")
# data2 = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\Hvac_07.json")
# data3 = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\Hvac.json")
#
#
# power = data["Hvac/0/Hvac"]['outputs']['electrical_power'][1:24]
# power1 = data1["Hvac/0/Hvac"]['outputs']['electrical_power'][1:24]
# power2 = data2["Hvac/0/Hvac"]['outputs']['electrical_power'][1:24]
# power3 = data3["Hvac/0/Hvac"]['outputs']['electrical_power'][1:24]
#
#
#
#
# print(f"tot consumption 09: {sum(power)} \n 08: {sum(power1)} \n  07: {sum(power2)} \n base: {sum(power3)}")
#


# # plt.plot(power,label='0.9')
# # plt.plot(power1, label='0.8')
# plt.plot(power2,label='0.7')
# plt.plot(power3,label='base')
# plt.legend()
# plt.show()