import sys
import numpy as np
import logging
from Model import Model
''' NB is possible to add logs also here to better debug the model'''

class Charger_dummy (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def step(self):

        self.outputs['voltage'] = self.params['charging_voltage']
        total_power = 0

        if self.inputs['current'] > 0:  # EV is still charging
                self.outputs['tot_power'] += (self.outputs['voltage'] * self.inputs['current'])


    def finalize(self):
        pass





if __name__ == '__main__':
    inputs_dict = {'current': None}
    outputs_dict = {'voltage': None,
                    'tot_power': None}
    sim_params = {'update_interval': 60,
                  'time': 0}

    params = { 'charge_rate': 1.8,
               'EV_lev':  1,
                }

    bat = Charger_dummy('Charger',inputs_dict,outputs_dict,sim_params,params)

    bat.initial_state = {
        'inputs': {'current': None},
        'outputs': {'voltage': None,
                    'tot_power': None},
        'params': {'charge_rate': 1.8,
                  'EV_lev':  1,
                },
        'sim_params':{'update_interval': 60,
                      'time': 0}
    }
    bat.memory = {'current_soc': []}