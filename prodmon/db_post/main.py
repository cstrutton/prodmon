#!/usr/bin/env python3

import glob
import os

from time import sleep

import mysql.connector

from prodmon.shared.configuration_file import read_config_file, config_default
from prodmon.shared.log_setup import get_logger

logger = get_logger()


def set_config_defaults(post_config):
    # Set default values for config keys
    config_default(post_config, 'sqldir', "./tempSQL/")
    config_default(post_config, 'polling_freq', 5)

    # testing values
    config_default(post_config["dbconfig"], 'database', 'prodrptdb')
    config_default(post_config["dbconfig"], 'user', 'stuser')
    config_default(post_config["dbconfig"], 'password', 'stp383')
    config_default(post_config["dbconfig"], 'host', '10.4.1.224')


def execute_sql(post_config):
    dbconfig = post_config['dbconfig']
    sqldir = post_config['sqldir']

    # TODO:  Check if sql file exists before opening mysql connection
    # if not os.path.exists(sqldir + '*.sql'):
    #     return

    cnx = mysql.connector.connect(**dbconfig)
    cursor = cnx.cursor()

    for filepath in glob.iglob(sqldir + '*.sql'):
        logger.info(f'Found {filepath}')
        with open(filepath, "r", encoding="utf-8") as file:
            for line in file:
                sql = line.strip()
                logger.debug(f'Posting {sql} to database')
                cursor.execute(sql)
        cnx.commit()
        os.remove(filepath)

    cursor.close()
    cnx.close()


@logger.catch()
def main():
    post_config = read_config_file('post')
    set_config_defaults(post_config)

    while True:
        execute_sql(post_config)
        sleep(post_config['polling_freq'])


if __name__ == '__main__':
    main()
