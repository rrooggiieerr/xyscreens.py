"""Synchronous unit test for the XYScreens library"""

# pylint: disable=missing-function-docstring
# pylint: disable=too-many-public-methods

import json
import time
from pathlib import Path
from typing import override
from unittest import TestCase

from xyscreens import XYScreens, XYScreensState

_SETTINGS_JSON = Path(__file__).with_name("settings.json").absolute()


class TestXYScreens(TestCase):
    """Synchronous unit test for the XYScreens library"""

    _url: str
    _address: bytes

    @override
    def setUp(self):
        with open(_SETTINGS_JSON, encoding="utf8") as settings_file:
            settings = json.load(settings_file)
            self._url = settings.get("url")
            self._address = bytes.fromhex(settings.get("address"))

    def test_constructor(self):
        screen = XYScreens(self._url, self._address, 60)
        self.assertIsNotNone(screen)

    def test_constructor2(self):
        screen = XYScreens(self._url, self._address, 60, 60)
        self.assertIsNotNone(screen)

    def test_constructor3(self):
        screen = XYScreens(self._url, self._address, 60, 60, 100.0)
        self.assertIsNotNone(screen)

    def test_constructor_up(self):
        screen = XYScreens(self._url, self._address, 60, position=0.0)
        self.assertIs(XYScreensState.UP, screen.state())
        self.assertIs(0.0, screen.position())

    def test_constructor_down(self):
        screen = XYScreens(self._url, self._address, 60, position=100.0)
        self.assertIs(XYScreensState.DOWN, screen.state())
        self.assertIs(100.0, screen.position())

    def test_constructor_stopped(self):
        screen = XYScreens(self._url, self._address, 60, position=50.0)
        self.assertIs(XYScreensState.STOPPED, screen.state())
        self.assertIs(50.0, screen.position())

    def test_constructor_negative_position(self):
        self.assertRaises(
            AssertionError,
            XYScreens,
            self._url,
            self._address,
            60,
            position=-0.00001,
        )

    def test_constructor_toolarge_position(self):
        self.assertRaises(
            AssertionError,
            XYScreens,
            self._url,
            self._address,
            60,
            position=100.00001,
        )

    def test_test_connection(self):
        screen = XYScreens(self._url, self._address, 60, 60)
        self.assertTrue(screen.test_connection())

    def test_test_connection_non_existing_port(self):
        screen = XYScreens("/dev/cu.non_existing_port", self._address, 60, 60)
        self.assertFalse(screen.test_connection())

    def test_test_connection_socket_non_existing_ip(self):
        screen = XYScreens("socket://0.0.0.0:23", self._address, 5, 5)
        self.assertFalse(screen.test_connection())

    def test_test_connection_esphome_non_existing_ip(self):
        screen = XYScreens(
            "esphome://0.0.0.0:6053/?port_name=UART1", self._address, 5, 5
        )
        self.assertFalse(screen.test_connection())

    def test_test_connection_socket_non_existing_host(self):
        screen = XYScreens("socket://non_existing_host:23", self._address, 5, 5)
        self.assertFalse(screen.test_connection())

    def test_test_connection_esphome_non_existing_host(self):
        screen = XYScreens(
            "esphome://non_existing_host:6053/?port_name=UART1", self._address, 5, 5
        )
        self.assertFalse(screen.test_connection())

    def test_down(self):
        screen = XYScreens(self._url, self._address, 60, 60)
        self.assertTrue(screen.down())

    def test_up(self):
        screen = XYScreens(self._url, self._address, 60, 60, 100)
        self.assertTrue(screen.up())

    def test_stop(self):
        screen = XYScreens(self._url, self._address, 60, 60)
        screen.down()
        time.sleep(1)
        self.assertTrue(screen.stop())

    def test_state_up(self):
        screen = XYScreens(self._url, self._address, 10, 10, 100)
        screen.up()
        time.sleep(10)
        self.assertIs(XYScreensState.UP, screen.state())

    def test_state_closing(self):
        screen = XYScreens(self._url, self._address, 60, 60, 100)
        screen.up()
        self.assertIs(XYScreensState.UPWARD, screen.state())

    def test_state_stopped(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        screen.down()
        time.sleep(5)
        screen.stop()
        self.assertIs(XYScreensState.STOPPED, screen.state())

    def test_state_downward(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        screen.down()
        self.assertIs(XYScreensState.DOWNWARD, screen.state())

    def test_state_down(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        screen.down()
        time.sleep(10)
        self.assertIs(XYScreensState.DOWN, screen.state())

    def test_position_up(self):
        screen = XYScreens(self._url, self._address, 10, 10, 100)
        screen.up()
        time.sleep(10)
        self.assertEqual(0.0, screen.position())

    def test_position_down(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        screen.down()
        time.sleep(10)
        self.assertEqual(100.0, screen.position())

    def test_position_halfway(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        screen.down()
        time.sleep(5)
        self.assertAlmostEqual(50.0, screen.position(), delta=1)

    def test_change_direction_down(self):
        screen = XYScreens(self._url, self._address, 10, 10, 100)
        screen.up()
        time.sleep(5)
        screen.down()
        state, position = screen.update_status()
        self.assertIs(XYScreensState.DOWNWARD, state)
        self.assertAlmostEqual(50.0, position, delta=1)

    def test_change_direction_up(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        screen.down()
        time.sleep(5)
        screen.up()
        state, position = screen.update_status()
        self.assertIs(XYScreensState.UPWARD, state)
        self.assertAlmostEqual(50.0, position, delta=1)

    def test_set_position_downward(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        screen.set_position(50.0)
        state, position = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertAlmostEqual(50.0, position, delta=1)

    def test_set_position_upward(self):
        screen = XYScreens(self._url, self._address, 10, 10, 100.0)
        screen.set_position(50.0)
        state, position = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertAlmostEqual(50.0, position, delta=1)

    def test_restore_position_up(self):
        screen = XYScreens(self._url, self._address, 60)
        screen.restore_position(0.0)
        state, position = screen.update_status()
        self.assertIs(XYScreensState.UP, state)
        self.assertEqual(0.0, position)

    def test_restore_position_down(self):
        screen = XYScreens(self._url, self._address, 60)
        screen.restore_position(100.0)
        state, position = screen.update_status()
        self.assertIs(XYScreensState.DOWN, state)
        self.assertEqual(100.0, position)

    def test_restore_position_halfway(self):
        screen = XYScreens(self._url, self._address, 60)
        screen.restore_position(50.0)
        state, position = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertEqual(50.0, position)
