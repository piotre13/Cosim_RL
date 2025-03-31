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

    def step(self, ts, **kwargs):


        if self.inputs['heating_target']>15000:
            self.inputs['heating_target']=15000
        elif self.inputs['heating_target']<0:
            self.inputs['heating_target']=0

        self.outputs['electrical_power'] = (self.inputs['heating_target'] / 3) * -1


        # self._fill_memory()

    def finalize(self):
        return super().finalize()
