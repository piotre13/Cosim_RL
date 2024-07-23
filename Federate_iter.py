import logging
from Federate import Federate
from iterutils import *
import sys
import numpy as np
import time
import pprint
pp = pprint.PrettyPrinter(indent=4)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)



#TODO need to implement also the convergence iteration type (it needs to iterate until convergence is achieved by both federates)
# thus it need configurations and correct implementation in the execution method as well as the possibility to configure the convergency check




class Federate_iter(Federate):
    def __init__(self, args):
        super().__init__(args)

        if self.iter_type == 'step': # must need a specified input order output
            try:
                assert 'var_order' in self._iter_conf.keys()
                # assert 'inputs' in self._iter_conf['var_order'].keys() and 'outputs' in self._iter_conf['var_order'].keys()
                # self.inputs_order = self._iter_conf['var_order']['inputs']
                # self.outputs_order = self._iter_conf['var_order']['outputs']
                self.var_order = self._iter_conf['var_order']
                self.max_iter = 10 # todo for now 10 use high number after debugging
                # self.additional_model_params()



            except AssertionError as err:
                logger.error(f"Iter type step but missing var_order information.\n")
        else:
            #todo implement here initialization of iteration federate that must go to convergence
            pass

    def model_kwargs(self, i, class_name):

        '''this method is important beacuse passes attributes to model instances, if different fgederates deal with different model requirements (e.g. RL agent do not have inputs outputs)
        this method must be overwritten in the specific Federate class'''
        kwargs = {}

        # basic attr
        kwargs['model_name'] = f"%s/%s/%s" % (self._name, i, class_name)
        kwargs['RL_training'] = self._fed_conf['RL_training']

        # basic knowledge on simulation
        kwargs['start_time'] = self.start_time  # datetime
        kwargs['start_period'] = self.start_period  # seconds
        kwargs['sim_period'] = self.sim_period  # seconds
        kwargs['real_period'] = self.real_period  # seconds
        kwargs['current_period'] = self.current_period  # seconds
        kwargs['end_period'] = self.end_period  # seconds
        kwargs['end_time'] = self.end_time  # datetime

        # required model specific attrs
        kwargs['inputs_list'] = self._model_conf['model_specific_required']['inputs_k']
        kwargs['outputs_list'] = self._model_conf['model_specific_required']['outputs_k']
        # kwargs['params_list'] = self._model_conf['model_specific_required']['params_k']
        kwargs['params_list'] = list(self._model_conf['model_specific_required']['params'].keys())

        # check initistate only if specified if not log the fact that models have not initial state
        if self._model_conf['model_specific_required']['init_state']:
            assert self.check_init_state(kwargs['inputs_list'], kwargs['outputs_list'], kwargs[
                'params_list']) == True  # every model must HAVE an init state (this is useful for RL (in future could be less restrictive)
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

        kwargs['params'] = {k: self._model_conf['model_specific_required']['params'][k][i] for k in
                            kwargs['params_list']}
        kwargs['init_state'] = {"inputs": kwargs['inputs'], "outputs": kwargs['outputs'], "params": kwargs['params']}

        kwargs['memory'] = self._fed_conf['memory']
        # pass all the model_specific_additional
        for k, val in self._model_conf['model_specific_additional'].items():
            kwargs[k] = val[i]

        self._iter_conf = self._fed_conf['iteration']
        self.iter_type = self._iter_conf['type']
        # self.inputs_order = self._iter_conf['var_order']['inputs']
        # self.outputs_order = self._iter_conf['var_order']['outputs']
        # kwargs['iter_type']= self.iter_type
        # kwargs['inputs_order']= self.inputs_order
        # kwargs['outputs_order']= self.outputs_order

        return kwargs
    # def additional_model_params(self):
    #     # passing iteration additional params
    #     self._iter_conf = self._config['iteration']
    #     self.iter_type = self._iter_conf['type']
    #     for model in self._model_instances:
    #         setattr(model, 'iter_type', self.iter_type)
    #         setattr(model, 'inputs_order', self.inputs_order)
    #         setattr(model, 'outputs_order', self.outputs_order)
    #


    def execution(self):
        h.helicsFederateEnterExecutingMode(self._fed)


        logger.info("@@ Entered HELICS execution mode @@ \n")
        # self.granted_period = h.helicsFederateGetCurrentTime(self._fed)
        self.granted_period = 0
        while self.granted_period < self.end_period:  # start the wrapping while loop
            # send triggering message:
            # for i in range(len(self._model_instances)):
            #     self.out_msgs[i] = []
            #     self.out_msgs[i].append(
            #         {"source": None, "time": None, "var_name": 'trigger', "destination": None, "value": None})
            # self._send_messages('iter_exchange')
            # self.in_msgs = {}

            # ++++++++++++++++++ setting time synchronization #no offset
            requested_period = self.granted_period + self.sim_period + self.offset
            # self.granted_period = h.helicsFederateRequestTime(self._fed, requested_period)
            logger.debug(
                f"************* Requesting time {requested_period} -- Granted time {self.granted_period} **************")
            self.current_period = h.helicsFederateGetCurrentTime(self._fed) - self.offset
            logger.debug(f"current time: {self.current_period}\n")



            #receive inputs or control or reset commands before starting the iteration (for the first iterating fed)

            # self._receive_messages()  # update self.in_msgs class variable
            # self._check_reset()
            # self._receive_inputs()  # update self.in_values class variable
            # self.inputs_to_model()

            #should perform the step anyways (if is a iter starter will produce outputs an publish them if not it will do nothing
            ts = int(self.current_period / self.sim_period)
            # for mod in self._model_instances:
            #     mod.step(ts, **{"itr": -1}) #this is a special step calling in whihc we state that this step is required using normal and non iterative inputs to start an iterative process


            #iter vars
            n_iter = 0
            converged = False  # for now does not should be used for convergency checking in the different iteration type
            itr_flag = h.helics_iteration_request_force_iteration # iteration flag
            # itr_flag = h.helics_iteration_request_iterate_if_needed
            # itr_state = -1
            

            #iteration loop
            do_step = 0
            while n_iter < self.max_iter:

                self.granted_period, itr_s = h.helicsFederateRequestTimeIterative(self._fed, requested_period, itr_flag)
                logger.debug(f"Entering iterative state... with itr_state = {itr_s}")
                n_iter+=1
                if do_step > len(list(self.var_order.keys()))-1 or n_iter== self.max_iter:
                    logger.debug(f"Iterative state EXITED\n")
                    self.granted_period = h.helicsFederateRequestTime(self._fed, requested_period)
                    break


                #receiving iter message
                self._receive_inputs()
                self._receive_messages()  # update self.in_msgs class variable # in the iteration loop data exchange is only done through messages endpoints

                #check iter state based on received inputs
                # itr_state = self.itr_state()
                # logger.debug(f"ITERATION_STATE: {itr_state}")


                if self.do_step_check(do_step):
                    self.clear_model_outputs()
                    self.inputs_to_model()
                    # performing step
                    logger.debug(f"PERFORMING STEP: {do_step}\n")
                    for mod in self._model_instances:
                        mod.step(ts, **{'itr': do_step})

                    self.outputs_from_model()  # only insert in the buffers the not None outputs
                    self._send_messages('iter_exchange')  # in the iteration loop data exchange is only done through messages endpoints
                    self._publish_outputs()

                    #dostep
                    do_step+=1

                else:
                    if n_iter== self.max_iter:
                        logger.debug(f"Iteration FAILED\n")
                        break
                    continue


            #     self.inputs_to_model() # impose the correct inputs and clear the buffers
            #
            #
            #     # itr, itr_started = self.itr_step(itr_started) # check the iteration state on the basis of the inputs arrived is the same for each model
            #     # logger.debug(f"&&& ITR: {itr}")
            #
            #
            #     # before performing the step i need to set to None all the models outputs so I,m sure that the model will only impose the right outputs and the in outputs_from model i will only take the not None outputs
            #     self.clear_model_outputs()
            #     #performing step
            #     for mod in self._model_instances:
            #         mod.step(ts, **{'itr':itr_state})
            #
            #     #sending iter message
            #     self.outputs_from_model() # only insert in the buffers the not None outputs
            #     self._send_messages('iter_exchange') # in the iteration loop data exchange is only done through messages endpoints
            #     self._publish_outputs()
            #
            #
            #     if itr_state == -2 or converged == True or  n_iter == self.max_iter:  # todo change n_iter with ma is onbly for safety while debugging
            #         logger.debug(f"Iterative state EXITED\n")
            #         break
            #
            #     else:
            #         n_iter +=1
            #         if n_iter == self.max_iter:
            #             logger.error(f" Federate iterative did not converge!\n")
            #
            # self.outputs_from_model()  # only insert in the buffers the not None outputs
            # self._send_messages(
            #     'iter_exchange')  # in the iteration loop data exchange is only done through messages endpoints
            # self._publish_outputs()
            # self.outputs_from_model()
            #
            #
            # # ++++++++++++++++++ sending ouytputs & messages
            # # self._send_messages()
            # self._publish_outputs()

        for mod in self._model_instances:
            mod.finalize()
            # self.save_results() # todo decide how to save results
        self._destroy_federate()  # todo this must be embedde in a proper stopping logic right now it destroy the federate at the end of the simulation period in case of RL must be used a flag


    def do_step_check(self,do_step):
        keys=[]
        for i in range(len(self._model_instances)):
            rec_inp_keys = []
            rec_msg_keys = []

            if self.in_values:
                rec_inp_keys = list(self.in_values[i].keys())

            if self.in_msgs:
                rec_msg_keys = list([k['var_name'] for k in self.in_msgs[i]])

            keys = rec_inp_keys + rec_msg_keys
        if all (k in keys for k in self.var_order[do_step]['inp']):
            return True
        else:
            return False
    def clear_model_outputs(self):
        for model in self._model_instances:
            outs = getattr(model, 'outputs')
            for k in outs.keys():
                getattr(model, 'outputs')[k] = None
    def itr_state(self):
        if self.empty_in():
            logger.debug(f" The federate has no incoming Inputs or messages for any of its model instances.")
            return -3

        else:
            match_iter_vars  = []
            for i in range(len(self._model_instances)):
                rec_inp_keys=[]
                rec_msg_keys=[]

                if self.in_values:
                    rec_inp_keys = list(self.in_values[i].keys())

                if self.in_msgs:
                    rec_msg_keys = list([k['var_name'] for k in self.in_msgs[i]])

                keys = rec_inp_keys + rec_msg_keys

                for j in range(len(self.inputs_order)):
                    if set(keys) == set(self.inputs_order[j]):
                        match_iter_vars.append(j)
                    else:
                        match_iter_vars.append(None)


            if not match_iter_vars.count(match_iter_vars[0]):
                logger.error("ERRROR the models are receiving different values or messages\n")
            else:
                if match_iter_vars[0] == None:
                    return -1
                elif match_iter_vars[0] > len(self.inputs_order):
                    return -2
                else:
                    return match_iter_vars[0]


    def outputs_from_model(self):
        ''' This method reads the model self.outputs and generate the sel.out_values always regenrating it from empty dict'''

        i=0
        self.out_values = {}
        self.out_msgs = {}
        for model in self._model_instances:
            self.out_values[i] = {}
            self.out_msgs[i] = []
            logger.debug(f"model_outputs = {getattr(model, 'outputs')}")
            for k, val in getattr(model, 'outputs').items():
                if val:
                    if k not in self.pub_ids[i]:
                        #put in message buffer
                        self.out_msgs[i].append({
                                                "source": self._fed.name+'/'+str(i)+'/'+k ,   #must contain the whole var name Federate/modnum/varname
                                                 "time": self.current_period,
                                                 "var_name": k,
                                                 "destination": None, #must contain the whole endpoint name to send to
                                                 "value": val})
                    else:
                        #put in val buffer
                        self.out_values[i][k]=val
                else:
                    pass
            i=+1






    # def itr_step(self, started):
    #     status = []
    #     for mod in self._model_instances:
    #         inputs = getattr(mod,'inputs')
    #         logger.debug(f"### == INPUTS in the Model: {pp.pformat(inputs)}")
    #         for i in range(len(self.inputs_order)):
    #             if all(inputs[k] for k in self.inputs_order[i]):
    #                 status.append(i)
    #                 started=True
    #
    #     if len(status)==0 and started:
    #         return -2, started
    #     elif len(status) == 0 and not started:
    #         return -1, started
    #     else:
    #         #check they are alligned
    #         assert status.count(status[0]) == len(status)
    #         return status[0], started
    def empty_in(self):
        if not self.in_values and not self.in_msgs:
            return True
        var=[]
        for i in range(len(self._model_instances)):

            if not self.in_values:
                if not self.in_msgs[i]:
                    var.append(True)
                else:
                    var.append(False)
            elif not self.in_msgs:
                if not self.in_values[i]:
                    var.append(True)
                else:
                    var.append(False)

            elif self.in_values and self.in_msgs:
                if not self.in_msgs[i] and not self.in_values[i]:
                    var.append(True)
                else:
                    var.append(False)

        if var.count(var[0])!= len(var):
            logger.error(f" Model instances are receiving different things\n")

        else:
            return var[0]
    def check_end_condition(self, itr):
        #todo da implementare la parte per convergenza con u if aggiuntivo esterno sul tipo di iter
        if itr ==-2:
            return True
        else:
            return False

    def inputs_to_model(self):
        i=0
        for model in self._model_instances:
            inputs_pool = {}
            if self.in_msgs:
                for msg in self.in_msgs[i]:
                    inputs_pool[msg['var_name']]= msg['value']
            if self.in_values:
                for var_name, value in self.in_values[i].items():
                    inputs_pool[var_name] = value

            #set to model all the inputs
            for inp_name, val in inputs_pool.items():
                getattr(model,'inputs')[inp_name] = val
            i+=1

        #clear in_msg and in_values
        self.in_values = {}
        self.in_msgs = {}

    # def inputs_to_model(self):
    #     ''' this method is the one to overwrite when dealing with different typologies of federates. In this case it represent a simple federate that is
    #     used for basic simulators that can receive both inputs and messages but only send outputs. In this function we read teh in_values and in_msgs buffers
    #      and impose in the models the corresponding inputs or params vars. '''
    #     #can be taken from both messages and inputs and matched with the corresponding mod.inputs  keys of the model
    #
    #     #clearing iterative inputs with None
    #     for model in self._model_instances:
    #         for inp_l in self.inputs_order:
    #             for k in inp_l:
    #                 getattr(model, 'inputs')[k] = None
    #
    #
    #     if not self.in_values  and not self.in_msgs:
    #         logger.debug(f" The federate has no incoming Inputs or messages for any of its model instances.")
    #         return
    #
    #     i = 0
    #     for model in self._model_instances:
    #         # check if there are any messages to change the inputs or the params (leaning it open to control params
    #         if self.in_msgs:
    #             for msg in self.in_msgs[i]:
    #                 if msg['destination'].endswith('actuator') or msg['destination'].endswith('iter_exchange') :
    #                     if msg['var_name'] in model.inputs.keys():
    #                         # impose tha value on the model input
    #                         getattr(model, 'inputs')[msg['var_name']]= msg['value']
    #                     elif msg['var_name'] in model.params.keys():
    #                         # impose tha value on the model param (not common only with RT param changing
    #                         getattr(model, 'params')[msg['var_name']]= msg['value']
    #
    #             # empty the buffers to be sure i can use inputs to model even if I only called one of _receive_inputs or _receive_message before
    #             self.in_msgs = {mod_num: [] for mod_num in range(len(self._model_instances))}
    #
    #         # Imposing inputs received as classic value based inputs only inputs params must be changed with messages
    #         if self.in_values:
    #             for var_name, value  in self.in_values[i].items():
    #                 if var_name in model.inputs.keys():
    #                     getattr(model, 'inputs')[var_name] = value
    #
    #             #empty the buffers to be sure i can use inputs to model even if I only called one of _receive_inputs or _receive_message before
    #             self.in_values = {mod_num:{} for mod_num in range(len(self._model_instances))}
    #         i+=1

    # def outputs_from_model(self):
    #     ''' This method reads the model self.outputs and generate the sel.out_values always regenrating it from empty dict'''
    #
    #     i = 0
    #     self.out_values = {}
    #     for model in self._model_instances:
    #         self.out_values[i] = {}
    #         self.out_msgs[i] = []
    #         outputs = getattr(model, 'outputs')
    #         for k, val in outputs.items():
    #             if k in self.pub_ids[i].keys():
    #                 self.out_values[i][k] = val
    #             else:
    #                 self.out_msgs[i].append({"source": self._fed.name+'/'+str(i)+'/'+k ,   #must contain the whole var name Federate/modnum/varname
    #                  "time": self.current_period,
    #                  "var_name": k,
    #                  "destination": None, #must contain the whole endpoint name to send to
    #                  "value": val})
    #         i += 1

if __name__ == "__main__":
    #args order 0: fed_conf path , 1: init_conf
    #argv = ['federations/example_federation/BatteryConfig.json',
    #       'federations/example_federation/BatteryConfig_init.yaml']
    #fed = ValueFederate(argv)  # only for testing when launching this autonomously

    fed = Federate_iter(sys.argv) #giusto da usare quando si runna da helics passando gli argv
    fed.execution()
    #fed = ValueFederate([0,'BatteryConfig_init.yaml', 'example_federation'])

