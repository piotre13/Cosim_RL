import logging
from models._baseModels.Model import Model
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype as is_datetime
from datetime import datetime

#TODO add conversions and possibility to change names from what is written in the CSV
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

class CSV (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = pd.read_csv(self.params['csv_file']) #now we index at 0 becuase we still using possibility of m,ultiple instances TODO this does not make sense with csv readers

        if 'DateTime' in self.data.columns:
            self.data.index = pd.to_datetime(self.data['DateTime'], format ='%Y-%m-%d %H:%M:%S')
        else:
            freq = self.time_frequency()
            end_time = self.start_time + pd.to_timedelta((len(self.data.index)*freq)-freq, unit='s')
            self.data.index = pd.date_range(self.start_time, end=end_time, freq="%s s" % freq)

        self.original_freq = self.time_frequency()

        if self.original_freq != self.real_period:
            self.data = self.data.resample(pd.Timedelta(seconds=self.real_period)).interpolate()





        #
        #
        # if 'DateTime' not in list(self.data.columns):
        #     if self.reset_period < self.end_period:
        #         end_time = self.start_time + pd.to_timedelta(self.reset_period-self.real_period, unit='s')
        #         self.data['DateTime'] = pd.date_range(self.start_time, end=end_time, freq="%s s"%self.real_period)
        #
        #     else:
        #         self.data['DateTime'] = pd.date_range(self.start_time, end=self.end_time, freq="%s s"%self.real_period)
        #
        #
        #
        # self.data.index = pd.to_datetime(self.data['DateTime'], format ='%Y-%m-%d %H:%M:%S')

        # self.datetime_index = pd.date_range(self.start_time, end=self.end_time, freq="%s s"%self.real_period) # for now not used we suppose data are given with correct lenght an
        # self.sim_start_date = self.start_time
        # self.sim_end_date = self.sim_start_date + pd.to_timedelta("%s s"%self.end_period)
        # self.initialization()
        self.replay = 1
        self.index = 0
        # if self.real_period != 3600:
        #     self.data = self.data.resample(pd.Timedelta(seconds=self.real_period)).interpolate()

        self.data.columns = map(str.lower, self.data.columns)
        self.data.reset_index(inplace=True)

        logger.debug(f"data ready: {self.data},\n data lenght: {self.data.shape}")


        # self.data = self.data.reset_index()

    # def initialization(self):
    #     #convert to lower case all column names
    #     self.data.columns = map(str.lower, self.data.columns)
    #     if 'date' in self.data.columns:
    #         self.data = self.data.set_index(self.data['date'])
    #         self.data = self.data.drop(['date'])
    #     else: # todo this assign index that might be longer/shorter than the simulation time
    #         self.data = self.data.set_index(pd.date_range(self.start_time, periods=self.data.shape[0], freq="%s s"%self.real_period))
    #
    #     self.resampling()
    #
    # def resampling (self):
    #     #todo perform checks on start end, frequency and allows for different resamplings
    #     if pd.to_timedelta(self.data.index.freq) != pd.to_timedelta(self.datetime_index.freq):
    #         self.data = self.data.resample(pd.to_timedelta("%s s"%self.real_period)).ffil()
    #         logger.debug(f"timeseries_data resampled")
    #     logger.debug(f"timeseries_data start = {self.data.index[0]}, end = {self.data.index[-1]}, freq = {self.data.index.freq}")

    def time_frequency(self):
        if isinstance(self.data.index, pd.DatetimeIndex):
            return self.data.index.freq.nanos / 1e9  # convert frequency to seconds
        else:
            # Assuming the whole extension of the data is one year
            total_seconds_in_a_year = 365 * 24 * 60 * 60

            # Estimate frequency based on the number of entries
            total_entries = len(self.data)
            estimated_freq = total_seconds_in_a_year / total_entries

            estimated_freq = 3600        #todo hardcoded for testing

            return estimated_freq
    def step(self, ts, **kwargs):

        # index = self.sim_start_date + pd.to_timedelta("%s s"%int(ts)*self.real_period)
        #do not stop if index is larger than data but start again
        if self.index not in self.data.index:
            self.index = 0
            # index = index - self.replay
        logger.debug(f"data index: {self.index}")
        for var in self.outputs:
            tmp = self.data.loc[self.index,var]


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

        self.index+=1

        # self._fill_memory()

    def finalize(self):
        return super().finalize()


