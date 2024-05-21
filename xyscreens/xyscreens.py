"""
Implements the XYScreens class for controlling XY Screens projector screens
and projector lifts.

Created on 17 Nov 2022

@author: Rogier van Staveren
"""

import asyncio
import logging
import time
from enum import IntEnum, StrEnum
from typing import Any, Tuple

import serial
import serial_asyncio_fast as serial_asyncio

logger = logging.getLogger(__name__)


class XYScreensConnectionError(Exception):
    """
    XY Screens Connection Error.

    When an error occurs while connecting to the projector screen or lift.
    """


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
    # The amount of time in seconds it takes the cover to close from the fully-open state.
    _up_duration: float
    # The amount of time in seconds it takes the screen to open up from the fully-closed state.
    _down_duration: float

    # Current state of the screen. Defaults to Up when object is created.
    _state: XYScreensState = XYScreensState.UP
    # Position of the screen where 0.0 is totally up and 100.0 is fully down.
    _position: float = 0.0
    # Timestamp then the position was last recomputed
    _last_recompute_time: int = 0

    # List of callbacks which need to be called when the screen status changes.
    _callbacks: list[Any] | None = None
    # The task that handles the set position functionality in async mode.
    _set_position_task: asyncio.Task | None = None

    def __init__(
        self,
        serial_port: str,  # The serial port where the RS-485 interface and screen is connected to.
        down_duration: float,  # Duration in seconds for the screen to go down.
        up_duration: (
            float | None
        ) = None,  # Duration in seconds for the screen to go up.
        position: float = 0.0,  # Position of the screen where 0.0 is totally up and 100.0 is
        # fully down.
    ):
        "Initialises the XYScreens object."
        # Validate the different arguments.
        assert serial_port is not None
        assert down_duration > 0.0
        assert up_duration is None or up_duration > 0.0

        self._serial_port = serial_port
        # Set the duration for the screen to go down.
        self._down_duration = down_duration

        # Set the duration for the screen to go up.
        if up_duration is not None:
            self._up_duration = up_duration
        # If no duration for the screen to go up is given use the same value as the duration for
        # the screen to go down.
        else:
            self._up_duration = self._down_duration

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

        self._last_recompute_time = time.time_ns()

    def add_callback(self, callback):
        """
        Adds an Event Occurred Callback to the UNii.
        """

        if self._callbacks is None:
            self._callbacks = []

        self._callbacks.append(callback)

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
            raise XYScreensConnectionError(
                f"Unable to connect to device {self._serial_port}"
            ) from ex
        logger.debug("Device %s connected", self._serial_port)

        try:
            # Open the connection.
            if not connection.is_open:
                connection.open()

            # Send the command.
            connection.write(command)
            connection.flush()
            logger.info("Command successfully sent")

            # Close the connection.
            connection.close()

            return True
        except serial.SerialException as ex:
            raise XYScreensConnectionError(
                f"Error while writing to device {self._serial_port}"
            ) from ex

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
            raise XYScreensConnectionError(
                f"Unable to connect to device {self._serial_port}"
            ) from ex
        logger.debug("Device %s connected", self._serial_port)

        try:
            # Send the command.
            writer.write(command)
            await writer.drain()
            logger.info("Command successfully sent")

            # Close the connection.
            writer.close()

            return True
        except serial.SerialException as ex:
            raise XYScreensConnectionError(
                f"Error while writing to device {self._serial_port}"
            ) from ex

        return False

    def update_status(self) -> Tuple[XYScreensState, float]:
        """
        Calculates and returns the status and position of the screen based on the direction the
        screen is moving.
        """
        if self._state == XYScreensState.DOWNWARD:
            direction = 1.0
            action_duration = self._down_duration
        elif self._state == XYScreensState.UPWARD:
            direction = -1.0
            action_duration = self._up_duration
        else:
            self._last_recompute_time = time.time_ns()
            return (self._state, self._position)

        now = time.time_ns()
        time_delta = now - self._last_recompute_time
        movement = direction * time_delta / (action_duration * 10000000)
        position = self._position + movement
        self._last_recompute_time = now

        if position >= 100.0:
            self._state = XYScreensState.DOWN
            position = 100.0
        if position <= 0.0:
            self._state = XYScreensState.UP
            position = 0.0

        self._position = position

        return (self._state, self._position)

    def _update_callbacks(self):
        if self._callbacks is None:
            return

        for callback in self._callbacks:
            try:
                callback(self._state, self._position)
            # pylint: disable=broad-exception-caught
            except Exception as ex:
                logger.error("Exception in callback: %s", ex)

    def _post_up(self) -> bool:
        if self._state not in (XYScreensState.UPWARD, XYScreensState.UP):
            self.update_status()
            self._state = XYScreensState.UPWARD
            return True

        return False

    # pylint: disable=C0103
    def up(self) -> bool:
        "Move the screen up."

        if self._send_command(XYScreensCommand.UP.to_bytes()):
            return self._post_up()

        return False

    async def async_up(self) -> bool:
        "Move the screen up."

        return await self.async_set_position(0.0)

    def _post_stop(self) -> bool:
        if self._state not in (
            XYScreensState.UP,
            XYScreensState.DOWN,
            XYScreensState.STOPPED,
        ):
            self.update_status()
            if self._state not in (XYScreensState.UP, XYScreensState.DOWN):
                self._state = XYScreensState.STOPPED
            return True

        return False

    def stop(self) -> bool:
        "Stop the screen."

        if self._send_command(XYScreensCommand.STOP.to_bytes()):
            return self._post_stop()

        return False

    async def async_stop(self) -> bool:
        "Stop the screen."

        await self._cancel_set_position()

        if (
            await self._async_send_command(XYScreensCommand.STOP.to_bytes())
            and self._post_stop()
        ):
            self._update_callbacks()
            return True

        return False

    def _post_down(self) -> bool:
        if self._state not in (XYScreensState.DOWNWARD, XYScreensState.DOWN):
            self.update_status()
            self._state = XYScreensState.DOWNWARD
            return True

        return False

    def down(self) -> bool:
        "Move the screen down."

        if self._send_command(XYScreensCommand.DOWN.to_bytes()):
            return self._post_down()

        return False

    async def async_down(self) -> bool:
        "Move the screen down."

        return await self.async_set_position(100.0)

    def _target_position_reached(self, target_position: float) -> bool:
        """Calculates if the target position has been reached."""
        self.update_status()

        if self._state == XYScreensState.DOWNWARD:
            return self._position >= target_position
        if self._state == XYScreensState.UPWARD:
            return self._position <= target_position

        # Target position has been reached
        return True

    def set_position(self, target_position: float) -> bool:
        """Initiates the screen to move to a given position."""
        assert 0.0 <= target_position <= 100.0

        if round(self._position) == round(target_position):
            return self.stop()

        if self._position < target_position and not self.down():
            return False
        if self._position > target_position and not self.up():
            return False

        sleep_duration = min(self._up_duration, self._down_duration) / 1000.0
        while True:
            if self._target_position_reached(target_position):
                if self._state in (XYScreensState.UPWARD, XYScreensState.DOWNWARD):
                    self.stop()
                break

            time.sleep(sleep_duration)

        return True

    async def async_set_position(self, target_position: float) -> bool:
        """Initiates the screen to move to a given position."""
        assert 0.0 <= target_position <= 100.0

        if round(self._position) == round(target_position):
            return await self.async_stop()

        await self._cancel_set_position()

        if self._position < target_position:
            if not await self._async_send_command(XYScreensCommand.DOWN.to_bytes()):
                return False
            self._post_down()
        elif self._position > target_position:
            if not await self._async_send_command(XYScreensCommand.UP.to_bytes()):
                return False
            self._post_up()

        self._set_position_task = asyncio.create_task(
            self._set_position_coroutine(target_position)
        )

        return True

    async def _cancel_set_position(self) -> bool:
        if self._set_position_task is not None and not (
            self._set_position_task.done() or self._set_position_task.cancelled()
        ):
            if not self._set_position_task.cancel():
                logger.error("Failed to cancel set position task")
                logger.debug("Set position task: %s", self._set_position_task)
                return False
            try:
                await self._set_position_task
            except asyncio.CancelledError:
                logger.debug("Set position task was cancelled")

        if self._set_position_task is not None:
            if self._set_position_task.done() or self._set_position_task.cancelled():
                self._set_position_task = None
            else:
                logger.error("Failed to cancel set position task")
                logger.debug("Set position task: %s", self._set_position_task)
                return False

        self.update_status()
        self._update_callbacks()

        return self._set_position_task is None

    async def _set_position_coroutine(self, target_position: float):
        sleep_duration = min(self._up_duration, self._down_duration) / 1000.0
        while True:
            try:
                target_position_reached = self._target_position_reached(target_position)

                self._update_callbacks()

                if target_position_reached:
                    if self._state in (
                        XYScreensState.UPWARD,
                        XYScreensState.DOWNWARD,
                    ) and await self._async_send_command(
                        XYScreensCommand.STOP.to_bytes()
                    ):
                        self._post_stop()
                        self._update_callbacks()
                    break

                await asyncio.sleep(sleep_duration)
            except asyncio.CancelledError:
                logger.debug("Set position task was canceled")
                break

    def state(self) -> XYScreensState:
        "Returns the current state of the screen."
        (state, _) = self.update_status()

        return state

    def position(self) -> float:
        """
        Returns the current position of the screen where 0.0 is totally up and 100.0 is fully down.
        """
        (_, position) = self.update_status()

        return position
