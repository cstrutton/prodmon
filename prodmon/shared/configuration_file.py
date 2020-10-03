import os
import sys
import yaml


def config_default(config_dict, key, default):
    if key not in config_dict:
        config_dict[key] = default


def get_config(config_key):
    if os.path.isfile(sys.argv[1]):
        config_path = sys.argv[1]
    elif os.path.isfile(f'/etc/prodmon/{config_key}.yml'):
        config_path = f'/etc/prodmon/{config_key}.yml'
    else:
        raise ValueError('Config file not found!')
    with open(config_path, 'r') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        config = config[config_key]

    return config
