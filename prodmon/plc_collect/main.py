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
    last_value = None
    last_read = None
    next_read = None

    def __init__(self, tag_name, scale, db_table):
        self.tag_name = tag_name
        self.scale = scale
        self.dbtable = db_table


class PylogixCounterTag(Tag):

    def __init__(self, tag_name, scale, db_table, machine, part_number):
        super().__init__(tag_name, scale, db_table)
        self.db_machine_data = machine
        self.db_part_number_data = part_number


class PylogixDataTag(Tag):

    def __init__(self, tag_name, scale, db_table, name, strategy):
        super().__init__(tag_name, scale, db_table)
        self.db_name_data = name
        self.strategy = strategy


class ModbusADAM6xxxCounterTag(Tag):
    def __init__(self, tag_name, scale, db_table):
        super().__init__(tag_name, scale, db_table)


class Device:
    tag_list = []

    def __init__(self, name, ip, frequency):
        self.name = name
        self.ip = ip
        self.frequency = frequency

    def add_data_points(self, tag_list):
        for tag in tag_list:
            self.add_data_point(tag)

    def add_data_point(self, tag):
        tag.type = tag.get('type', None)
        self.tag_list.append(self.add_data_point(tag))

    def read_tags(self):
        pass

    def is_valid(self):
        if not self.driver:
            return False
        if not self.ip:
            return False


class PylogixDevice(Device):
    tag_names = []

    def __init__(self, name, ip, frequency, slot):
        super().__init__(name, ip, frequency)
        self.driver = "pylogix"
        self.processor_slot = slot

    def add_data_point(self, tag):
        tag_type = tag.get('type', None)
        tag_name = tag.get('tag', None)
        scale = tag.get('scale', 1)
        db_table = tag.get('table', None)

        if tag_type == 'counter':
            machine = tag.get('machine', None)
            part_number = tag.get('part_number', None)
            tag_object = PylogixCounterTag(tag_name, scale, db_table, machine, part_number)
        elif tag_type == 'data':
            name = tag.get('name', None)
            strategy = tag.get('strategy', None)
            tag_object = PylogixDataTag(tag_name, scale, db_table, name, strategy)

        self.tag_names.append(tag_object.tag_name)

    def is_valid(self):
        if not super().is_valid():
            return False


class ModbusDevice(Device):

    def __init__(self, name, ip, frequency):
        super().__init__(name, ip, frequency)
        self.driver = "modbus"

    def add_data_point(self, tag):
        tag_type = tag.get('type', None)
        register = tag.get('register', None)
        scale = tag.get('scale', 1)
        db_table = tag.get('table', None)

        if tag_type == 'ADAM_counter':
            machine = tag.get('machine', None)
            part_number = tag.get('part_number', None)
            tag_object = ModbusADAM6xxxCounterTag(register, scale, db_table, machine, part_number)
        elif tag_type == 'data':
            name = tag.get('name', None)
            strategy = tag.get('strategy', None)
            tag_object = PylogixDataTag(tag_name, scale, db_table, name, strategy)


    def is_valid(self):
        if not super().is_valid():
            return False


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
    devices = []

    # reads the yaml config file and returns it as a data structure
    config = get_config('collect')

    for device in config['devices']:

        name = device.get('name', None)
        ip = device.get('ip', None)
        frequency = device.get('frequency', 1)

        driver = device.get('driver', None)
        if driver == 'pylogix':
            slot = device.get('processor_slot', 0)
            device_entry = PylogixDevice(name, ip, frequency, slot)
        elif driver == 'modbus':
            device_entry = ModbusDevice(driver, name, ip, frequency)

        for tag in device['tags']:
            device_entry.add_data_point(tag)




            pass

    # while True:
    #     loop(collect_config)


if __name__ == "__main__":
    main()
