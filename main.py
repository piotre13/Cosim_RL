import os
import subprocess
import helics as h
import time
from subprocess import Popen, PIPE, run
from utils import read_yaml, save_yaml
import sys
#helics run --path=test_case1_runner.json

#subprocess.run(["pwd"])


def prepare_federation(RL_config, run_path):
    end_period = (RL_config['training_duration']+RL_config['testing_duration']) * RL_config['unit_train_test_seconds']
    RL_training = True
    episode_period = RL_config['episode_duration'] * RL_config['episode_seconds']  # day in seconds
    training_episodes = int(RL_config['training_duration']*RL_config['unit_train_test_seconds']/episode_period)

    fed_path = os.path.dirname(run_path)
    for file in os.listdir(fed_path):
        if file.endswith(".yaml"):
            file = os.path.join(fed_path,file)
            config = read_yaml(file)
            config['fed_conf']['sim_params']['end_period'] = end_period
            config['fed_conf']['RL_training'] = RL_training
            config['fed_conf']['training_episodes'] = training_episodes
            config['fed_conf']['episode_period'] = episode_period
            config['fed_conf']['sim_params']['reset_period'] = RL_config['unit_train_test_seconds']
            save_yaml(file,config)



#     pass
def main_run(run_path):
    exec = 'helics'
    args = ['run', '--path='+run_path]
    command = 'helics -v run --path='+run_path
    #p = Popen([exec,*args], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    t_start = time.time()
    print(f"Starting simulation! federation: {run_path}")
    result = run(command, stdout=PIPE, stderr=PIPE, text=True)
    print(result.returncode, result.stdout, result.stderr)
    print(f"Execution took: {time.time()-t_start} s ")

def save_results():
    pass

#TODO when the simulation ends need to store the results in dedicated folder specifing the simulation




if __name__ == "__main__":
    output_path = os.getcwd()

    # run_path = output_path + '\\federations\\test_case_dest_setpoint_control_FMU\\runner.json'
    run_path = output_path + '\\federations\\test_case_dest_setpoint_control_Dest\\runner.json'
    # run_path = output_path + '\\federations\\test_case_dest_setpoint_control_Dest_ventQ\\runner.json'



    #training dur in years
    #testing_dur in years
    #episode_dur in days
    # RL_config_FMU = {
    #     "training":True,
    #     "training_duration":1,
    #     "testing_duration":1,
    #     "episode_duration":2,
    #     "episode_seconds":86400,
    #     "unit_train_test_seconds":7776000} # when using years 31536000


    RL_config_Dest = {
        "training": True,
        "training_duration": 100,
        "testing_duration": 1,
        "episode_duration": 2,
        "episode_seconds": 86400,
        "unit_train_test_seconds": 7776000}  # when using years 31536000

    prepare_federation(RL_config_Dest, run_path)
    main_run(run_path) # main simulation run!!!
