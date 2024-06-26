import numpy as np
from models._baseModels.Model import Model


''' NB is possible to add logs also here to better debug the model'''

class Battery_dummy (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def step(self, ts):
        self.params['R'] = np.interp(self.params['current_soc'], np.array([0,1]), np.array([8,150]))

        if self.params['current_soc'] >= 1:
            self.outputs['current'] = 0
        else:
            self.outputs['current'] = self.inputs['voltage'] / self.params['R']

        self.params['added_energy'] = (self.outputs['current'] * self.inputs['voltage'] * self.params['update_interval'] / 3600) / 1000
        self.params['current_soc'] = self.params['current_soc'] + self.params['added_energy'] / self.params['size']
        return super().step(ts) #for debugging


    def finalize(self):
        return super().finalize()






if __name__ == '__main__':
    inputs_dict = {'voltage': None}
    outputs_dict = {'current': None,
                    'current_soc':None}
    sim_params = {'update_interval': 60,
                  'time': 0}

    params = {'size': np.random.choice([25, 62, 100], 1, p=[0.2, 0.2, 0.6]).tolist()[0],
              'socs': np.array([0, 1]),
              'effective_R': np.array([8, 150]),
              'current_soc': (np.random.randint(0, 60)) / 100,
              'R': None,
              'added_energy': None
    }

    bat = Battery_dummy('Battery',inputs_dict,outputs_dict,sim_params,params)

    bat.initial_state = {
        'inputs': {'voltage': None},
        'outputs': {'current': None,
                    'current_soc': None},
        'params': {'size': np.random.choice([25, 62, 100], 1, p=[0.2, 0.2, 0.6]).tolist()[0],
                  'socs': np.array([0, 1]),
                  'effective_R': np.array([8, 150]),
                  'current_soc': (np.random.randint(0, 60)) / 100,
                  'R': None,
                  'added_energy': None},
        'sim_params':{'update_interval': 60,
                      'time': 0}
    }
    bat.memory = {'current_soc': []}