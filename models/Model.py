import numpy as np
import logging
from copy import deepcopy
from abc import ABC,  abstractmethod
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Model(ABC):
#    def __init__(self, name, inputs_dict, outputs_dict, mess_dict, sim_params, params, **kwargs):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        #todo perform a chekc on strictly required arguments
        #possible call of initialization() #todo think about it
        logger.info(f"\t\tModel {self.model_name} instantiated with the following kwargs: {kwargs}!")

        self._set_additionals()


    def _set_additionals(self):
        if getattr(self, '__stateful', None):
            self._init_memory()
            logger.info(f"\t\tMemory instantiated for Model {self.model_name}!") #todo better logging
        if getattr(self, '__RL_training', None):
            self._init_state()
            logger.info(f"\t\tInitial state for Model {self.model_name} set as follow: {self.initial_state}")  # todo better logging

    def _init_memory(self):
        self.memory = {'inputs':{},
                       'outputs':{},
                       'messages':{},
                       'params':{},
                       'sim_params':{}}
        if getattr(self, '__mem_attrs', None):
            for attr in getattr(self, '__mem_attrs'):
                self.memory[attr.split('.')[0]][attr.split('.')[1]] = []
        else:
            logger.warning('\t\tMemory attrs are not specified in the init_config. NO MEMORY WILL BE INITIATED!')

    def _init_state(self):
        self.initial_state = {'inputs': deepcopy(self.inputs),
           'outputs': deepcopy(self.outputs),
           'messages': deepcopy(self.messages),
           'params': deepcopy(self.params),
           'sim_params': deepcopy(self.sim_params)}

    def _fill_memory(self):
        if not self.memory:
            return
        else:
            for var in self.memory:
                if var in self.inputs.keys():
                    self.memory['inputs'][var].append(deepcopy(self.inputs[var]))
                elif var in self.outputs.keys():
                    self.memory['outputs'][var].append(deepcopy(self.outputs[var]))
                elif var in self.messages.keys():
                    self.memory['messages'][var].append(deepcopy(self.messages[var]))
                elif var in self.sim_params.keys():
                    self.memory['sim_params'][var].append(deepcopy(self.sim_params[var]))
                elif var in self.params.keys():
                    self.memory['params'][var].append((deepcopy(self.params[var])))
                else:
                    logger.error(f'\t\t{var} not defined in init config for memory')

    def _reset(self):
        self.inputs = self.initial_state['inputs']
        self.outputs = self.initial_state['outputs']
        self.sim_params = self.initial_state['sim_params']
        self.params = self.initial_state['params']
        for var in self.memory:
            self.memory[var] = []
    def get_time(self):
        return self.sim_params['time']
    def _set_time(self, ts):
        self.sim_params['time'] = ts
    @abstractmethod
    def step(self):
        '''overwrite this method with the actual model calculations:
        rememeber the needed inputs and outputs are in self.inputs[chosen_name] and self.outputs[chosen_name], these are variables that comes from outside the model and need tpo leave the model
        any paarameter for the physical model can be found in self.params[chosen_name],
        any parameter relative to the simulation can be found in self.sim_params[standard_name]'''
        return
    @abstractmethod
    def finalize(self):
        pass


if __name__ == '__main__':

    #todo probably no need of sim params they can be retrieved from federate

    inputs_dict = {'voltage': None}
    outputs_dict = {'current': None}
    sim_params = {'update_interval': 60,
                  'current_time': 0}
    params = {}