import os
import sys
import yaml


def config_default(config_dict, key, default):
    if key not in config_dict:
        config_dict[key] = default


def get_config(config_key):
    if len(sys.argv) == 2:
        config_path = f'configs/{sys.argv[1]}.yml'
    else:
        config_path = f'/etc/prodmon/{config_key}.yml'
    print(f'opening {config_path}')
    if not os.path.isfile(config_path):
        raise ValueError('Config file not found!')

    with open(config_path, 'r') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    return config
