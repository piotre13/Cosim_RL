import matplotlib.pyplot as plt
from utils import read_json
import numpy as np

def moving_average(x, w):

    # Define the kernel for the moving average
    kernel = np.ones(w) / w

    return np.convolve(x, kernel, 'same')





# baseline =  read_json("old_tests/baseline\\RLController.json")
data = read_json("../federations/dest_ventq_new/results/RLController.json")
# data = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\Analysis\\finalfinal\\dest_setpoint_myrew_gamma0.9\\RLController.json")

# envelope_bas = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control_Dest\\results\\Envelope.json")
# envelope = read_json("scenarios_test\\niceone\\Envelope.json")
#
# t_1 = np.array(envelope['Envelope/0/Envelope']['outputs']['zone.ac_t 8674'][1:72])
# t_2 = np.array(envelope['Envelope/0/Envelope']['outputs']['zone.ac_t 8677'][1:72])
# t_3 = np.array(envelope['Envelope/0/Envelope']['outputs']['zone.ac_t 8680'][1:72])
# t_4 = np.array(envelope['Envelope/0/Envelope']['outputs']['zone.ac_t 8692'][1:72])
# t_5 = np.array(envelope['Envelope/0/Envelope']['outputs']['zone.ac_t 73086'][1:72])
#
# t_1B = np.array(envelope_bas['Envelope/0/Envelope']['outputs']['zone.ac_t 8674'][1:72])
# t_2B = np.array(envelope_bas['Envelope/0/Envelope']['outputs']['zone.ac_t 8677'][1:72])
# t_3B = np.array(envelope_bas['Envelope/0/Envelope']['outputs']['zone.ac_t 8680'][1:72])
# t_4B = np.array(envelope_bas['Envelope/0/Envelope']['outputs']['zone.ac_t 8692'][1:72])
# t_5B = np.array(envelope_bas['Envelope/0/Envelope']['outputs']['zone.ac_t 73086'][1:72])
#
#
#
#
# q_1 = np.array(envelope['Envelope/0/Envelope']['outputs']['zone.vent_q 8674'][1:])
# q_2 = np.array(envelope['Envelope/0/Envelope']['outputs']['zone.vent_q 8677'][1:])
# q_3 = np.array(envelope['Envelope/0/Envelope']['outputs']['zone.vent_q 8680'][1:])
# q_4 = np.array(envelope['Envelope/0/Envelope']['outputs']['zone.vent_q 8692'][1:])
# q_5 = np.array(envelope['Envelope/0/Envelope']['outputs']['zone.vent_q 73086'][1:])
#
# q_1B = np.array(envelope_bas['Envelope/0/Envelope']['outputs']['zone.vent_q 8674'][1:])
# q_2B = np.array(envelope_bas['Envelope/0/Envelope']['outputs']['zone.vent_q 8677'][1:])
# q_3B = np.array(envelope_bas['Envelope/0/Envelope']['outputs']['zone.vent_q 8680'][1:])
# q_4B = np.array(envelope_bas['Envelope/0/Envelope']['outputs']['zone.vent_q 8692'][1:])
# q_5B = np.array(envelope_bas['Envelope/0/Envelope']['outputs']['zone.vent_q 73086'][1:])
#
#
#
#
# tot2 = sum(q_2+q_1+q_4+q_5+q_3)
# tot2_bas = sum(q_2B+q_5B+q_3B+q_4B+q_1B)
#
#
# # avg = (t_1+t_2+t_3+t_4+t_5)/5
#
# #
# plt.plot(t_1, label='temp1')
# plt.plot(t_2, label='temp2')
# plt.plot(t_3, label='temp3')
# plt.plot(t_4, label='temp4')
# plt.plot(t_5, label='temp5')
# plt.legend()
# plt.show()
# plt.close()
#
# # plt.plot(q_1, label='Q1')
# plt.plot(q_2, label='Q2')
# plt.plot(q_2B, label='Q2_base')
# # plt.plot(q_4, label='Q4')
# # plt.plot(q_5, label='Q5')
# plt.legend()
# plt.show()
# plt.close()
# envelope_baseline = read_json("old_tests/baseline\\Envelope.json")
# envelope_controlled = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\Envelope.json")
# weather = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\Weather.json")
#
# power_baseline = np.array(envelope_baseline['Envelope/0/Envelope']['outputs']['zone.vent_q 8674']) + np.array(envelope_baseline['Envelope/0/Envelope']['outputs']['zone.vent_q 8677']) + np.array(envelope_baseline['Envelope/0/Envelope']['outputs']['zone.vent_q 8680']) +np.array(envelope_baseline['Envelope/0/Envelope']['outputs']['zone.vent_q 8692']) +np.array(envelope_baseline['Envelope/0/Envelope']['outputs']['zone.vent_q 73086'])
# power_controlled = np.array(envelope_controlled['Envelope/0/Envelope']['outputs']['zone.vent_q 8674']) + np.array(envelope_controlled['Envelope/0/Envelope']['outputs']['zone.vent_q 8677']) + np.array(envelope_controlled['Envelope/0/Envelope']['outputs']['zone.vent_q 8680']) +np.array(envelope_controlled['Envelope/0/Envelope']['outputs']['zone.vent_q 8692']) +np.array(envelope_controlled['Envelope/0/Envelope']['outputs']['zone.vent_q 73086'])
#
# controlled_setpoint = envelope_controlled['Envelope/0/Envelope']['inputs']['schedule.ac_t_max 8674']
# baseline_setpoint = envelope_baseline['Envelope/0/Envelope']['inputs']['schedule.ac_t_max 8674']
#
# controlled_air = envelope_controlled['Envelope/0/Envelope']['outputs']['zone.ac_t 8674']
# baseline_air = envelope_baseline['Envelope/0/Envelope']['outputs']['zone.ac_t 8674']
# t_ext = weather['Weather/0/CSV']['outputs']['drybulb']
#
# check_ = envelope_controlled['Envelope/0/Envelope']['outputs']['zone.vent_q 8674']
#
# max = max(power_controlled)
# argmax = power_controlled.argmax()
#
# tot_power_baseline=sum(abs(power_baseline/3600))
# tot_power_controlled = sum(abs(power_controlled/3600))
#
# print(f"Power consumption baseline: {tot_power_baseline}")
# print(f"Power consumption RL: {tot_power_controlled}")
#
# power_sorted = sorted(power_baseline)
#
# plt.plot(power_sorted)
# plt.show()
# plt.close()
#


cum_reward = data['DQN_agent']['cum_reward'][1:]
cum_rew_avg = moving_average(cum_reward,30)[30:-30]
reward = data['DQN_agent']['reward'][1:]
C1 = np.array(data['DQN_agent']['C1_temp'][1:])
C2 = np.array(data['DQN_agent']['C2_power'][1:])

plt.plot(C1, label='C1_temp')
plt.legend()
plt.show()
plt.close()
plt.plot(C2, label='C2_power')
plt.legend()
plt.show()
plt.close()

#
# tmp = np.where(C1>63)






#
# plt.plot(power_baseline)
# plt.plot(power_controlled)
# plt.show()
# plt.close()
#
#
# plt.plot(controlled_setpoint, label='RL-setpoint')
# plt.plot(baseline_setpoint, label ='Scheduled-setpoint')
# plt.legend()
# plt.show()
# plt.close()
#
#
#
# # plt.plot(t_ext, label ='t_ext')
# # plt.plot(controlled_setpoint[1500:1800], label='RL-setpoint')
# plt.plot(controlled_air, label ='RL-tair')
# plt.plot(baseline_air, label= 'baseline_air')
# plt.legend()
# plt.show()
# plt.close()
#
#
#
# plt.plot(t_ext, label ='t_ext')
# plt.plot(baseline_setpoint, label='baseline-setpoint')
# plt.plot(baseline_air, label ='baseline_tair')
# plt.legend()
# plt.show()
# plt.close()

print('stocazz')
# # data = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\RLController_gamma09.json")
# data1 = read_json("/Analysis/RLController_gamma08.json")
# data2 = read_json("/Analysis/RLController_gamma07.json")
# data3 = read_json("/Analysis/RLController_base.json")

#
#
# data_env = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\Envelope.json")
#
# data_con = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\federations\\test_case_dest_setpoint_control\\results\\Controller.json")


# pos_max = np.argmax(data["DQN_agent"]['cum_reward'])
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



# plt.plot(data['DQN_agent']['cum_reward'])
# plt.show()
#
# plt.plot(data_env['Envelope/0/Envelope']['outputs']["zone.ac_t 8674"][1:1440])
# plt.show()
#
#
# reward = data["DQN_agent"]['cum_reward'][1:]
# # reward1 = data1["DQN_agent"]['cum_reward'][1:]
# # reward2 = data2["DQN_agent"]['cum_reward'][1:]
# # reward3 = data3["DQN_agent"]['cum_reward'][1:]
#
# ep_reward = np.array(reward)
# # ep_reward1 = np.array(reward1)
# # ep_reward2 = np.array(reward2)
# # ep_reward3 = np.array(reward3)


# def moving_average_1(a, n=3):
#     ret = np.cumsum(a, dtype=float)
#     ret[n:] = ret[n:] - ret[:-n]
#     return ret[n - 1:] / n








plt.plot(cum_reward[:-30], label= 'cum_reward')
plt.plot(cum_rew_avg, label='CUM_AVG_reward')
plt.legend()
plt.show()
plt.close()

plt.plot(reward, label= 'reward')
plt.legend()
plt.show()
plt.close()



#
# plt.plot(C2, label= 'C2')
# plt.legend()
# plt.show()
# plt.close()
