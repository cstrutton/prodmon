import os
import yaml

CONFIG_FILE_PATH = '/etc/prodmon/'


def config_default(config, key, default):
    if key not in config:
        config[key] = default


def get_config(config_key: str):
    config_file_path = f'{CONFIG_FILE_PATH}{config_key}.config'
    if not os.path.isfile(config_file_path):
        raise ValueError(f'Config file {config_file_path} not found.')

    with open(config_file_path, 'r') as file:
        try:
            config = yaml.load(file, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                print(f'Error position: {mark.line + 1}{mark.column + 1}')
                exit(-1)
        return config
