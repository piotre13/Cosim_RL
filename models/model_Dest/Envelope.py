import numpy as np
from model_Dest.Envelope_Dest import Simulator
from _baseModels.Model import Model #rember the top level running python script is al;ways main
import logging
import time
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class Envelope(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = None
        self.initialize()

    def initialize(self):

        # self.casefile = self.casefile.replace('\\', '\\\\')
        self.model = Simulator(self.executable,self.casefile,self.silent)
        out_list = self.prepare_varnames(self.outputs, set=False)
        # logger.debug(f"+++++par ={self.params}, req={self.required}, out={out_list}")
        list_rooms = []

        self.model.initialize(params=self.params, required=self.required, outputs=out_list)


    # def step(self, ts, **kwargs):
    #     logger.debug(f'@@@@###@@@ iter_type at model level {self.iter_type}')
    #     if self.iter_type == 'no_iter':
    #         mod_run = 1
    #         inps = self.prepare_varnames(self.inputs)
    #         out_dict = self.model.step(ts, inps, mode=mod_run)
    #         self.read_outputs(out_dict)
    #     else:
    #         if kwargs['iter_n'] == 0:
    #             mod_run = 0
    #             inps_dict = {key: self.inputs[key] for key in self.inputs_order[kwargs['iter_n']]}
    #             outs_dict = {key: self.outputs[key] for key in self.outputs_order[kwargs['iter_n']]}
    #             inps = self.prepare_varnames(inps_dict)
    #             outs = self.prepare_varnames(outs_dict)
    #             out_dict = self.model.step(ts, inps, outputs=outs, mode=mod_run)
    #             self.read_outputs(out_dict)
    #         elif kwargs['iter_n'] == 1:
    #             mod_run = 0
    #             inps_dict = {key: self.inputs[key] for key in self.inputs_order[kwargs['iter_n']]}
    #             outs_dict = {key: self.outputs[key] for key in self.outputs_order[kwargs['iter_n']]}
    #             inps = self.prepare_varnames(inps_dict)
    #             outs = self.prepare_varnames(outs_dict)
    #             out_dict = self.model.step(ts, inps, outputs=outs, mode=mod_run)
    #             self.read_outputs(out_dict)
    #         elif kwargs['iter_n']==2:
    #             mod_run = 1
    #             inps_dict = {key: self.inputs[key] for key in self.inputs_order[kwargs['iter_n']]}
    #             outs_dict = {key: self.outputs[key] for key in self.outputs_order[kwargs['iter_n']]}
    #             inps = self.prepare_varnames(inps_dict)
    #             outs = self.prepare_varnames(outs_dict)
    #             out_dict = self.model.step(ts, inps, outputs=outs, mode=mod_run)
    #             self.read_outputs(out_dict)
    #
    #         self._fill_memory(itr=kwargs['iter_n'])
    #     return

    def step(self, ts , **kwargs):
        if self.iter_type == 'no_iter':
            mod_run = 1
            inps = self.prepare_varnames(self.inputs)
            out_dict = self.model.step(ts, inps, mode=mod_run)
            self.read_outputs(out_dict)
        else:
            if kwargs['iter_n'] == len(self.inputs_order)-1:
                mod_run = 1
                inps = {k: val for k, val in self.inputs.items() if k in self.inputs_order[kwargs['iter_n']]}
                inps = self.prepare_varnames(inps)
                if any("vent_q" in s for s in inps.keys()):
                    out_dict = self.model.calc_tair(inps, mod_run)
                    self.read_outputs(out_dict)
                elif len(inps)>0:
                    out_dict = self.model.calc_demand(inps, mod_run)
                    self.read_outputs(out_dict)
                else:
                    pass
            else:
                mod_run =0
                inps = {k:val for k,val in self.inputs.items() if k in self.inputs_order[kwargs['iter_n']]}
                inps = self.prepare_varnames(inps)
                if any("vent_q" in s for s in inps.keys()):
                    out_dict = self.model.calc_tair(inps, mod_run)
                    self.read_outputs(out_dict)
                elif len(inps)>0:
                    out_dict = self.model.calc_demand(inps, mod_run)
                    self.read_outputs(out_dict)
                    # logger.debug(f"#### out_dict from calc_Demand {self.outputs}")
                else:
                    pass
    def prepare_varnames(self, base_dict, set=True):
        # todo NB questa funzione e' molto IMPORTANTE il nome degli input se ha uno spazio significa che sono quelli da modificare con la lista degli ids da MODIFICARE leggendo gli ids e usando startswith and endswith per riempire il dizionario
        vars_dict = {}
        names_dict = {}
        vals_dict = {}

        for k, val in base_dict.items():
            if " " in k and k.split(" ")[0] not in names_dict.keys():
                names_dict[k.split(" ")[0]]="[%s]"%k.split(" ")[-1]
                vals_dict[k.split(" ")[0]] = [val]
            elif " " in k and k.split(" ")[0] in names_dict.keys():
                names_dict[k.split(" ")[0]] = names_dict[k.split(" ")[0]][:-1]+ ", %s]"%k.split(" ")[-1]
                vals_dict[k.split(" ")[0]].append(val)
            else:
                # names_dict[k] = k
                # vals_dict[k] = val
                vars_dict[k]=val

        for k,val in zip(names_dict,vals_dict.values()):
            name = k + " %s"%names_dict[k]
            vars_dict[name]=val
        if set:
            # logger.debug(f'##### input_dict to fed to the model {vars_dict}')
            return vars_dict
        else:
            # logger.debug(f'##### outputs names to fed to the model {vars_dict.keys()}')
            return list(vars_dict.keys())




    def read_outputs(self, out_dict):
        for k_variable, val_tuple in out_dict.items():
            for zone_id, val in zip(val_tuple[0], val_tuple[1]):
                name = k_variable + ' ' + zone_id
                if k_variable == 'zone.load_s' or k_variable == 'zone.fresh_vent_load_s':
                    val *= 3600
                self.outputs[name] = val
    def finalize(self):
        return super().finalize()
        pass