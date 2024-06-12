import numpy as np
import logging
from copy import deepcopy
from abc import ABC,  abstractmethod
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Model(ABC):

    def __init__(self, **kwargs):

        for key, value in kwargs.items():
            setattr(self,key,value)
        #todo perform a chekc on strictly required arguments
        #possible call of initialization() #todo think about it
        self._msg_out = {"var_name":None,
                         "value":None,
                         "destination":None}
        logger.info(f"\t\tModel {self.model_name} instantiated with the following kwargs: {kwargs}!")


    def __setattr__(self, name, value):
        if name == 'mem_attrs' and value :
            self._init_memory(value)
        if name == 'init_state':
            self._init_state(value)
        super().__setattr__(name, value)

    def _init_memory(self, value): # todo does not memorize messages
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
        self.initial_state = {'inputs': {},'outputs': {}, 'messages_in': {},
           'messages_out': {},
           'params': {}}
        for k, val in value.items():
            kind = k.split('.')[0]
            var = k.split('.')[-1]
            self.initial_state[kind][var] = val
        self.initial_state['params'] = deepcopy(self.params)

        logger.info(f"\t\tInitial state for Model {self.model_name} set as follow: {self.initial_state}")  # todo better logging

    def _fill_memory(self):
        if not self.memory:
            return
        else:
            for typ in self.memory:
                for  var in self.memory[typ]:
                    self.memory[typ][var].append(deepcopy(getattr(self, typ)[var]))


    def _reset(self):
        self.inputs = self.initial_state['inputs']
        self.outputs = self.initial_state['outputs']
        self.params = self.initial_state['params']
        for var in self.memory:
            self.memory[var] = []
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