"""
Created on 16 Nov 2022

@author: Rogier van Staveren
"""

import logging
import time
import unittest

from xyscreens import XYScreens

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG
)


serial_port = "/dev/tty.usbserial-110"


class TestXYScreens(unittest.TestCase):
    def test_constructor(self):
        screen = XYScreens(serial_port)
        self.assertIsNotNone(screen)

    def test_constructor2(self):
        screen = XYScreens(serial_port, 60, 60)
        self.assertIsNotNone(screen)

    def test_constructor3(self):
        screen = XYScreens(serial_port, 60, 60, 100.0)
        self.assertIsNotNone(screen)

    def test_constructor_up(self):
        screen = XYScreens(serial_port, position=0.0)
        self.assertIs(XYScreens.STATE_UP, screen.state())
        self.assertIs(0.0, screen.position())

    def test_constructor_down(self):
        screen = XYScreens(serial_port, position=100.0)
        self.assertIs(XYScreens.STATE_DOWN, screen.state())
        self.assertIs(100.0, screen.position())

    def test_constructor_stopped(self):
        screen = XYScreens(serial_port, position=50.0)
        self.assertIs(XYScreens.STATE_STOPPED, screen.state())
        self.assertIs(50.0, screen.position())

    def test_constructor_negative_position(self):
        self.assertRaises(AssertionError, XYScreens, serial_port, position=-0.00001)

    def test_constructor_toolarge_position(self):
        self.assertRaises(AssertionError, XYScreens, serial_port, position=100.00001)

    def test_down(self):
        screen = XYScreens(serial_port, 60, 60)
        self.assertTrue(screen.down())

    def test_up(self):
        screen = XYScreens(serial_port, 60, 60, 100)
        self.assertTrue(screen.up())

    def test_stop(self):
        screen = XYScreens(serial_port, 60, 60)
        screen.down()
        time.sleep(1)
        self.assertTrue(screen.stop())

    def test_state_up(self):
        screen = XYScreens(serial_port, 10, 10, 100)
        screen.up()
        time.sleep(10)
        self.assertIs(XYScreens.STATE_UP, screen.state())

    def test_state_closing(self):
        screen = XYScreens(serial_port, 60, 60, 100)
        screen.up()
        self.assertIs(XYScreens.STATE_UPWARD, screen.state())

    def test_state_stopped(self):
        screen = XYScreens(serial_port, 10, 10)
        screen.down()
        time.sleep(5)
        screen.stop()
        self.assertIs(XYScreens.STATE_STOPPED, screen.state())

    def test_state_downward(self):
        screen = XYScreens(serial_port, 10, 10)
        screen.down()
        self.assertIs(XYScreens.STATE_DOWNWARD, screen.state())

    def test_state_down(self):
        screen = XYScreens(serial_port, 10, 10)
        screen.down()
        time.sleep(10)
        self.assertIs(XYScreens.STATE_DOWN, screen.state())

    def test_position_up(self):
        screen = XYScreens(serial_port, 10, 10, 100)
        screen.up()
        time.sleep(10)
        self.assertEquals(0.0, screen.position())

    def test_position_down(self):
        screen = XYScreens(serial_port, 10, 10)
        screen.down()
        time.sleep(10)
        self.assertEquals(100.0, screen.position())

    def test_position_halfway(self):
        screen = XYScreens(serial_port, 10, 10)
        screen.down()
        time.sleep(5)
        self.assertAlmostEqual(50.0, screen.position(), delta=0.1)

    def test_change_direction_down(self):
        screen = XYScreens(serial_port, 10, 10, 100)
        screen.up()
        time.sleep(5)
        screen.down()
        self.assertIs(XYScreens.STATE_DOWNWARD, screen.state())

    def test_change_direction_up(self):
        screen = XYScreens(serial_port, 10, 10)
        screen.down()
        time.sleep(5)
        screen.up()
        self.assertIs(XYScreens.STATE_UPWARD, screen.state())

    def test_set_position_up(self):
        screen = XYScreens(serial_port)
        screen.set_position(0.0)
        self.assertEqual(0.0, screen.position())
        self.assertIs(XYScreens.STATE_UP, screen.state())

    def test_set_position_down(self):
        screen = XYScreens(serial_port)
        screen.set_position(100.0)
        self.assertEqual(100.0, screen.position())
        self.assertIs(XYScreens.STATE_DOWN, screen.state())

    def test_set_position_halfway(self):
        screen = XYScreens(serial_port)
        screen.set_position(50.0)
        self.assertAlmostEqual(50.0, screen.position())
        self.assertIs(XYScreens.STATE_STOPPED, screen.state())


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testConstructor']
    unittest.main()
