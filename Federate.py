import os
import sys
import helics as h
import logging
from utils import read_yaml, save_json
import importlib.util
import json
import copy

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
        self.subs = {}
        self.ends = {}
        self.inps = {}

        #models
        self.mod_insts = []
        self.mod_names = []

        #time synchronization
        self.period = None #will be set when the federate is created
        self.offset = None #will be set when the federate is created
        self.granted_time = None #will be set when the federate is created
        self.tot_time = None #will be set when the federate is created


        #performing tasks
        self.registering()
        self.register_connections()
        self.model_instantiation()
        self.execution()


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
                    self.fed.property[getattr(h,prop_name)] = int(self.init_config['fed_properties'][prop])
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



    def register_connections(self):

        # for mod_num in self.connection_ref['pub']:
        #     for topic in self.connection_ref['pub'][mod_num]:
        #         if topic not in self.pubs.keys():
        #             pubid =self.fed.register_publication(topic, kind='double', local=False)
        #             self.pubs[topic] = pubid # todo what to do with the unit of measurement?
        #             logger.debug(f"\tRegistered publication: {pubid} for {topic}")
        #         else:
        #             logger.error('ERROR Publication for topic {} already registered'.format(topic)) # todo raise something?

        for mod_num in self.connection_ref['pub']:
            for pub_info in self.connection_ref['pub'][mod_num]:
                topic = pub_info['key']
                if topic not in self.pubs.keys():
                    pubid =self.fed.register_publication(topic, kind=pub_info['type'], local=not pub_info['global'], units=pub_info['units'])
                    if 'targets' in pub_info:
                        for t in pub_info['targets']:
                            pubid.add_target(t)
                    self.pubs[topic] = pubid # todo what to do with the unit of measurement?
                    logger.debug(f"\tRegistered publication: {pubid} for {topic}")
                else:
                    logger.error('ERROR Publication for topic {} already registered'.format(topic)) # todo raise something?
        for mod_num in self.connection_ref['sub']: #todo this will probably be deprecated in favor of inputs
            for topic in self.connection_ref['sub'][mod_num]:
                if topic not in self.subs.keys():
                    subid =self.fed.register_subscription(topic)
                    mod_receiver = self.fed.name +'/'+ str(mod_num)+'/'+topic.split('/')[-1]
                    self.subs[mod_receiver] = subid
                    logger.debug(f"\tRegistered subscription: {subid} for {mod_receiver} from {topic}")

                else:
                    logger.error('\tERROR Subscription for topic {} already registered'.format(topic))
        for mod_num in self.connection_ref['inp']:
            for inp_info in self.connection_ref['inp'][mod_num]:
                mod_receiver = self.fed.name+'/'+inp_info['key']
                if mod_receiver not in self.inps.keys():
                    inpid = self.fed.register_input(name=inp_info['key'],kind=inp_info['type'], units=inp_info['units'])
                    if 'targets' in inp_info.keys():
                        for t in inp_info['targets']:
                            inpid.add_target(t)
                    else:
                        logger.error(f'\tERROR Input {inpid.name} does not have targets!')
                    if "multi_input_handling_method" in inp_info.keys():
                        inpid.option['MULTI_INPUT_HANDLING_METHOD'] = h.helicsGetOptionValue('sum') #todo raise error
                    self.inps[mod_receiver]= inpid
                    logger.debug(f"\tRegistered input: {inpid.name} for {mod_receiver} from {inp_info['targets']}")
                else:
                    logger.debug('\tERROR Input for model and var {} already registered'.format(mod_receiver))
        for mod_num in self.connection_ref['end']:
            for end_info in self.connection_ref['end'][mod_num]:
                ep = self.fed.register_global_endpoint(end_info['key'])
                if end_info['destinations']:
                    ep.destination_target = end_info['destinations']
                if end_info['sources']:
                    for src in end_info['sources']:
                        ep.subscribe(src)
                if end_info['key'] not in self.ends.keys(): #end_info key must be the same of mod_receiver
                    self.ends[end_info['key']] = ep
                    logger.debug(f"\tRegistered endpoint: {ep.name} with destinations {end_info['destinations']} and sources {end_info['sources']}")

        #todo properly understand and implment endpoints and inputs



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
        kwargs['RL_training'] = self.init_config['fed_conf']['RL_training']
        kwargs['stateful'] = self.init_config['fed_conf']['stateful']
        kwargs['mem_attrs'] = self.init_config['fed_conf']['mem_attrs']
        kwargs['inputs'] = {k: self.init_config['model_conf']['inputs'][k][i] for k in self.init_config['model_conf']['inputs']}
        kwargs['outputs'] = {k: self.init_config['model_conf']['outputs'][k][i] for k in self.init_config['model_conf']['outputs']}
        kwargs['messages_in'] = {k:[] for k in self.init_config['model_conf']['messages_in']}
        kwargs['messages_out'] = {k:[] for k in self.init_config['model_conf']['messages_out']}
        kwargs['params'] = {k: self.init_config['model_conf']['params'][k][i] for k in
                              self.init_config['model_conf']['params']}
        return  kwargs


    def execution(self):
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

            #++++++++++++++++++ getting inputs
            inputs = self.communication_management()
            #*****************************************************************************************

            #++++++++++++++++++ set inputs to model instances
            self.set_inputs(inputs)
            #****************************************************************************************

            #++++++++++++++++++ models execution
            for mod in self.mod_insts:
                mod.step(current_ts/self.period)
            #****************************************************************************************

            #++++++++++++++++++ get models values
            outputs = self.get_outputs()
            #****************************************************************************************


            #++++++++++++++++++ publish models data
            self.communication_management(send=True, data=outputs)
            #****************************************************************************************


        #when final time and granted time are equal, sto the execution and destry the federate todo this wil be embedded in the while loop
        for mod in self.mod_insts:
            mod.finalize()
        self.save_results()
        self.destroy_federate() # todo this must be embedde in a proper stopping logic right now it destroy the federate at the end of the simulation period in case of RL must be used a flag




    def communication_management(self, send=False, data=None):
        if send: #SENDING  # todo just testing
            for topic, pubid in self.pubs.items():
                # Publish out
                h.helicsPublicationPublishDouble(pubid, data['outputs'][topic]) # todo generalize pubblication type
            for ep_name, ep in self.ends.items():
                if ep_name in data['messages_out'].keys():
                    for dest in ep.destination_target:

                        ep.send_data(str(data['messages_out'][ep_name]), destination=dest) # this only works if in data there is a message for the specific endpoint, menaing that the key must be the same of the endpoint name
            logger.debug(f"\t Sent data as publications {data['outputs']} and as messages {data['messages_out']}")

        else: #RECEIVING
            data = {'inputs': {},
                    'messages_in': {}}
            #subscriptions
            for mod_receiver, subid in self.subs.items():
                value = h.helicsInputGetDouble(subid)
                data['inputs'][mod_receiver] = value

            #inputs
            for mod_receiver, inpid in self.inps.items():
                value = h.helicsInputGetDouble(inpid)
                data['inputs'][mod_receiver] = value

            # MESSAGES ( NO WAITING ONLY READING IF A MESSAGE IS PRESENT)
            for mod_receiver, ep in self.ends.items():
                data['messages_in'][mod_receiver] = []
                while ep.has_message():
                    msg = ep.get_message()
                    data['messages_in'][mod_receiver].append(msg.data)


            logger.debug(f"\tReceived data as inputs or subscription {data['inputs']}  and as messages {data['messages_in']}")
            return data


    def set_inputs(self, data):
        try:
            for typology in data: # questo serve per discriminare tra subscritpions e messages, todo implementare parte messages potrebbe essere ridotta senza if
                if typology == 'inputs':
                    for mod_receiver in data[typology]:
                        mod_num = int(mod_receiver.split('/')[1])
                        var_name = mod_receiver.split('/')[-1]
                        val = data[typology][mod_receiver]
                        getattr(self.mod_insts[mod_num], typology)[var_name] = val
                elif typology == 'messages_in':
                    for mod_receiver in data[typology]:
                        mod_num = int(mod_receiver.split('/')[1])
                        var_name = mod_receiver.split('/')[-1]
                        val = data[typology][mod_receiver]
                        getattr(self.mod_insts[mod_num], typology)[var_name] = val
        except Exception as e:
            logger.error(f"\t ERROR: {e} ---> {data} at ts: {h.helicsFederateGetCurrentTime(self.fed)}")
            return

    def get_outputs(self):
        data = {'outputs':{},
                'messages_out':{}}
        for typology in data:
            if typology == 'outputs':
                for k, list_of_pubs in self.connection_ref['pub'].items():
                    mod_num = int(k)
                    for pub in list_of_pubs:
                        topic = pub['key']
                        var_name = topic.split('/')[-1]
                        val = getattr(self.mod_insts[mod_num], typology)[var_name]
                        if topic in data[typology].keys(): logger.error(f"\tERROR multiple models instances publish on same topic: {topic}") #todo should assert or raise error
                        data[typology][topic] = val
            elif typology =='messages_out':
                for ep_name, ep in self.ends.items():
                    mod_num = int(ep_name.split('/')[1])
                    var_name = ep_name.split('/')[-1]
                    sending_endpoint =  [i['destinations'] for i in self.connection_ref['end'][mod_num] if i['key']== ep_name and len(i['destinations'])>0]
                    if self.connection_ref['end'][mod_num] and  sending_endpoint:
                        val = getattr(self.mod_insts[mod_num], typology)[var_name] #only one message per endpoint per var per model
                        data['messages_out'][ep_name]={}
                        data['messages_out'][ep_name]= val



        logger.debug(f"testtest {data}")
        return data
    def save_results(self):
        res_file = self.fed.name+'.json'
        path = os.path.join(os.getcwd(), 'federations', self.federation_name, 'results',res_file)
        fed_res = {}
        for mod in self.mod_insts:
            fed_res[mod.model_name]= mod.memory
        save_json(path,fed_res)
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

    #fed = ValueFederate([0,'BatteryConfig_init.yaml', 'example_federation'])

