import os
import time

from pylogix import PLC
from prodmon.shared.configuration_file import get_config, config_default
from prodmon.shared.log_setup import get_logger

logger = get_logger()


def set_config_defaults(config):
    # Set default values for config keys
    config_default(config, 'sqldir', "./tempSQL/")
    config_default(config, 'minimum_cycle', .5)
    config_default(config, 'Part_Number', '')
    config_default(config, 'nextread', 0)
    config_default(config, 'lastcount', 0)
    config_default(config, 'lastread', 0)


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

        if entry['type'] == 'pylogix':
            read_pylogix_counter(entry, config)

        # set the next read timestamp
        entry['nextread'] += frequency


def read_pylogix_counter(counter_entry, config):
    with PLC() as comm:
        comm.IPAddress = counter_entry['processor_ip']
        comm.ProcessorSlot = counter_entry['processor_slot']

        part_count = comm.Read(counter_entry['tag'])
        if part_count.Status != 'Success':
            logger.error('Failed to read ', part_count)
            return

        logger.debug(f'Read counter:{part_count}, tag:{counter_entry["tag"]}')

        count = part_count.Value * counter_entry.get('Scale', 1)

        if count == 0:
            counter_entry['lastcount'] = count
            return  # machine count rolled over or is not running

        if counter_entry['lastcount'] == 0:  # first time through...
            counter_entry['lastcount'] = count
            logger.info('First pass through')

        if count > counter_entry['lastcount']:
            for part_count_entry in range(counter_entry['lastcount'] + 1, count + 1):
                create_part_count_entry(counter_entry, part_count_entry, config)
                logger.info(f'Creating entry for part#{part_count_entry}')
            counter_entry['lastcount'] = count


def create_part_count_entry(counter_entry, count, config):
    timestamp = str(int(counter_entry['lastread']))
    file_path = f'{config["sqldir"]}{timestamp}.sql'
    sql = part_count_entry_sql(counter_entry, count)
    write_sql_file(sql, file_path)


def part_count_entry_sql(counter_entry, count):
    part_number = counter_entry.get('Part_Number')
    table = counter_entry['table']
    timestamp = counter_entry['lastread']
    machine = counter_entry['Machine']

    sql = f'INSERT INTO {table} '
    sql += f'(Machine, '
    if part_number:
        sql += f'Part, '
    sql += f'PerpetualCount, Timestamp) '
    sql += f'VALUES ("{machine}" ,'
    if part_number:
        sql += f'"{part_number}" '
    sql += f',{count}, {timestamp});\n'

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
