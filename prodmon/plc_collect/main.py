#!/usr/bin/env python3

import time

from pyModbusTCP.client import ModbusClient
from pylogix import PLC

from prodmon.shared.configuration_file import read_config_file
from prodmon.shared.log_setup import get_logger

test_count = 25

SQL_DIRECTORY = 'tempSQL/'

logger = get_logger()


class Tag:

    def __init__(self, parent, tag_name, scale, frequency, db_table):
        self.parent = parent
        self.tag_name = tag_name
        self.type = None
        self.scale = scale
        self.frequency = frequency
        self.dbtable = db_table
        self.next_read = time.time()
        self.last_value = None

    def poll(self):
        pass

    def read(self):
        pass

    def write_sql_file(self, count, timestamp):
        pass


class CounterTag(Tag):

    def __init__(self, parent, tag_name, scale, frequency, db_table, machine, part_number):
        super().__init__(parent, tag_name, scale, frequency, db_table)
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
                    logger.info(f'Counter Rolled over: Successfully read \
                        {self.parent.name}:{self.tag_name} ({count})')
                else:
                    logger.info(f'First pass through: Successfully read \
                            {self.parent.name}:{self.tag_name} ({count})')
                self.last_value = count
                return

            # no change
            if not count > self.last_value:
                return

            # create entry for new values
            for part_count_entry in range(self.last_value + 1, count + 1):
                write_sql_file(self, part_count_entry, timestamp)

    # def read(self):
    #     count, error_flag = self.parent.read(self)
    #     count
    #     return count, error_flag


class DataTag(Tag):

    def __init__(self, parent, tag_name, scale, frequency, db_table, machine, part_number):
        super().__init__(parent, tag_name, scale, frequency, db_table)
        self.type = 'data'

    def poll(self):
        pass
        # timestamp = time.time()
        # if self.next_read < timestamp:
        #     # increment now so it doesn't get missed
        #     self.next_read = timestamp + self.frequency
        #
        #     count, error_flag = self.read()
        #     count *= self.scale
        #     if error_flag:
        #         return
        #
        #     # last_value is 0 or Null
        #     if not self.last_value:
        #         if self.last_value == 0:
        #             logger.info(f'Counter Rolled over: Successfully read \
        #                 {self.parent.name}:{self.tag_name} ({count})')
        #         else:
        #             logger.info(f'First pass through: Successfully read \
        #                     {self.parent.name}:{self.tag_name} ({count})')
        #         self.last_value = count
        #         return
        #
        #     # no change
        #     if not count > self.last_value:
        #         return
        #
        #     # create entry for new values
        #     for part_count_entry in range(self.last_value + 1, count + 1):
        #         write_sql_file(self, part_count_entry, timestamp)

    # def read(self):
    #     count, error_flag = self.parent.read(self)
    #     return count, error_flag


class ModbusADAM6xxxCounterTag(Tag):
    def __init__(self, parent, tag_name, scale, frequency, db_table, machine, part_number):
        super().__init__(parent, tag_name, scale, frequency, db_table)
        self.type = 'counter'
        self.register = tag_name
        self.machine = machine
        self.part_number = part_number


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
        ret = self.comm.Read(tag.tag_name)
        ret.Value = test_count
        ret.Status = 'Success'

        if ret.Status != "Success":
            logger.info(f'Failed to read \
                {self.name}:{tag.tag_name} ({ret.Status})')
            error_flag = True
        else:
            logger.debug(f'Successfully read \
                {self.name}:{tag.tag_name} ({ret.Value})')
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
            tag_object = ModbusADAM6xxxCounterTag(parent, register, scale, frequency, db_table, machine, part_number)
        elif tag_type == 'data':
            name = tag.get('name', None)
            strategy = tag.get('strategy', None)
            # tag_object = PylogixDataTag(tag_name, scale, db_table, name, strategy)

        super().add_data_point(tag_object)

    def read_tag(self, tag):
        regs = self.comm.read_holding_registers(tag.register, 2)
        count = regs[0] + (regs[1] * 65536)
        # TODO: catch errors and log
        # if ret.Status != "Success":
        #     logger.info(f'Failed to read {self.name}:{tag.tag_name} ({ret.Status})')
        #     continue
        logger.debug(f'Successfully read \
                {self.name}:{tag.tag_name} ({count})')
        return count


def write_sql_file(tag, count, timestamp):
    # create entry for new value
    file_path = f'{SQL_DIRECTORY}{timestamp}.sql'
    part_number = tag.db_part_number_data
    table = tag.dbtable
    machine = tag.db_machine_data
    sql = f'INSERT INTO {table} '
    sql += f'(Machine, '
    if part_number:
        sql += f'Part, '
    sql += f'PerpetualCount, Timestamp) '
    sql += f'VALUES ("{machine}" ,'
    if part_number:
        sql += f'"{part_number}" , '
    sql += f'{count}, {timestamp});\n'
    with open(file_path, "a+") as file:
        file.write(sql)


def process_config():
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

# def loop(config):
#     for device in config['devices']:
#         # get current timestamp
#         now = time.time()
#
#     for entry in config['tags']:
#
#         frequency = entry['frequency']
#
#         # make sure we are not polling too fast
#         if frequency < minimum_cycle:
#             frequency = minimum_cycle
#
#         # handle first pass through
#         if entry['nextread'] == 0:
#             entry['nextread'] = now
#
#         if entry['nextread'] > now:
#             continue  # too soon move on
#
#         entry['lastread'] = now
#
#         # get counter reading
#         count = -1
#         if entry['type'] == 'pylogix':
#             count = read_pylogix_counter(entry)
#         if entry['type'] == 'modbus':
#             count = read_modbus_counter(entry)
#         if count == -1:
#             continue
#
#         # adjust for Scale factor
#         count = count * entry.get('Scale', 1)
#
#         machine = entry['Machine']
#
#         # deal with counter == 0 edge case
#         if count == 0:
#             entry['lastcount'] = count
#             return  # machine count rolled over or is not running
#
#         if entry['lastcount'] == 0:  # first time through...
#             entry['lastcount'] = count
#             logger.info(f'First pass through on machine {machine}')
#
#         if count > entry['lastcount']:
#             for part_count_entry in range(entry['lastcount'] + 1, count + 1):
#                 create_part_count_entry(entry, part_count_entry, config)
#                 logger.info(f'Creating entry for: {machine} - {part_count_entry} ')
#             entry['lastcount'] = count
#
#         # set the next read timestamp
#         entry['nextread'] += frequency


# def read_modbus_counter(entry):
#     c = ModbusClient(host=entry['processor_ip'], auto_open=True, auto_close=True)
#     regs = c.read_holding_registers(entry['register'], 2)
#     return regs[0] + (regs[1] * 65536)


# def read_pylogix_counter(counter_entry):
#     with PLC() as comm:
#         comm.IPAddress = counter_entry['processor_ip']
#         comm.ProcessorSlot = counter_entry['processor_slot']
#
#         tag = counter_entry['tag']
#         part_count = comm.Read(tag)
#
#         if part_count.Status != 'Success':
#             logger.error(f'Failed to read: {part_count} : {tag}')
#             return -1
#
#         logger.debug(f'Read pylogix counter:{part_count}, tag:{counter_entry["tag"]}')
#
#     return part_count.Value



@logger.catch()
def main():
    devices = process_config()
    while True:
        for device in devices:
            device.poll_tags()


if __name__ == "__main__":
    main()
