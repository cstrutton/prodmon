import unittest
from unittest.mock import patch, mock_open

from prodmon.plc_collect.main import part_count_entry


class ReadPylogixCounterTestSuit(unittest.TestCase):

    def setUp(self):
        self.counter_entry = {
            # processor_ip is the controller's ip address
            'processor_ip': '127.0.0.1',
            # processor_slot is the controller's slot
            'processor_slot': 3,
            # tag is the PLC tag to read
            'tag': 'Program:Production.ProductionData.DailyCounts.DailyTotal',
            # how often to try to read the tag in seconds
            'frequency': .5,
            # database table to write to
            'table': 'Test Entry DB Table',
            # Machine is written into the machine column in the database table
            'Machine': 'Test Entry Machine',
            # used internally to track the readings
            'nextread': 0,  # timestamp of the next reading
            'lastcount': 0,  # last counter value
            'lastread': 0  # timestamp of the last read
        }
        self.pylogix_entry = {
            **self.counter_entry,
            'type': 'pylogix',
            'Part_Number': 'SimplePartType',
            'Scale': 1
        }

        self.test_config = {
            'sqldir': "./tempSQL/",
            'minimum_cycle': 1,
            'tags': []
        }

    def test_no_part_number_in_config(self):
        # create the counter entry
        config = self.test_config
        config['tags'] = [self.pylogix_entry]

        config['tags'][0]['Part_Number'] = ''
        config['tags'][0]['lastread'] = '1234567890'

        counter_entry = config['tags'][0]

        count = 1
        part_number = counter_entry['Part_Number']

        with patch('prodmon.plc_collect.main.open', mock_open()) as mocked_file:
            # call part_count_entry
            part_count_entry(counter_entry, count, part_number, config)

            table = counter_entry['table']
            timestamp = counter_entry['lastread']
            machine = counter_entry['Machine']

            sql = f'INSERT INTO {table} '
            sql += f'(Machine, '
            sql += f'PerpetualCount, Timestamp) '
            sql += f'VALUES ("{machine}" ,'
            sql += f',{count}, {timestamp});\n'

            # assert if write(content) was called from the file opened
            # in another words, assert if the specific content was written in file
            mocked_file().write.assert_called_once_with(sql)
