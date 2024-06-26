import numpy as np
from _baseModels.Model import Model  # rember the top level running python script is al;ways main
import logging
import time

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Controller(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.schedule= {0:16,1:16,2:16,3:16,4:16,5:16,6:20,7:20,8:20,9:20,10:20,11:16,12:16,13:16,14:16,15:20,16:20,17:20,18:20,19:20,20:20,21:20,22:20,23:16}
        self.day = 0
    def step(self, ts, **kwargs):


        ts= ts-23*self.day
        out = self.schedule[int(ts)]

        if ts%23 == 0:
            self.day+=1

        for output in self.outputs:
            self.outputs[output] = out
        return super().step(ts)

    def finalize(self):
        return super().finalize()
