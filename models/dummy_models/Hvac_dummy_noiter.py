import numpy as np
from _baseModels.Model import Model #rember the top level running python script is al;ways main
import logging
from copy import deepcopy

import time
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class Hvac(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start=True
        self.initialize()
    def initialize(self):
        list_rooms = []
        for inp_key in self.inputs:
            if " " in inp_key:
                number = inp_key.split(" ")[-1]
                if number not in list_rooms:
                    list_rooms.append(number)
        self.rooms = list_rooms
    def step(self, ts):
        actual_power = 0
        for room in self.rooms:
            demand = self.inputs['power_load_s %s' % room] + self.inputs['power_fresh_vent_load_s %s' % room]
            self.memory['inputs']['power_load_s %s' % room].append(deepcopy(self.inputs['power_load_s %s' % room]))
            self.memory['inputs']['power_fresh_vent_load_s %s' % room].append(deepcopy(self.inputs['power_fresh_vent_load_s %s' % room]))
            actual = demand # this is where we introduce HVAC logic

            #todo for now in case demand is negative (coling) we force return 0
            if demand <= 0:
                actual = 0.0
            self.outputs['actual_power %s' % room] = actual
            actual_power += actual
            self.memory['outputs']['actual_power %s' % room].append(deepcopy(self.outputs['actual_power %s' % room]))

        self.outputs['electrical_power'] = (actual_power / 3) * -1 # this should be the sum of actual now that we return all the demand is ok
        self.memory['outputs']['electrical_power'].append(deepcopy(self.outputs['electrical_power']))


    def finalize(self):
            return super().finalize()
