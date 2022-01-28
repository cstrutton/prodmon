#!/usr/bin/env python3

import os
import sys
import time

from pylogix import PLC
from pyModbusTCP.client import ModbusClient

from prodmon.shared.configuration_file import get_config, config_default
from prodmon.shared.log_setup import get_logger

logger = get_logger()


class Tag:
    name = ''
    last_value = None

    def __init__(self, name):
        self.name = name


class Device:
    name = ''
    ip = ''
    processor_slot = 0
    tag_list = []
    tag_names = []

    def __init__(self, driver, name, ip, slot=0):
        self.driver = driver
        self.name = name
        self.ip = ip
        self.processor_slot = slot

    def add_tag(self, tag):
        self.tag_list.append(tag)
        self.tag_names.append(tag.name)

    def read_tags(self):
        pass


def loop(config):
    for device in config['devices']:
        # get current timestamp
        now = time.time()

    for entry in config['tags']:

        frequency = entry['frequency']

        # make sure we are not polling too fast
        if frequency < minimum_cycle:
            frequency = minimum_cycle

        # handle first pass through
        if entry['nextread'] == 0:
            entry['nextread'] = now

        if entry['nextread'] > now:
            continue  # too soon move on

        entry['lastread'] = now

        # get counter reading
        count = -1
        if entry['type'] == 'pylogix':
            count = read_pylogix_counter(entry)
        if entry['type'] == 'modbus':
            count = read_modbus_counter(entry)
        if count == -1:
            continue

        # adjust for Scale factor
        count = count * entry.get('Scale', 1)

        machine = entry['Machine']

        # deal with counter == 0 edge case
        if count == 0:
            entry['lastcount'] = count
            return  # machine count rolled over or is not running

        if entry['lastcount'] == 0:  # first time through...
            entry['lastcount'] = count
            logger.info(f'First pass through on machine {machine}')

        if count > entry['lastcount']:
            for part_count_entry in range(entry['lastcount'] + 1, count + 1):
                create_part_count_entry(entry, part_count_entry, config)
                logger.info(f'Creating entry for: {machine} - {part_count_entry} ')
            entry['lastcount'] = count

        # set the next read timestamp
        entry['nextread'] += frequency


def read_modbus_counter(entry):
    c = ModbusClient(host=entry['processor_ip'], auto_open=True, auto_close=True)
    regs = c.read_holding_registers(entry['register'], 2)
    return regs[0] + (regs[1] * 65536)


def read_pylogix_counter(counter_entry):
    with PLC() as comm:
        comm.IPAddress = counter_entry['processor_ip']
        comm.ProcessorSlot = counter_entry['processor_slot']

        tag = counter_entry['tag']
        part_count = comm.Read(tag)

        if part_count.Status != 'Success':
            logger.error(f'Failed to read: {part_count} : {tag}')
            return -1

        logger.debug(f'Read pylogix counter:{part_count}, tag:{counter_entry["tag"]}')

    return part_count.Value


def create_part_count_entry(counter_entry, count, config):
    timestamp = str(int(counter_entry['lastread']))
    file_path = f'{config["sqldir"]}{timestamp}.sql'
    sql = part_count_entry_sql(counter_entry, count)
    write_sql_file(sql, file_path)


def part_count_entry_sql(counter_entry, count):
    part_number = counter_entry.get('Part_Number')
    extra_data = counter_entry.get('extra_data', '')
    table = counter_entry['table']
    timestamp = counter_entry['lastread']
    machine = counter_entry['Machine']

    sql = f'INSERT INTO {table} '
    sql += f'(Machine, '
    if part_number:
        sql += f'Part, '
    if extra_data:
        sql += f'ExtraData, '
    sql += f'PerpetualCount, Timestamp) '
    sql += f'VALUES ("{machine}" ,'
    if part_number:
        sql += f'"{part_number}" , '
    if extra_data:
        sql += f'"{extra_data}", '
    sql += f'{count}, {timestamp});\n'
    return sql


def write_sql_file(sql, path):
    with open(path, "a+") as file:
        file.write(sql)


@logger.catch()
def main():
    collect_config = get_config('collect')



    set_config_defaults(collect_config)

    while True:
        loop(collect_config)


if __name__ == "__main__":
    main()
