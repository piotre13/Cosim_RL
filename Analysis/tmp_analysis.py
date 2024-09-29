import matplotlib.pyplot as plt
from utils import read_json
import numpy as np


#
# def capacity_lim():
# 	capacity_limit = []
#
# 	list_q = [q_1, q_2, q_3, q_4, q_5]
#
# 	for q in list_q:
# 		q = sorted(q, reverse=True)
# 		perc20 = int(len(q) * 0.2)
# 		q = q[perc20:]
# 		capacity_limit.append(q[0])
#
#
#
#
envelope_data = read_json("C:\\Users\\Pietro\\Code\\Cosim_RL\\Analysis\\finalfinal\\baselineDest\\Envelope.json")
#
#
#
# baseline_data = read_json("FINAL_scenarios\\baseline20_16_nocapacity\\Envelope.json")
# # RL_data = read_json("FINAL_scenarios\\final_1_noCap\\Envelope.json")
#
q_1 = np.array(envelope_data['Envelope/0/Envelope']['outputs']['zone.vent_q 8674'])[:720]
q_2 = np.array(envelope_data['Envelope/0/Envelope']['outputs']['zone.vent_q 8677'])[:720]
q_3 = np.array(envelope_data['Envelope/0/Envelope']['outputs']['zone.vent_q 8680'])[:720]
q_4 = np.array(envelope_data['Envelope/0/Envelope']['outputs']['zone.vent_q 8692'])[:720]
q_5 = np.array(envelope_data['Envelope/0/Envelope']['outputs']['zone.vent_q 73086'])[:720]

q_tot = q_1+q_2+q_3+q_4+q_5

sorted_qtot = sorted(q_tot)


plt.plot(sorted_qtot)
plt.show()
plt.close()


print('yo')

power_values = list(np.linspace(sorted_qtot[100], sorted_qtot[350],20))
power_values.insert(0,0.0)
power_values.append(max(sorted_qtot))

print('yo')

#
# q_1B = np.array(baseline_data['Envelope/0/Envelope']['outputs']['zone.vent_q 8674'])
# t1_B = np.array(baseline_data['Envelope/0/Envelope']['outputs']['zone.ac_t 8674'])
# q_2B = np.array(envelope_data['Envelope/0/Envelope']['outputs']['zone.vent_q 8674'])
# t2_B = np.array(envelope_data['Envelope/0/Envelope']['outputs']['zone.ac_t 8674'])
# # q_2B = np.array(baseline_data['Envelope/0/Envelope']['outputs']['zone.vent_q 8677'])
# # q_3B = np.array(baseline_data['Envelope/0/Envelope']['outputs']['zone.vent_q 8680'])
# # q_4B = np.array(baseline_data['Envelope/0/Envelope']['outputs']['zone.vent_q 8692'])
# # q_5B = np.array(baseline_data['Envelope/0/Envelope']['outputs']['zone.vent_q 73086'])
#
#
#
# plt.plot(q_1B[0:24], label='q1hour', marker='o')
# plt.legend()
# plt.show()
# plt.close()
#
# plt.plot(t1_B[0:24], label='T1hour', marker='o')
# plt.legend()
# plt.show()
# plt.close()
#
# plt.plot(q_2B[0:96], label='q15min', marker='o')
# plt.legend()
# plt.show()
# plt.close()
#
# plt.plot(t2_B[0:96], label='T15min', marker='o')
# plt.legend()
# plt.show()
# plt.close()
#
#
#
#
#
#
# tot_q_baseline = sum(q_1B+q_2B+q_3B+q_4B+q_5B)
# tot_q_RL = sum(q_1+q_2+q_3+q_4+q_5)
# perc_reduction = ((tot_q_baseline-tot_q_RL)/tot_q_baseline)*100
#
# print(f"tot Q baseline: {tot_q_baseline} --- tot q RL = {tot_q_RL} -- percentual reduction = {perc_reduction} %")
#
# # plt.plot(q_1, label='q1')
# # plt.plot(q_1B, label='q1B')
# plt.plot(q_1B[0:24], label='q1B', marker='o')
# # plt.plot(q_3, label='q3')
# # plt.plot(q_3B, label='q3B')
# # plt.plot(q_4, label='q4')
# # plt.plot(q_4B, label='q4B')
# # plt.plot(q_5, label='q5')
# # plt.plot(q_5B, label='q5B')
# plt.legend()
# plt.show()
# plt.close()
#
# plt.plot(t1_B[0:24], label='T1B', marker='o')
# # plt.plot(q_3, label='q3')
# # plt.plot(q_3B, label='q3B')
# # plt.plot(q_4, label='q4')
# # plt.plot(q_4B, label='q4B')
# # plt.plot(q_5, label='q5')
# # plt.plot(q_5B, label='q5B')
# plt.legend()
# plt.show()
# plt.close()
#
# print('yo')
#
#
#
#
#
#
#
# # tot_vent_q = abs(t_1+t_2+t_3+t_4+t_5)
# # min_value = tot_vent_q.min()
# # max_value = tot_vent_q.max()
# # actions=list( np.linspace(min_value, max_value, 30))
# # actions_geom= list(np.geomspace(0.001, max_value, num=30, dtype=float))
# # actions_log = list(np.logspace(0.1, max_value, num=30))
# #
# #
# #
# # bin_edges = np.linspace(min_value, max_value, 30 + 1)
# #
# # # Assign values to bins based on distribution
# # bin_indices = np.digitize(sorted(tot_vent_q), bin_edges, right=True)
# # unique, counts = np.unique(bin_indices, return_counts=True)
# # perc_ = [u/len(bin_indices) for u in counts]
# #
# # tmp_list = []
# # i = 0
# # for p in perc_:
# # 	n_bins = p * 30
# # 	min = bin_edges[i]
# # 	max = bin_edges[i+1]
# # 	if int(n_bins) == 0:
# # 		n_bins =1
# # 	tmp = np.linspace(min, max, int(n_bins))
# # 	tmp_list.append(tmp)
# # 	i+=1
# #
# # final = np.concatenate(tmp_list)
# # tot = sum(perc_)
# #
# # plt.plot(final, label='final')
# # plt.legend()
# # plt.show()
# # plt.close()
#
# # print(tot_vent_q)
#
#
#
# # final = [ 0.0, 102.11797698, 204.23595396, 306.35393094, 408.47190792, 510.5898849, 612.70786188, 714.82583886, 816.94381584, 919.06179282, 1021.1797698, 1123.29774678,  1225.41572376,  1327.53370074,  1429.65167772,  1531.7696547,  1531.7696547, 3063.5393094, 3063.5393094, 3829.42413675,  4595.3089641, 4595.3089641, 6127.0786188, 6127.0786188, 7658.8482735, 7658.8482735, 9190.6179282, 10722.3875829, 12254.1572376, 13785.9268923, 15317.696547, 16849.4662017, 18381.2358564, 19913.0055111, 21444.7751658, 22976.5448205, 24508.3144752, 26040.0841299, 27571.8537846, 29103.6234393, 30635.393094, 32167.1627487, 33698.9324034, 35230.7020581, 36762.4717128, 38294.2413675, 39826.0110222, 41357.7806769, 42889.5503316]
#
# # final_3600 = [ 0.0, 370.39451813, 740.78903627, 1111.1835544, 1481.57807253, 1851.97259067, 2222.3671088, 2592.76162693,  2963.15614507, 3333.5506632, 3333.5506632, 6667.1013264,  6667.1013264, 10000.6519896, 10000.6519896, 13334.2026528, 16667.753316, 16667.753316, 20001.3039792, 20001.3039792, 23334.8546424, 26668.4053056, 30001.955968, 33335.506632, 36669.0572952, 40002.6079584, 43336.1586216, 46669.7092848, 50003.259948, 53336.810611, 56670.3612744 ]