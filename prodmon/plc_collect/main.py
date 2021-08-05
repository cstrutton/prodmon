import os
import time

from pylogix import PLC
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import word_list_to_long

from prodmon.shared.configuration_file import get_config, config_default
from prodmon.shared.log_setup import get_logger

logger = get_logger()


def set_config_defaults(config):
    # Set default values for config keys
    config_default(config, 'sqldir', "./tempSQL/")
    config_default(config, 'minimum_cycle', .5)
    config_default(config, 'Part_Number', '')
    for tag in config['tags']:
        config_default(tag, 'nextread', 0)
        config_default(tag, 'lastvalue', 0)
        config_default(tag, 'lastread', 0)


def loop(config):
    minimum_cycle = config['minimum_cycle']

    for entry in config['tags']:

        # get current timestamp
        now = time.time()

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

        if entry['type'] == 'counter':
            count = None
            if entry['driver'] == 'pylogix':
                count = read_pylogix_tag(entry)
            elif entry['driver'] == 'modbus':
                count = read_modbus_holding(entry)
            if count:
                process_counter(entry, count, config)

        if entry['type'] == 'state':
            state = 'NoValue'
            if entry['driver'] == 'pylogix':
                state = read_pylogix_tag(entry)
                logger.info(f'State: {entry["tag"]}= {state}')
            elif entry['type'] == 'modbus':
                state = read_modbus_holding(entry)
            if state is not 'NoValue':
                process_state(entry, state, config)

        # set the next read timestamp
        entry['nextread'] = frequency + entry['lastread']


def process_state(entry, state, config):
    if (state != entry['lastvalue']) or entry['always']:
        create_state_entry(entry, state, config)
        entry['lastvalue'] = state
        logger.info(f'Process state:{state}, tag:{entry["tag"]}')


def create_state_entry(entry, state, config):
    timestamp = str(int(entry['lastread']))
    file_path = f'{config["sqldir"]}{timestamp}.sql'
    sql = state_entry_sql(entry, state)
    print(sql)
    write_sql_file(sql, file_path)


def state_entry_sql(entry, state):
    data_tag = entry.get('data_tag')
    table = entry.get('table')
    timestamp = time.time()

    sql = f'INSERT INTO {table} '
    sql += f'(timestamp, tag, value ) '
    sql += f'VALUES ("{timestamp}" ,"{data_tag}", "{state}");\n'
    return sql


def process_counter(entry, count, config):
    # adjust for Scale factor
    count = count * entry.get('Scale', 1)

    # deal with counter == 0 edge case
    if count == 0:
        entry['lastvalue'] = count
        return  # machine count rolled over or is not running

    if entry['lastvalue'] == 0:  # first time through...
        entry['lastvalue'] = count
        logger.info('First pass through')

    if count > entry['lastvalue']:
        for part_count_entry in range(entry['lastvalue'] + 1, count + 1):
            create_part_count_entry(entry, part_count_entry, config)
            logger.info(f'Creating entry for part#{part_count_entry}')
        entry['lastvalue'] = count


def read_modbus_holding(entry):
    c = ModbusClient(host=entry['processor_ip'], auto_open=True, auto_close=True, timeout=2)
    regs = c.read_holding_registers(entry['register'], entry['reg_size'])
    if regs:
        logger.debug(f'Read modbus register:{str(regs)}, register:{entry["register"]}, {entry["reg_size"]}')
        converted = word_list_to_long(regs, big_endian=False)
        return converted[0]
    else:  # regs will be None if there was an error
        logger.error(f'Failed to read modbus register:{entry["register"]}')
        return regs


def read_pylogix_tag(entry):
    with PLC() as comm:
        comm.IPAddress = entry['processor_ip']
        comm.ProcessorSlot = entry['processor_slot']

        tag = comm.Read(entry['tag'])

        if tag.Status != 'Success':
            logger.error('Failed to read ', tag)
            return None

        logger.debug(f'Read pylogix tag:{tag}, tag:{entry["tag"]}')

    return tag.Value


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

    # if os.environ.get("DEBUG", default=False):
    #     logger.add('templogs/prodmon-collect.log')
    # else:
    #     logger.add('/var/log/prodmon-collect.log', rotation="10 Mb")
    #

    collect_config = get_config('collect')

    set_config_defaults(collect_config)

    while True:
        loop(collect_config)


if __name__ == "__main__":
    main()
