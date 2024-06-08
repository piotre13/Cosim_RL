import sys
import numpy as np
import logging
from Model import Model
import pandas as pd

#TODO add conversions and possibility to change names from what is written in the CSV
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class CSV (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = pd.read_csv(self.params['csv_file']) #now we index at 0 becuase we still using possibility of m,ultiple instances TODO this does not make sense with csv readers
        self.initialization()
    def initialization(self):
        #convert to lower case all column names
        self.data.columns = map(str.lower, self.data.columns)
    def step(self, ts, **kwargs):

        for var in self.outputs:
            tmp = self.data.loc[ts,var]
            if 'additioner' in self.params.keys():
                if self.params['additioner'] and var in self.params['additioner'].keys():
                    #self.outputs[var] = self.data.loc[ts - 1, var] + self.params['additioner'][var]
                    tmp+=self.params['additioner'][var]
            if 'multiplier' in self.params.keys():
                if self.params['multiplier'] and var in self.params['multiplier'].keys():
                    #self.outputs[var] = self.data.loc[ts-1,var] * self.params['multiplier'][var]
                    tmp*=self.params['multiplier'][var]

            # else:
            #     self.outputs[var]= self.data.loc[ts-1,var]
            self.outputs[var] = tmp

        return super().step(ts)

    def finalize(self):
        return super().finalize()
