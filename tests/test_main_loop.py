import time
import unittest
from unittest.mock import patch

from prodmon.plc_collect.main import loop


class MainLoopTestSuit(unittest.TestCase):
    """main loop test cases."""

    def setUp(self):
        self.counter_entry = {
            # type = counter|value
            'type': 'pylogix',
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

    @patch("prodmon.plc_collect.main.read_pylogix_counter")
    def test_polling_too_fast(self, mock_read_counter):
        """
        Tests Polling faster than the specified minimum cycle

        - try reading twice back to back (mocked read is almost instantainious)
        - should call read counter exactly one time
        """
        mock_read_counter.return_value = [1, 2]
        config = self.test_config
        config['minimum_cycle'] = 1
        config['tags'][0]['type'] = 'pylogix'

        loop(config)
        loop(config)

        mock_read_counter.assert_called_once()

    @patch("prodmon.plc_collect.main.read_pylogix_counter")
    def test_polling(self, mock_read_counter):
        """
        Tests that the Minimum Cycle is observed

        - try looping 3 times waiting for half minimum cycle between each
        - should call read counter exactly 2 times
        """
        mock_read_counter.return_value = [1, 2]
        config = self.test_config
        minimum_cycle = 1
        config['minimum_cycle'] = minimum_cycle
        config['tags'][0]['type'] = 'pylogix'

        loop(config)

        time.sleep(minimum_cycle / 2)

        loop(config)

        time.sleep(minimum_cycle / 2)

        loop(config)

        self.assertEqual(mock_read_counter.call_count, 2)

    @patch("prodmon.plc_collect.main.read_pylogix_counter")
    def test_first_pass_through(self, mock_read_counter):
        """
        Tests first pass behaviour

        """
        mock_read_counter.return_value = 1

        config = self.test_config
        minimum_cycle = 1
        config['minimum_cycle'] = minimum_cycle
        config['tags'][0]['type'] = 'pylogix'

        config['tags'][0]['nextread'] = 0

        loop(config)

        self.assertNotEqual(config['tags'][0]['nextread'], 0)

    @patch("prodmon.plc_collect.main.create_part_count_entry")
    @patch("prodmon.plc_collect.main.read_pylogix_counter")
    def test_read_zero_part_count(self, mock_read_pylogix_counter, mock_part_count_entry):
        """
        Tests ignoring zero part count readings
        Call read twice with 0 as a response

        """

        mock_read_pylogix_counter.side_effect = [0, 0]
        LAST_PART_COUNT = 250
        PART_COUNT = 0

        config = self.test_config

        config['tags'][0]['lastcount'] = LAST_PART_COUNT

        loop(config)
        loop(config)

        self.assertEqual(config['tags'][0]['lastcount'], PART_COUNT)

        mock_part_count_entry.assert_not_called()

    # create_part_count_entry(counter_entry, count, config):
    @patch("prodmon.plc_collect.main.create_part_count_entry")
    @patch("prodmon.plc_collect.main.read_pylogix_counter")
    def test_read_with_scaling(self, mock_read_pylogix_counter, mock_part_count_entry):
        """
        Tests reading with scaling
        Read one part with a scale of 2
        Should call part_count_entry 2 times
        """
        TEST_SCALE = 2
        LAST_PART_COUNT = 250
        PART_COUNT = LAST_PART_COUNT + 1
        mock_read_pylogix_counter.return_value = PART_COUNT

        config = self.test_config

        config['tags'][0]['lastcount'] = LAST_PART_COUNT * TEST_SCALE
        config['tags'][0]['Scale'] = TEST_SCALE

        loop(config)

        self.assertEqual(mock_part_count_entry.call_count, TEST_SCALE)



if __name__ == '__main__':
    unittest.main()
