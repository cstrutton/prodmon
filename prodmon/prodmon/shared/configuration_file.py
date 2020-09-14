import os
import sys
import yaml


def config_default(dict, key, default):
    if not key in dict:
        dict[key] = default


def get_config(config_key):

    if len(sys.argv) < 2:
        raise ValueError("Need config file")

    if not os.path.isfile(sys.argv[1]):
        raise ValueError("Config file does not exist")

    with open(sys.argv[1], 'r') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        config = config[config_key]

    return config
