import numpy as np
from _baseModels.Model import Model #rember the top level running python script is al;ways main
import logging
import time
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

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
        self.tot_actual =0
        if "HeatingLoadTarget" in self.inputs.keys():
            self.outputs['electrical_power'] = (abs(self.inputs['heating_target']) / 3) * -1
            return

        for room in self.rooms:
            # demand = self.inputs['zone.load_s %s' % room] + self.inputs['zone.fresh_vent_load_s %s' % room] #old one
            demand = self.inputs["zone.vent_q %s" %room]
            actual = demand
            self.tot_actual += actual

        self.outputs['electrical_power'] = (abs(self.tot_actual)/3)*-1

        # self._fill_memory()

    def finalize(self):
        return super().finalize()
