from prodmon.shared.configuration_file import get_config, config_default
import glob
import os

from time import sleep

import mysql.connector


def set_config_defaults():
    # Set default values for config keys
    config_default(config, 'polling_freq', 5)

    # testing values
    config_default(config["dbconfig"], 'database', 'prodrptdb')
    config_default(config["dbconfig"], 'user', 'stuser')
    config_default(config["dbconfig"], 'password', 'stp383')
    config_default(config["dbconfig"], 'host', '10.4.1.224')


def execute_sql():
    dbconfig = config['dbconfig']
    sqldir = config['sqldir']

    # TODO:  Check if sql file exists before opening mysql connection
    # if not os.path.exists(sqldir + '*.sql'):
    #     return

    cnx = mysql.connector.connect(**dbconfig)
    cursor = cnx.cursor()

    for filepath in glob.iglob(sqldir + '*.sql'):
        with open(filepath, "r", encoding="utf-8") as file:
            for line in file:
                sql = line.strip()
                cursor.execute(sql)
                print(sql)
        cnx.commit()
        os.remove(filepath)

    cursor.close()
    cnx.close()


if __name__ == '__main__':

    config = get_config('post')
    set_config_defaults()

    while True:
        execute_sql()
        sleep(config['polling_freq'])
