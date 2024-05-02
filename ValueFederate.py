import os
import sys
import helics as h
import logging
from utils import read_yaml
import importlib.util
import copy

sys.path.append('models/')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class ValueFederate:
    def __init__(self, args):

        self.fed_config, self.init_config = self.init_config(args)
        self.mod_insts = []
        self.mod_names = []
        self.fed = None
        self.federate_name = None
        #time synchronization
        self.period = self.fed_config['period']
        self.offset = self.fed_config['offset']
        self.granted_time = 0.0
        #data exchange
        self.sub_count = None
        self.pub_count = None
        self.end_count = None
        self.sub_id = {}
        self.pub_id = {}
        self.end_id = {}

        #performing tasks
        self.registering()
        self.execution()





    @staticmethod
    def init_config(args):
        federation_name = args[-1]
        #todo federations is hardcoded must be taken from a global path config file
        fed_config = os.path.join(os.getcwd(), 'federations', federation_name, args[1])
        init_config = read_yaml(os.path.join(os.getcwd(), 'federations', federation_name, args[2]))

        return fed_config, init_config
    def registering(self):
        self.fed = h.helicsCreateValueFederateFromConfig(
            self.fed_config)

        self.federate_name = h.helicsFederateGetName(self.fed)
        logger.info(f"Created federate {self.federate_name}")

        # counting subscriptiona and pubblications
        #todo shopuld generalize also the endpoints
        self.end_count = h.helicsFederateGetEndpointCount(self.fed)
        logger.info(f"\tNumber of endpoints: {self.end_count}")
        self.sub_count = h.helicsFederateGetInputCount(self.fed)
        logger.debug(f"\tNumber of subscriptions: {self.sub_count}")
        self.pub_count = h.helicsFederateGetPublicationCount(self.fed)
        logger.debug(f"\tNumber of publications: {self.pub_count}")

        #model instantiation
        self.model_inst()

        #registering subscriptions
        for i in range(0, self.sub_count):
            self.sub_id[i] = h.helicsFederateGetInputByIndex(self.fed, i)
            sub_name = h.helicsInputGetTarget(self.sub_id[i])
            logger.debug(f"\tRegistered subscription---> {sub_name}")
        #registering publication
        for i in range(0, self.pub_count):
            self.pub_id[i] = h.helicsFederateGetPublicationByIndex(self.fed, i)
            pub_name = h.helicsPublicationGetName(self.pub_id[i])
            logger.debug(f"\tRegistered publication---> {pub_name}")
        #registering endpoints
        for i in range(0, self.end_count):
            self.end_id[i] = h.helicsFederateGetEndpointByIndex(self.fed, i)
            end_name = h.helicsEndpointGetName(self.end_id[i])
            logger.debug(f"\tRegistered Endpoint ---> {end_name}")


    def model_inst(self):
        """ IT IS CALLED INSIDE registering()
        this method allows multiple instantiation of models for one federate.
        It saves the models instantiation in self.mod_insts and their names in self.mod_names"""
        dir_path = 'models'  #TODO avoid hardcodding add in config (MAYBE CREATE A BASIC PATH CONFIG)
        module_name = dir_path + '.' + self.init_config['_model_script'].split('.')[0]
        if 'class_name' not in self.init_config.keys():
            class_name = self.init_config['_model_script'].split('.')[0]
        else:
            class_name = self.init_config['_class_name']

        module = importlib.import_module(module_name)
        my_class = getattr(module, class_name)

        for i in range(self.init_config['_n_instances']):

            kwargs = self.init_kwargs(i, class_name)







            #model_name = class_name + '_' + str(i)

            #inp_dict, out_dict, mess_dict, sim_params, params = self.init_dicts(i)
            #model_inst = my_class(model_name, inp_dict, out_dict, mess_dict, sim_params, params)
            model_inst = my_class(**kwargs)

            #check if init_conf states RL application and memory
            # if self.init_config['stateful']:
            #     model_inst.init_memory = True
            # if self.init_config['RL_training']:
            #     model_inst.save_init_state = True

            self.mod_insts.append(model_inst) # appending model instances
            self.mod_names.append(model_inst.model_name) # appending model instances names
        logger.debug(f"\tModels instantiation from fed: {self.federate_name} succesfull!")
        logger.debug(f"\tModel instances names: {self.mod_names}")


    def init_kwargs(self, i, class_name):
        kwargs = {}
        kwargs['model_name'] = class_name + '_' + str(i)
        for k, v in self.init_config.items():
            if k.startswith('__'):
                kwargs[k] = v
            elif not k.startswith('__') and not k.startswith('_') and v:
                kwargs[k] = {key: v[key][i] for key in v.keys()}
            elif not k.startswith('__') and not k.startswith('_') and not v:
                kwargs[k] = {}
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
            logger.error(f"\tIndex Error for {i} model instance belongin to {self.federate_name}")
            raise IndexError(
                f"Not enough params for the number of model_instances. Check init_config file in params!")

        return inp_dict, out_dict, mess_dict, sim_params, params




    def execution(self):
        # +++++++++++++++++++ enetering execution mode++++++++++++++++++
        h.helicsFederateEnterExecutingMode(self.fed)
        logger.info("\tEntered HELICS execution mode")


        #start the wrapping while loop
            #set time
            #set values to the model
            #execute the modle
            #get values from the model
            #publish models data


        #when final time and granted time are equal, sto the execution and destry the federate todo this wil be embedded in the while loop
        self.destroy_federate()  # todo remove when finished to implement need only in developing stage remove as soon as possible
    # def time_management(self):
    #     #
    #     logger.debug(f"Requesting time {requested_time}")
    #      = self.fed.request_time(requested_time)
    #     logger.debug(f"Granted time {grantedtime}")

    def communication_management(self, send=False):
        if self.end_count!=0:
            print('do stuff')
        elif self.sub_count !=0:
            print('dostuff')
        elif self.pub_count !=0:
            print('dostuff')

        pass


    def receive_sub(self):
        pass
    def receive_message(self):
        pass
    def pubblish(self):
        pass
    def send_message(self):
        pass
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
    fed = ValueFederate(sys.argv) #giusto da usare quando si runna da helics passando gli argv


