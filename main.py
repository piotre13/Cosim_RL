import os
import subprocess


#helics run --path=test_case1_runner.json

#subprocess.run(["pwd"])
output_path = os.getcwd()

run_path = output_path +'\\federations\\test_case1\\test_case1_runner.json'
subprocess.call('helics run --path='+run_path,shell=True)