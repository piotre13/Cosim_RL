import sys
import logging
from Federate import Federate
from iterutils import *
import struct
import pprint

pp = pprint.PrettyPrinter(indent=4)
sys.path.append('models/')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Federate_RL_Agent(Federate):
    def __init__(self, args):
        super().__init__(args)




    def execution(self): # execution base for inp out exchange and message receiver
        # +++++++++++++++++++ enetering execution mode++++++++++++++++++
        h.helicsFederateEnterExecutingMode(self.fed)
        logger.info("\tEntered HELICS execution mode")
        self.granted_time = h.helicsFederateGetCurrentTime(self.fed)

        while self.granted_time < self.tot_time: #start the wrapping while loop



            #++++++++++++++++++ setting time synchronization #todo this is the basic default example may require to build a more structured method for time synchornization
            requested_time = self.granted_time + self.period + self.offset
            self.granted_time = h.helicsFederateRequestTime(self.fed, requested_time)
            logger.debug(f"************* Requesting time {requested_time} -- Granted time {self.granted_time} **************")
            current_ts = h.helicsFederateGetCurrentTime(self.fed)
            logger.debug(f"\tcurrent timestep: {current_ts}")
            #*****************************************************************************************

            #retrieve observations
            logger.debug("@@@@@@@@@@@@@@@@@@@")
            obs = self.receive_observations()

        #     #++++++++++++++++++ models execution
        #     ts_idx_sim = (int(current_ts-self.offset) / self.period) - 1
        #     ts_idx_real = (int(current_ts - self.offset) / self.real_period) - 1
        #     if ts_idx_sim == ts_idx_real:
        #         for mod in self.mod_insts:
        #             mod.step(ts_idx_sim, **{}) # passing the index of timestep starting from 0
        #     else:
        #         for mod in self.mod_insts:
        #             mod.step(ts_idx_real+1, **{}) # passing the index of timestep starting from 0
        #         #****************************************************************************************
        #
        #
        #     #++++++++++++++++++ sending ouytputs & messages
            for var in self.out_vars:
                self.publish(var)
        #     #self.send_messages()
        #     #self.reset_messages() # remember to always reset the messages
        #     #****************************************************************************************
        #
        #
        for mod in self.mod_insts:
            mod.finalize()
        self.save_results()
        self.destroy_federate() # todo this must be embedde in a proper stopping logic right now it destroy the federate at the end of the simulation period in case of RL must be used a flag



    def receive_observations(self):
        obs = []

        if self.ends:
            for mod_num in range(len(self.mod_insts)):
                ep = self.ends[mod_num]['observation']
                msg_buffer = []
                while ep.has_message():
                    message = ep.get_message()
                    source = h.helicsMessageGetSource(message)
                    msg_bytes = bytearray(message.raw_data)
                    del msg_bytes[0:8]
                    msg_int = struct.unpack('d', msg_bytes)  # long long int
                    msg = msg_int[0]


                    msg_buffer.append((source,msg))

                logger.debug(f"\n RL agent has received the following msg: {msg_buffer}")

                    # msg_data = json.loads(msg.data)
                    # data = {'var_name':msg_data['var_name'] , 'value':msg_data['value'] ,'source':msg.source}
                    # self.mod_insts[mod_num].messages_in.append(data)
        return obs


    # def receive_inputs(self, var_name):
    #     #todo delaing with different tipe of pubblications (eg. string etc and also multiinputhandling can receive vectors
    #     if self.inps:
    #         for mod_num in range(len(self.mod_insts)):
    #             inpid = self.inps[mod_num][var_name]
    #             if inpid.is_updated(): # todo check understand properly what this means
    #                 value = h.helicsInputGetDouble(inpid)
    #                 getattr(self.mod_insts[mod_num], 'inputs')[var_name]= value
    #                 logger.debug(f"\tModel_{mod_num} received input {var_name}={value}")
    #
    # def publish(self, var_name):
    #     ''' this method when is called on a specific ver_name allows all the model instances to publish their value on their specific topic'''
    #     if self.pubs:
    #         for mod_num in range(len(self.mod_insts)):
    #             pubid = self.pubs[mod_num][var_name]
    #             value = getattr(self.mod_insts[mod_num],'outputs')[var_name]
    #             h.helicsPublicationPublishDouble(pubid, value)
    #             logger.debug(f"\tModel_{mod_num} published output {var_name}={value}")
    #
    # def send_messages(self):
    #     if self.ends:
    #         for mod_num in range(len(self.mod_insts)):
    #             ep = self.ends[mod_num][0]
    #             for msg in getattr(self.mod_insts[mod_num], 'messages_out'):
    #                 out_msg = ep.create_message()
    #                 out_msg.data = json.dumps({'value':msg['value'], 'var_name':msg['var_name']})
    #                 out_msg.destination = msg['dest']
    #                 ep.send_data(out_msg)
    # def check_for_reset(self):
    #     if self.ends:
    #         for mod_num, ep in self.ends.items():
    #             while ep.has_message():
    #                 msg = ep.get_message()
    #                 msg_data = json.loads(msg.data)
    #                 if 'RESET' in msg_data.keys():
    #                     if msg_data['RESET']:
    #                         #do reset
    #                         self.reset()
    #                     else:
    #                         pass
    #                 else:
    #                     pass
    # def reset(self):
    #     logger.debug(f"*************** Federate{self.fed} RESETTING! ***********************")
    #     pass
    #
    #
    # def save_results(self):
    #     res_file = self.fed.name+'.json'
    #     path = os.path.join(os.getcwd(), 'federations', self.federation_name, 'results',res_file)
    #     fed_res = {}
    #     for mod in self.mod_insts:
    #         fed_res[mod.model_name]= mod.memory
    #     save_json(path,fed_res)

    def eval_data_flow_graph(self):
        #todo better understand and logg
        query = h.helicsCreateQuery("broker", "data_flow_graph")
        graph = h.helicsQueryExecute(query, self.fed)
        logger.debug(f"Data-flow graph :\n{pp.pformat(graph)}")

        return graph
    def eval_dependency_graph(self):
        #todo better understand and logg
        query = h.helicsCreateQuery("federate", "dependency_graph")
        graph = h.helicsQueryExecute(query, self.fed)
        logger.debug(f"Dependency graph :\n{pp.pformat(graph)}")

        return graph
    def destroy_federate(self):
        """

        """

        # Adding extra time request to clear out any pending messages to avoid
        #   annoying errors in the broker log. Any message are tacitly disregarded.
        #grantedtime = h.helicsFederateRequestTime(self.fed, h.HELICS_TIME_MAXTIME)
        status = h.helicsFederateDisconnect(self.fed)
        h.helicsFederateDestroy(self.fed)
        logger.info("\tFederate finalized")






# import gym
# from gym import spaces
#
# class CustomEnv(gym.Env):
#   """Custom Environment that follows gym interface"""
#   metadata = {'render.modes': ['human']}
#
#   def __init__(self, arg1, arg2, ...):
#     super(CustomEnv, self).__init__()
#     # Define action and observation space
#     # They must be gym.spaces objects
#     # Example when using discrete actions:
#     self.action_space = spaces.Discrete(N_DISCRETE_ACTIONS)
#     # Example for using image as input:
#     self.observation_space = spaces.Box(low=0, high=255,
#                                         shape=(HEIGHT, WIDTH, N_CHANNELS), dtype=np.uint8)
#
#   def step(self, action):
#     ...
#     return observation, reward, done, info
#   def reset(self):
#     ...
#     return observation  # reward, done, info can't be included
#   def render(self, mode='human'):
#     ...
#   def close (self):
#     ...


if __name__ == "__main__":
    #args order 0: fed_conf path , 1: init_conf
    #argv = ['federations/example_federation/BatteryConfig.json',
    #       'federations/example_federation/BatteryConfig_init.yaml']
    #fed = ValueFederate(argv)  # only for testing when launching this autonomously

    fed = Federate_RL_Agent(sys.argv) #giusto da usare quando si runna da helics passando gli argv
    fed.execution()
    #fed = ValueFederate([0,'BatteryConfig_init.yaml', 'example_federation'])

