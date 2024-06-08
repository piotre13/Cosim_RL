import os
import sys
import helics as h
import logging
from utils import read_yaml, save_json
import importlib.util
import pprint
import json
import copy
pp = pprint.PrettyPrinter(indent=4)
sys.path.append('models/')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Federate:
    def __init__(self, args):

        #self.fed_config, self.init_config = self.init_config(args)
        self.federation_name = None
        self.init_config = self.set_conf(args)
        self.fed = None

        #connections
        self.connection_ref = self.init_config['fed_connections']
        self.pubs = {}
        self.out_vars = []
        #self.subs = {} will not use this
        self.ends = {}
        self.inps = {}
        self.in_vars = []
        self.in_vars = []
        self.msg_var_dest = {}

        #models
        self.mod_insts = []
        self.mod_names = []

        #time synchronization
        self.period = None #will be set when the federate is created
        self.real_period = None
        self.offset = None #will be set when the federate is created
        self.granted_time = None #will be set when the federate is created
        self.tot_time = None #will be set when the federate is created


        #performing tasks
        self.registering()

        self.register_connections()
        #self.eval_data_flow_graph()
        #self.eval_dependency_graph()
        self.model_instantiation()



    def set_conf(self, args):
        self.federation_name = args[-1]
        init_config = read_yaml(os.path.join(os.getcwd(), 'federations', self.federation_name, args[1]))
        return init_config
    def registering(self):

        fedInfo = h.helicsCreateFederateInfo()
        for info in self.init_config['fed_info']:
            if self.init_config['fed_info'][info]:
                setattr(fedInfo, info, self.init_config['fed_info'][info])

        self.fed = h.helicsCreateCombinationFederate(self.init_config['fed_name'],fedInfo)

        # set properties
        for prop in self.init_config['fed_properties']:
            prop_name = 'HELICS_PROPERTY_{}'.format(prop)
            if self.init_config['fed_properties'][prop]:
                if prop.startswith('INT'):
                    h.helicsFederateSetIntegerProperty(self.fed,getattr(h,prop_name),int(self.init_config['fed_properties'][prop]))
                    #self.fed.property[getattr(h,prop_name)] = int(self.init_config['fed_properties'][prop])
                else:
                    self.fed.property[getattr(h,prop_name)] = float(self.init_config['fed_properties'][prop])

        # set flags
        for prop in self.init_config['fed_flags']:
            prop_name = 'HELICS_FLAG_{}'.format(prop)
            if self.init_config['fed_flags'][prop]:
                self.fed.flag[getattr(h,prop_name)] = self.init_config['fed_flags'][prop]


        self.period = int(h.helicsFederateGetTimeProperty(self.fed, h.HELICS_PROPERTY_TIME_PERIOD))
        self.offset = int(h.helicsFederateGetTimeProperty(self.fed, h.HELICS_PROPERTY_TIME_OFFSET))
        self.tot_time = int((h.helicsFederateGetTimeProperty(self.fed, h.HELICS_PROPERTY_TIME_STOPTIME)))


        self.real_period = self.init_config['fed_conf']['real_period']



    def register_connections(self):

        for mod_num in self.connection_ref['pub']:
            self.pubs[mod_num] = {}
            for pub_info in self.connection_ref['pub'][mod_num]:
                var_name = pub_info['key']
                if var_name not in self.out_vars: self.out_vars.append(var_name)
                if var_name not in self.pubs[mod_num].keys():
                    topic = self.fed.name + '/' + str(mod_num) + '/' + var_name
                    pubid = self.fed.register_global_publication(topic, kind=pub_info['type'], units=pub_info['units'])
                    if 'targets' in pub_info:
                        for t in pub_info['targets']:
                            pubid.add_target(t)
                    self.pubs[mod_num][var_name] = pubid
                    logger.debug(f"\tRegistered publication: {pubid} for {topic}")
                else:
                    logger.error('ERROR Publication for topic {} already registered'.format(topic))

        for mod_num in self.connection_ref['inp']:
            self.inps[mod_num] = {}
            for inp_info in self.connection_ref['inp'][mod_num]:
                var_name = inp_info['key']
                if var_name not in self.in_vars: self.in_vars.append(var_name)
                if var_name not in self.inps[mod_num].keys():
                    inp_name = self.fed.name + '/'+ str(mod_num) + '/' + var_name
                    inpid = self.fed.register_global_input(name=inp_name,kind=inp_info['type'], units=inp_info['units'])
                    if 'targets' in inp_info:
                        for t in inp_info['targets']:
                            inpid.add_target(t)
                    else:
                        logger.error(f'\tInput {inp_name} does not have any target!')
                        raise Exception(f'\tInput {inp_name} does not have any target!')

                    if "multi_input_handling_method" in inp_info.keys():
                        inpid.option['MULTI_INPUT_HANDLING_METHOD'] = h.helicsGetOptionValue(inp_info['multi_input_handling_method'])
                    else:
                        if len(inp_info['targets']) > 1:
                            logger.error(f'\tInput {inp_name} has more than 1 target and no multi inputs handling method!')
                            raise Exception(f'\tInput {inp_name} no specified MULTI INPUT HANDLING METHOD')

                    self.inps[mod_num][var_name] = inpid
                    logger.debug(f"\tRegistered input: {inpid.name} for {mod_num} from {inp_info['targets']}")

        for mod_num, ep_info in self.connection_ref['end'].items(): #ep_name and mod_num are the same ONLY one endpoint per model instance
            ep = self.fed.register_endpoint(str(mod_num))
            if str(mod_num) not in self.ends.keys(): #end_info key must be the same of mod_receiver
                self.ends[mod_num] = ep
                logger.debug(f"\tRegistered endpoint: {ep.name} ")

        logger.debug(f"testetstetste {self.ends}\n {self.pubs}\n{self.inps}")


        logger.debug(f"\tRegistering connections ended for fed {self.fed.name} list of output vars {self.out_vars}, list for in_vars{self.in_vars}")





    def model_instantiation(self):
        """ IT IS CALLED INSIDE __init__()
        this method allows multiple instantiation of models for one federate.
        It saves the models instantiation in self.mod_insts and their names in self.mod_names"""
        dir_path = 'models'  #TODO avoid hardcodding add in config (MAYBE CREATE A BASIC PATH CONFIG)
        module_name = self.init_config['fed_conf']['model_script'].split('.')[0]
        module_import = module_name.replace('/','.')
        #module_import = dir_path + '.' + self.init_config['fed_conf']['model_script'].split('.')[0]
        if 'class_name' not in self.init_config['fed_conf'].keys():
            class_name = self.init_config['fed_conf']['model_script'].split('.')[0]
        else:
            class_name = self.init_config['fed_conf']['class_name']

        module = importlib.import_module(module_import)
        my_class = getattr(module, class_name)

        for i in range(self.init_config['fed_conf']['n_instances']):
            kwargs = self.init_kwargs(i, class_name)
            model_inst = my_class(**kwargs)
            self.mod_insts.append(model_inst) # appending model instances
            self.mod_names.append(model_inst.model_name) # appending model instances names

        logger.debug(f"\tModels instantiation from fed: {self.fed.name} succesfull!")
        logger.debug(f"\tModel instances names: {self.mod_names}")



    def init_kwargs(self, i, class_name):
        kwargs = {}
        kwargs['model_name'] = class_name + '.' + str(i)
        kwargs['inputs'] = { k: 0.0 for k in self.in_vars}
        kwargs['outputs'] = { k: 0.0 for k in self.out_vars}
        kwargs['messages_in'] = []
        kwargs['messages_out'] = []
        kwargs['params'] = {k: self.init_config['model_conf']['params'][k][i] for k in self.init_config['model_conf']['params']}

        if self.msg_var_dest: kwargs['msg_var_dest'] = self.msg_var_dest[i]
        else: kwargs['msg_var_dest'] = {}

        #kwargs['msg_in'] =
        kwargs['RL_training'] = self.init_config['fed_conf']['RL_training']
        #kwargs['stateful'] = self.init_config['fed_conf']['stateful']
        kwargs['mem_attrs'] = self.init_config['fed_conf']['mem_attrs']
        if 'fmu' in self.init_config['fed_conf'].keys():
            kwargs['fmu'] = self.init_config['fed_conf']['fmu']
        if 'init_state' in self.init_config['model_conf']:
            kwargs['init_state'] = {k:val[i] for k, val in self.init_config['model_conf']['init_state'].items()}
        else:
            kwargs['init_state'] = {}

        kwargs['real_period'] = self.init_config['fed_conf']['real_period']
        kwargs['end_time'] = h.helicsFederateGetTimeProperty(self.fed,h.HELICS_PROPERTY_TIME_STOPTIME)
        return  kwargs


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

            #++++++++++++++++++ getting inputs & messages
            #self.receive_messages()
            for var in self.in_vars:
                self.receive_inputs(var)

            #++++++++++++++++++ models execution
            ts_idx = (int(current_ts-self.offset) / self.period) - 1
            #ts_idx = (current_ts / self.real_period) - 1

            for mod in self.mod_insts:
                mod.step(ts_idx, **{}) # passing the index of timestep starting from 0
            #****************************************************************************************


            #++++++++++++++++++ sending ouytputs & messages
            for var in self.out_vars:
                self.publish(var)
            #self.send_messages()
            #self.reset_messages() # remember to always reset the messages
            #****************************************************************************************


        for mod in self.mod_insts:
            mod.finalize()
        self.save_results()
        self.destroy_federate() # todo this must be embedde in a proper stopping logic right now it destroy the federate at the end of the simulation period in case of RL must be used a flag



    def receive_messages(self):
        if self.ends:
            for mod_num in range(len(self.mod_insts)):
                ep = self.ends[mod_num][0]
                while ep.has_message():
                    msg = ep.get_message()
                    msg_data = json.loads(msg.data)
                    data = {'var_name':msg_data['var_name'] , 'value':msg_data['value'] ,'source':msg.source}
                    self.mod_insts[mod_num].messages_in.append(data)


    def receive_inputs(self, var_name):
        if self.inps:
            for mod_num in range(len(self.mod_insts)):
                inpid = self.inps[mod_num][var_name]
                if inpid.is_updated(): # todo check understand properly what this means
                    value = h.helicsInputGetDouble(inpid)
                    getattr(self.mod_insts[mod_num], 'inputs')[var_name]= value
                    logger.debug(f"\tModel_{mod_num} received input {var_name}={value}")

    def publish(self, var_name):
        ''' this method when is called on a specific ver_name allows all the model instances to publish their value on their specific topic'''
        if self.pubs:
            for mod_num in range(len(self.mod_insts)):
                pubid = self.pubs[mod_num][var_name]
                value = getattr(self.mod_insts[mod_num],'outputs')[var_name]
                h.helicsPublicationPublishDouble(pubid, value)
                logger.debug(f"\tModel_{mod_num} published output {var_name}={value}")

    def send_messages(self):
        if self.ends:
            for mod_num in range(len(self.mod_insts)):
                ep = self.ends[mod_num][0]
                for msg in getattr(self.mod_insts[mod_num], 'messages_out'):
                    out_msg = ep.create_message()
                    out_msg.data = json.dumps({'value':msg['value'], 'var_name':msg['var_name']})
                    out_msg.destination = msg['dest']
                    ep.send_data(out_msg)
    def check_for_reset(self):
        if self.ends:
            for mod_num, ep in self.ends.items():
                while ep.has_message():
                    msg = ep.get_message()
                    msg_data = json.loads(msg.data)
                    if 'RESET' in msg_data.keys():
                        if msg_data['RESET']:
                            #do reset
                            self.reset()
                        else:
                            pass
                    else:
                        pass
    def reset(self):
        logger.debug(f"*************** Federate{self.fed} RESETTING! ***********************")
        pass


    # def reset_messages(self):
    #     for mod in self.mod_insts:
    #         mod.messages_in = []
    #         mod.messages_out = []


    #***************************** new methods Testing block
    # def set_inputs(self, data):
    #     try:
    #         for typology in data: # questo serve per discriminare tra subscritpions e messages, todo implementare parte messages potrebbe essere ridotta senza if
    #             if typology == 'inputs':
    #                 for mod_num in data[typology]:
    #                     #mod_num = int(mod_receiver.split('/')[1])
    #                     for k, val in data[typology][mod_num]:
    #                     #var_name = mod_receiver.split('/')[-1]
    #                     #val = data[typology][mod_receiver]
    #                         getattr(self.mod_insts[mod_num], typology)[k] = val
    #             elif typology == 'messages_in':
    #                 for mod_num in data[typology]:
    #
    #                     #mod_num = int(mod_receiver.split('/')[1])
    #                     #var_name = mod_receiver.split('/')[-1]
    #                     #val = data[typology][mod_receiver]
    #                     setattr(self.mod_insts[mod_num], typology, data[typology][mod_num])
    #     except Exception as e:
    #         logger.error(f"\t ERROR: {e} ---> {data} at ts: {h.helicsFederateGetCurrentTime(self.fed)}")
    #         return
    #
    # def get_outputs(self):
    #     data = {'outputs':{},
    #             'messages_out':{}}
    #     for typology in data:
    #         if typology == 'outputs':
    #             for k, list_of_pubs in self.connection_ref['pub'].items():
    #                 mod_num = int(k)
    #                 for pub in list_of_pubs:
    #                     topic = pub['key']
    #                     var_name = topic.split('/')[-1]
    #                     val = getattr(self.mod_insts[mod_num], typology)[var_name]
    #                     if topic in data[typology].keys(): logger.error(f"\tERROR multiple models instances publish on same topic: {topic}") #todo should assert or raise error
    #                     data[typology][topic] = val
    #         elif typology =='messages_out':
    #             for ep_name, ep in self.ends.items():
    #                 mod_num = int(ep_name.split('/')[1])
    #                 var_name = ep_name.split('/')[-1]
    #                 sending_endpoint =  [i['destinations'] for i in self.connection_ref['end'][mod_num] if i['key']== ep_name and len(i['destinations'])>0]
    #                 if self.connection_ref['end'][mod_num] and  sending_endpoint:
    #                     val = getattr(self.mod_insts[mod_num], typology)[var_name] #only one message per endpoint per var per model
    #                     data['messages_out'][ep_name]={}
    #                     data['messages_out'][ep_name]= val
    #
    #
    #
    #     logger.debug(f"testtest {data}")
    #     return data
    def save_results(self):
        res_file = self.fed.name+'.json'
        path = os.path.join(os.getcwd(), 'federations', self.federation_name, 'results',res_file)
        fed_res = {}
        for mod in self.mod_insts:
            fed_res[mod.model_name]= mod.memory
        save_json(path,fed_res)

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




if __name__ == "__main__":
    #args order 0: fed_conf path , 1: init_conf
    #argv = ['federations/example_federation/BatteryConfig.json',
    #       'federations/example_federation/BatteryConfig_init.yaml']
    #fed = ValueFederate(argv)  # only for testing when launching this autonomously

    fed = Federate(sys.argv) #giusto da usare quando si runna da helics passando gli argv
    fed.execution()
    #fed = ValueFederate([0,'BatteryConfig_init.yaml', 'example_federation'])

