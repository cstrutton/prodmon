import unittest
from unittest.mock import patch

from pylogix.lgx_response import Response

from prodmon.plc_collect.main import read_pylogix_counter


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
        self.typed_counter_entry = {
            **self.counter_entry,
            'type': 'pylogix_typed_counter',
            'Part_Type_Tag': 'Line.PartType',
            'Part_Type_Map': {'1': 'PartType1', '2': 'PartType2'}
        }
        self.simple_counter_entry = {
            **self.counter_entry,
            'type': 'pylogix_simple_counter',
            'Part_Number': 'SimplePartType',
            'Scale': 1
        }

        self.test_config = {
            'minimum_cycle': 1,
            'tags': []
        }

    @patch("prodmon.plc_collect.main.part_count_entry")
    @patch("prodmon.plc_collect.main.PLC.Read")
    def test_first_pass_through(self, mock_pylogix_Read, mock_part_count_entry):
        """
        Tests first pass behaviour
        Should create one entry

        """
        LAST_PART_COUNT = 0
        PART_COUNT = 250
        PART_TYPE = '1'

        config = self.test_config
        config['tags'] = [self.typed_counter_entry]

        config['tags'][0]['lastcount'] = LAST_PART_COUNT

        part_count_res = Response(
            tag_name=config['tags'][0]['tag'], value=PART_COUNT, status='Success')
        part_type_res = Response(
            tag_name=config['tags'][0]['tag'], value=PART_TYPE, status='Success')

        mock_pylogix_Read.side_effect = [part_count_res, part_type_res]

        config['tags'][0]['lastread'] = 0

        read_pylogix_counter(config['tags'][0], config)

        self.assertEqual(config['tags'][0]['lastcount'], PART_COUNT)

        mock_part_count_entry.assert_not_called()

    @patch("prodmon.plc_collect.main.part_count_entry")
    @patch("prodmon.plc_collect.main.PLC.Read")
    def test_read_zero_part_count(self, mock_pylogix_Read, mock_part_count_entry):
        """
        Tests ignoring zero part count readings
        Call read twice with 0 as a response

        """
        LAST_PART_COUNT = 250
        PART_COUNT = 0
        PART_TYPE: str = '1'

        config = self.test_config
        config['tags'] = [self.typed_counter_entry]

        config['tags'][0]['lastcount'] = LAST_PART_COUNT

        part_count_res = Response(
            tag_name=config['tags'][0]['tag'], value=PART_COUNT, status='Success')
        part_type_res = Response(
            tag_name=config['tags'][0]['tag'], value=PART_TYPE, status='Success')

        mock_pylogix_Read.side_effect = [part_count_res, part_type_res, part_count_res, part_type_res]

        read_pylogix_counter(config['tags'][0], config)
        read_pylogix_counter(config['tags'][0], config)

        self.assertEqual(config['tags'][0]['lastcount'], PART_COUNT)

        mock_part_count_entry.assert_not_called()

    @patch("prodmon.plc_collect.main.part_count_entry")
    @patch("prodmon.plc_collect.main.PLC.Read")
    def test_read_with_scaling(self, mock_pylogix_Read, mock_part_count_entry):
        """
        Tests reading with scaling
        Read one part with a scale of 2
        Should call part_count_entry 2 times
        """
        TEST_SCALE = 2
        LAST_PART_COUNT = 250
        PART_COUNT = LAST_PART_COUNT + 1

        config = self.test_config
        config['tags'] = [self.simple_counter_entry]

        config['tags'][0]['lastcount'] = LAST_PART_COUNT * TEST_SCALE
        config['tags'][0]['Scale'] = TEST_SCALE

        part_count_res = Response(
            tag_name=config['tags'][0]['tag'], value=PART_COUNT, status='Success')

        mock_pylogix_Read.side_effect = [part_count_res]

        read_pylogix_counter(config['tags'][0], config)

        self.assertEqual(mock_part_count_entry.call_count, TEST_SCALE)


if __name__ == '__main__':
    unittest.main()
