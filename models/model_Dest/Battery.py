import numpy as np
from model_Dest.Battery_Dest import BESS
from _baseModels.Model import Model #rember the top level running python script is al;ways main

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

        self.outputs['energy_out'] = self.model.calculatepower(self.inputs['power'], dt=3600)
        self.params['SOC'] = self.model.SOC
        return super().step(ts)

    def finalize(self):
        return super().finalize()
        pass