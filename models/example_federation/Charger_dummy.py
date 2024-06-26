from models._baseModels.Model import Model
''' NB is possible to add logs also here to better debug the model'''

class Charger_dummy (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def step(self, ts):

        if self.inputs['current'] > 0:  # EV is still charging
            self.params['power'] += (self.outputs['voltage'] * self.inputs['current'])
        self.outputs['voltage'] += 1
        return super().step(ts)


    def finalize(self):
        return super().finalize()





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