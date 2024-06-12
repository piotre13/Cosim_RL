import os
import subprocess
import helics as h

#helics run --path=test_case1_runner.json

#subprocess.run(["pwd"])
output_path = os.getcwd()
#WORKING
#run_path = output_path +'\\federations\\example_federation\\example_federation_runner.json'
#run_path = output_path +'\\federations\\test_case1\\test_case1_runner.json'
#run_path = output_path +'\\federations\\test_case1_2\\runner.json'
#run_path = output_path +'\\federations\\test_case2\\runner.json'
#run_path = output_path +'\\federations\\test_iteration\\runner.json'


#ON DEVELOPEMENT
#run_path = output_path +'\\federations\\test_case1_1\\test_case1_runner.json' # not working beacuse logic for messages has not been decided
#run_path = output_path +'\\federations\\fmu_test\\runner.json' # not working beacuse of FMu using matlab
#run_path = output_path +'\\federations\\fmu_test2\\runner.json' # not working beacuse of FMu using matlab
#run_path = output_path +'\\federations\\fmu_test3\\runner.json'
#run_path = output_path +'\\federations\\test_reset\\runner.json'
#run_path = output_path +'\\federations\\test_case_dest1\\runner.json'
#run_path = output_path +'\\federations\\test_control\\runner.json'



try:
    subprocess.call('helics run --path='+run_path,shell=True)
except Exception:
    subprocess.call('helics kill-all-brokers', shell= True)
