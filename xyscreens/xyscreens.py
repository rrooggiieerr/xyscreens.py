"""
Implements the XYScreens class for controlling XY Screens projector screens
and projector lifts.

Created on 17 Nov 2022

@author: Rogier van Staveren
"""

import logging
import time
from enum import IntEnum, StrEnum

import serial
import serial_asyncio

logger = logging.getLogger(__name__)


class XYScreensCommand(StrEnum):
    "The commands needed to move and stop the screen"

    UP = "FFAAEEEEDD"
    STOP = "FFAAEEEECC"
    DOWN = "FFAAEEEEEE"

    def to_bytes(self):
        "The command in bytes."
        return bytes.fromhex(self.value)


class XYScreensState(IntEnum):
    "The different states the screen can be."

    # Stopped, standing still in a position anywhere between up and down but not up and down.
    STOPPED = 0
    # Up, stopped and totally retracted to the highest position.
    UP = 1
    # Upward, moving in an upwards direction.
    UPWARD = 2
    # Downward, moving in a downwards direction.
    DOWNWARD = 3
    # Down, stopped and totally extended to the lowest position.
    DOWN = 4

    def __str__(self) -> str:
        "Human readable states."
        return {
            self.STOPPED: "Stopped",
            self.UP: "Up",
            self.UPWARD: "Upward",
            self.DOWNWARD: "Downward",
            self.DOWN: "Down",
        }[self]


class XYScreens:
    "XYScreens class for controlling XY Screens projector screens and projector lifts."

    # The serial port where the RS-485 interface and screen is connected to.
    _serial_port: str | None = None
    # Time in seconds for the screen to go up.
    _time_up: float
    # Time in seconds for the screen to go down.
    _time_down: float

    # Current state of the screen. Defaults to Up when object is created.
    _state: XYScreensState = XYScreensState.UP
    # Position of the screen where 0.0 is totally up and 100.0 is fully down.
    _position: float = 0.0
    # Timestamp when the up or down command has been executed.
    _timestamp: float

    def __init__(
        self,
        serial_port: str,  # The serial port where the RS-485 interface and screen is connected to.
        time_down: float,  # Time in seconds for the screen to go down.
        time_up: float | None = None,  # Time in seconds for the screen to go up.
        position: float = 0.0,  # Position of the screen where 0.0 is totally up and 100.0 is
        # fully down.
    ):
        "Initialises the XYScreens object."
        # Validate the different arguments.
        assert serial_port is not None
        assert time_down > 0.0
        assert time_up is None or time_up > 0.0

        self._serial_port = serial_port
        # Set the time for the screen to go down.
        self._time_down = time_down

        # Set the time for the screen to go up.
        if time_up is not None:
            self._time_up = time_up
        # If no time for the screen to go up is given use the same value as the time for the screen
        # to go down.
        else:
            self._time_up = time_down

        # Set the initial position of the screen.
        self.restore_position(position)

    def restore_position(self, position: float) -> None:
        """
        Restores the position of the screen, mainly introduced to restore the screen state in Home
        Assistant.

        Not to be used to move the screen to a position
        """
        # Make sure the given screen position is within the range of 0.0% to 100.0%
        assert 0.0 <= position <= 100.0

        self._position = position

        # Define the current state of the screen based on the position of the screen. When the
        # screen position is set it is unknown if the screen is moving and in which direction.
        # If screen position is 0.0% it's in a totally retracted position and the state is Up
        if self._position == 0.0:
            self._state = XYScreensState.UP
        # If screen position is 100.0% it's in a totally extended position and the state is Down
        elif self._position == 100.0:
            self._state = XYScreensState.DOWN
        # If screen position is anywhere in between 0.0% and 100.0% the state is Stopped
        else:
            self._state = XYScreensState.STOPPED

    def _send_command(self, command: bytes) -> bool:
        try:
            # Create the connection instance.
            connection = serial.Serial(
                port=self._serial_port,
                baudrate=2400,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
            )
        except serial.SerialException as ex:
            logger.exception(
                "Unable to connect to the device %s: %s", self._serial_port, ex
            )
            return False
        logger.debug("Device %s connected", self._serial_port)

        try:
            # Open the connection.
            if not connection.is_open:
                connection.open()

            # Send the command.
            connection.write(command)
            connection.flush()
            logger.info("Command successfully send")

            # Close the connection.
            connection.close()
        except serial.SerialException as ex:
            logger.exception("Error while writing device %s: %s", self._serial_port, ex)
        else:
            return True

        return False

    async def _async_send_command(self, command: bytes) -> bool:
        try:
            _, writer = await serial_asyncio.open_serial_connection(
                url=self._serial_port,
                baudrate=2400,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
            )
        except serial.SerialException as ex:
            logger.exception(
                "Unable to connect to the device %s: %s", self._serial_port, ex
            )
            return False
        logger.debug("Device %s connected", self._serial_port)

        try:
            # # Open the connection.
            # if not writer.is_open:
            #     writer.open()

            # Send the command.
            writer.write(command)
            await writer.drain()
            logger.info("Command successfully send")

            # Close the connection.
            writer.close()
        except serial.SerialException as ex:
            logger.exception("Error while writing device %s: %s", self._serial_port, ex)
        else:
            return True

        return False

    def _update(self) -> None:
        "Calculates the position of the screen based on the direction the screen is moving."
        if self._state == XYScreensState.DOWNWARD:
            self._position = ((time.time() - self._timestamp) / self._time_down) * 100.0
            if self._position >= 100.0:
                self._state = XYScreensState.DOWN
                self._position = 100.0
        elif self._state == XYScreensState.UPWARD:
            self._position = ((time.time() - self._timestamp) / self._time_up) * 100.0
            self._position = 100 - self._position
            if self._position <= 0.0:
                self._state = XYScreensState.UP
                self._position = 0.0

    def _post_up(self) -> bool:
        if self._state is XYScreensState.DOWNWARD:
            self._update()

        if self._state not in (XYScreensState.UPWARD, XYScreensState.UP):
            self._timestamp = time.time() - (
                (100.0 - self._position) * (self._time_up / 100)
            )
            logger.debug("up() time stamp: %s", self._timestamp)
            logger.debug("up() position: %s", self._position)
            self._state = XYScreensState.UPWARD
            return True

        return False

    # pylint: disable=C0103
    def up(self) -> bool:
        "Move the screen up."
        logger.debug("up()")

        if self._send_command(XYScreensCommand.UP.to_bytes()):
            return self._post_up()

        return False

    async def async_up(self) -> bool:
        "Move the screen up."
        logger.debug("async_up()")

        if await self._async_send_command(XYScreensCommand.UP.to_bytes()):
            return self._post_up()

        return False

    def _post_stop(self) -> bool:
        if self._state not in (
            XYScreensState.UP,
            XYScreensState.DOWN,
            XYScreensState.STOPPED,
        ):
            self._update()
            if self._state not in (XYScreensState.UP, XYScreensState.DOWN):
                self._state = XYScreensState.STOPPED
            return True

        return False

    def stop(self) -> bool:
        "Stop the screen."
        logger.debug("stop()")

        if self._send_command(XYScreensCommand.STOP.to_bytes()):
            return self._post_stop()

        return False

    async def async_stop(self) -> bool:
        "Stop the screen."
        logger.debug("async_stop()")

        if await self._async_send_command(XYScreensCommand.STOP.to_bytes()):
            return self._post_stop()

        return False

    def _post_down(self) -> bool:
        if self._state is XYScreensState.UPWARD:
            self._update()

        if self._state not in (XYScreensState.DOWNWARD, XYScreensState.DOWN):
            self._timestamp = time.time() - (self._position * (self._time_down / 100))
            logger.debug("down() time stamp: %s", self._timestamp)
            logger.debug("down() position: %s", self._position)
            self._state = XYScreensState.DOWNWARD
            return True

        return False

    def down(self) -> bool:
        "Move the screen down."
        logger.debug("down()")

        if self._send_command(XYScreensCommand.DOWN.to_bytes()):
            return self._post_down()

        return False

    async def async_down(self) -> bool:
        "Move the screen down."
        logger.debug("async_down()")

        if await self._async_send_command(XYScreensCommand.DOWN.to_bytes()):
            return self._post_down()

        return False

    def state(self) -> XYScreensState:
        "Returns the current state of the screen."
        self._update()

        return self._state

    def position(self) -> float:
        """
        Returns the current position of the screen where 0.0 is totally up and 100.0 is fully down.
        """
        self._update()

        return self._position
