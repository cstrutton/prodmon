import time

from pylogix import PLC
from prodmon.shared.configuration_file import get_config, config_default

# VERBOSE = False
# DEBUG = False


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

        if entry['type'] == 'pylogix_counter':
            read_pylogix_counter(entry)

        # set the next read timestamp
        entry['nextread'] += frequency


def read_pylogix_counter(counter_entry):
    with PLC() as comm:
        comm.IPAddress = counter_entry['processor_ip']
        comm.ProcessorSlot = counter_entry['processor_slot']

        # read the tag
        part_count = comm.Read(counter_entry['tag'])
        # if DEBUG:
        #     print(part_count.TagName, part_count.Value, part_count.Status)
        if part_count.Status != 'Success':
            # print('failed to read ', part_count)
            return

        # read the Part Type Tag
        part_type = comm.Read(counter_entry['Part_Type_Tag'])
        if part_type.TagName == 'NA':
            part_type.Value = '0'
            part_type.Status = 'Success'
        if part_type.Status != 'Success':
            # print('failed to read ', part_type)
            return
        # if DEBUG:
        #     print(part_type)

        if part_count.Value == 0:
            counter_entry['lastcount'] = part_count.Value
            return  # machine count rolled over or is not running

        if counter_entry['lastcount'] == 0:  # first time through...
            counter_entry['lastcount'] = part_count.Value - 1  # only count 1 part
            # if VERBOSE:
            #     print('first time through, lastcount=', counter_entry['lastcount'])

        if part_count.Value > counter_entry['lastcount']:
            for entry in range(counter_entry['lastcount'] + 1, part_count.Value + 1):
                part_count_entry(
                    table=counter_entry['table'],
                    timestamp=counter_entry['lastread'],
                    count=entry,
                    machine=counter_entry['Machine'],
                    parttype=counter_entry['Part_Type_Map'][str(
                        part_type.Value)]
                )
            counter_entry['lastcount'] = part_count.Value


def part_count_entry(table, timestamp, count, machine, parttype):
    # if VERBOSE:
    #     print('{} made a {} ({})'.format(machine, parttype, count))

    file_path = '{}{}.sql'.format(
        config['sqldir'], str(int(timestamp)))

    with open(file_path, "a+") as file:
        sql = ('INSERT INTO {} '
               '(Machine, Part, PerpetualCount, Timestamp) '
               'VALUES ("{}", "{}" ,{} ,{});\n'.format(
                table, machine, parttype, count, timestamp))
        file.write(sql)


if __name__ == "__main__":

    post_config = get_config('collect')
    set_config_defaults()
    # if VERBOSE:
    #     print(config)

    while True:
        loop(post_config)
