"""Synchronous unit test for the XYScreens library"""

# pylint: disable=missing-function-docstring

import time
from collections.abc import Generator
from socket import gaierror
from unittest.mock import Mock, patch

import pytest
from serialx import SerialException

from xyscreens import XYScreens, XYScreensState


@pytest.fixture(autouse=True)
def mock_base_serial() -> Generator[Mock, None, None]:
    """Mock serialx BaseSerial."""

    with (
        patch(
            "serialx.common.BaseSerial",
            autospec=True,
        ) as mock_connection,
    ):
        connection = mock_connection.return_value
        connection.from_url = Mock(side_effect=OSError())

        yield connection


def test_constructor():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60)
    assert screen is not None


def test_constructor2():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, 60)
    assert screen is not None


def test_constructor3():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, 60, 100.0)
    assert screen is not None


def test_constructor_up():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, position=0.0)
    assert screen.state() == XYScreensState.UP
    assert screen.position() == 0.0


def test_constructor_down():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, position=100.0)
    assert screen.state() == XYScreensState.DOWN
    assert screen.position() == 100.0


def test_constructor_stopped():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, position=50.0)
    assert screen.state() == XYScreensState.STOPPED
    assert screen.position() == 50.0


def test_constructor_negative_position():
    with (pytest.raises(AssertionError),):
        XYScreens("/dev/cu.some_port", b"AAEEEE", 60, position=-0.00001)


def test_constructor_toolarge_position():
    with (pytest.raises(AssertionError),):
        XYScreens("/dev/cu.some_port", b"AAEEEE", 60, position=100.00001)


def test_test_connection():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, 60)
    assert screen.test_connection() is True


def test_test_connection_non_existing_port():
    with patch("serialx.common.BaseSerial.from_url", side_effect=FileNotFoundError):
        screen = XYScreens("/dev/cu.non_existing_port", b"AAEEEE", 60, 60)
        assert screen.test_connection() is False


def test_test_connection_socket_non_existing_ip():
    with patch(
        "serialx.common.BaseSerial.from_url", side_effect=ConnectionRefusedError
    ):
        screen = XYScreens("socket://0.0.0.0:23", b"AAEEEE", 5, 5)
        assert screen.test_connection() is False


def test_test_connection_esphome_non_existing_ip():
    with patch("serialx.common.BaseSerial.from_url", side_effect=SerialException):
        screen = XYScreens("esphome://0.0.0.0:6053/?port_name=UART1", b"AAEEEE", 5, 5)
        assert screen.test_connection() is False


def test_test_connection_socket_non_existing_host():
    with patch("serialx.common.BaseSerial.from_url", side_effect=gaierror):
        screen = XYScreens("socket://non_existing_host:23", b"AAEEEE", 5, 5)
        assert screen.test_connection() is False


def test_test_connection_esphome_non_existing_host():
    with patch("serialx.common.BaseSerial.from_url", side_effect=SerialException):
        screen = XYScreens(
            "esphome://non_existing_host:6053/?port_name=UART1", b"AAEEEE", 5, 5
        )
        assert screen.test_connection() is False


def test_down():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, 60)
    assert screen.down() is True


def test_up():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, 60, 100)
    assert screen.up() is True


def test_stop():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, 60)
    screen.down()
    time.sleep(1)
    assert screen.stop() is True


def test_state_up():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10, 100)
    screen.up()
    time.sleep(10)
    assert screen.state() == XYScreensState.UP


def test_state_closing():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60, 60, 100)
    screen.up()
    assert screen.state() == XYScreensState.UPWARD


def test_state_stopped():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    screen.down()
    time.sleep(5)
    screen.stop()
    assert screen.state() == XYScreensState.STOPPED


def test_state_downward():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    screen.down()
    assert screen.state() == XYScreensState.DOWNWARD


def test_state_down():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    screen.down()
    time.sleep(10)
    assert screen.state() == XYScreensState.DOWN


def test_position_up():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10, 100)
    screen.up()
    time.sleep(10)
    assert screen.position() == 0.0


def test_position_down():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    screen.down()
    time.sleep(10)
    assert screen.position() == 100.0


def test_position_halfway():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    screen.down()
    time.sleep(5)
    assert screen.position() == pytest.approx(50.0, 1)


def test_change_direction_down():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10, 100)
    screen.up()
    time.sleep(5)
    screen.down()
    state, position = screen.update_status()
    assert state == XYScreensState.DOWNWARD
    assert position == pytest.approx(50.0, 1)


def test_change_direction_up():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    screen.down()
    time.sleep(5)
    screen.up()
    state, position = screen.update_status()
    assert state == XYScreensState.UPWARD
    assert position == pytest.approx(50.0, 1)


def test_set_position_downward():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10)
    screen.set_position(50.0)
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == pytest.approx(50.0, 1)


def test_set_position_upward():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 10, 10, 100.0)
    screen.set_position(50.0)
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == pytest.approx(50.0, 1)


def test_restore_position_up():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60)
    screen.restore_position(0.0)
    state, position = screen.update_status()
    assert state == XYScreensState.UP
    assert position == 0.0


def test_restore_position_down():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60)
    screen.restore_position(100.0)
    state, position = screen.update_status()
    assert state == XYScreensState.DOWN
    assert position == 100.0


def test_restore_position_halfway():
    screen = XYScreens("/dev/cu.some_port", b"AAEEEE", 60)
    screen.restore_position(50.0)
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == 50.0
