import numpy as np
from _baseModels.Model import Model  # rember the top level running python script is al;ways main
import logging
import time
import json
import yaml
import pprint
import ast
pp = pprint.PrettyPrinter(indent=4)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.CRITICAL)


class Controller(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        logger.debug(f"model_kwargs: {pp.pformat(self.__dict__)}")
        self.heating_schedule = ast.literal_eval(self.heating_schedule)
        self.cooling_schedule = ast.literal_eval(self.cooling_schedule)
        self.heating_season = ast.literal_eval(self.heating_season)
        self.cooling_season = ast.literal_eval(self.cooling_season)
        self.on_off_season = ast.literal_eval(self.on_off_season)

        #initial condition for now always from 0
        self.day_of_year = 0
        self.hour_of_day = 0
        self.rep_counter = 0
        self.n_steps = int(self.reset_period/self.real_period)




    def step(self, ts, **kwargs):

        if ts%self.n_steps == 0 and ts!=0:
            self.rep_counter+=1
            self.day_of_year = 0
            self.hour_of_day = 0
        else:
            # hourly_ts = (ts-self.step_in_year*self.year) if self.real_period == 3600 else int((ts-self.step_in_year*self.year)/6)
            hourly_ts = int(((ts-(self.n_steps*self.rep_counter))*self.real_period)/3600)
            logger.debug(f"hourly TS: {hourly_ts}")
            self.day_of_year = int(hourly_ts / 24)
            self.hour_of_day = hourly_ts % 24

        season = None
        on_off = None
        if any(self.day_of_year in range(per[0], per[1]) for per in self.heating_season):
            season = 'heating'
        elif any(self.day_of_year in range(per[0], per[1]) for per in self.cooling_season):
            season = 'cooling'
        else:
            raise ValueError(f'ts not in any season nor heating nor cooling ts value = {ts}')

        for slot in self.on_off_season:
            if self.day_of_year in range(slot[0][0], slot[0][1]):
                on_off = slot[1]

        if season == 'heating':
            logger.info(f"ts:{ts}")
            # ts= ts-23*self.day
            # logger.info(f"day = {self.day}, ts: {ts}")
            out = self.heating_schedule[self.hour_of_day]
            #
            # if ts%23 == 0:
            #     self.day+=1
            #
            # for output in self.outputs:
            #     self.outputs[output] = out
            # return super().step(ts)
        else:
            # ts = ts - 23 * self.day
            self.outputs['day_of_year'] =-1
            out = self.cooling_schedule[self.hour_of_day]
            # if ts % 23 == 0:
            #     self.day += 1
            #
            # for output in self.outputs:
            #     self.outputs[output] = out
            #
            # return super().step(ts)

        for output in self.outputs:
            self.outputs[output] = out
        if on_off == 1 and season=='cooling':
            self.outputs['ac_on_off'] = -1
        else:
            self.outputs['ac_on_off'] = on_off
        self.outputs['day_of_year'] = self.day_of_year

        if self.outputs['tSetMax'] == 16:
            self.outputs['hour_of_day'] = 0
        else:
            self.outputs['hour_of_day'] = 1

    def finalize(self):
        return super().finalize()
