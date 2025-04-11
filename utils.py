import yaml
import json
import numpy as np

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

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
        json.dump(data, f, indent=4, cls=NpEncoder)


def save_yaml(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f)


import logging
import sys

# ANSI escape codes
COLOR_RESET = "\033[0m"
COLOR_MAP = {
    'main': '\033[94m',
    'federate': '\033[92m',
    'default': '\033[90m',
}

# Only colorize if stdout is a terminal (not piped)
USE_COLOR = sys.stdout.isatty()

class ScriptColorFormatter(logging.Formatter):
    def format(self, record):
        if USE_COLOR:
            script_name = record.name.split('.')[0]
            color = COLOR_MAP.get(script_name, COLOR_MAP['default'])
            original = super().format(record)
            return f"{color}{original}{COLOR_RESET}"
        else:
            return super().format(record)

def setup_logger(name: str, logfile: str = None, level=logging.DEBUG) -> logging.Logger:
    """
    Set up a logger with optional file and console handlers.
    :param name: Logger name (usually __name__)
    :param logfile: Optional log file path
    :param level: Logging level
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if already set
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter("%(name)s - %(message)s")
    color_formatter = ScriptColorFormatter("%(name)s - %(message)s")

    # File handler (no color)
    if logfile:
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Console handler (color if possible)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)

    return logger