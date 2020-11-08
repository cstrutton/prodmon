import os
import time

from pylogix import PLC
from prodmon.shared.configuration_file import get_config, config_default
from prodmon.shared.log_setup import get_logger

logger = get_logger()


def set_config_defaults(config):
    # Set default values for config keys
    config_default(config, 'sqldir', "./tempSQL")
    config_default(config, 'minimum_cycle', .5)


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

        if entry['type'] == 'pylogix_typed_counter':
            read_pylogix_counter(entry, config)

        if entry['type'] == 'pylogix_simple_counter':
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

        if counter_entry['type'] == 'pylogix_typed_counter':
            # read the Part Type Tag
            part_type_res = comm.Read(counter_entry['Part_Type_Tag'])
            if part_type_res.Status != 'Success':
                logger.error('Failed to read ', part_type_res)
                return
            part_type = counter_entry['Part_Type_Map'][str(part_type_res.Value)]

        elif counter_entry['type'] == 'pylogix_simple_counter':
            part_type = counter_entry['Part_Number']

        logger.debug(f'Read counter:{part_count}, type:{part_type}')

        count = part_count.Value * counter_entry.get('scale', 1)

        if count == 0:
            counter_entry['lastcount'] = count
            return  # machine count rolled over or is not running

        if counter_entry['lastcount'] == 0:  # first time through...
            counter_entry['lastcount'] = count
            logger.info('First pass through')

        if count > counter_entry['lastcount']:
            for entry in range(counter_entry['lastcount'] + 1, count + 1):

                part_count_entry(
                    counter_entry=counter_entry,
                    count=entry,
                    parttype=part_type,
                    config=config
                )
                logger.info(f'Creating entry for part#{entry}')
            counter_entry['lastcount'] = count


def part_count_entry(counter_entry, count, parttype, config):

    table = counter_entry['table']
    timestamp = counter_entry['lastread']
    machine = counter_entry['Machine']
    file_path = f'{config["sqldir"]}{str(int(timestamp))}.sql'

    with open(file_path, "a+") as file:
        sql = (f'INSERT INTO {table} (Machine, Part, PerpetualCount, Timestamp) '
               f'VALUES ("{machine}" ,"{parttype}" ,{count}, {timestamp});\n')
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
