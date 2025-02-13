"""
Created on 16 Nov 2022

@author: Rogier van Staveren
"""

# pylint: disable=missing-function-docstring
# pylint: disable=too-many-public-methods

import asyncio
import json
import time
import unittest
from unittest.mock import Mock

from xyscreens import XYScreens, XYScreensState

_SETTINGS_JSON = "settings.json"


class TestXYScreens(unittest.IsolatedAsyncioTestCase):
    """Unit test for the XYScreens library"""

    serial_port: str = None
    address: bytes = None

    async def asyncSetUp(self):
        with open(_SETTINGS_JSON, encoding="utf8") as settings_file:
            settings = json.load(settings_file)
            self.serial_port = settings.get("serial_port")
            self.address = bytes.fromhex(settings.get("address"))

    def test_constructor(self):
        screen = XYScreens(self.serial_port, self.address, 60)
        self.assertIsNotNone(screen)

    def test_constructor2(self):
        screen = XYScreens(self.serial_port, self.address, 60, 60)
        self.assertIsNotNone(screen)

    def test_constructor3(self):
        screen = XYScreens(self.serial_port, self.address, 60, 60, 100.0)
        self.assertIsNotNone(screen)

    def test_constructor_up(self):
        screen = XYScreens(self.serial_port, self.address, 60, position=0.0)
        self.assertIs(XYScreensState.UP, screen.state())
        self.assertIs(0.0, screen.position())

    def test_constructor_down(self):
        screen = XYScreens(self.serial_port, self.address, 60, position=100.0)
        self.assertIs(XYScreensState.DOWN, screen.state())
        self.assertIs(100.0, screen.position())

    def test_constructor_stopped(self):
        screen = XYScreens(self.serial_port, self.address, 60, position=50.0)
        self.assertIs(XYScreensState.STOPPED, screen.state())
        self.assertIs(50.0, screen.position())

    def test_constructor_negative_position(self):
        self.assertRaises(
            AssertionError, XYScreens, self.serial_port, self.address, 60, position=-0.00001
        )

    def test_constructor_toolarge_position(self):
        self.assertRaises(
            AssertionError, XYScreens, self.serial_port, self.address, 60, position=100.00001
        )

    def test_down(self):
        screen = XYScreens(self.serial_port, self.address, 60, 60)
        self.assertTrue(screen.down())

    def test_up(self):
        screen = XYScreens(self.serial_port, self.address, 60, 60, 100)
        self.assertTrue(screen.up())

    def test_stop(self):
        screen = XYScreens(self.serial_port, self.address, 60, 60)
        screen.down()
        time.sleep(1)
        self.assertTrue(screen.stop())

    def test_state_up(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10, 100)
        screen.up()
        time.sleep(10)
        self.assertIs(XYScreensState.UP, screen.state())

    def test_state_closing(self):
        screen = XYScreens(self.serial_port, self.address, 60, 60, 100)
        screen.up()
        self.assertIs(XYScreensState.UPWARD, screen.state())

    def test_state_stopped(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        screen.down()
        time.sleep(5)
        screen.stop()
        self.assertIs(XYScreensState.STOPPED, screen.state())

    def test_state_downward(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        screen.down()
        self.assertIs(XYScreensState.DOWNWARD, screen.state())

    def test_state_down(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        screen.down()
        time.sleep(10)
        self.assertIs(XYScreensState.DOWN, screen.state())

    def test_position_up(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10, 100)
        screen.up()
        time.sleep(10)
        self.assertEqual(0.0, screen.position())

    def test_position_down(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        screen.down()
        time.sleep(10)
        self.assertEqual(100.0, screen.position())

    def test_position_halfway(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        screen.down()
        time.sleep(5)
        self.assertAlmostEqual(50.0, screen.position(), delta=0.3)

    def test_change_direction_down(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10, 100)
        screen.up()
        time.sleep(5)
        screen.down()
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.DOWNWARD, state)
        self.assertAlmostEqual(50.0, position, delta=0.6)

    def test_change_direction_up(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        screen.down()
        time.sleep(5)
        screen.up()
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.UPWARD, state)
        self.assertAlmostEqual(50.0, position, delta=0.6)

    def test_set_position_downward(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        screen.set_position(50.0)
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertAlmostEqual(50.0, position, delta=0.3)

    def test_set_position_upward(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10, 100.0)
        screen.set_position(50.0)
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertAlmostEqual(50.0, position, delta=0.3)

    async def test_async_down(self):
        screen = XYScreens(self.serial_port, self.address, 5, 5)
        callback = Mock()
        screen.add_callback(callback)
        self.assertTrue(await screen.async_down())
        await asyncio.sleep(5.1)
        callback.assert_called_with(XYScreensState.DOWN, 100.0)

    async def test_async_up(self):
        screen = XYScreens(self.serial_port, self.address, 5, 5, 100)
        callback = Mock()
        screen.add_callback(callback)
        self.assertTrue(await screen.async_up())
        await asyncio.sleep(5.1)
        callback.assert_called_with(XYScreensState.UP, 0.0)

    async def test_async_stop(self):
        screen = XYScreens(self.serial_port, self.address, 60, 60)
        await screen.async_down()
        await asyncio.sleep(1)
        self.assertTrue(await screen.async_stop())

    async def test_async_state_up(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10, 100)
        await screen.async_up()
        await asyncio.sleep(10.1)
        self.assertIs(XYScreensState.UP, screen.state())

    async def test_async_state_closing(self):
        screen = XYScreens(self.serial_port, self.address, 60, 60, 100)
        await screen.async_up()
        self.assertIs(XYScreensState.UPWARD, screen.state())
        await screen.async_stop()

    async def test_async_state_stopped(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(5)
        await screen.async_stop()
        self.assertIs(XYScreensState.STOPPED, screen.state())

    async def test_async_state_downward(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        await screen.async_down()
        self.assertIs(XYScreensState.DOWNWARD, screen.state())
        await screen.async_stop()

    async def test_async_state_down(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(10.1)
        self.assertIs(XYScreensState.DOWN, screen.state())

    async def test_async_position_up(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10, 100)
        await screen.async_up()
        await asyncio.sleep(10.1)
        self.assertEqual(0.0, screen.position())

    async def test_async_position_down(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(10.1)
        self.assertEqual(100.0, screen.position())

    async def test_async_position_halfway(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(5)
        self.assertAlmostEqual(50.0, screen.position(), delta=0.3)
        await screen.async_stop()

    async def test_async_change_direction_down(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10, 100)
        await screen.async_up()
        await asyncio.sleep(5)
        await screen.async_down()
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.DOWNWARD, state)
        self.assertAlmostEqual(50.0, position, delta=0.3)
        await screen.async_stop()

    async def test_async_change_direction_up(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(5)
        await screen.async_up()
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.UPWARD, state)
        self.assertAlmostEqual(50.0, position, delta=0.3)
        await screen.async_stop()

    async def test_async_set_position_downward(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        await screen.async_set_position(50.0)
        await asyncio.sleep(5.1)
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertAlmostEqual(50.0, position, delta=0.3)

    async def test_async_set_position_upward(self):
        screen = XYScreens(self.serial_port, self.address, 10, 10, 100.0)
        await screen.async_set_position(50.0)
        await asyncio.sleep(5.1)
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertAlmostEqual(50.0, position, delta=0.3)

    async def test_async_set_position_stop(self):
        """Test stopping the screen while it is moving to a given position."""
        screen = XYScreens(self.serial_port, self.address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(5)
        await screen.async_stop()
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertAlmostEqual(50.0, position, delta=0.3)

    def test_restore_position_up(self):
        screen = XYScreens(self.serial_port, self.address, 60)
        screen.restore_position(0.0)
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.UP, state)
        self.assertEqual(0.0, position)

    def test_restore_position_down(self):
        screen = XYScreens(self.serial_port, self.address, 60)
        screen.restore_position(100.0)
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.DOWN, state)
        self.assertEqual(100.0, position)

    def test_restore_position_halfway(self):
        screen = XYScreens(self.serial_port, self.address, 60)
        screen.restore_position(50.0)
        (state, position) = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertEqual(50.0, position)
