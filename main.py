import os
import subprocess


#helics run --path=example_federation_runner.json

#subprocess.run(["pwd"])
output_path = os.getcwd()

run_path = output_path +'\\federations\\example_federation\\example_federation_runner.json'
subprocess.call('helics run --path='+run_path,shell=True)