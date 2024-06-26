import numpy as np
from _baseModels.Model import Model #rember the top level running python script is al;ways main
import logging
import time
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class Hvac(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initialize()
    def initialize(self):
        list_rooms = []
        for inp_key in self.inputs:
            if " " in inp_key:
                number = inp_key.split(" ")[-1]
                if number not in list_rooms:
                    list_rooms.append(number)
        self.rooms = list_rooms
    def step(self, ts, **kwargs):
        if kwargs['iter_n']==0:
            return
        elif kwargs['iter_n']==1:

            for room in self.rooms:
                demand = self.inputs['power_load_s %s' % room] + self.inputs['power_fresh_vent_load_s %s' % room]
                actual = demand
                self.outputs['actual_power %s' % room] = actual
        elif kwargs['iter_n']==2:
            self.outputs['electrical_power'] = self.inputs['power']/3

        self._fill_memory(itr=kwargs['iter_n'])

        return

    def finalize(self):
        return super().finalize()
