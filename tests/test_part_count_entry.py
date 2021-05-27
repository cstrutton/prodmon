import unittest

from prodmon.plc_collect.main import part_count_entry_sql


class PartCountEntryTestSuit(unittest.TestCase):

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

        self.pylogix_test_config = {
            'sqldir': "./tempSQL/",
            'minimum_cycle': 1,
            'tags': [self.pylogix_entry]
        }

    def test_no_part_number_in_config(self):
        # create the counter entry
        counter_entry = self.pylogix_entry

        counter_entry['Part_Number'] = ''
        counter_entry['lastread'] = '1234567890'

        count = 1

        result = part_count_entry_sql(counter_entry, count)
        self.assertNotIn('Part', result)

    def test_with_part_number_in_config(self):
        # create the counter entry
        counter_entry = self.pylogix_entry

        counter_entry['Part_Number'] = 'TestPartNumber'
        counter_entry['lastread'] = '1234567890'

        count = 1

        result = part_count_entry_sql(counter_entry, count)
        self.assertIn('Part', result)
        self.assertIn(counter_entry['Part_Number'], result)
