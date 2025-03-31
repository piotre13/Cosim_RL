import subprocess
import os
import time

from sympy.codegen.ast import stderr


def cmd_send(process, cmds):
    for cmd in cmds:
        process.stdin.write("%s\n" % cmd)
    process.stdin.flush()


exec_path = '/home/pietrorm/Documents/CODE/Cosim_RL/models/model_Dest/DestKernel/bterminal_older'

#extract_command = f'tar -xjf {exec_path}'
case_file = '/home/pietrorm/Documents/CODE/Cosim_RL/models/model_Dest/DestKernel/5rooms.db'
# Launch the process to extract the .tbz file
# subprocess.run(extract_command, shell=True)

#
# # Find the extracted executable dynamically
# extracted_dir = os.path.dirname(exec_path)
# extracted_files = os.listdir(extracted_dir)
# extracted_executable = [file for file in extracted_files if file.endswith('.tbz')][0]
# extracted_executable_path = os.path.join(extracted_dir, extracted_executable)

# After extraction, you can then run the extracted executable with an argument
# Argument to pass to the executable
argument = '-q'
print(exec_path)

# process = subprocess.run([exec_path,argument,case_file], shell=True)









# Launch the extracted executable with the argument
process = subprocess.Popen([exec_path, argument, case_file],stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)




while True:
    cmd_0 = ["set run.time_step = 3600",
     "require zone.ac_t zone.load_s zone.fresh_vent_load_s zone.load_dehumi zone.fresh_vent_load_dehumi", "prepare"]
    cmd_send(process, cmd_0)
    cmd_1 = ["out zone.ac_t [8674, 8677, 8680, 8692, 73086]" , "out zone.load_s [8674, 8677, 8680, 8692, 73086]" ,
                            "out zone.fresh_vent_load_s [8674, 8677, 8680, 8692, 73086]"]
    cmd_send(process, cmd_1)
    cmds_run1 = ["in zone.vent_q [8674, 8677, 8680, 8692, 73086] = [10000,10000,10000,10000,10000]",
                                      "in zone.ac_on_off [8674, 8677, 8680, 8692, 73086] = %s"%[0,0,0,0,0], "run 1"]

    cmd_send(process, cmds_run1)

    for i in range(3):
        # logger.debug(f"!!!!read line {i}")
        print(i)
        res = process.stdout.readline()
        print(res)


    time.sleep(1)
