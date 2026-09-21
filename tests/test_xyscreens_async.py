"""Asynchronous unit test for the XYScreens library"""

# pylint: disable=missing-function-docstring

import asyncio
from collections.abc import Generator
from socket import gaierror
from unittest.mock import AsyncMock, Mock, patch

import pytest
from serialx import SerialException

from xyscreens import XYScreens, XYScreensState

from . import ADDRESS, INF, NAN, URL


@pytest.fixture()
def mock_async_serial() -> Generator[AsyncMock, None, None]:
    """Mock serialx AsyncSerial."""

    with (
        patch(
            "serialx.async_serial.AsyncSerial",
            autospec=True,
        ) as mock_connection,
    ):
        connection = mock_connection.return_value
        connection.open = AsyncMock()
        connection.__aenter__.return_value = connection

        yield connection


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_test_connection():
    screen = XYScreens(URL, ADDRESS, 5, 5)
    assert await screen.async_test_connection() is True


async def test_async_test_connection_non_existing_port():
    with patch("serialx.async_serial.AsyncSerial.open", side_effect=FileNotFoundError):
        screen = XYScreens("/dev/cu.non_existing_port", ADDRESS, 5, 5)
        assert not await screen.async_test_connection()


async def test_async_test_connection_socket_non_existing_ip():
    with patch(
        "serialx.async_serial.AsyncSerial.open", side_effect=ConnectionRefusedError
    ):
        screen = XYScreens("socket://0.0.0.0:23", ADDRESS, 5, 5)
        assert not await screen.async_test_connection()


async def test_async_test_connection_esphome_non_existing_ip():
    with patch("serialx.async_serial.AsyncSerial.open", side_effect=SerialException):
        screen = XYScreens("esphome://0.0.0.0:6053/?port_name=UART1", ADDRESS, 5, 5)
        assert not await screen.async_test_connection()


async def test_async_test_connection_socket_non_existing_host():
    with patch("serialx.async_serial.AsyncSerial.open", side_effect=gaierror):
        screen = XYScreens("socket://non_existing_host:23", ADDRESS, 5, 5)
        assert not await screen.async_test_connection()


async def test_async_test_connection_esphome_non_existing_host():
    with patch("serialx.async_serial.AsyncSerial.open", side_effect=SerialException):
        screen = XYScreens(
            "esphome://non_existing_host:6053/?port_name=UART1", ADDRESS, 5, 5
        )
        assert not await screen.async_test_connection()


async def test_async_down(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 5, 5)
    assert await screen.async_down() is True
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    await asyncio.sleep(5.1)
    state, position = screen.update_status()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    assert state == XYScreensState.DOWN
    assert position == 100.0


async def test_async_down_when_down(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 5, 5, 100)
    assert await screen.async_down() is True
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    state, position = screen.update_status()
    assert state == XYScreensState.DOWN
    assert position == 100.0


async def test_async_down_with_callback(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 5, 5)
    callback = Mock()
    screen.add_callback(callback)
    assert await screen.async_down() is True
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    await asyncio.sleep(5.1)
    callback.assert_called_with(XYScreensState.DOWN, 100.0)


async def test_async_up(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 5, 5, 100)
    assert await screen.async_up() is True
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    await asyncio.sleep(5.1)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    state, position = screen.update_status()
    assert state == XYScreensState.UP
    assert position == 0.0


async def test_async_up_when_up(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 5, 5)
    assert await screen.async_up() is True
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    state, position = screen.update_status()
    assert state == XYScreensState.UP
    assert position == 0.0


async def test_async_up_with_callback(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 5, 5, 100)
    callback = Mock()
    screen.add_callback(callback)
    assert await screen.async_up() is True
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    await asyncio.sleep(5.1)
    callback.assert_called_with(XYScreensState.UP, 0.0)


async def test_async_stop(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 60, 60)
    await screen.async_down()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    await asyncio.sleep(1)
    mock_async_serial.reset_mock()
    assert await screen.async_stop() is True
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xcc")


async def test_async_state_up(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 10, 10, 100)
    await screen.async_up()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    assert screen.state() == XYScreensState.UPWARD
    await asyncio.sleep(10.1)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    assert screen.state() == XYScreensState.UP


async def test_async_state_stopped(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 10, 10)
    await screen.async_down()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    await asyncio.sleep(5)
    mock_async_serial.reset_mock()
    await screen.async_stop()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xcc")
    assert screen.state() == XYScreensState.STOPPED


async def test_async_state_downward(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 10, 10)
    await screen.async_down()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    assert screen.state() == XYScreensState.DOWNWARD
    await screen.async_stop()


async def test_async_state_down(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 10, 10)
    await screen.async_down()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    await asyncio.sleep(10.1)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    assert screen.state() == XYScreensState.DOWN


async def test_async_position_up(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 10, 10, 100)
    await screen.async_up()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    await asyncio.sleep(10.1)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    assert screen.position() == 0.0


async def test_async_position_down(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 10, 10)
    await screen.async_down()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    await asyncio.sleep(10.1)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    assert screen.position() == 100.0


async def test_async_position_halfway(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 10, 10)
    await screen.async_down()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    await asyncio.sleep(5)
    assert screen.position() == pytest.approx(50.0, abs=1)


async def test_async_change_direction_down(mock_async_serial: AsyncMock):
    """Test changing the screen direction while it is moving upward."""
    screen = XYScreens(URL, ADDRESS, 10, 10, 100)
    await screen.async_up()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    await asyncio.sleep(5)
    mock_async_serial.reset_mock()
    await screen.async_down()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    state, position = screen.update_status()
    assert state == XYScreensState.DOWNWARD
    assert position == pytest.approx(50.0, abs=1)
    await asyncio.sleep(5.1)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    state, position = screen.update_status()
    assert state == XYScreensState.DOWN
    assert position == 100.0


async def test_async_change_direction_up(mock_async_serial: AsyncMock):
    """Test changing the screen direction while it is moving downward."""
    screen = XYScreens(URL, ADDRESS, 10, 10)
    await screen.async_down()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    await asyncio.sleep(5)
    mock_async_serial.reset_mock()
    await screen.async_up()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    state, position = screen.update_status()
    assert state == XYScreensState.UPWARD
    assert position == pytest.approx(50.0, abs=1)
    await asyncio.sleep(5.1)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    state, position = screen.update_status()
    assert state == XYScreensState.UP
    assert position == 0.0


async def test_async_set_position_downward(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 10, 10)
    await screen.async_set_position(50.0)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    mock_async_serial.reset_mock()
    await asyncio.sleep(5.1)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xcc")
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == pytest.approx(50.0, abs=1)


async def test_async_set_position_downward_when_down(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 10, 10, 100)
    await screen.async_set_position(100.0)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    state, position = screen.update_status()
    assert state == XYScreensState.DOWN
    assert position == 100.0


async def test_async_set_position_upward(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 10, 10, 100.0)
    await screen.async_set_position(50.0)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    mock_async_serial.reset_mock()
    await asyncio.sleep(5.1)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xcc")
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == pytest.approx(50.0, abs=1)


async def test_async_set_position_upward_when_up(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 10, 10)
    await screen.async_set_position(0.0)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xdd")
    state, position = screen.update_status()
    assert state == XYScreensState.UP
    assert position == 0.0


async def test_async_set_position_stop(mock_async_serial: AsyncMock):
    """Test stopping the screen while it is moving to a given position."""
    screen = XYScreens(URL, ADDRESS, 10, 10)
    await screen.async_set_position(90.0)
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xee")
    mock_async_serial.reset_mock()
    await asyncio.sleep(5)
    await screen.async_stop()
    mock_async_serial.write.assert_awaited_once_with(b"\xff" + ADDRESS + b"\xcc")
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == pytest.approx(50.0, abs=1)


async def test_async_set_position_negative_position():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    with pytest.raises(ValueError):
        await screen.async_set_position(-0.00001)


async def test_async_set_position_toolarge_position():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    with pytest.raises(ValueError):
        await screen.async_set_position(100.00001)


async def test_async_set_position_nan(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 60)
    with pytest.raises(ValueError):
        await screen.async_set_position(NAN)


async def test_async_set_position_inf(mock_async_serial: AsyncMock):
    screen = XYScreens(URL, ADDRESS, 60)
    with pytest.raises(ValueError):
        await screen.async_set_position(INF)
