import os
import sys
import helics as h
import logging
from utils import read_yaml, save_json
import importlib.util
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
        #for debugging only #todo remove
        broker = h.helicsCreateBroker("zmq", "", "-f 1 --name=mainbroker")


        fedInfo = h.helicsCreateFederateInfo()
        for info in self.init_config['fed_info']:
            if self.init_config['fed_info'][info]:
                setattr(fedInfo, info, self.init_config['fed_info'][info])
        setattr(fedInfo, 'core_init', "-f 1 --name=mainbroker")

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

        for mod_num in self.connection_ref['pub']:
            for topic in self.connection_ref['pub'][mod_num]:
                if topic not in self.pubs.keys():
                    pubid =self.fed.register_publication(topic, kind='double', local=False)
                    self.pubs[topic] = pubid # todo what to do with the unit of measurement?
                    logger.debug(f"\tRegistered publication: {pubid} for {topic}")
                else:
                    logger.error('ERROR Publication for topic {} already registered'.format(topic)) # todo raise something?

        for mod_num in self.connection_ref['sub']:
            for topic in self.connection_ref['sub'][mod_num]:
                if topic not in self.subs.keys():
                    subid =self.fed.register_subscription(topic)
                    self.subs[topic] = subid
                    logger.debug(f"\tRegistered subscription: {subid} for {topic}")

                else:
                    logger.error('\tERROR Subscription for topic {} already registered'.format(topic))


        #todo properly understand and implment endpoints and inputs



    def model_instantiation(self):
        """ IT IS CALLED INSIDE __init__()
        this method allows multiple instantiation of models for one federate.
        It saves the models instantiation in self.mod_insts and their names in self.mod_names"""
        dir_path = 'models'  #TODO avoid hardcodding add in config (MAYBE CREATE A BASIC PATH CONFIG)
        module_name = dir_path + '.' + self.init_config['fed_conf']['model_script'].split('.')[0]
        if 'class_name' not in self.init_config['fed_conf'].keys():
            class_name = self.init_config['fed_conf']['model_script'].split('.')[0]
        else:
            class_name = self.init_config['fed_conf']['class_name']

        module = importlib.import_module(module_name)
        my_class = getattr(module, class_name)

        for i in range(self.init_config['fed_conf']['n_instances']):
            kwargs = self.init_kwargs(i, class_name)
            model_inst = my_class(**kwargs)
            self.mod_insts.append(model_inst) # appending model instances
            self.mod_names.append(model_inst.model_name) # appending model instances names

        logger.debug(f"\tModels instantiation from fed: {self.fed.name} succesfull!")
        logger.debug(f"\tModel instances names: {self.mod_names}")



    def init_kwargs(self, i, class_name):
        #todo generailze in for loops for each different data typology
        kwargs = {}
        kwargs['model_name'] = class_name + '.' + str(i)
        kwargs['RL_training'] = self.init_config['fed_conf']['RL_training']
        kwargs['stateful'] = self.init_config['fed_conf']['stateful']
        kwargs['mem_attrs'] = self.init_config['fed_conf']['mem_attrs']
        kwargs['inputs'] = {k : self.init_config['model_conf']['inputs'][k][i] for k in self.init_config['model_conf']['inputs']}
        kwargs['outputs'] = {k : self.init_config['model_conf']['outputs'][k][i] for k in self.init_config['model_conf']['outputs']}
        kwargs['messages'] = {k : self.init_config['model_conf']['messages'][k][i] for k in self.init_config['model_conf']['messages']}
        kwargs['params'] = {k: self.init_config['model_conf']['params'][k][i] for k in
                              self.init_config['model_conf']['params']}
        return  kwargs


    def init_dicts(self, i):
        """ THIS METHOD PREPARES THE DICTIONARIES TO PASS TO THE MODEL INSTANCES """
        inp_dict = {k: v for k, v in zip(self.init_config['inputs'], [0] * len(self.init_config['inputs']))}
        out_dict = {k: v for k, v in zip(self.init_config['outputs'], [0] * len(self.init_config['outputs']))}
        mess_dict = {k: v for k, v in zip(self.init_config['messages'], [0] * len(self.init_config['messages']))}
        sim_params = {'update_interval': 60, 'current_time': 0}  # maybe not needed
        try:
            params = {k: self.init_config['params'][k][i] for k in self.init_config['params'].keys()}
            logger.debug(f"\t params in Federate for model{params}")
        except IndexError:
            logger.error(f"\tIndex Error for {i} model instance belongin to {self.fed.name}")
            raise IndexError(
                f"Not enough params for the number of model_instances. Check init_config file in params!")

        return inp_dict, out_dict, mess_dict, sim_params, params




    def execution(self):
        # +++++++++++++++++++ enetering execution mode++++++++++++++++++
        h.helicsFederateEnterExecutingMode(self.fed)
        logger.info("\tEntered HELICS execution mode")
        self.granted_time = h.helicsFederateGetCurrentTime(self.fed)

        while self.granted_time < self.tot_time: #start the wrapping while loop
            #++++++++++++++++++ setting time synchronization #todo this is the basic default example may require to build a more structured method for time synchornization
            requested_time = self.granted_time + self.period + self.offset
            logger.debug(f"Requesting time {requested_time}")
            self.granted_time = h.helicsFederateRequestTime(self.fed, requested_time)
            logger.debug(f"Granted time {self.granted_time}")
            #*****************************************************************************************

            #++++++++++++++++++ getting inputs
            inputs = self.communication_management()
            #*****************************************************************************************

            #++++++++++++++++++ set inputs to model instances
            self.set_inputs(inputs)
            #****************************************************************************************

            #++++++++++++++++++ models execution
            current_ts = h.helicsFederateGetCurrentTime(self.fed)/self.period
            for mod in self.mod_insts:
                mod.step(current_ts)
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
        self.destroy_federate() # todo remove when finished to implement need only in developing stage remove as soon as possible




    def communication_management(self, send=False, data=None):
        if send: #SENDING  # todo just testing
            for topic, pubid in self.pubs.items():
                # Publish out
                h.helicsPublicationPublishDouble(pubid, data['outputs'][topic])

        else: #RECEIVING
            data = {'inputs': {},
                    'messages': {}}
            for topic, subid in self.subs.items():
                value = h.helicsInputGetDouble(subid)
                data['inputs'][topic] = value
                logger.debug(f"\tReceived value {value:.2f}"
                             f" from topic {topic}")

            logger.debug(f"\tdata from inputs {data}")
            return data


    def set_inputs(self, data):
        try:
            for typology in data: # questo serve per discriminare tra subscritpions e messages, todo implementare parte messages
                if typology == 'inputs':
                    for k , list_of_topics in self.connection_ref['sub'].items(): #todo this only works for subscription understand if can be used the same for messsages
                        mod_num = int(k)
                        for topic in list_of_topics:
                            var_name = topic.split('/')[-1]
                            val = data[typology][topic]
                            getattr(self.mod_insts[mod_num], typology)[var_name] = val
        except Exception as e:
            logger.error(f"\t ERROR: {e} ---> {data} at ts: {h.helicsFederateGetCurrentTime(self.fed)}")
            return

    def get_outputs(self):
        data = {'outputs':{},
                'messages':{}}
        for typology in data:
            if typology == 'outputs':
                for k, list_of_topics in self.connection_ref['pub'].items():
                    mod_num = int(k)
                    for topic in list_of_topics:
                        var_name = topic.split('/')[-1]
                        val = getattr(self.mod_insts[mod_num], typology)[var_name]
                        if topic in data[typology].keys(): logger.error(f"\tERROR multiple models instances publish on same topic: {topic}") #todo should assert or raise error
                        data[typology][topic] = val
        logger.debug(f"\tPublishing data : {data}")
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
    argv = [0,'PV_conf.yaml',
          'test_case1']


    fed = Federate(argv)

