import unittest
from unittest.mock import patch

from pylogix.lgx_response import Response

from prodmon.plc_collect.main import read_pylogix_counter


class ReadPylogixCounterTestSuit(unittest.TestCase):

    def setUp(self):
        self.counter_entry = {
            # type = counter|value
            'type': 'pylogix_counter',
            # processor_ip is the controller's ip address
            'processor_ip': '127.0.0.1',
            # processor_slot is the controller's slot
            'processor_slot': 3,
            # tag is the PLC tag to read
            'tag': 'Program:Production.ProductionData.DailyCounts.DailyTotal',
            # tag containing what part type is currently running
            'Part_Type_Tag': 'Line.PartType',
            # map values in above to a string to write in the part type db colum
            'Part_Type_Map': {'1': '50-4865', '2': '50-5081'},
            # how often to try to read the tag in seconds
            'frequency': .5,
            # database table to write to
            'table': 'GFxPRoduction',
            # Machine is written into the machine colum in the database table
            'Machine': '1617',
            # used internally to track the readings
            'nextread': 0,  # timestamp of the next reading
            'lastcount': 0,  # last counter value
            'lastread': 0  # timestamp of the last read
        }
        self.test_config = {
            'minimum_cycle': 1,
            'tags': [self.counter_entry]
        }

    @patch("prodmon.plc_collect.main.part_count_entry")
    @patch("prodmon.plc_collect.main.PLC.Read")
    def test_first_pass_through(self, mock_read_pylogix_counter, mock_part_count_entry):
        """
        Tests first pass behaviour
        Should create one entry

        """
        LAST_PART_COUNT = 0
        PART_COUNT = 250
        PART_TYPE = '1'

        self.test_config['tags'][0]['lastcount'] = LAST_PART_COUNT
        self.test_config['tags'][0]['type'] = 'pylogix_counter'

        part_count_res = Response(
            tag_name=self.test_config['tags'][0]['tag'], value=PART_COUNT, status='Success')
        part_type_res = Response(
            tag_name=self.test_config['tags'][0]['tag'], value=PART_TYPE, status='Success')

        mock_read_pylogix_counter.side_effect = [part_count_res, part_type_res]

        self.test_config['tags'][0]['lastread'] = 0

        read_pylogix_counter(self.test_config['tags'][0])

        self.assertEqual(self.test_config['tags'][0]['lastcount'], PART_COUNT)

        mock_part_count_entry.assert_called_once()

    @patch("prodmon.plc_collect.main.part_count_entry")
    @patch("prodmon.plc_collect.main.PLC.Read")
    def test_read_zero_part_count(self, mock_read_pylogix_counter, mock_part_count_entry):
        """
        Tests ignoring zero part count readings
        Call read twice with 0 as a response

        """
        LAST_PART_COUNT = 250
        PART_COUNT = 0
        PART_TYPE: str = '1'

        self.test_config['tags'][0]['lastcount'] = LAST_PART_COUNT
        self.test_config['tags'][0]['type'] = 'pylogix_counter'

        part_count_res = Response(
            tag_name=self.test_config['tags'][0]['tag'], value=PART_COUNT, status='Success')
        part_type_res = Response(
            tag_name=self.test_config['tags'][0]['tag'], value=PART_TYPE, status='Success')

        mock_read_pylogix_counter.side_effect = [part_count_res, part_type_res, part_count_res, part_type_res]

        read_pylogix_counter(self.test_config['tags'][0])
        read_pylogix_counter(self.test_config['tags'][0])

        self.assertEqual(self.test_config['tags'][0]['lastcount'], PART_COUNT)

        mock_part_count_entry.assert_not_called()


if __name__ == '__main__':
    unittest.main()
