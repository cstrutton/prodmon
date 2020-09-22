import time
import unittest
from unittest.mock import patch

from prodmon.plc_collect.main import loop


class MainLoopTestSuit(unittest.TestCase):
    """main loop test cases."""

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

    @patch("prodmon.plc_collect.main.read_pylogix_counter")
    def test_polling_too_fast(self, mock_read_counter):
        """
        Tests Polling faster than the specified minimum cycle

        - try reading twice back to back (mocked read is almost instantainious)
        - should call read counter exactly one time
        """
        config = self.test_config
        config['minimum_cycle'] = 1
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
        loop(self.test_config)

        time.sleep(self.test_config['minimum_cycle'] / 2)

        loop(self.test_config)

        time.sleep(self.test_config['minimum_cycle'] / 2)

        loop(self.test_config)

        self.assertEqual(mock_read_counter.call_count, 2)

    @patch("prodmon.plc_collect.main.read_pylogix_counter")
    def test_first_pass_through(self, mock_read_counter):
        """
        Tests first pass behaviour

        """
        self.test_config['tags'][0]['nextread'] = 0

        loop(self.test_config)

        self.assertNotEqual(self.test_config['tags'][0]['nextread'], 0)


if __name__ == '__main__':
    unittest.main()
