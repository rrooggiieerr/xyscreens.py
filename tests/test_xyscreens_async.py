"""Asynchronous unit test for the XYScreens library"""

# pylint: disable=missing-function-docstring
# pylint: disable=too-many-public-methods

import asyncio
import json
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock

from xyscreens import XYScreens, XYScreensState

_SETTINGS_JSON = Path(__file__).with_name("settings.json").absolute()


class TestXYScreens(IsolatedAsyncioTestCase):
    """Asynchronous unit test for the XYScreens library"""

    _url: str
    _address: bytes

    async def asyncSetUp(self):
        with open(_SETTINGS_JSON, encoding="utf8") as settings_file:
            settings = json.load(settings_file)
            self._url = settings.get("url")
            self._address = bytes.fromhex(settings.get("address"))

    async def test_async_test_connection(self):
        screen = XYScreens(self._url, self._address, 5, 5)
        self.assertTrue(await screen.async_test_connection())

    async def test_async_test_connection_non_existing_port(self):
        screen = XYScreens("/dev/cu.non_existing_port", self._address, 5, 5)
        self.assertFalse(await screen.async_test_connection())

    async def test_async_test_connection_socket_non_existing_ip(self):
        screen = XYScreens("socket://0.0.0.0:23", self._address, 5, 5)
        self.assertFalse(await screen.async_test_connection())

    async def test_async_test_connection_esphome_non_existing_ip(self):
        screen = XYScreens(
            "esphome://0.0.0.0:6053/?port_name=UART1", self._address, 5, 5
        )
        self.assertFalse(await screen.async_test_connection())

    async def test_async_test_connection_socket_non_existing_host(self):
        screen = XYScreens("socket://non_existing_host:23", self._address, 5, 5)
        self.assertFalse(await screen.async_test_connection())

    async def test_async_test_connection_esphome_non_existing_host(self):
        screen = XYScreens(
            "esphome://non_existing_host:6053/?port_name=UART1", self._address, 5, 5
        )
        self.assertFalse(await screen.async_test_connection())

    async def test_async_down(self):
        screen = XYScreens(self._url, self._address, 5, 5)
        callback = Mock()
        screen.add_callback(callback)
        self.assertTrue(await screen.async_down())
        await asyncio.sleep(5.1)
        callback.assert_called_with(XYScreensState.DOWN, 100.0)

    async def test_async_up(self):
        screen = XYScreens(self._url, self._address, 5, 5, 100)
        callback = Mock()
        screen.add_callback(callback)
        self.assertTrue(await screen.async_up())
        await asyncio.sleep(5.1)
        callback.assert_called_with(XYScreensState.UP, 0.0)

    async def test_async_stop(self):
        screen = XYScreens(self._url, self._address, 60, 60)
        await screen.async_down()
        await asyncio.sleep(1)
        self.assertTrue(await screen.async_stop())

    async def test_async_state_up(self):
        screen = XYScreens(self._url, self._address, 10, 10, 100)
        await screen.async_up()
        await asyncio.sleep(10.1)
        self.assertIs(XYScreensState.UP, screen.state())

    async def test_async_state_closing(self):
        screen = XYScreens(self._url, self._address, 60, 60, 100)
        await screen.async_up()
        self.assertIs(XYScreensState.UPWARD, screen.state())
        await screen.async_stop()

    async def test_async_state_stopped(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(5)
        await screen.async_stop()
        self.assertIs(XYScreensState.STOPPED, screen.state())

    async def test_async_state_downward(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        await screen.async_down()
        self.assertIs(XYScreensState.DOWNWARD, screen.state())
        await screen.async_stop()

    async def test_async_state_down(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(10.1)
        self.assertIs(XYScreensState.DOWN, screen.state())

    async def test_async_position_up(self):
        screen = XYScreens(self._url, self._address, 10, 10, 100)
        await screen.async_up()
        await asyncio.sleep(10.1)
        self.assertEqual(0.0, screen.position())

    async def test_async_position_down(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(10.1)
        self.assertEqual(100.0, screen.position())

    async def test_async_position_halfway(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(5)
        self.assertAlmostEqual(50.0, screen.position(), delta=1)
        await screen.async_stop()

    async def test_async_change_direction_down(self):
        screen = XYScreens(self._url, self._address, 10, 10, 100)
        await screen.async_up()
        await asyncio.sleep(5)
        await screen.async_down()
        state, position = screen.update_status()
        self.assertIs(XYScreensState.DOWNWARD, state)
        self.assertAlmostEqual(50.0, position, delta=1)
        await screen.async_stop()

    async def test_async_change_direction_up(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(5)
        await screen.async_up()
        state, position = screen.update_status()
        self.assertIs(XYScreensState.UPWARD, state)
        self.assertAlmostEqual(50.0, position, delta=1)
        await screen.async_stop()

    async def test_async_set_position_downward(self):
        screen = XYScreens(self._url, self._address, 10, 10)
        await screen.async_set_position(50.0)
        await asyncio.sleep(5.1)
        state, position = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertAlmostEqual(50.0, position, delta=1)

    async def test_async_set_position_upward(self):
        screen = XYScreens(self._url, self._address, 10, 10, 100.0)
        await screen.async_set_position(50.0)
        await asyncio.sleep(5.1)
        state, position = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertAlmostEqual(50.0, position, delta=1)

    async def test_async_set_position_stop(self):
        """Test stopping the screen while it is moving to a given position."""
        screen = XYScreens(self._url, self._address, 10, 10)
        await screen.async_down()
        await asyncio.sleep(5)
        await screen.async_stop()
        state, position = screen.update_status()
        self.assertIs(XYScreensState.STOPPED, state)
        self.assertAlmostEqual(50.0, position, delta=1)
