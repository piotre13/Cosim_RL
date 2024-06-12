import subprocess
import os
import signal
import time


class Simulator:
    def __init__(self, casefile, silent=True):
        if silent:
            args = ["DestKernel\\bterminal.exe", "-q" ]
        else:
            args = ["DestKernel\\bterminal.exe"]
        args.append(casefile)

        self.proc = subprocess.Popen(args=args, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

        self.fixed_outputs = None


    def initialize(self, params=None, required=None, outputs=None):
        if outputs is None:
            outputs = []
        if required is None:
            required = []
        if params is None:
            params = {}
        self.fixed_outputs = len(outputs)
        cmd_list = []
        cmd_list.append("set")
        for name in params:
            cmd_list[0] += f" {name}={params[name]}"
        cmd_list.append("require")
        for req in required:
            cmd_list[1] += f" {req}"
        cmd_list.append("prepare")
        self.cmd_flush(cmd_list)
        if self.fixed_outputs: #setting the output vars only in the case of fixed for the whole execution
            for out in outputs:
                cmd = f"out {out}"
                cmd_list.append(cmd)
            self.cmd_flush(cmd_list)



    def __del__(self):
        self.proc.terminate()
        self.proc.wait()
    def set_inputs(self,inputs):
        cmd_list = []
        for name in inputs:
            cmd = f"in {name}={inputs[name]}"
            cmd_list.append(cmd)
        self.cmd_flush(cmd_list)
    def set_outputs(self,outputs):
        cmd_list = []
        for name in outputs:
            cmd = f"out {name}"
            cmd_list.append(cmd)
        self.cmd_flush(cmd_list)
    # def get_outputs(self, outputs):
    #     out_dic = {}
    #     lines = len(outputs) if outputs else self.fixed_outputs
    #     # for i in range(lines):
    #     #     #res = self.proc.stdout.readline().decode('utf-8')
    #     #     key = res.split(" ")[-2]
    #     #     room_temp = [list(map(float, x.strip()[1:-1].split(','))) for x in res.split("=")[1].split(";")][0]
    #     #     out_dic[key] = room_temp
    #     return out_dic
    def step (self, inputs, ts, mode=1, outputs=None):


        if not self.fixed_outputs:
            self.set_outputs(outputs)
            lines = len(outputs)
        else:
            lines = self.fixed_outputs

        self.set_inputs(inputs)


        #run the model in specific mode with setted inputs
        self.cmd_flush([f"run {mode}"])
        #time.sleep(4)
        out_dict = self.read_stdout(lines, typology = 'outputs')

        return out_dict


    def read_stdout(self, lines = 1, typology='outputs'):
        out_dict = {}

        for i in range(lines):
            res = self.proc.stdout.readline().decode('utf-8')
            if typology == 'outputs':
                res = res.split(' ')[-2:]
                res[1]=res[1][:-2]
                key = res[0]
                val = [list(map(float, x.strip()[1:-1].split(','))) for x in res[1].split("=")[1].split(";")][0]
            elif typology == 'ids':
                # not workling they outputs always different staff?? todo ask
                if i>0:
                    # out_dict [i-1] = [int(r) for r in res.strip().split(' ')]
                    out_dict={}
        return out_dict

    def get_ids(self, var_name):
        #not working todo ask (problem in what outputs the print command...
        cmd_list = []
        if isinstance(var_name, list):
            for var in var_name:
                if 'ids' in var:
                    cmd_list.append(f"print db.{var}")
                else:
                    cmd_list.append(f"print db.{var}.ids")
        else:
            cmd_list[0] = f"print db.{var_name}.ids"

        self.cmd_flush(cmd_list)
        ids_dict = self.read_stdout(lines=len(cmd_list), typology='ids')
        i=0
        for var in var_name:
            ids_dict[var] = ids_dict.pop(i)
            i+=1
        return ids_dict
    def finalize (self):
        self.proc.terminate()
        self.proc.wait()

    def cmd_flush(self, cmds):
        for cmd in cmds:
            self.proc.stdin.write(bytes("%s\n" % cmd, encoding='utf-8'))
        self.proc.stdin.flush()



if __name__ =='__main__':


    s = Simulator("DestKErnel\\5rooms.db")
    par = {'run.as_nature_state': 'true'}
    req = ["zone.ac_t", "zone.load_s","zone.fresh_vent_load_s",]
    out = ["zone.ac_t [8674, 8677, 8680, 8692, 73086]"]
    s.initialize(par, req)

    res = []
    for i in range(24):
        for j in range(2):
            if j==0:
                inps = {"schedule.ac_t_max [8674, 8677, 8680, 8692, 73086]":[20]*5,
                        "schedule.ac_t_min [8674, 8677, 8680, 8692, 73086]":[20]*5}
                out = ["zone.ac_t [8674, 8677, 8680, 8692, 73086]", "zone.load_s [8674, 8677, 8680, 8692, 73086]", "zone.fresh_vent_load_s [8674, 8677, 8680, 8692, 73086]"]
                r = s.step(inps,ts=i,mode=j,outputs=out)
                #zone_load_s = r["zone.load_s"]
                #zone_fresh_vent_load_s = r["zone.fresh_vent_load_s"]
                tot = [100000 for i in range(5)]
            if j==1:
                inps = {"zone.vent_q [8674, 8677, 8680, 8692, 73086]":tot,
                        "zone.ac_on_off [8674, 8677, 8680, 8692, 73086]": [0]*5}
                out = ["zone.ac_t [8674, 8677, 8680, 8692, 73086]", "zone.load_s [8674, 8677, 8680, 8692, 73086]", "zone.fresh_vent_load_s [8674, 8677, 8680, 8692, 73086]"]
                r1=s.step(inps, ts=i, mode=j, outputs=out)
                res.append(r1)



    print(res)
