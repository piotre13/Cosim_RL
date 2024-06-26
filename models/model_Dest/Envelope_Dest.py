import subprocess
import os
import signal
from time import sleep
import logging
import select
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)



class Simulator:
    def __init__(self,executable, casefile, silent = True ):


        if silent:
            args = ["%s"%executable, "-q" ]
        else:
            args = ["%s"%executable]
        args.append(casefile)

        logger.debug(f"## args for run {args} ##")

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
        if params:
            cmd_list.append("set")
        for name in params:
            cmd_list[0] += f" {name}={params[name]}"
        cmd_list.append("require")
        for re in required:
            cmd_list[-1] += f" {re}"
        cmd_list.append("prepare")
        # logger.debug(f"## cmd_list for init general {cmd_list} ##")
        self.cmd_send(cmd_list)
        if self.fixed_outputs:
            cmd_list = []
            for ou in outputs:
                cmd = f"out {ou}"
                cmd_list.append(cmd)
            # logger.debug(f"## cmd_list for init fixed outputs {cmd_list} ##")
            self.cmd_send(cmd_list)



    def __del__(self):
        self.proc.terminate()
        logger.debug("process terminated")
        self.proc.wait()


    def run(self,inputs, mode=1):
        cmd_list = []
        for name in inputs:
            cmd = f"in {name} = {inputs[name]}"
            cmd_list.append(cmd)

        if len(cmd_list)==0:
            return 1
        else:
            if 'vent_q' in cmd_list[0]: #todo hardcoded
                cmd_list.append(f"in zone.ac_on_off [8674, 8677, 8680, 8692, 73086] = {[0]*5}") #TODO HARDCODED AVOID!!
            cmd_list.append(f"run {mode}")
            # logger.debug(f"## cmd_list for setting inputs {cmd_list} ##")
            self.cmd_send(cmd_list)
            return

    def set_outputs(self,outputs):
        cmd_list = []
        for name in outputs:
            cmd = f"out {name}"
            cmd_list.append(cmd)
        # logger.debug(f"## cmd_list for setting outputs {cmd_list} ##")
        self.cmd_send(cmd_list)


    def calc_demand(self,inputs, mode = 0):
        cmd_list = []
        for name in inputs:
            cmd = f"in {name} = {inputs[name]}"
            cmd_list.append(cmd)
        cmd_list.append(f"run {mode}")
        self.cmd_send(cmd_list)
        out_dict = self.read_stdout(self.fixed_outputs)

        return out_dict


    def calc_tair(self, inputs, mode = 1):
        cmd_list = []
        for name in inputs:
            cmd = f"in {name} = {inputs[name]}"
            cmd_list.append(cmd)
        cmd_list.append(f"in zone.ac_on_off [8674, 8677, 8680, 8692, 73086] = {[0] * 5}")  # TODO HARDCODED AVOID!!
        cmd_list.append(f"run {mode}")
        self.cmd_send(cmd_list)
        out_dict = self.read_stdout(self.fixed_outputs)
        return out_dict

    def step (self, ts, inputs, outputs=None, mode=1):
        ''' this method implment the workflow set T --> step --> P_demand (mode =0); p_actual --> step --> t_air (mode=1)'''

        lines = self.fixed_outputs

        _r = self.run(inputs, mode)

        if not _r:
            logger.debug(f"@@@@@@@@@lines to read {lines}")

            out_dict = self.read_stdout(lines)
        else:
            out_dict={}

        return out_dict


    def read_stdout(self, lines = 10, typology='outputs'):
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
                out_dict[key]=values
            elif typology == 'ids': # for now no use to this
                # not workling they outputs always different staff?? todo ask
                if i>0:
                    #out_dict [i-1] = [int(r) for r in res.strip().split(' ')]
                    out_dict={}
        # logger.debug(f"the output_dict = {out_dict}")
        return out_dict


    def finalize (self):
        self.proc.terminate()
        self.proc.wait()

    def cmd_send(self, cmds):

        logger.debug(f"!!command: {cmds}")
        for cmd in cmds:
            self.proc.stdin.write(bytes("%s\n" % cmd, encoding='utf-8'))
        self.proc.stdin.flush()


        #self.search_for_output(["5room"])
            # self.proc.stdin.close()
            # stderr_fd = self.proc.stderr.fileno()
            #
            # stdout_lines = []
            # stderr_lines = []
            #
            # # Monitor stderr for any output
            # while True:
            #     # Use select to check if there is data to read on stderr
            #     ready, _, _ = select.select([stderr_fd], [], [], 0.1)  # Timeout of 0.1 seconds
            #     if ready:
            #         line = self.proc.stderr.readline()
            #         if line:
            #             stderr_lines.append(line)
            #             print("Received on stderr:", line.decode().strip())
            #         else:
            #             # No more data on stderr, break the loop
            #             break



    def get_char(self):
        character = self.proc.stdout.read1()
        char = character.decode("utf-8")
        logger.debug(f"char {char}")
        # print(
        #     character.decode("utf-8"),
        #     end="",
        #     flush=True,  # Unbuffered print
        # )
        return character.decode("utf-8")


if __name__ =='__main__':


    s = Simulator("DestKernel\\bterminal.exe","DestKernel\\5rooms.db")
    par = {}
    req = ["zone.ac_t", "zone.load_s","zone.fresh_vent_load_s",]
    out = ["zone.ac_t [8674, 8677, 8680, 8692, 73086]"]
    s.initialize(par, req)

    res = []
    for i in range(24):
        for j in range(2):
            if j==0:
                inps = {"schedule.ac_t_max [8674, 8677, 8680, 8692, 73086]":[20.0]*5,
                        "schedule.ac_t_min [8674, 8677, 8680, 8692, 73086]":[20.0]*5}
                out = ["zone.ac_t [8674, 8677, 8680, 8692, 73086]", "zone.load_s [8674, 8677, 8680, 8692, 73086]", "zone.fresh_vent_load_s [8674, 8677, 8680, 8692, 73086]"]
                r = s.step(i, inps,mode=j,outputs=out)
                #zone_load_s = r["zone.load_s"]
                #zone_fresh_vent_load_s = r["zone.fresh_vent_load_s"]
                tot = [100000 for i in range(5)]
            if j==1:
                inps = {"zone.vent_q [8674, 8677, 8680, 8692, 73086]":tot,
                        "zone.ac_on_off [8674, 8677, 8680, 8692, 73086]": [0]*5}
                out = ["zone.ac_t [8674, 8677, 8680, 8692, 73086]", "zone.load_s [8674, 8677, 8680, 8692, 73086]", "zone.fresh_vent_load_s [8674, 8677, 8680, 8692, 73086]"]
                r1=s.step(i,inps, mode=j, outputs=out)
                res.append(r1)



    print(res)
