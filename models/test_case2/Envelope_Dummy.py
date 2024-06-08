import numpy as np
from Model import Model #rember the top level running python script is al;ways main
import logging
import time
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class Envelope(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.T_set= 20
        self.end_iter = False


    def step(self, ts, **kwargs):
        iter_test_var = range(15)
        iter_num = kwargs['iter_n']
        logger.debug(f"++++++ step {ts}, inputs: {self.inputs}, outputs: {self.outputs} iter{kwargs['iter_n']}")
        self.end_iter = False

        if iter_num == 0:
            # time.sleep(0.02)

            #get text and tset
            self.outputs['p_demand'] = iter_test_var[ts]  # non generalizable with iteration for convergence beacuse no inputs outputs order is present
            self.memory['outputs']['p_demand'].append(self.outputs['p_demand'])

        if iter_num == 1:
            self.memory['inputs']['p_actual'].append(self.inputs['p_actual'])
            self.outputs['t_in'] = iter_test_var[
                ts]  # non generalizable with iteration for convergence beacuse no inputs outputs order is present
            self.memory['outputs']['t_in'].append(self.outputs['t_in'])
            # time.sleep(0.02)
            pass

        if iter_num == 2:
            self.end_iter = True

            # time.sleep(0.02)
            # #recieve p_actual
            # self.memory['inputs']['p_actual'].append(self.inputs['p_actual'])
            # self.outputs['t_in'] = iter_test_var[ts]  # non generalizable with iteration for convergence beacuse no inputs outputs order is present
            # self.memory['outputs']['t_in'].append(self.outputs['t_in'])
        if iter_num ==3:
            # time.sleep(0.02)
            self.end_iter = True


            #return super().step(ts)

    def finalize(self):
        return super().finalize()
        pass