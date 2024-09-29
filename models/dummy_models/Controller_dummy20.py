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
        self.schedule= {0:20,1:20,2:20,3:20,4:20,5:20,6:20,7:20,8:20,9:20,10:20,11:20,12:20,13:20,14:20,15:20,16:20,17:20,18:20,19:20,20:20,21:20,22:20,23:20}
        self.schedule_cool= {0:25,1:25,2:25,3:25,4:25,5:25,6:25,7:25,8:25,9:25,10:25,11:25,12:25,13:25,14:25,15:25,16:25,17:25,18:25,19:25,20:25,21:25,22:25,23:25}
        self.day_of_year = 0
        self.hour_of_day = 0
        self.year = 0
        self.heating_season = [[0, 91], [274, 365]]  # todo this is hardcoded should be passed as a config parmas
        self.cooling_season = [[91, 274]]  # todo this is hardcoded should be passed as a config parmas
        # self.heating_season = [[0,8761]]
    def step(self, ts, **kwargs):



            for output in self.outputs:
                self.outputs[output] = 20

            # return super().step(ts)
    def finalize(self):
        return super().finalize()
