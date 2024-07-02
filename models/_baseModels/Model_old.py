import numpy as np
import logging
from copy import deepcopy
from abc import ABC,  abstractmethod
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


''' This class must be inherited from every model and is used to ensure that the needed methods are implemented as well as 
embedding some useful functionalities ( starting init, reset method, ... todo
'''





class Model(ABC):

    def __init__(self, **kwargs):

        for key, value in kwargs.items():
            setattr(self,key,value)

        logger.info(f"\t\tModel {self.model_name} instantiated with the following kwargs: {kwargs}!")


    # def __setattr__(self, name, value):
    #     if name == 'mem_attrs':
    #         self._init_memory(value)
    #     if name == 'init_state':
    #         self._init_state(value)
    #     super().__setattr__(name, value)

    def _init_memory(self, value):
        self.memory = {'inputs': {},
                       'outputs': {},
                       'params': {}}
        if isinstance(value, list):
            if len(value)>0:
                for attr in value:
                    self.memory[attr.split('.')[0]][attr.split('.')[1]] = []
            elif len(value)==0:
                self.memory['inputs'] = {k: [] for k in self.inputs.keys()}
                self.memory['outputs'] = {k: [] for k in self.outputs.keys()}
                self.memory['params'] = {k: [] for k in self.params.keys()}
                logger.warning('\t\tMemory attrs are not specified in the init_config. everything will be memorized.')
            logger.info(f"\t\tMemory instantiated for Model {self.model_name}!")
        else:

            logger.info(f"\t\tNO Memory instantiated for Model {self.model_name}!") #todo better logging


    def _init_state(self, value):
        self.initial_state = {'inputs': {},'outputs': {},'params': {}}
        for k, val in value.items():
            kind = k.split('.')[0]
            var = k[len(kind)+1:] #taking the rest after typology. (e.g. inpus.T_set, takes everything that after inputs.)
            self.initial_state[kind][var] = val
        self.initial_state['params'] = deepcopy(self.params)

        #creata l'init state per inputs, params and outputs folr thos value that has an initial value set it
        for out_k, val in self.initial_state['outputs'].items():
            self.outputs[out_k] = val
        for inp_k, val in self.initial_state['inputs'].items():
            self.inputs[inp_k] = val


        logger.info(f"\t\tInitial state for Model {self.model_name} set as follow: {self.initial_state}")  # todo better logging

    def _fill_memory(self, var_list = None):
        '''this method when called store in memory either all the memory values or only the specified var_name in the var_list attr'''
        if not self._memory:
            return

        elif self._memory and not var_list:
            # memorize all inside memory keys
            for k, var_dict in self._memory.items():
                for var_name in var_dict:
                    var_dict.append(deepcopy(getattr(self,k)[var_name]))

            return

        else:
            # memorize only the one asked by simulator model (maybe) iteration
            for var_name in var_list:
                if var_name in self.inputs.keys():
                    self._memory['inputs'][var_name].append(deepcopy(getattr(self,'inputs')[var_name]))
                elif var_name in self.outputs.keys():
                    self._memory['outputs'][var_name].append(deepcopy(getattr(self, 'outputs')[var_name]))
                elif var_name in self.params.keys():
                    self._memory['params'][var_name].append(deepcopy(getattr(self, 'params')[var_name]))


    def _reset(self):
        self.inputs = self.initial_state['inputs']
        self.outputs = self.initial_state['outputs']
        self.params = self.initial_state['params']
        for var in self.memory:
            self.memory[var] = []

    @property
    def memory(self):
        return self._memory
    @memory.setter
    def memory(self, name_list):
        mem_dict = {'inputs':{},'outputs':{}, 'params':{}}
        if len(name_list) == 0:
            mem_dict['inputs'] = {k:[] for k in self.inputs}
            mem_dict['outputs'] = {k: [] for k in self.outputs}
            mem_dict['params'] = {k: [] for k in self.params}
        else:
            for name in name_list:
                if name in self.inputs.keys():
                    mem_dict['inputs'][name] = []
                elif name in self.outputs.keys():
                    mem_dict['outputs'][name] = []
                elif name in self.params.keys():
                    mem_dict['params'][name] = []

    @abstractmethod
    def step(self, ts, *args, **kwargs):
        '''overwrite this method with the actual model calculations:
        rememeber the needed inputs and outputs are in self.inputs[chosen_name] and self.outputs[chosen_name], these are variables that comes from outside the model and need tpo leave the model
        any paarameter for the physical model can be found in self.params[chosen_name],
        any parameter relative to the simulation can be found in self.sim_params[standard_name]'''

        self._fill_memory()
        logger.debug(
            "\t\t Model {self.model_name} step completed.")
        return
    @abstractmethod
    def finalize(self):
        logger.debug(f"\t\t Model {self.model_name} finalized with Memory : {self.memory}")
        pass


if __name__ == '__main__':

    #todo probably no need of sim params they can be retrieved from federate

    inputs_dict = {'voltage': None}
    outputs_dict = {'current': None}
    messages_dict ={}
    params = {}