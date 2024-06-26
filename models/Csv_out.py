import logging
from models._baseModels.Model import Model
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from datetime import datetime

#TODO add conversions and possibility to change names from what is written in the CSV
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class CSV (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = pd.read_csv(self.params['csv_file']) #now we index at 0 becuase we still using possibility of m,ultiple instances TODO this does not make sense with csv readers
        self.datetime_index = pd.date_range(self.sim_start, periods=self.end_time, freq="%s s"%self.real_period) # for now not used we suppose data are given with correct lenght an
        self.sim_start_date = pd.to_datetime(self.sim_start, format='%Y-%m-%d %H:%M:%S')
        self.sim_end_date = self.sim_start_date + pd.to_timedelta("%s s"%self.end_time)
        self.initialization()
    def initialization(self):
        #convert to lower case all column names
        self.data.columns = map(str.lower, self.data.columns)
        if 'date' in self.data.columns:
            self.data = self.data.set_index(self.data['date'])
            self.data = self.data.drop(['date'])
        else: # todo this assign index that might be longer/shorter than the simulation time
            self.data = self.data.set_index(pd.date_range(self.sim_start, periods=self.data.shape[0], freq="%s s"%self.real_period))

        self.resampling()

    def resampling (self):
        #todo perform checks on start end, frequency and allows for different resamplings
        if pd.to_timedelta(self.data.index.freq) != pd.to_timedelta(self.datetime_index.freq):
            self.data = self.data.resample(pd.to_timedelta("%s s"%self.real_period)).ffil()
            logger.debug(f"timeseries_data resampled")
        logger.debug(f"timesereis_data start = {self.data.index[0]}, end = {self.data.index[-1]}, freq = {self.data.index.freq}")

    def step(self, ts, **kwargs):

        index = self.sim_start_date + pd.to_timedelta("%s s"%int(ts)*self.real_period)
        for var in self.outputs:
            tmp = self.data.loc[index,var]


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
