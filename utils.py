import yaml
import json


def read_yaml(yaml_file):
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    return data


def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def save_yaml(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f)
