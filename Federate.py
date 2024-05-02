#todo create a generalized and abstract class for each federates
import sys
import helics as h
import logging
from utils import read_yaml
import importlib.util
from abc import ABC, abstractmethod
sys.path.append('models/')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Federate(ABC):
    def __init__(self, args):
        self.fed_config, self.init_config = self.init_config(args)
        self.mod_insts = []
        self.mod_names = []
        self.fed = None
        self.registering()
        self.model_inst()
        self.destroy_federate()  # need only in developing stage remove as soon as possible

    @staticmethod
    def init_config(args):
        fed_config = args[0]
        init_config = read_yaml(args[1])

        return fed_config, init_config

    def registering(self):
        self.fed = h.helicsCreateValueFederateFromConfig(
            self.fed_config)
        self.federate_name = h.helicsFederateGetName(self.fed)
        logger.info(f"Created federate {self.federate_name}")

        #sub_count = h.helicsFederateGetInputCount(self.fed)
        #logger.debug(f"\tNumber of subscriptions: {sub_count}")
        #pub_count = h.helicsFederateGetPublicationCount(self.fed)
        #logger.debug(f"\tNumber of publications: {pub_count}")

        #instance the number of models that is expressed by the pub_count

    def receive_inputs(self):
        pass

    def send_outputs(self):
        pass

    def req_time(self):
        #to synchronize with the federation
        pass
    def execution(self):
        #set time
        #set values to the model
        #execute the modle
        #get values from the model
        #publish models data
        pass


    def destroy_federate(self):
        """

        """

        # Adding extra time request to clear out any pending messages to avoid
        #   annoying errors in the broker log. Any message are tacitly disregarded.
        #grantedtime = h.helicsFederateRequestTime(self.fed, h.HELICS_TIME_MAXTIME)
        status = h.helicsFederateDisconnect(self.fed)
        h.helicsFederateDestroy(self.fed)
        logger.info("Federate finalized")


if __name__ == "__main__":
    #args order 0: fed_conf path , 1: init_conf
    argv = ['federations/example_federation/BatteryConfig.json',
            'federations/example_federation/BatteryConfig_init.yaml']
    fed = ValueFederate(argv)  # only for testing when launching this autonomously
    #fed = Federate(sys.argv) giusto da usare quando si runna da helics passando gli argv
    #fed.registering()
    fed.execution()
