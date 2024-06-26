import numpy as np
from _baseModels.Model import Model #rember the top level running python script is al;ways main
import logging
import subprocess
from copy import deepcopy
import time
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class Envelope (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.silent:
            args = ["%s" % self.executable, "-q"]
        else:
            args = ["%s" % self.executable]
        args.append(self.casefile)

        logger.debug(f"## args for run {args} ##")

        self.proc = subprocess.Popen(args=args, stdout=subprocess.PIPE, stdin=subprocess.PIPE)


        #send command for require and outputs TOdo hardcoded generalize
        cmd_list = ["require zone.ac_t zone.load_s zone.fresh_vent_load_s","prepare"]
        self.cmd_send(cmd_list)
        cmd_list = ["out zone.ac_t [8674, 8677, 8680, 8692, 73086]", "out zone.load_s [8674, 8677, 8680, 8692, 73086]", "out zone.fresh_vent_load_s [8674, 8677, 8680, 8692, 73086]"]
        self.cmd_send(cmd_list)
        self.fixed_outputs = len(cmd_list)
        self.in_vars_p_demand = ['schedule.ac_t_max', 'schedule.ac_t_min']
        self.in_vars_t_air = ['zone.vent_q','zone.ac_on_off']

    def __del__(self):
        self.proc.terminate()
        logger.debug("process terminated")
        self.proc.wait()

    def step(self, ts, **kwargs):
        ts = int(ts * self.real_period)
        logger.debug(f"ts: {ts} outputs of module {ts%self.real_period}, real_period = {self.real_period}")
        if (ts % self.real_period) != 0 : # or ts < self.real_period:
            mod_run = 0
            inps = self.prepare_varnames({k:val for k, val in self.inputs.items() if any(i in k for i in self.in_vars_p_demand)})
            cmd_list = []
            for name in inps:
                cmd = f"in {name} = {inps[name]}"
                cmd_list.append(cmd)
            cmd_list.append(f"run {mod_run}")
            self.cmd_send(cmd_list)
            out_dict = self.read_stdout(self.fixed_outputs)
            self.read_outputs(out_dict)
            for out in self.outputs:
                if 'load_s' in out :
                    self.memory['outputs'][out].append(deepcopy(self.outputs[out]))
            return
        else:
            mod_run = 1
            inps = self.prepare_varnames(
                {k: val for k, val in self.inputs.items() if any(i in k for i in self.in_vars_t_air)})
            cmd_list = []
            for name in inps:
                cmd = f"in {name} = {inps[name]}"
                cmd_list.append(cmd)
            cmd_list.append(f"in zone.ac_on_off [8674, 8677, 8680, 8692, 73086] = {[0] * 5}")
            cmd_list.append(f"run {mod_run}")
            self.cmd_send(cmd_list)
            out_dict = self.read_stdout(self.fixed_outputs)
            self.read_outputs(out_dict)
            for out in self.outputs:
                if 'ac_t' in out:
                    self.memory['outputs'][out].append(deepcopy(self.outputs[out]))
            return
    def cmd_send(self, cmds):

        logger.debug(f"!!command: {cmds}")
        for cmd in cmds:
            self.proc.stdin.write(bytes("%s\n" % cmd, encoding='utf-8'))
        self.proc.stdin.flush()
    def read_outputs(self, out_dict):
        for k_variable, val_tuple in out_dict.items():
            for zone_id, val in zip(val_tuple[0], val_tuple[1]):
                name = k_variable + ' ' + zone_id
                if k_variable == 'zone.load_s' or k_variable == 'zone.fresh_vent_load_s':
                    val *= 3600
                self.outputs[name] = val
    def prepare_varnames(self, base_dict):
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

        return vars_dict

    def read_stdout(self, lines=10, typology='outputs'):
        out_dict = {}
        for i in range(lines):
            logger.debug(f"!!!!read line {i}")
            res = self.proc.stdout.readline().decode('utf-8')
            logger.debug(f" results of step : {res}")
            if typology == 'outputs':
                key = res.split(' ')[-2]
                zones_ids = [i for i in res.split(' ')[-1].split('=')[0].strip()[1:-1].split(',')]
                vals = [float(i) for i in res.split(' ')[-1].split('=')[1].strip()[1:-1].split(',')]
                values = (zones_ids, vals)
                out_dict[key] = values
            elif typology == 'ids':  # for now no use to this
                # not workling they outputs always different staff?? todo ask
                if i > 0:
                    # out_dict [i-1] = [int(r) for r in res.strip().split(' ')]
                    out_dict = {}
        # logger.debug(f"the output_dict = {out_dict}")
        return out_dict
    def finalize(self):
        return super().finalize()
