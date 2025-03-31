import numpy as np
from Model import Model #rember the top level running python script is al;ways main
import logging
import time
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class Hvac(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.P_actual = [1,2,3,4,5,6,7,8,9,10, 11]
        #self.P_demand = [1,2,3,4,5,6,7,8,9,10]
        self.pub_vars = []
        self.end_iter = False



    def step(self, ts, **kwargs):
        iter_test_var = range(15)
        logger.debug(f"++++++ step {ts}, inputs: {self.inputs}, outputs: {self.outputs} iter{kwargs['iter_n']}")
        iter_num = kwargs['iter_n']
        self.end_iter = False
        if iter_num == 0:
            # time.sleep(0.02)
            # #self.outputs['p_actual'] = iter_test_var[ts]  # non generalizable with iteration for convergence beacuse no inputs outputs order is present
            # self.outputs['p_actual'] = iter_test_var[ts]  # non generalizable with iteration for convergence beacuse no inputs outputs order is present
            # self.memory['inputs']['p_demand'].append(self.inputs['p_demand'])
            # self.memory['outputs']['p_actual'].append(self.outputs['p_actual'])
            pass
        if iter_num==1:
            # time.sleep(0.02)
            self.outputs['p_actual'] = iter_test_var[ts]  # non generalizable with iteration for convergence beacuse no inputs outputs order is present
            self.memory['inputs']['p_demand'].append(self.inputs['p_demand'])
            self.memory['outputs']['p_actual'].append(self.outputs['p_actual'])
            pass
        if iter_num ==2:
            # time.sleep(0.02)
            self.end_iter=True
        #return super().step(ts)


    def finalize(self):
        return super().finalize()
