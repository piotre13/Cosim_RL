import numpy as np
from model_Dest.Battery_Dest import BESS
from _baseModels.Model import Model #rember the top level running python script is al;ways main
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
class Battery(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = None
        self.initialization()
    def initialization(self):
        self.model = BESS()
        for par in self.params:
            setattr(self.model, par, self.params[par])
        self.model.setSOC(self.model.SOC)

    def step(self, ts):

        self.outputs['energy_out'] = self.model.calculatepower(self.inputs['power'], dt=self.real_period)
        logger.debug(f"##### ENERGY { self.outputs['energy_out']}")
        self.params['SOC'] = self.model.SOC
        # self._fill_memory()

    def finalize(self):
        return super().finalize()
        pass