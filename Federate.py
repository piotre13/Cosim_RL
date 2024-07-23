import os
import sys
import helics as h
import logging
import pandas as pd
from utils import read_yaml, save_json
import importlib.util
import pprint
import json
from definitions import *
import copy
pp = pprint.PrettyPrinter(indent=4)
sys.path.append('models/')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Federate:
    def __init__(self, args):

        #configs:
        self._config = read_yaml(os.path.join(FEDERATIONS_dir, args[-1], args[-2]))
        self._name = self._config['fed_name']
        self._connections = self._config['fed_connections']
        self._fed_conf = self._config['fed_conf']
        self._model_conf = self._config['model_conf']

        # helics specific information
        self._fed_info = self._config['fed_info']
        self._fed_flags = self._config['fed_flags']
        self.fed_properties = self._fed_conf['sim_params']



        #simulation params
        self.start_time = pd.to_datetime(self._fed_conf['sim_params']['start_time'],format='%Y-%m-%d %H:%M:%S') # datetime
        self.start_period = 0 # seconds
        self.offset = self._fed_conf['sim_params']['offset']
        self.ts = 0 #unitless counter for simulation steps
        self.sim_period = self._fed_conf['sim_params']['sim_period'] #seconds
        self.real_period = self._fed_conf['sim_params']['real_period'] # seconds
        self.current_period = self.start_period
        self.end_period = self._fed_conf['sim_params']['end_period'] # seconds
        self.end_time = self.start_time + pd.to_timedelta(self.end_period) # datetime

        # federate
        self._fed = self.register_federate()
        self.federation_name = args[-1]

        # connection interfaces
        self.inp_ids, self.pub_ids, self.end_ids = self.register_connections()

        #buffer for receiving sending
        self.in_values = {}
        self.out_values = {}
        self.in_msgs = {}
        self.out_msgs = {}

        #models
        self._model_instances, self._model_names = self.instantiate_models()


    def register_federate(self):

        # create combination federate *****
        fedInfo = h.helicsCreateFederateInfo()

        if self._fed_info:
            for k, val in self._fed_info.items():
                setattr(fedInfo, k, val)
        else:
            logger.warning(f"Federate info in yaml config file are empty!\n")

        fed = h.helicsCreateCombinationFederate(self._name, fedInfo)
        # set properties ******
        h.helicsFederateInfoSetTimeProperty(fedInfo, h.helics_property_time_period, self.sim_period)
        h.helicsFederateInfoSetTimeProperty(fedInfo, h.helics_property_time_offset, self.offset)
        if self._fed_properties:
            for prop in self._fed_properties:
                prop_name = 'HELICS_PROPERTY_{}'.format(prop)
                if prop.startswith('INT'):
                    h.helicsFederateSetIntegerProperty(fed, getattr(h, prop_name),
                                                       int(self._fed_properties[prop]))
                else:
                    fed.property[getattr(h, prop_name)] = float(self._fed_properties[prop])
        else:
            logger.warning(f"Federate properties in yaml config file are empty!\n")

        #set flags *****
        if self._fed_flags:
            for flag in self._fed_flags:
                flag_name = 'HELICS_FLAG_{}'.format(flag)
                fed.flag[getattr(h,flag_name)] = self._fed_flags[flag]
        else:
            logger.warning(f"Federate Flags in yaml config file are empty!\n")

        logger.info(f"Federate : {fed.name} registered!\n")

        return fed

    def register_connections(self):
        #todo should tranform each single registration type ina method to reuse them in case
        inp_ids = {}
        pub_ids = {}
        end_ids = {}

        for mod_num in self._connections['pub']:
            pub_ids[mod_num] = {}
            for pub_info in self._connections['pub'][mod_num]:
                var_name = pub_info['key']
                if var_name not in pub_ids[mod_num].keys():
                    topic = self._fed.name + '/' + str(mod_num) + '/' + var_name
                    pubid = self._fed.register_global_publication(topic, kind=pub_info['type'], units=pub_info['units'])
                    pub_ids[mod_num][var_name] = pubid
                    logger.debug(f"Registered publication: {pubid} for {topic}\n")
                else:
                    logger.warning(f"Publication for {self._name}/{mod_num}/{var_name} already registered! DUPLICATE in config yaml.\n")

        for mod_num in self._connections['inp']:
            inp_ids[mod_num] = {}
            for inp_info in self._connections['inp'][mod_num]:
                var_name = inp_info['key']
                if var_name not in inp_ids[mod_num].keys():
                    inp_name = self._fed.name + '/'+ str(mod_num) + '/' + var_name
                    inpid = self._fed.register_global_input(name=inp_name,kind=inp_info['type'], units=inp_info['units'])
                    if 'targets' in inp_info:
                        for t in inp_info['targets']:
                            inpid.add_target(t)
                    else:
                        logger.error(f'Input {inp_name} does not have any target!\n')
                        raise Exception(f'Input {inp_name} does not have any target!')

                    if "multi_input_handling_method" in inp_info.keys():
                        inpid.option['MULTI_INPUT_HANDLING_METHOD'] = h.helicsGetOptionValue(inp_info['multi_input_handling_method'])

                    else:
                        if len(inp_info['targets']) > 1:
                            logger.error(f'Input {inp_name} has more than 1 target and no multi inputs handling method!\n')
                            raise Exception(f'Input {inp_name} no specified MULTI INPUT HANDLING METHOD')

                    inp_ids[mod_num][var_name] = inpid
                    logger.debug(f"Registered input: {inpid.name} for {mod_num} from {inp_info['targets']}\n")
                else:
                    logger.warning(f"Input for {self._name}/{mod_num}/{var_name} already registered! DUPLICATE in config yaml.\n")

        for mod_num in self._connections['end']:
            end_ids[mod_num] = {}
            for end_info in self._connections['end'][mod_num]:
                if end_info['ep_name'] not in end_ids[mod_num].keys():
                    ep_name = self._fed.name + '/'+ str(mod_num) + '/' + end_info['ep_name']
                    ep = self._fed.register_global_endpoint(ep_name)
                    if "default" in end_info.keys(): # it means that it is used to send message to a specific sim endpoint
                        h.helicsEndpointSetDefaultDestination(ep,end_info['default'])

                    end_ids[mod_num][end_info['ep_name']]=ep
                    logger.debug(f"Registered endpoint: {ep.name} for {mod_num}\n")

                else:
                    logger.warning(f"Endpoint for {self._name} model_inst {mod_num} and name {end_info['ep_name']} already registered! DUPLICATE in config yaml.\n")

        logger.debug(f"\nFederate registered interfaces\n     Endpoint: {pp.pformat(end_ids)}\n     Publications: {pp.pformat(pub_ids)}\n     Inputs: {pp.pformat(inp_ids)}\n")

        return inp_ids, pub_ids, end_ids

    def instantiate_models(self):

        if self._model_conf:
            model_instances = []
            model_names = []
            module_import = self._model_conf['generic']['model_script'].split('.')[0].replace('/', '.')

            if 'class_name' not in self._model_conf['generic'].keys():
                class_name = module_import.split('.')[-1]
            else:
                class_name = self._model_conf['generic']['class_name']

            logger.debug(f"@@@@ module import = {module_import}")
            module = importlib.import_module(module_import)
            my_class = getattr(module, class_name)

            for i in range(self._model_conf['generic']['n_instances']):
                kwargs = self.model_kwargs(i, class_name)
                model_inst = my_class(**kwargs)
                model_instances.append(model_inst)  # appending model instances
                model_names.append(model_inst.model_name)  # appending model instances names

            logger.info(f"Models instantiation succesfull!\n")
            logger.debug(f"Model instances names:\n {model_names}\n")


        else:
            logger.error(f"No model config in config file! without a model Federate is only an empty box!\n")
            raise Exception ("No model. see LOG.")

        return model_instances, model_names

    def model_kwargs(self, i, class_name):

        '''this method is important beacuse passes attributes to model instances, if different fgederates deal with different model requirements (e.g. RL agent do not have inputs outputs)
        this method must be overwritten in the specific Federate class'''
        kwargs = {}

        #basic attr
        kwargs['model_name'] = f"%s/%s/%s"%(self._name,i,class_name)
        kwargs['RL_training'] = self._fed_conf['RL_training']

        #basic knowledge on simulation
        kwargs['start_time'] = self.start_time #datetime
        kwargs['start_period'] = self.start_period # seconds
        kwargs['sim_period'] = self.sim_period #seconds
        kwargs['real_period'] = self.real_period #seconds
        kwargs['current_period'] = self.current_period #seconds
        kwargs['end_period'] = self.end_period #seconds
        kwargs['end_time'] = self.end_time # datetime

        #required model specific attrs
        kwargs['inputs_list'] = self._model_conf['model_specific_required']['inputs_k']
        kwargs['outputs_list'] = self._model_conf['model_specific_required']['outputs_k']
        # kwargs['params_list'] = self._model_conf['model_specific_required']['params_k']
        kwargs['params_list'] = list(self._model_conf['model_specific_required']['params'].keys())

        #check initistate only if specified if not log the fact that models have not initial state
        if self._model_conf['model_specific_required']['init_state']:
            assert self.check_init_state(kwargs['inputs_list'],kwargs['outputs_list'],kwargs['params_list']) == True # every model must HAVE an init state (this is useful for RL (in future could be less restrictive)
            kwargs['inputs'] = {k: self._model_conf['model_specific_required']['init_state']['inp.' + k] for k in
                                kwargs['inputs_list']}
            kwargs['outputs'] = {k: self._model_conf['model_specific_required']['init_state']['out.' + k] for k in
                                 kwargs['outputs_list']}
        else:
            kwargs['inputs'] = {k: 0.0 for k in
                                kwargs['inputs_list']}
            kwargs['outputs'] = {k: 0.0 for k in
                                 kwargs['outputs_list']}
            logger.warning(f"The models of this federate do not have Initial state!\n")


        kwargs['params'] = {k: self._model_conf['model_specific_required']['params'][k][i] for k in kwargs['params_list']}
        kwargs['init_state'] = {"inputs" : kwargs['inputs'],"outputs" : kwargs['outputs'],"params" : kwargs['params'] }

        kwargs['memory'] = self._fed_conf['memory']
        #pass all the model_specific_additional
        for k, val in self._model_conf['model_specific_additional'].items():
            kwargs[k] = val[i]


        return kwargs

    def check_init_state(self, inp_list, out_list, par_list):

        if not par_list.sort() == list(self._model_conf['model_specific_required']['params'].keys()).sort(): #todo probably never triggered no more params_k needed
            logger.error(f"Assigned params does not match the params keys in model configuration!\n")
            return False
        elif not inp_list.sort() == list([k.split('.')[-1] for k in self._model_conf['model_specific_required']['init_state'] if k.startswith('inp')]).sort():
            return False
        elif not out_list.sort() == list(
                [k.split('.')[-1] for k in self._model_conf['model_specific_required']['init_state'] if
                 k.startswith('out')]).sort():
            return False
        else:
            return True

    def _receive_messages(self):
        ''' DO NOT TOUCH this mesthod it recieves whatever message arrives to the endpoint an dtores it in the message buffer self.in_msgs :
                {mod_num: [ {msg_dict}, {msg_dict}...],
                 mod_num: ...}

                 correct form msg_dict:
                 {"source": None,   #must contain the whole var name Federate/modnum/varname
                             "time": None,
                             "var_name": None,
                             "destination": None, #must contain the whole endpoint name to send to
                             "value": None} '''
        if self.end_ids:
            for mod_num, ep_dict in self.end_ids.items():
                self.in_msgs[mod_num] = []
                for ep_name, ep in ep_dict.items():
                    while ep.has_message():
                        msg = ep.get_message()
                        msg_data = json.loads(msg.data)
                        msg_data['source'] = msg.source
                        msg_data['destination'] = msg.destination
                        self.in_msgs[mod_num].append(msg_data)
            logger.debug(f"Received the following messages :\n {self.in_msgs}\n")
        else:
            logger.debug(f"No endpoints registered for federate\n")

    def _receive_inputs(self):
        ''' DO NOT TOUCH this method it receives everything and store inside self.in_values in proper form
        self.out_values  = {mod_num = {var_name:var_vale},...}  '''
        if self.inp_ids:
            for mod_num, inp_dict in self.inp_ids.items():
                self.in_values[mod_num] = {}
                for var_name, inpid in inp_dict.items():
                    value = h.helicsInputGetDouble(inpid)
                    self.in_values[mod_num][var_name] = value
            logger.debug(f"Received the following Input values :\n {pp.pformat(self.in_values)}\n")
        else:
            logger.debug(f"No value based Input interfaces registered for the federate!\n")

    def _publish_outputs(self):
        ''' DO NOT TOUCH this method it publishes everything is inside self.out_values in proper form
        self.out_values  = {mod_num = {var_name:var_vale},...}  '''
        if self.pub_ids:
            logger.debug(f"Federate will publish following values {pp.pformat(self.out_values)}\n")

            for mod_num, var_dict in self.out_values.items():
                for var_name, value in var_dict.items():
                    pubid = self.pub_ids[mod_num][var_name]
                    h.helicsPublicationPublishDouble(pubid, value)
                    logger.debug(f"actual publication performed from the federate {mod_num}/{var_name} : {value}\n")
        else:
            logger.debug(f"No value based Output interfaces registered for the federate!\n")

    def _send_messages(self, ep_name):
        ''' DO NOT TOUCH this mesthod it send whatever is in the correct form inside self.out_msg
        correct_form msg buffer :
        {mod_num: [ {msg_dict}, {msg_dict}...],
         mod_num: ...}

         correct form msg_dict:
         {"source": None,   #must contain the whole var name Federate/modnum/varname
                     "time": None,
                     "var_name": None,
                     "destination": None, #must contain the whole endpoint name to send to
                     "value": None} '''
        if self.end_ids:
            logger.debug(f"Federate will send the following messages {pp.pformat(self.out_msgs)}\n")
            for mod_num, message_list in self.out_msgs.items():
                ep = self.end_ids[mod_num][ep_name]
                for msg in message_list:
                    out_msg = ep.create_message()
                    out_msg.data = json.dumps(msg)
                    if msg['destination']:
                        out_msg.destination = msg['destination']
                    else:
                        out_msg.original_destination = ep.default_destination
                    out_msg.source = ep.name
                    ep.send_data(out_msg)
                    # logger.debug(f"MESSAGE SENT: {out_msg} by endpoint: {ep}")
        else:
            logger.debug(f"No endpoints registered for federate\n")

    def _check_reset(self):
        if not self.in_msgs:
            return
        # i = 0
        # for model in self._model_instances:
        #     if self.in_msgs[i]:
        #         if any('reset_now' in key['destination'] for key in self.in_msgs[i]):  # todo check loogic
        #             model.reset()  # EACH MODEL MUST HAVE A RESET METHOD
        #     i += 1

    def execution(self): # execution base for inp out exchange and message receiver
        # +++++++++++++++++++ enetering execution mode++++++++++++++++++
        h.helicsFederateEnterExecutingMode(self._fed)
        logger.info("@@ Entered HELICS execution mode @@ \n")
        self.granted_period = h.helicsFederateGetCurrentTime(self._fed)

        while self.granted_period < self.end_period: #start the wrapping while loop



            #++++++++++++++++++ setting time synchronization #no offset
            requested_period = self.granted_period + self.sim_period + self.offset
            self.granted_period = h.helicsFederateRequestTime(self._fed, requested_period)
            logger.debug(f"************* Requesting time {requested_period} -- Granted time {self.granted_period} **************")
            self.current_period = h.helicsFederateGetCurrentTime(self._fed) - self.offset
            logger.debug(f"current time: {self.current_period}\n")
            #*****************************************************************************************

            #getting inputs & messages
            self._receive_messages() # update self.in_msgs class variable
            self._check_reset()
            self._receive_inputs() # update self.in_values class variable


            #prepare inputs for model
            self.inputs_to_model()

            #++++++++++++++++++ models execution

            ts = int(self.current_period/self.sim_period)
            for mod in self._model_instances:
                mod.step(ts)
            # ts_idx_sim = (int(current_ts-self.offset) / self.period) - 1
            # ts_idx_real = (int(current_ts - self.offset) / self.real_period) - 1
            # if ts_idx_sim == ts_idx_real:
            #     for mod in self.mod_insts:
            #         mod.step(ts_idx_sim, **{}) # passing the index of timestep starting from 0
            # else:
            #     for mod in self.mod_insts:
            #         mod.step(ts_idx_real+1, **{}) # passing the index of timestep starting from 0
                #****************************************************************************************

            #prepare outputs from model
            self.outputs_from_model()


            #++++++++++++++++++ sending ouytputs & this federate do not send messages
            self._publish_outputs()

        for mod in self._model_instances:
            mod.finalize()
        # self.save_results() # todo decide how to save results
        self._destroy_federate() # todo this must be embedde in a proper stopping logic right now it destroy the federate at the end of the simulation period in case of RL must be used a flag

    def inputs_to_model(self):
        ''' this method is the one to overwrite when dealing with different typologies of federates. In this case it represent a simple federate that is
        used for basic simulators that can receive both inputs and messages but only send outputs. In this function we read teh in_values and in_msgs buffers
         and impose in the models the corresponding inputs or params vars. '''
        #can be taken from both messages and inputs and matched with the corresponding mod.inputs  keys of the model
        if not self.in_values  and not self.in_msgs:
            logger.debug(f" The federate has no incoming Inputs or messages for any of its model instances.")
            return

        i = 0
        for model in self._model_instances:
            # check if there are any messages to change the inputs or the params (leaning it open to control params
            if self.in_msgs:
                for msg in self.in_msgs[i]:
                    if msg['var_name'] in model.inputs.keys():
                        # impose tha value on the model input
                        getattr(model, 'inputs')[msg['var_name']]= msg['value']
                    elif msg['var_name'] in model.params.keys():
                        # impose tha value on the model param (not common only with RT param changing
                        getattr(model, 'params')[msg['var_name']]= msg['value']


                # empty the buffers to be sure i can use inputs to model even if I only called one of _receive_inputs or _receive_message before
                self.in_msgs = {mod_num: [] for mod_num in range(len(self._model_instances))}

            # Imposing inputs received as classic value based inputs only inputs params must be changed with messages
            if self.in_values:
                for var_name, value  in self.in_values[i].items():
                    if var_name in model.inputs.keys():
                        getattr(model, 'inputs')[var_name] = value

                # empty the buffers to be sure i can use inputs to model even if I only called one of _receive_inputs or _receive_message before
                self.in_values = {mod_num: {} for mod_num in range(len(self._model_instances))}

            i+=1


    def outputs_from_model(self):
        ''' This method reads the model self.outputs and generate the sel.out_values always regenrating it from empty dict'''

        i=0
        self.out_values = {}
        for model in self._model_instances:
            self.out_values[i] = {}
            outputs = getattr(model,'outputs')
            for k, val in outputs.items():
                self.out_values[i][k] = val
            i+=1

    def create_std_message(self): # NOT used
        #for now this will only be used in RL federates all the others sends only values based and can receive the reset command
        std_message = {"source": None,   #must contain the whole var name Federate/modnum/varname
                     "time": None,
                     "var_name": None,
                     "destination": None, #must contain the whole endpoint name to send to
                     "value": None}

    def _save_results(self):

        path = os.path.join(FEDERATIONS_dir,self.federation_name, 'results')
        os.makedirs(path, exist_ok=True)


        fed_res = {}
        for mod in self._model_instances:
            fed_res[mod.model_name] = mod.memory
        file_name = self._fed.name +'.json'
        file_path = os.path.join(path, file_name)
        save_json(file_path, fed_res)

    def _destroy_federate(self):
        """

        """
        # Adding extra time request to clear out any pending messages to avoid
        #   annoying errors in the broker log. Any message are tacitly disregarded.
        # grantedtime = h.helicsFederateRequestTime(self.fed, h.HELICS_TIME_MAXTIME)
        self._save_results()
        status = h.helicsFederateDisconnect(self._fed)
        h.helicsFederateDestroy(self._fed)
        logger.info("Federate finalized\n")

    def reset(self):
        logger.debug(f"*************** Federate{self._fed} RESETTING! ***********************")
        pass

    @property
    def fed_properties(self):
        return self._fed_properties

    @fed_properties.setter
    def fed_properties(self, value):
        min_req = ['TIME_PERIOD', 'TIME_STOPTIME']
        matching_dict = {
            'time_delta': 'TIME_DELTA',
            'sim_period': 'TIME_PERIOD',
            'offset': 'TIME_OFFSET',
            'rt_lag': 'TIME_RT_LAG',
            'rt_lead': 'TIME_RT_LEAD',
            'rt_tolerance': 'TIME_RT_TOLERANCE',
            'input_delay': 'TIME_INPUT_DELAY',
            'output_delay': 'TIME_OUTPUT_DELAY',
            'end_period': 'TIME_STOPTIME',
            'grant_timeout': 'TIME_GRANT_TIMEOUT',
            'current_iter': 'INT_CURRENT_ITERATION',
            'max_iter': 'INT_MAX_ITERATIONS',
            'int_log_level': 'INT_LOG_LEVEL',
            'int_file_log_level': 'INT_FILE_LOG_LEVEL',
            'int_console_log_level': 'INT_CONSOLE_LOG_LEVEL',
            'int_log_buffer': 'INT_LOG_BUFFER',
            'int_index_group': 'INT_INDEX_GROUP'
        }
        fed_prop = {}
        for k, val in value.items():
            if k in matching_dict.keys():
                fed_prop[matching_dict[k]] = val

        if not all(i in fed_prop.keys() for i in min_req):
            logger.error(f"Missing params: minimal requirements {min_req} missing in sim_params!\n")
        else:
            self._fed_properties = fed_prop


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
        graph = h.helicsQueryExecute(query, self._fed)
        logger.debug(f"Data-flow graph :\n{pp.pformat(graph)}")

        return graph
    def eval_dependency_graph(self):
        #todo better understand and logg
        query = h.helicsCreateQuery("federate", "dependency_graph")
        graph = h.helicsQueryExecute(query, self._fed)
        logger.debug(f"Dependency graph :\n{pp.pformat(graph)}")

        return graph





if __name__ == "__main__":
    #args order 0: fed_conf path , 1: init_conf
    #argv = ['federations/example_federation/BatteryConfig.json',
    #       'federations/example_federation/BatteryConfig_init.yaml']
    #fed = ValueFederate(argv)  # only for testing when launching this autonomously

    fed = Federate(sys.argv) #giusto da usare quando si runna da helics passando gli argv
    fed.execution()
    #fed = ValueFederate([0,'BatteryConfig_init.yaml', 'example_federation'])

