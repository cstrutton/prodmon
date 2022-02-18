#!/usr/bin/env python3
import sys
import time

from pyModbusTCP.client import ModbusClient
from pylogix import PLC

from prodmon.shared.configuration_file import read_config_file
from prodmon.shared.log_setup import get_logger

test_count = 25

SQL_DIRECTORY = 'tempSQL/'

logger = get_logger()


class Tag:

    def __init__(self, parent, address, scale, frequency, db_table):
        self.parent = parent
        self.address = address
        self.type = None
        self.scale = scale
        self.frequency = frequency
        self.dbtable = db_table
        self.next_read = time.time()
        self.last_value = None

    def poll(self):
        pass

    def write_sql_file(self, count, timestamp):
        pass


class CounterTag(Tag):

    def __init__(self, parent, address, scale, frequency, db_table, machine, part_number):
        super().__init__(parent, address, scale, frequency, db_table)
        self.type = 'counter'
        self.db_machine_data = machine
        self.db_part_number_data = part_number

    def poll(self):
        timestamp = time.time()
        if self.next_read < timestamp:
            # increment now so it doesn't get missed
            self.next_read = timestamp + self.frequency

            count, error_flag = self.parent.read(self)
            if error_flag:
                return
            count *= self.scale

            # last_value is 0 or Null
            if not self.last_value:
                if self.last_value == 0:
                    logger.info(f'Counter Rolled over: Successfully read {self.parent.name}:{self.address} ({count})')
                else:
                    logger.info(f'First pass through: Successfully read {self.parent.name}:{self.address} ({count})')
                self.last_value = count
                return

            # no change
            if not count > self.last_value:
                return

            # create entry for new values
            for part_count_entry in range(self.last_value + 1, count + 1):
                logger.info(f'Creating entry for: {self.parent.name}:{self.address} ({count})')
                sys.stdout.flush()
                file_path = f'{SQL_DIRECTORY}{timestamp}.sql'
                sql = self.entry_sql(part_count_entry, timestamp)
                with open(file_path, "a+") as file:
                    file.write(sql)

            self.last_value = count

    def entry_sql(self, count, timestamp):
        # create entry for new value
        part_number = self.db_part_number_data
        table = self.dbtable
        machine = self.db_machine_data

        sql = f'INSERT INTO {table} '
        sql += f'(Machine, '
        if part_number:
            sql += f'Part, '
        sql += f'PerpetualCount, Timestamp) '
        sql += f'VALUES ("{machine}" ,'
        if part_number:
            sql += f'"{part_number}" , '
        sql += f'{count}, {timestamp});\n'
        return sql


class DataTag(Tag):

    def __init__(self, parent, address, scale, frequency, db_table, machine, part_number):
        raise NotImplementedError
        super().__init__(parent, address, scale, frequency, db_table)
        self.type = 'data'

    def poll(self):
        pass


class Device:

    def __init__(self, name, ip, frequency):
        self.name = name
        self.ip = ip
        self.frequency = frequency
        self.tag_list = []

    def add_data_point(self, tag):
        self.tag_list.append(tag)

    def poll_tags(self):
        for tag in self.tag_list:
            tag.poll()

    def process_counter_tag(self, tag):
        pass

    def read_tag(self, tag):
        pass


class PylogixDevice(Device):

    def __init__(self, name, ip, frequency, slot):
        super().__init__(name, ip, frequency)
        self.driver = "pylogix"
        self.processor_slot = slot
        self.comm = PLC(ip_address=self.ip, slot=self.processor_slot)

    def add_data_point(self, tag):
        tag_type = tag.get('type', None)
        tag_name = tag.get('tag', None)
        scale = tag.get('scale', 1)
        frequency = tag.get('frequency', 0)
        frequency = max(self.frequency, frequency)
        db_table = tag.get('table', None)
        parent = self

        if tag_type == 'counter':
            machine = tag.get('machine', None)
            part_number = tag.get('part_number', None)
            new_tag_object = CounterTag(parent, tag_name, scale, frequency, db_table, machine, part_number)

        elif tag_type == 'data':
            raise NotImplementedError
            name = tag.get('name', None)
            strategy = tag.get('strategy', None)
            new_tag_object = DataTag(parent, tag_name, scale, db_table, name, strategy)

        else:
            raise NotImplementedError

        super().add_data_point(new_tag_object)

    def read(self, tag):
        error_flag = False
        ret = self.comm.Read(tag.address)

        if ret.Status != "Success":
            logger.info(f'Failed to read {self.name}:{tag.address} ({ret.Status})')
            error_flag = True
        else:
            logger.debug(f'Successfully read {self.name}:{tag.address} ({ret.Value})')
        return ret.Value, error_flag


class ModbusDevice(Device):

    def __init__(self, name, ip, frequency):
        super().__init__(name, ip, frequency)
        self.driver = "modbus"
        self.comm = ModbusClient(host=ip, auto_open=True, auto_close=True)

    def add_data_point(self, tag):
        tag_type = tag.get('type', None)
        register = tag.get('register', None)
        scale = tag.get('scale', 1)
        frequency = tag.get('frequency', 0)
        frequency = max(self.frequency, frequency)
        db_table = tag.get('table', None)
        parent = self

        if tag_type == 'ADAM_counter':
            machine = tag.get('machine', None)
            part_number = tag.get('part_number', None)
            tag_object = CounterTag(parent, register, scale, frequency, db_table, machine, part_number)
        elif tag_type == 'data':
            name = tag.get('name', None)
            strategy = tag.get('strategy', None)
            # tag_object = PylogixDataTag(tag_name, scale, db_table, name, strategy)

        super().add_data_point(tag_object)

    def read(self, tag):
        error_flag = False
        count = None
        regs = self.comm.read_holding_registers(tag.address, 2)

        if regs:
            count = regs[0] + (regs[1] * 65536)
            logger.debug(f'Successfully read {self.name}:{tag.address} ({count})')
        else:
            error_flag = True
            count = None
            logger.info(f'Failed to read {self.name}:{tag.address}')

        return count, error_flag


def process_collect_config():
    devices = []

    # reads the yaml config file and returns it as a data structure
    config = read_config_file('collect')

    for device in config['devices']:

        name = device.get('name', None)
        ip = device.get('ip', None)
        frequency = device.get('frequency', 1)

        driver = device.get('driver', None)

        if driver == 'pylogix':
            slot = device.get('processor_slot', 0)
            device_entry = PylogixDevice(name, ip, frequency, slot)

        elif driver == 'modbus':
            device_entry = ModbusDevice(name, ip, frequency)

        for tag in device['tags']:
            device_entry.add_data_point(tag)
        devices.append(device_entry)

    return devices


@logger.catch()
def main():
    devices = process_collect_config()
    while True:
        for device in devices:
            device.poll_tags()


if __name__ == "__main__":
    main()
