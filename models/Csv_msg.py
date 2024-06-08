import sys
import numpy as np
import logging
from Model import Model
import pandas as pd

#TODO add conversions and possibility to change names from what is written in the CSV


class CSV (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = pd.read_csv(self.params['csv_file']) #now we index at 0 becuase we still using possibility of m,ultiple instances TODO this does not make sense with csv readers
        self.initialization()
    def initialization(self):
        #convert to lower case all column names
        self.data.columns = map(str.lower, self.data.columns)
    def step(self, ts, **kwargs):
        for var in self.messages_out:
            if self.params['multiplier'] and var in self.params['multiplier'].keys():
                self.messages_out[var] = self.data.loc[ts,var] * self.params['multiplier'][var]
            else:
                self.messages_out[var]= self.data.loc[ts,var]
        return super().step(ts)

    def finalize(self):
        return super().finalize()
