"""Asynchronous unit test for the XYScreens library"""

# pylint: disable=missing-function-docstring

import asyncio
from collections.abc import Generator
from socket import gaierror
from unittest.mock import AsyncMock, Mock, patch

import pytest
from serialx import SerialException

from xyscreens import XYScreens, XYScreensState


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

        yield connection


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_test_connection():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 5, 5)
    assert await screen.async_test_connection() is True


async def test_async_test_connection_non_existing_port():
    with patch("serialx.async_serial.AsyncSerial.open", side_effect=FileNotFoundError):
        screen = XYScreens("/dev/cu.non_existing_port", b"AAEEEE", 5, 5)
        assert await screen.async_test_connection() is False


async def test_async_test_connection_socket_non_existing_ip():
    with patch(
        "serialx.async_serial.AsyncSerial.open", side_effect=ConnectionRefusedError
    ):
        screen = XYScreens("socket://0.0.0.0:23", b"AAEEEE", 5, 5)
        assert await screen.async_test_connection() is False


async def test_async_test_connection_esphome_non_existing_ip():
    with patch("serialx.async_serial.AsyncSerial.open", side_effect=SerialException):
        screen = XYScreens("esphome://0.0.0.0:6053/?port_name=UART1", b"AAEEEE", 5, 5)
        assert await screen.async_test_connection() is False


async def test_async_test_connection_socket_non_existing_host():
    with patch("serialx.async_serial.AsyncSerial.open", side_effect=gaierror):
        screen = XYScreens("socket://non_existing_host:23", b"AAEEEE", 5, 5)
        assert await screen.async_test_connection() is False


async def test_async_test_connection_esphome_non_existing_host():
    with patch("serialx.async_serial.AsyncSerial.open", side_effect=SerialException):
        screen = XYScreens(
            "esphome://non_existing_host:6053/?port_name=UART1", b"AAEEEE", 5, 5
        )
        assert await screen.async_test_connection() is False


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_down():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 5, 5)
    callback = Mock()
    screen.add_callback(callback)
    assert await screen.async_down() is True
    await asyncio.sleep(5.1)
    callback.assert_called_with(XYScreensState.DOWN, 100.0)


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_up():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 5, 5, 100)
    callback = Mock()
    screen.add_callback(callback)
    assert await screen.async_up() is True
    await asyncio.sleep(5.1)
    callback.assert_called_with(XYScreensState.UP, 0.0)


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_stop():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, 60)
    await screen.async_down()
    await asyncio.sleep(1)
    assert await screen.async_stop() is True


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_state_up():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10, 100)
    await screen.async_up()
    await asyncio.sleep(10.1)
    assert screen.state() == XYScreensState.UP


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_state_closing():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, 60, 100)
    await screen.async_up()
    assert screen.state() == XYScreensState.UPWARD
    await screen.async_stop()


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_state_stopped():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    await screen.async_down()
    await asyncio.sleep(5)
    await screen.async_stop()
    assert screen.state() == XYScreensState.STOPPED


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_state_downward():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    await screen.async_down()
    assert screen.state() == XYScreensState.DOWNWARD
    await screen.async_stop()


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_state_down():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    await screen.async_down()
    await asyncio.sleep(10.1)
    assert screen.state() == XYScreensState.DOWN


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_position_up():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10, 100)
    await screen.async_up()
    await asyncio.sleep(10.1)
    assert screen.position() == 0.0


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_position_down():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    await screen.async_down()
    await asyncio.sleep(10.1)
    assert screen.position() == 100.0


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_position_halfway():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    await screen.async_down()
    await asyncio.sleep(5)
    assert screen.position() == pytest.approx(50.0, 1)
    await screen.async_stop()


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_change_direction_down():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10, 100)
    await screen.async_up()
    await asyncio.sleep(5)
    await screen.async_down()
    state, position = screen.update_status()
    assert state == XYScreensState.DOWNWARD
    assert position == pytest.approx(50.0, 1)
    await screen.async_stop()


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_change_direction_up():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    await screen.async_down()
    await asyncio.sleep(5)
    await screen.async_up()
    state, position = screen.update_status()
    assert state == XYScreensState.UPWARD
    assert position == pytest.approx(50.0, 1)
    await screen.async_stop()


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_set_position_downward():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    await screen.async_set_position(50.0)
    await asyncio.sleep(5.1)
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == pytest.approx(50.0, 1)


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_set_position_upward():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10, 100.0)
    await screen.async_set_position(50.0)
    await asyncio.sleep(5.1)
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == pytest.approx(50.0, 1)


@pytest.mark.usefixtures("mock_async_serial")
async def test_async_set_position_stop():
    """Test stopping the screen while it is moving to a given position."""
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    await screen.async_down()
    await asyncio.sleep(5)
    await screen.async_stop()
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == pytest.approx(50.0, 1)
