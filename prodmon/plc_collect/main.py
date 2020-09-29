import time
from loguru import logger

from pylogix import PLC
from prodmon.shared.configuration_file import get_config, config_default


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
        logger.debug(part_count)

        if counter_entry['type'] == 'pylogix_typed_counter':
            # read the Part Type Tag
            part_type_res = comm.Read(counter_entry['Part_Type_Tag'])
            logger.debug(part_type_res)
            if part_type_res.Status != 'Success':
                logger.error('Failed to read ', part_type_res)
                return
            part_type = counter_entry['Part_Type_Map'][str(part_type_res.Value)]

        elif counter_entry['type'] == 'pylogix_simple_counter':
            part_type = counter_entry['part_type']

        if part_count.Value == 0:
            counter_entry['lastcount'] = part_count.Value
            return  # machine count rolled over or is not running

        if counter_entry['lastcount'] == 0:  # first time through...
            counter_entry['lastcount'] = part_count.Value - 1  # only count 1 part

        if part_count.Value > counter_entry['lastcount']:
            for entry in range(counter_entry['lastcount'] + 1, part_count.Value + 1):
                part_count_entry(
                    counter_entry=counter_entry,
                    count=entry,
                    parttype=part_type,
                    config=config
                )
            counter_entry['lastcount'] = part_count.Value


def part_count_entry(counter_entry, count, parttype, config):
    # if VERBOSE:
    #     print('{} made a {} ({})'.format(machine, parttype, count))

    table = counter_entry['table']
    timestamp = counter_entry['lastread'],
    machine = counter_entry['Machine'],

    file_path = '{}{}.sql'.format(
        config['sqldir'], str(int(timestamp)))

    with open(file_path, "a+") as file:
        sql = ('INSERT INTO {} '
               '(Machine, Part, PerpetualCount, Timestamp) '
               'VALUES ("{}", "{}" ,{} ,{});\n'.format(
                table, machine, parttype, count, timestamp))
        file.write(sql)


@logger.catch()
def main():
    collect_config = get_config('collect')
    set_config_defaults(collect_config)

    while True:
        loop(collect_config)


if __name__ == "__main__":
    logger.add('/var/log/prodmon-collect.log', rotation="10 Mb")
    main()
