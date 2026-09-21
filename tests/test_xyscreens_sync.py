"""Synchronous unit test for the XYScreens library"""

# pylint: disable=missing-function-docstring

import time
from collections.abc import Generator
from socket import gaierror
from unittest.mock import Mock, patch

import pytest
from serialx import SerialException

from xyscreens import XYScreens, XYScreensState

from . import ADDRESS, NAN, URL


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

        yield connection


def test_constructor():
    screen = XYScreens(URL, ADDRESS, 60)
    assert screen is not None


def test_constructor2():
    screen = XYScreens(URL, ADDRESS, 60, 60)
    assert screen is not None


def test_constructor3():
    screen = XYScreens(URL, ADDRESS, 60, 60, 100.0)
    assert screen is not None


def test_constructor_up():
    screen = XYScreens(URL, ADDRESS, 60, position=0.0)
    assert screen.state() == XYScreensState.UP
    assert screen.position() == 0.0


def test_constructor_down():
    screen = XYScreens(URL, ADDRESS, 60, position=100.0)
    assert screen.state() == XYScreensState.DOWN
    assert screen.position() == 100.0


def test_constructor_stopped():
    screen = XYScreens(URL, ADDRESS, 60, position=50.0)
    assert screen.state() == XYScreensState.STOPPED
    assert screen.position() == 50.0


def test_constructor_negative_down_duration():
    with (pytest.raises(ValueError),):
        XYScreens(URL, ADDRESS, -0.00001)


def test_constructor_nan_down_duration():
    with (pytest.raises(ValueError),):
        XYScreens(URL, ADDRESS, NAN)


def test_constructor_negative_up_duration():
    with (pytest.raises(ValueError),):
        XYScreens(URL, ADDRESS, 60, -0.00001)


def test_constructor_nan_up_duration():
    with (pytest.raises(ValueError),):
        XYScreens(URL, ADDRESS, 60, NAN)


def test_constructor_negative_position():
    with (pytest.raises(ValueError),):
        XYScreens(URL, ADDRESS, 60, position=-0.00001)


def test_constructor_toolarge_position():
    with (pytest.raises(ValueError),):
        XYScreens(URL, ADDRESS, 60, position=100.00001)


def test_constructor_nan_position():
    with (pytest.raises(ValueError),):
        XYScreens(URL, ADDRESS, 60, 60, NAN)


def test_test_connection():
    screen = XYScreens(URL, ADDRESS, 60, 60)
    assert screen.test_connection() is True


def test_test_connection_non_existing_port():
    with patch("serialx.common.BaseSerial.from_url", side_effect=FileNotFoundError):
        screen = XYScreens("/dev/cu.non_existing_port", ADDRESS, 60, 60)
        assert not screen.test_connection()


def test_test_connection_socket_non_existing_ip():
    with patch(
        "serialx.common.BaseSerial.from_url", side_effect=ConnectionRefusedError
    ):
        screen = XYScreens("socket://0.0.0.0:23", ADDRESS, 5, 5)
        assert not screen.test_connection()


def test_test_connection_esphome_non_existing_ip():
    with patch("serialx.common.BaseSerial.from_url", side_effect=SerialException):
        screen = XYScreens("esphome://0.0.0.0:6053/?port_name=UART1", ADDRESS, 5, 5)
        assert not screen.test_connection()


def test_test_connection_socket_non_existing_host():
    with patch("serialx.common.BaseSerial.from_url", side_effect=gaierror):
        screen = XYScreens("socket://non_existing_host:23", ADDRESS, 5, 5)
        assert not screen.test_connection()


def test_test_connection_esphome_non_existing_host():
    with patch("serialx.common.BaseSerial.from_url", side_effect=SerialException):
        screen = XYScreens(
            "esphome://non_existing_host:6053/?port_name=UART1", ADDRESS, 5, 5
        )
        assert not screen.test_connection()


def test_down():
    screen = XYScreens(URL, ADDRESS, 5, 5)
    assert screen.down() is True
    time.sleep(5.1)
    state, position = screen.update_status()
    assert state == XYScreensState.DOWN
    assert position == 100.0


def test_down_when_down():
    screen = XYScreens(URL, ADDRESS, 5, 5, 100)
    assert screen.down() is True
    state, position = screen.update_status()
    assert state == XYScreensState.DOWN
    assert position == 100.0


def test_up():
    screen = XYScreens(URL, ADDRESS, 5, 5, 100)
    assert screen.up() is True
    time.sleep(5.1)
    state, position = screen.update_status()
    assert state == XYScreensState.UP
    assert position == 0.0


def test_up_when_up():
    screen = XYScreens(URL, ADDRESS, 5, 5)
    assert screen.up() is True
    state, position = screen.update_status()
    assert state == XYScreensState.UP
    assert position == 0.0


def test_stop():
    screen = XYScreens(URL, ADDRESS, 5, 5)
    screen.down()
    time.sleep(1)
    assert screen.stop() is True


def test_state_up():
    screen = XYScreens(URL, ADDRESS, 5, 5, 100)
    screen.up()
    time.sleep(5.1)
    assert screen.state() == XYScreensState.UP


def test_state_closing():
    screen = XYScreens(URL, ADDRESS, 60, 60, 100)
    screen.up()
    assert screen.state() == XYScreensState.UPWARD
    screen.stop()


def test_state_stopped():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    screen.down()
    time.sleep(5)
    screen.stop()
    assert screen.state() == XYScreensState.STOPPED


def test_state_downward():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    screen.down()
    assert screen.state() == XYScreensState.DOWNWARD


def test_state_down():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    screen.down()
    time.sleep(10)
    assert screen.state() == XYScreensState.DOWN


def test_position_up():
    screen = XYScreens(URL, ADDRESS, 10, 10, 100)
    screen.up()
    time.sleep(10)
    assert screen.position() == 0.0


def test_position_down():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    screen.down()
    time.sleep(10)
    assert screen.position() == 100.0


def test_position_halfway():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    screen.down()
    time.sleep(5)
    assert screen.position() == pytest.approx(50.0, abs=1)


def test_change_direction_down():
    screen = XYScreens(URL, ADDRESS, 10, 10, 100)
    screen.up()
    time.sleep(5)
    screen.down()
    state, position = screen.update_status()
    assert state == XYScreensState.DOWNWARD
    assert position == pytest.approx(50.0, abs=1)
    time.sleep(5.1)
    state, position = screen.update_status()
    assert state == XYScreensState.DOWN
    assert position == 100.0


def test_change_direction_up():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    screen.down()
    time.sleep(5)
    screen.up()
    state, position = screen.update_status()
    assert state == XYScreensState.UPWARD
    assert position == pytest.approx(50.0, abs=1)
    time.sleep(5.1)
    state, position = screen.update_status()
    assert state == XYScreensState.UP
    assert position == 0.0


def test_set_position_downward():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    screen.set_position(50.0)
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == pytest.approx(50.0, abs=1)


def test_set_position_downward_when_down():
    screen = XYScreens(URL, ADDRESS, 10, 10, 100)
    screen.set_position(100.0)
    state, position = screen.update_status()
    assert state == XYScreensState.DOWN
    assert position == 100.0


def test_set_position_upward():
    screen = XYScreens(URL, ADDRESS, 10, 10, 100.0)
    screen.set_position(50.0)
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == pytest.approx(50.0, abs=1)


def test_set_position_upward_when_up():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    screen.set_position(0.0)
    state, position = screen.update_status()
    assert state == XYScreensState.UP
    assert position == 0.0


def test_set_position_negative_position():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    with (pytest.raises(ValueError),):
        screen.set_position(-0.00001)


def test_set_position_toolarge_position():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    with (pytest.raises(ValueError),):
        screen.set_position(100.00001)


def test_set_position_nan():
    screen = XYScreens(URL, ADDRESS, 10, 10)
    with (pytest.raises(ValueError),):
        screen.set_position(NAN)


def test_restore_position_up():
    screen = XYScreens(URL, ADDRESS, 60)
    screen.restore_position(0.0)
    state, position = screen.update_status()
    assert state == XYScreensState.UP
    assert position == 0.0


def test_restore_position_down():
    screen = XYScreens(URL, ADDRESS, 60)
    screen.restore_position(100.0)
    state, position = screen.update_status()
    assert state == XYScreensState.DOWN
    assert position == 100.0


def test_restore_position_halfway():
    screen = XYScreens(URL, ADDRESS, 60)
    screen.restore_position(50.0)
    state, position = screen.update_status()
    assert state == XYScreensState.STOPPED
    assert position == 50.0


def test_restore_position_negative_position():
    screen = XYScreens(URL, ADDRESS, 60)
    with (pytest.raises(ValueError),):
        screen.restore_position(-0.00001)


def test_restore_position_toolarge_position():
    screen = XYScreens(URL, ADDRESS, 60)
    with pytest.raises(ValueError):
        screen.restore_position(100.00001)


def test_restore_position_nan():
    screen = XYScreens(URL, ADDRESS, 60)
    with pytest.raises(ValueError):
        screen.restore_position(NAN)
