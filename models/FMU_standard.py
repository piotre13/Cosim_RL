import logging
from Model import Model
import collections
import os, sys
import random
import json
import numpy as np
from fmpy.util import plot_result
from fmpy import read_model_description, extract, dump
from fmpy.fmi1 import FMU1Slave
from fmpy.fmi2 import FMU2Slave

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class FMU (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fmu_path = os.path.join('models\\fmus', f'{kwargs["fmu"]}.fmu') # todo this is hardcoded not good
        self.fmu = None
        self.in_vars = {}
        self.ou_vars = {}
        self.params_vars = {}
        self.fmu_unpacking()
        self.initialization()


    def fmu_unpacking(self):
        # initialize the fMU and set the parameters
        # should add the checker as in coesi todo
        logger.debug(f'FMU info: {dump(self.fmu_path)}')

        # Extract model description from xml
        self.model_description = read_model_description(self.fmu_path,
                                                        validate=True)  # todo the validate flag was set to False maybe return to it

        # Collect in a dictionaries all the model variables taken from the values reference vrs = {
        # 'variable_name' : value_ref}
        self.vars = {v.name: (v.valueReference, v.type, v.causality, v.variability) for v in self.model_description.modelVariables}
        self.params_vars = {v.name: (v.valueReference, v.type) for v in self.model_description.modelVariables if
                            v.causality == 'parameter'}  # extend to different causality
        self.in_vars = {v.name: (v.valueReference, v.type) for v in self.model_description.modelVariables if
                        v.causality == 'input'}
        self.ou_vars = {v.name: (v.valueReference, v.type) for v in self.model_description.modelVariables if
                        v.causality == 'output'}
        logger.debug(f"\t\t * the FMU {self.fmu_path} has been unpacked and the following vars has been found:\n paramters: {self.params_vars} ****")
        self.unzipdir = extract(self.fmu_path)

        self.fmiVersion = self.model_description.fmiVersion
    def initialization(self):

        # Instantiation of the FMU
        if self.fmiVersion == '1.0':
            self.fmu = FMU1Slave(guid=self.model_description.guid, unzipDirectory=self.unzipdir,
                                           modelIdentifier=self.model_description.coSimulation.modelIdentifier,
                                           instanceName=self.model_name)
            self.fmu.instantiate()
        elif self.fmiVersion == '2.0':
            self.fmu = FMU2Slave(guid=self.model_description.guid, unzipDirectory=self.unzipdir,
                                           modelIdentifier=self.model_description.coSimulation.modelIdentifier,
                                           instanceName=self.model_name)

            self.fmu.instantiate(loggingOn=7) # todo for now logging level is fixed must be passed from outside
        else:
            raise Exception('The FMU-CS version is not supported. Check the FMU version.')

        #*********** Setting vars in Instantiated 
        self.set_inital_state()
        #************************************************************************************************************
        
        if self.fmiVersion == '2.0':
            # Setup experiment: set the independent variable time
            self.fmu.setupExperiment(startTime=0, stopTime=self.end_time)

            # Initialization. Set the INPUT values at time = startTime and also variables with initial = exact
            self.fmu.enterInitializationMode()
            #todo maybe some setting should be done here even if it has restrictions to  for a variable with variability≠"constant" that has initial="exact", or causality="input"
            status = self.fmu.exitInitializationMode()
            assert status == 0
        else:
            logger.debug(f'Initialization for FMI 1.0 version not Coded!')
            # if start_in_vrs:
            #     self.entities[eid].setReal([self.entity_vrs[eid][x] for x in start_in_vrs.keys()],
            #                                list(start_in_vrs.values()))
            status = self.fmu.initialize(tStart=0, stopTime=self.end_time)
            assert status == 0
            #raise Exception('fmi 1.0 NOT SUPPORTED')

        print('yo')
    def step(self, ts, **kwargs):
        self.rows = []
        fmu_time = ts * self.real_period
        # Set inputs
        self.set_inputs()
        logger.debug(f"###fmu_time = {fmu_time}, self.real period+ {self.real_period}")
        self.fmu.doStep(currentCommunicationPoint=fmu_time, communicationStepSize=self.real_period)
        self.get_outputs()
        #self.rows.append((ts, self.outputs['SOC']))
        return super().step(ts)

    def set_inital_state(self):
        if self.initial_state:
            for kind in self.initial_state:
                if kind not in ['messages_in', 'messages_out']: # todo for now like this because the messages_in and out are lists...
                    for var, value in self.initial_state[kind].items():
                        if kind == 'params':
                            self.set_var(self.params_vars[var][0],value)
                        elif kind == 'inputs':
                            self.set_var(self.in_vars[var][0],value)
                        elif kind == 'outputs':
                            self.set_var(self.ou_vars[var][0], value)
    def set_params(self):
        if self.params:
            for var, value in self.params.items():
                self.set_var(self.params_vars[var][0], value)
    def set_inputs(self):
        if self.inputs:
            logger.debug(f"$$$$$setting the following inputs{self.inputs}!!!")
            for var, value in self.inputs.items():
                self.set_var(self.in_vars[var][0], value)
    def get_outputs(self):
        ''' this function get outputs and save them inside the self.outputs class variable'''
        if self.outputs:
            for var in self.outputs:
                self.outputs[var] = self.get_vars(self.ou_vars[var][0],self.ou_vars[var][1])
    def get_vars(self, value_ref, tp):
        if tp == 'Real':
            var = self.fmu.getReal([value_ref])[0]
        elif tp == 'Integer':
            var = self.fmu.getInteger([value_ref])[0]
        elif tp == 'String':
            var = self.fmu.getString([value_ref])[0]
        elif tp == 'Boolean':
            var = self.fmu.getBoolean([value_ref])[0]
        else:
            logger.error(f"type of variable {tp} not recognized! - GET VAR -")
            var = None
        return var
    def set_var(self, value_ref,value):
        if isinstance(value, float):
            self.fmu.setReal([value_ref], [value])
        elif isinstance(value, int):
            self.fmu.setInteger([value_ref], [value])
        elif isinstance(value, str):
            self.fmu.setString([value_ref], [value])
        elif isinstance(value, bool):
            self.fmu.setBoolean([value_ref], [value])
        else:
            logger.error(f"{type(value)} variable type not supported - SET VAR -")
    
    def reset_fmu(self):
        self.fmu.reset()
        # perform a faster initialization
    
    def finalize(self):
        # result = np.array(self.rows, dtype=np.dtype([('time', np.float64), ('SOC', np.float64)]))
        # plot_result(result)
        self.fmu.terminate()
        return super().finalize()




if __name__ == '__main__':
    kwargs={}
#    kwargs['model_name'] = 'FMU' + '.' + str(0)
    kwargs['model_name'] = 'FMU' + '.' + str(0)
    kwargs['inputs'] = {'P':0.0}
    # kwargs['outputs'] = {'P':0.0,
    #                      'Pcmax':0.0,
    #                      'Pdmax':0.0,
    #                      'SOC':0.0}
    kwargs['outputs'] = {'E_out': 0.0,
                         'SOC': 0.0}
    kwargs['messages_in'] = []
    kwargs['messages_out'] = []
    kwargs['params'] = {
        'CH_eff': 0.97,
        'CH_max_P': 8000.0,
        'DI_eff': 0.97,
        'DI_max_P': 8000.0,
        'Discharge_rate': 0.0,
        'Rated_capacity': 40000.0,
        'SOC_lower': 0.25,
        'SOC_upper': 0.95,
        'dt': 3600.0,
    }
    # kwargs['params'] = {
    #     'C0': 30.0,
    #     'R_c':0.97,
    #     'Pdecharge':0.9,
    #     'R_charge':0.9,
    #     'R_decharge':0.9,
    #     'technoBattOnd.Cmax': 2.0,
    #     'technoBattOnd.P_onduleur':10000.0,
    #     'technoBattOnd.Pmaxc': 8000.0,
    #     'technoBattOnd.Pmaxd':5000.0,
    # }

    kwargs['msg_var_dest'] = {}

    # kwargs['msg_in'] =
    kwargs['RL_training'] = True
    # kwargs['stateful'] = self.init_config['fed_conf']['stateful']
    #kwargs['mem_attrs'] = ['inputs.P_consigne','outputs.SOC']
    kwargs['mem_attrs'] = ['inputs.P','outputs.SOC','outputs.E_out']

    kwargs['fmu'] = 'Battery_test'

    kwargs['initial_state']={'inputs':{'P':0.0},'outputs':{'SOC':0.25},'params': kwargs['params']}


    fmu = FMU(**kwargs)
    i=0
    while i<24:
        getattr(fmu,'inputs')['P'] = random.uniform(-3000.9, 3000.9)
        fmu.step(i, **{'real_period':3600})
        i+=1

    fmu.finalize()