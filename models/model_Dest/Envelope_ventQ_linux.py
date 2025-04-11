from _baseModels.Model import Model #rember the top level running python script is al;ways main
import logging
from utils import setup_logger
import subprocess
import os

# logger = logging.getLogger(__name__)
# logger.addHandler(logging.StreamHandler())
# logger.setLevel(logging.DEBUG)
logger = setup_logger(__name__)

''''Pdemand only for heating case it calculates with 0 the demand and than calculate with 1 the inverse by passing the exact loads. In case the 
estimated loads are negative in the second step it passes 0 as vent_q'''


#
# class Envelope (Model):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         # if self.silent:
#         #     args = ["%s" % self.executable, "-q"]
#         # else:
#         #     args = ["%s" % self.executable]
#         # args.append(self.casefile)
#         #
#         # logger.debug(f"## args for run {args} ##")
#         #
#         # self.proc = subprocess.Popen(args=args, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
#         #
#         #
#         # #send command for require and outputs TOdo hardcoded generalize
#         # cmd_list = ["require zone.ac_t zone.load_s zone.fresh_vent_load_s","prepare"]
#         # self.cmd_send(cmd_list)
#         # cmd_list = ["out zone.ac_t [8674, 8677, 8680, 8692, 73086]", "out zone.load_s [8674, 8677, 8680, 8692, 73086]", "out zone.fresh_vent_load_s [8674, 8677, 8680, 8692, 73086]"]
#         # self.cmd_send(cmd_list)
#         # self.fixed_outputs = len(cmd_list)
#         params = {}
#         for par in self.params:
#             for id_room in self.zone_ids:
#                 name = par +' '+str(id_room)
#                 params[name] = []
#         self.params = params
#         self.memory = [] # this is need beause we perform a change in params and later also in input outputs so that we can refresh the memroy to be compliant with new (room specific) keys
#
#         self.commands = {
#             'init': ["set run.time_step = %s"%self.real_period, "require zone.ac_t zone.load_s zone.fresh_vent_load_s zone.load_dehumi zone.fresh_vent_load_dehumi", "prepare"],
#             'out_heating': ["out zone.ac_t %s" % self.zone_ids, "out zone.load_s %s" % self.zone_ids,
#                             "out zone.fresh_vent_load_s %s" % self.zone_ids],
#             'out_cooling': ["out zone.ac_t %s" % self.zone_ids, "out zone.load_s %s" % self.zone_ids,
#                             "out zone.fresh_vent_load_s %s" % self.zone_ids, "out zone.load_dehumi %s" % self.zone_ids,
#                             "out zone.fresh_vent_load_dehumi %s" % self.zone_ids],
#             'run0': ["in schedule.ac_t_max %s = %s", "in schedule.ac_t_min %s = %s","in zone.ac_on_off %s = %s", "run 0"],
#             'run1': ["in zone.vent_q %s = %s", "in zone.ac_on_off %s = %s", "run 1"]
#         }
#         self.start()
#         self.in_vars_p_demand = ['schedule.ac_t_max', 'schedule.ac_t_min']
#
#         self.in_vars_t_air = ['zone.vent_q','zone.ac_on_off']
#
#         # self.heating_season = [[0,2160],[6480,8761]] # todo this should become an input froma controller/scehduler
#         # self.cooling_season = [[2160,6480]] # todo this should become an input froma controller/scehduler
#         self.heating_season = [[0, 2520], [6960, 8760]]
#         self.cooling_season = [[2520, 6960]]
#
#         self.limit_heating = [14020.6806, 3320.6274359999998, 3175.690968, 6741.66276, 2815.0116479999997]
#         self.limit_cooling = 100000000 # per zone
#         self.ts = 0
#         logger.info(f"params of model = {self.params}")
#         logger.info(f"memory or model = {self.memory}")
#
#     def __del__(self):
#         self.proc.terminate()
#         logger.debug("process terminated")
#         self.proc.wait()
#         logger.debug("process terminated")
#         self.proc.wait()
#     def terminate(self):
#         self.proc.terminate()
#
#
#
#     def start(self):
#
#         # Command to extract the .tbz file
#         # extract_command = f'tar -xjf {self.executable}'
#         #
#         # # Launch the process to extract the .tbz file
#         # subprocess.run(extract_command, shell=True)
#
#         # Find the extracted executable dynamically
#         # extracted_dir = os.path.dirname(self.executable)
#         # extracted_files = os.listdir(extracted_dir)
#         # extracted_executable = [file for file in extracted_files if os.access(os.path.join(extracted_dir, file), os.X_OK)][0]
#         # extracted_executable_path = os.path.join(extracted_dir, extracted_executable)
#
#         # After extraction, you can then run the extracted executable with an argument
#         # Argument to pass to the executable
#         argument = [self.executable,'-q', self.casefile]
#
#         # Launch the extracted executable with the argument
#         self.proc = subprocess.Popen(argument,  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
#                                    stderr=subprocess.PIPE, text=True)
#         #stdout, stderr = self.proc.communicate()
#
#         # Check for any errors
#         #if stderr:
#         #    print(f"Error: {stderr.decode()}")
#         #else:
#         #    print(f"Output: {stdout.decode()}")
#
#         # if self.silent:
#         #     args = ["%s" % self.executable, "-q"]
#         # else:
#         #     args = ["%s" % self.executable]
#         # args.append(self.casefile)
#         #
#         # logger.debug(f"## args for run {args} ##")
#         #
#         # self.proc = subprocess.Popen(args=args, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
#
#         # send command for require and outputs TOdo hardcoded generalize
#         cmd_list = self.commands['init']
#         self.cmd_send(cmd_list)
#         cmd_list = self.commands['out_cooling']
#         self.cmd_send(cmd_list)
#
#
#         self.fixed_outputs = len(cmd_list)
#
#     def step(self, ts, **kwargs):
#         if self.ts >= int(self.reset_period / self.real_period):
#             if self.ts % int(
#                     self.reset_period / self.real_period) == 0:  # todo should be not hardcoded and esxpress the reset position with the ts we want to reset
#                 # restart
#                 self.terminate()
#                 self.start()
#                 logger.info("RESTART!!")
#             timestep = self.ts % int(self.reset_period / self.real_period)
#             logger.info(f"$$$$$ ts = {timestep}")
#
#         season = 'heating'
#
#         # mod_run = 0
#         # inps = self.prepare_varnames(
#         #     {k: val for k, val in self.inputs.items() if any(i in k for i in self.in_vars_p_demand)})
#         # cmd_list = []
#         # for name in inps:
#         #     cmd = f"in {name} = {inps[name]}"
#         #     cmd_list.append(cmd)
#         # cmd_list.append(self.commands['run0'][-2]%(self.zone_ids,[1,1,1,1,1])) # todo test
#         # cmd_list.append(f"run {mod_run}")
#         # self.cmd_send(cmd_list)
#         # out_dict = self.read_stdout(self.fixed_outputs)
#         # self.read_outputs(out_dict, mode=0)
#         #
#         #
#         # self.vent_q = {}
#         # vent_q_list = []
#         # load_req = 0
#         # for k_variable, val_tuple in out_dict.items():  # they should always have same order
#         #     if 'load_s' in k_variable:
#         #         for zone_id, val in zip(val_tuple[0], val_tuple[1]):
#         #             if zone_id not in self.vent_q.keys():  # todo add conversion if needed
#         #                 self.vent_q[zone_id] = val * self.real_period
#         #             else:
#         #                 self.vent_q[zone_id] += val * self.real_period
#         #
#         # for k, val in self.vent_q.items():
#         #     vent_q_list.append((val))
#         #
#         # load_req = sum([val for k,val in self.vent_q.items()])
#         #
#         # logger.debug(f"ventQlist = {vent_q_list}")
#         # if load_req!=0:
#         #     proportions = [i/load_req for i in vent_q_list ]
#         #     if season == 'cooling':
#         #         vent_q_list = [self.inputs['vent_q']*prop*-1 for prop in proportions]
#         #     else:
#         #         vent_q_list = [self.inputs['vent_q']*prop for prop in proportions]
#
#
#         vent_q_list = [self.inputs['vent_q'], 0.0, 0.0, 0.0, 0.0]
#
#         # logger.debug(f" received ventq = {self.inputs['vent_q']}, load required for proportions = {load_req} and list for proportion {vent_q_list} ")
#         # new commands generic
#         cmds_run1 = ["in zone.vent_q [8674, 8677, 8680, 8692, 73086] = %s"%vent_q_list,
#                                   "in zone.ac_on_off [8674, 8677, 8680, 8692, 73086] = %s"%[0,0,0,0,0], "run 1"]
#         # cmd_list = [cmds_run1[0] % vent_q_list, cmds_run1[1] % [0,0,0,0,0], cmds_run1[2]]
#         self.cmd_send(cmds_run1)
#         out_dict = self.read_stdout(self.fixed_outputs)
#         self.read_outputs(out_dict, mode = 1)
#         # self.outputs['load_req'] = load_req
#         self.ts+=1
#
#
#         # for out in self.outputs:
#         #     self.memory['outputs'][out].append(deepcopy(self.outputs[out]))
#         # self._fill_memory()
#
#
#     def cmd_send(self, cmds):
#
#         logger.debug(f"!!command: {cmds}")
#         for cmd in cmds:
#             #self.proc.stdin.write(bytes("%s\n" % cmd, encoding='utf-8'))
#             self.proc.stdin.write("%s\n" % cmd)
#         self.proc.stdin.flush()
#     def read_outputs(self, out_dict, mode):
#         #this is only for publish and maybe memory todo check this logic if i want to add something to be used i must also add the publication or can i avoid it?
#
#         for k_variable, val_tuple in out_dict.items():
#             for zone_id, val in zip(val_tuple[0], val_tuple[1]):
#                 name = k_variable + ' ' + zone_id
#                 if 'load_s' in k_variable or 'vent_q' in k_variable or 'dehumi' in k_variable:
#                     val*=1000
#                     # val*=1
#                 if mode == 0 and 'load_s' in k_variable:
#                     self.params[name] = val
#                 elif mode == 0 and 'dehumi' in k_variable:
#                     self.params[name] = val
#                 elif mode == 1 and 'ac_t' in k_variable:
#                     self.outputs[name] = val
#                 # elif mode == 1 :
#                 #     name = "zone.vent_q "+ zone_id
#                 #     self.outputs[name] = self.vent_q[zone_id]
#
#     def prepare_varnames(self, base_dict):
#         vars_dict = {}
#         names_dict = {}
#         vals_dict = {}
#
#         for k, val in base_dict.items():
#             if " " in k and k.split(" ")[0] not in names_dict.keys():
#                 names_dict[k.split(" ")[0]]="[%s]"%k.split(" ")[-1]
#                 vals_dict[k.split(" ")[0]] = [val]
#             elif " " in k and k.split(" ")[0] in names_dict.keys():
#                 names_dict[k.split(" ")[0]] = names_dict[k.split(" ")[0]][:-1]+ ", %s]"%k.split(" ")[-1]
#                 vals_dict[k.split(" ")[0]].append(val)
#             else:
#                 # names_dict[k] = k
#                 # vals_dict[k] = val
#                 vars_dict[k]=val
#
#         for k,val in zip(names_dict,vals_dict.values()):
#             name = k + " %s"%names_dict[k]
#             vars_dict[name]=val
#
#         return vars_dict
#
#     def read_stdout(self, lines=10, typology='outputs'):
#         out_dict = {}
#         for i in range(lines):
#             # logger.debug(f"!!!!read line {i}")
#             res = self.proc.stdout.readline()
#             # logger.debug(f" results of step : {res}")
#             if typology == 'outputs':
#                 key = res.split(' ')[-2]
#                 zones_ids = [i for i in res.split(' ')[-1].split('=')[0].strip()[1:-1].split(',')]
#                 vals = [float(i) for i in res.split(' ')[-1].split('=')[1].strip()[1:-1].split(',')]
#                 values = (zones_ids, vals)
#                 out_dict[key] = values
#             elif typology == 'ids':  # for now no use to this
#                 # not workling they outputs always different staff?? todo ask
#                 if i > 0:
#                     # out_dict [i-1] = [int(r) for r in res.strip().split(' ')]
#                     out_dict = {}
#         # logger.debug(f"the output_dict = {out_dict}")
#         return out_dict
#     def finalize(self):
#         return super().finalize()
#


####################################################################################################################################################################################################################################


class Envelope (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        params = {}
        for par in self.params:
            for id_room in self.zone_ids:
                name = par +' '+str(id_room)
                params[name] = []
        self.params = params
        self.memory = [] # this is need beause we perform a change in params and later also in input outputs so that we can refresh the memroy to be compliant with new (room specific) keys

        self.commands = {
            'init': ["set run.time_step = %s"%self.real_period, "require zone.ac_t", "prepare"],
            'out_heating': ["out zone.ac_t %s" % self.zone_ids],
            'out_cooling': ["out zone.ac_t %s" % self.zone_ids, "out zone.load_s %s" % self.zone_ids,
                            "out zone.fresh_vent_load_s %s" % self.zone_ids, "out zone.load_dehumi %s" % self.zone_ids,
                            "out zone.fresh_vent_load_dehumi %s" % self.zone_ids],
            'run': ["in zone.vent_q %s = %s", "in zone.ac_on_off %s = %s", "run 1"]
        }
        self.start()
        self.in_vars_p_demand = ['schedule.ac_t_max', 'schedule.ac_t_min']

        self.in_vars_t_air = ['zone.vent_q','zone.ac_on_off']

        # self.heating_season = [[0,2160],[6480,8761]] # todo this should become an input froma controller/scehduler
        # self.cooling_season = [[2160,6480]] # todo this should become an input froma controller/scehduler
        self.heating_season = [[0, 2520], [6960, 8760]]
        self.cooling_season = [[2520, 6960]]

        self.limit_heating = [14020.6806, 3320.6274359999998, 3175.690968, 6741.66276, 2815.0116479999997]
        self.limit_cooling = 100000000 # per zone
        self.ts = 0
        logger.info(f"params of model = {self.params}")
        logger.info(f"memory or model = {self.memory}")

    def __del__(self):
        self.proc.terminate()
        logger.debug("process terminated")
        self.proc.wait()
        logger.debug("process terminated")
        self.proc.wait()
    def terminate(self):
        self.proc.terminate()



    def start(self):


        # Argument to pass to the executable
        argument = [self.executable,'-q', self.casefile]

        # Launch the extracted executable with the argument
        self.proc = subprocess.Popen(argument,  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        # send command for require and outputs TOdo hardcoded generalize
        cmd_list = self.commands['init']
        self.cmd_send(cmd_list)
        cmd_list = self.commands['out_heating']
        self.cmd_send(cmd_list)
        self.fixed_outputs = len(cmd_list)

    def step(self, ts, **kwargs):
        if self.ts >= int(self.reset_period / self.real_period):
            if self.ts % int(
                    self.reset_period / self.real_period) == 0:  # todo should be not hardcoded and esxpress the reset position with the ts we want to reset
                # restart
                self.terminate()
                self.start()
                logger.info("RESTART!!")
            timestep = self.ts % int(self.reset_period / self.real_period)
            logger.info(f"$$$$$ ts = {timestep}")

        season = 'heating'


        vent_q_list = [self.inputs['vent_q'], 0.0, 0.0, 0.0, 0.0]

        # logger.debug(f" received ventq = {self.inputs['vent_q']}, load required for proportions = {load_req} and list for proportion {vent_q_list} ")
        # new commands generic
        cmds_run1 = ["in zone.vent_q [8674, 8677, 8680, 8692, 73086] = %s"%vent_q_list,
                                  "in zone.ac_on_off [8674, 8677, 8680, 8692, 73086] = %s"%[0,0,0,0,0], "run 1"]
        # cmd_list = [cmds_run1[0] % vent_q_list, cmds_run1[1] % [0,0,0,0,0], cmds_run1[2]]
        self.cmd_send(cmds_run1)
        out_dict = self.read_stdout(self.fixed_outputs)
        self.read_outputs(out_dict, mode = 1)
        # self.outputs['load_req'] = load_req
        self.ts+=1


        # for out in self.outputs:
        #     self.memory['outputs'][out].append(deepcopy(self.outputs[out]))
        # self._fill_memory()


    def cmd_send(self, cmds):

        logger.debug(f"!!command: {cmds}")
        for cmd in cmds:
            #self.proc.stdin.write(bytes("%s\n" % cmd, encoding='utf-8'))
            self.proc.stdin.write("%s\n" % cmd)
        self.proc.stdin.flush()
    def read_outputs(self, out_dict, mode):
        #this is only for publish and maybe memory todo check this logic if i want to add something to be used i must also add the publication or can i avoid it?

        for k_variable, val_tuple in out_dict.items():
            for zone_id, val in zip(val_tuple[0], val_tuple[1]):
                name = k_variable + ' ' + zone_id
                if 'load_s' in k_variable or 'vent_q' in k_variable or 'dehumi' in k_variable:
                    val*=1000
                    # val*=1
                if mode == 0 and 'load_s' in k_variable:
                    self.params[name] = val
                elif mode == 0 and 'dehumi' in k_variable:
                    self.params[name] = val
                elif mode == 1 and 'ac_t' in k_variable:
                    self.outputs[name] = val
                # elif mode == 1 :
                #     name = "zone.vent_q "+ zone_id
                #     self.outputs[name] = self.vent_q[zone_id]

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
            # logger.debug(f"!!!!read line {i}")
            res = self.proc.stdout.readline()
            # logger.debug(f" results of step : {res}")
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


