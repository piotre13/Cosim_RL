import sys
import logging
from Federate import Federate
import helics as h
from iterutils import *
import numpy as np
import time
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class Federate_iter(Federate):
    def __init__(self, args):
        super().__init__(args)
        self.feditr = FedItr(logger)
        if 'inputs_order' in self.init_config['fed_conf'].keys():
            self.inputs_order = self.init_config['fed_conf']['inputs_order']
            for mod in self.mod_insts:
                setattr(mod, 'inputs_order', self.inputs_order)
        if 'outputs_order' in self.init_config['fed_conf'].keys():
            self.outputs_order = self.init_config['fed_conf']['outputs_order']
            for mod in self.mod_insts:
                setattr(mod, 'outputs_order', self.outputs_order)
        assert len(self.inputs_order) == len(self.outputs_order)


    def execution(self): # execution base for inp out exchange and message receiver
    # +++++++++++++++++++ enetering execution mode++++++++++++++++++
        h.helicsFederateEnterExecutingMode(self.fed)
        logger.info("\tEntered HELICS execution mode")
        self.granted_time = h.helicsFederateGetCurrentTime(self.fed)


        itr_convergence = True
        itr_flag = h.helics_iteration_request_force_iteration

        # setting the number of iterations: if inputs order ha len > 0 fixed number of iterations else iterate until convergence or max iter num
        # if 'inputs_order' in self.__dict__.keys():
        #     if len(self.inputs_order) > 0:
        #         itr_needed = len(self.inputs_order)
        #         itr_convergence = False
        #     else:
        #         itr_needed = self.init_config['fed_properties']['INT_MAX_ITERATIONS'] #int(h.helicsFederateGetTimeProperty(self.fed, h.HELICS_PROPERTY_INT_MAX_ITERATIONS))
        #         logger.debug(f"\tIteration type : CONVERGENCE - inputs order not specified. MAX iter = { itr_needed}")
        #
        # else:
        #     itr_needed = self.init_config['fed_properties']['INT_MAX_ITERATIONS'] #int(h.helicsFederateGetTimeProperty(self.fed, h.HELICS_PROPERTY_INT_MAX_ITERATIONS))
        #     logger.debug(f"\tIteration type : CONVERGENCE - inputs order not present. MAX iter = { itr_needed}")

        # while self.granted_time < self.tot_time: #start the wrapping while loop
        for t in np.arange(self.period, self.tot_time, self.period):
            #++++++++++++++++++ setting time synchronization
            #self.granted_time = h.helicsFederateGetCurrentTime(self.fed)


            #requested_time = self.granted_time + self.period + self.offset
            current_ts = h.helicsFederateRequestTime(self.fed, t)


            logger.debug(
                f"************* Requesting time {t} -- Granted time {current_ts} **************")

            itr = 0
            # self.granted_time, itr_state = self.feditr.request_time(self.fed, requested_time, itr, itr_flag,
            #                                                         itr_max=itr_needed)
            # while True: # starting the iteration loop
            current_ts = h.helicsFederateGetCurrentTime(self.fed)

            for itr in range(100):

                #********* stopping condition for fixed itarations or max iteration
                # if itr_state == h.helics_iteration_result_next_step:
                #     logger.debug("\tIteration complete!")
                #     break
                time.sleep(0.02)

                current_ts, itr_state = h.helicsFederateRequestTimeIterative(
                    self.fed,
                    t,
                    h.helics_iteration_request_force_iteration
                )

                #******************************************************************

                # Get Subscriptions
                #for var in self.inputs_order[itr]:
                #    self.receive_inputs(var)

                for var in self.in_vars:
                    self.receive_inputs(var)
                #********* stopping condition for fixed itarations or max iteration
                # if  itr_convergence:
                #     #todo define a logic for sgenarilzed convergency stopping conditions ( will need to specify in conf the target variable to be converging and the error tolerance
                #     # if the logic satisfied use continue that should avoid step and publishing thus automatically letting know helics that is over (maybe for the convergence will need a preliminary publish...
                #     # error = self.feditr.check_error(self.conv_var)
                #     # logger.debug(f"\tError = {error}")
                #     # if (error < self.epsilon) and (itr > 0):
                #     # no further iteration necessary
                #     #continue
                #     pass
                #     # else:
                    #     pass
                #*****************************************************************

                #logger.debug(f"\tstep iter {itr}:")
                ts_idx = int(current_ts / self.period) # todo the integer conversion could be a problem when using microstepping
                logger.debug(f"TS:{ts_idx}")
                for mod in self.mod_insts:
                    mod.step(ts_idx, **{'iter_n':itr})

                for var in self.out_vars:
                    self.publish(var)

                if itr == len(self.outputs_order)-1:
                    break
                itr += 1

              #  self.granted_time, itr_state = self.feditr.request_time(self.fed, requested_time, itr, itr_flag, itr_max=itr_needed)

            logger.debug("******************************************************************************************")

        for mod in self.mod_insts:
            mod.finalize()
        self.save_results()
        self.destroy_federate() # todo this must be embedde in a proper stopping logic right now it destroy the federate at the end of the simulation period in case of RL must be used a flag

if __name__ == '__main__':
    fed = Federate_iter(sys.argv)  # giusto da usare quando si runna da helics passando gli argv
    fed.execution()
    # fed = ValueFederate([0,'BatteryConfig_init.yaml', 'example_federation'])

