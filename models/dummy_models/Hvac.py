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
        self.tot_actual=0


    def step(self, ts, **kwargs):


        if kwargs['itr'] == 0:
            # in iteration
            for room in self.list_rooms:
                demand = self.inputs['zone.load_s %s' % room] + self.inputs['zone.fresh_vent_load_s %s' % room]
                actual = demand
                self.tot_actual += actual
                self.outputs['zone.vent_q %s' % room] = actual


        elif kwargs['itr'] == 1:

            self.outputs['electrical_power'] = self.tot_actual / 3
            self.tot_actual = 0


    def finalize(self):
        return super().finalize()
