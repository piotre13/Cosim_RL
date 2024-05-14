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
        self.ts = 0
        #todo perform a chekc on strictly required arguments
        #possible call of initialization() #todo think about it
        logger.info(f"\t\tModel {self.model_name} instantiated with the following kwargs: {kwargs}!")

        self._set_additionals()


    def _set_additionals(self):
        if getattr(self, 'stateful', None):
            self._init_memory()
            logger.info(f"\t\tMemory instantiated for Model {self.model_name}!") #todo better logging
        if getattr(self, 'RL_training', None):
            self._init_state()
            logger.info(f"\t\tInitial state for Model {self.model_name} set as follow: {self.initial_state}")  # todo better logging

    def _init_memory(self):
        self.memory = {'inputs': {},
                       'outputs': {},
                       'messages_in': {},
                       'messages_out':{},
                       'params': {}}
        if getattr(self, 'mem_attrs', None):
            for attr in getattr(self, 'mem_attrs'):
                self.memory[attr.split('.')[0]][attr.split('.')[1]] = []
        else:
            self.memory['inputs'] = {k:[] for k in self.inputs.keys()}
            self.memory['outputs'] = {k:[] for k in self.outputs.keys()}
            self.memory['messages_in'] = {k:[] for k in self.messages_in.keys()}
            self.memory['messages_out'] = {k:[] for k in self.messages_out.keys()}
            self.memory['params'] = {k:[] for k in self.params.keys()}
            logger.warning('\t\tMemory attrs are not specified in the init_config. everything will be memorized.')

    def _init_state(self):
        self.initial_state = {'inputs': deepcopy(self.inputs),
           'outputs': deepcopy(self.outputs),
           'messages_in': deepcopy(self.messages_in),
           'messages_out': deepcopy(self.messages_out),
           'params': deepcopy(self.params)}

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
    def step(self, ts):
        '''overwrite this method with the actual model calculations:
        rememeber the needed inputs and outputs are in self.inputs[chosen_name] and self.outputs[chosen_name], these are variables that comes from outside the model and need tpo leave the model
        any paarameter for the physical model can be found in self.params[chosen_name],
        any parameter relative to the simulation can be found in self.sim_params[standard_name]'''

        self._fill_memory()
        logger.debug(f"\t\t Model {self.model_name} step completed.")
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