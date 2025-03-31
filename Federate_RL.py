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
#
#
# class CustomEnv():
#     pass
#
#
#

class Federate_RL_Agent(Federate):
    def __init__(self, args):
        self.model = None
        super().__init__(args)

        # removing the possibility of multiple model instances
        self.model = self._model_instances[0]



    def model_kwargs(self, i, class_name):
        #instantiate the mode
        kwargs = {}
        for k, val in self._model_conf['RL_params'].items():
            kwargs[k]=val
        kwargs['model_name'] = 'DQN_agent'
        self.action_vars = self._model_conf['RL_params']['action_vars']
        self.training = self._fed_conf['RL_training']
        self.train_end_period = self._fed_conf['training_episodes'] * self._fed_conf['episode_period']
        self.train_end_ts = int(self.train_end_period / self.real_period)
        kwargs['training'] = self.training
        kwargs['train_end_period'] = self.train_end_period
        kwargs['train_end_ts'] = self.train_end_ts
        kwargs['n_episodes'] = self._fed_conf['training_episodes']
        kwargs['episode_ts'] = int(self._fed_conf['episode_period']/self._fed_conf['sim_params']['real_period'])

        return kwargs
    def execution(self): # execution base for inp out exchange and message receiver

        # +++++++++++++++++++ enetering execution mode++++++++++++++++++
        h.helicsFederateEnterExecutingMode(self._fed)
        logger.info("@@ Entered HELICS execution mode @@ \n")
        self.granted_period = h.helicsFederateGetCurrentTime(self._fed)
        self.ts = 0
        while self.granted_period < self.end_period:  # start the wrapping while loop
            if (self.ts/int(self.end_period/self.real_period))*100 in [10, 20, 30, 40 ,50 ,60, 70, 80, 90, 100]:
                print(f"Simulation progress == {int((self.ts/int(self.end_period/self.real_period))*100)} %")
                logger.critical(f"TS:{self.ts}")

            logger.debug("==============================================================================================================================")
            if self.ts > self.train_end_ts or self.granted_period > self.train_end_period:      # ridondante
                self.training = False
                setattr(self.model, 'training', False)
                # logger.info("Started TESTING phase!")
                # setattr(self.model, '') # model does not have the training flag

            # ++++++++++++++++++ setting time synchronization #no offset
            requested_period = self.granted_period + self.sim_period + self.offset
            self.granted_period = h.helicsFederateRequestTime(self._fed, requested_period)
            logger.info(
                f"************* Requesting time {requested_period} -- Granted time {self.granted_period} **************")
            self.current_period = h.helicsFederateGetCurrentTime(self._fed) - self.offset
            # logger.debug(f"current time: {self.current_period}\n")
            # *****************************************************************************************

            # getting inputs & messages
            self._receive_messages()  # update self.in_msgs class variable
            self._receive_inputs()  # update self.in_values class variable


            obs_vars, reward_vars = self.process_inputs()
            # logger.debug(f"OBS_VARS= {obs_vars}, REWARD_VARS= {reward_vars}")
            # getting federate inputs as observation
            self.model.get_observations(obs_vars)  # get observatioon # normalize
            self.model.evaluate_agent(reward_vars) #reward calculation and agent evaluation during training it evaluates the step before

            #reward = self.model.estimate_reward(reward_vars) #get_reward
            if self.training and self.ts != 0: # and training_step<=training_step_end:  # if training and not ts==0
                #update agent
                self.model.update_agent(self.ts)  # update agent
                # logger.debug("Agent updated!")
            #getting federate inputs as observation
            action = self.model.predict_action() # predict actions (model call) # normalized
            # logger.debug(f"Action chosen {action}")

            # publish actions  TODO should add a non HARDCODED way and standard to put actions inside out_values
            self.out_values[0] = {} #remove only for debugging
            self.out_values[0][self.action_vars[0]] = action
            # self.out_values[0]['tset'] = action #remove only for debugging
            # self.out_values[0]['vent_q']= action
            # self.out_values[0]['tset_min']= action
            # self.out_values[0]['tset_max']= action
            # logger.debug(f"self.out_values {self.out_values}")

            self._publish_outputs()

            self.ts+=1
            logger.debug("==============================================================================================================================")

        self.destroy_federate()



    def process_inputs(self):
        obs = {}
        reward = {}
        self.other_inputs = {}
        # only one model
        in_values = self.in_values[0]
        in_msgs = self.in_msgs[0]


        if in_msgs:
            for msg in in_msgs:
                if msg['var_name'] in self.model.observation_vars:
                    obs[msg['var_name']] = msg['value']
                if msg['var_name'] in self.model.reward_vars:
                    reward[msg['var_name']] = msg['value']

        if in_values:
            for var_name, value in in_values.items():
                if var_name in self.model.observation_vars:
                    obs[var_name] = value
                if var_name in self.model.reward_vars:
                    reward[var_name] = value
                else:
                    self.other_inputs[var_name]=value
        self.model.other_inputs = self.other_inputs
        return obs, reward

    def process_action(self):
        pass

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
        #   annoying errors in the broker log. Any message are tacitly d
        #   isregarded.
        #grantedtime = h.helicsFederateRequestTime(self.fed, h.HELICS_TIME_MAXTIME)
        self._save_results()
        status = h.helicsFederateDisconnect(self._fed)
        h.helicsFederateDestroy(self._fed)
        logger.info("\tFederate finalized")






if __name__ == '__main__':
    fed = Federate_RL_Agent(sys.argv)  # giusto da usare quando si runna da helics passando gli argv
    fed.execution()
    # fed = ValueFederate([0,'BatteryConfig_init.yaml', 'example_federation'])

#
# # import gym
# # from gym import spaces
# #
# # class CustomEnv(gym.Env):
# #   """Custom Environment that follows gym interface"""
# #   metadata = {'render.modes': ['human']}
# #
# #   def __init__(self, arg1, arg2, ...):
# #     super(CustomEnv, self).__init__()
# #     # Define action and observation space
# #     # They must be gym.spaces objects
# #     # Example when using discrete actions:
# #     self.action_space = spaces.Discrete(N_DISCRETE_ACTIONS)
# #     # Example for using image as input:
# #     self.observation_space = spaces.Box(low=0, high=255,
# #                                         shape=(HEIGHT, WIDTH, N_CHANNELS), dtype=np.uint8)
# #
# #   def step(self, action):
# #     ...
# #     return observation, reward, done, info
# #   def reset(self):
# #     ...
# #     return observation  # reward, done, info can't be included
# #   def render(self, mode='human'):
# #     ...
# #   def close (self):
# #     ...
#
#
# if __name__ == "__main__":
#     #args order 0: fed_conf path , 1: init_conf
#     #argv = ['federations/example_federation/BatteryConfig.json',
#     #       'federations/example_federation/BatteryConfig_init.yaml']
#     #fed = ValueFederate(argv)  # only for testing when launching this autonomously
#
#     fed = Federate_RL_Agent(sys.argv) #giusto da usare quando si runna da helics passando gli argv
#     fed.execution()
#     #fed = ValueFederate([0,'BatteryConfig_init.yaml', 'example_federation'])
#
