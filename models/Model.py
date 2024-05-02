import numpy as np
import logging
from copy import deepcopy
from abc import ABC,  abstractmethod
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Model(ABC):
    def __init__(self, name, inputs_dict, outputs_dict, sim_params, params):
        self.name = name
        self.inputs = inputs_dict
        self.outputs = outputs_dict
        self.sim_params = sim_params
        self.params = params
        self.initial_state = {}
        self.memory = {}
        self._init_memory = None
        self._save_init_state = None

        #todo execute initialstate_setting
        logger.info(f"\t\tModel {self.name} instantiated!")

    def __setattr__(self, name, value):
        if name == 'init_memory':
            self._mem_callback(value)
        elif name == 'save_init_state':
            self._initial_state_callback(value)
        super().__setattr__(name, value)
    def _mem_callback(self, val):
        if val:
            logger.info(f"\t\tMemory of Model {self.name} initiated: \n{self.memory}")
            #memorize everything
            pass
    def _initial_state_callback(self, val):
        if val:
            self.initial_state ['inputs'] = self.inputs
            self.initial_state['outputs'] = self.outputs
            self.initial_state['sim_params'] = self.sim_params
            self.initial_state['params'] = self.params
        logger.info(f"\t\tInitial state of Model {self.name} initiated and saved:\n{self.initial_state}")

    def _fill_memory(self):
        if not self.memory:
            return
        else:
            for var in self.memory:
                if var in self.inputs.keys():
                    self.memory[var].append(deepcopy(self.inputs[var]))
                elif var in self.outputs.keys():
                    self.memory[var].append(deepcopy(self.outputs[var]))
                elif var in self.sim_params.keys():
                    self.memory[var].append(deepcopy(self.sim_params[var]))
                elif var in self.params.keys():
                    self.memory[var].append((deepcopy(self.params[var])))
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