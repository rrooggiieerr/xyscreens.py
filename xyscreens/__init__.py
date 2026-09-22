"""
Implements the XYScreens library for controlling XY Screens projector screens and projector lifts.

Created on 17 Nov 2022

@author: Rogier van Staveren
"""

import math

try:
    from ._version import __version__ as __version__
except ModuleNotFoundError:
    pass

import asyncio
import logging
import time
from collections.abc import Callable
from enum import IntEnum
from typing import Final, override

import serialx
from serialx import Parity, StopBits

from .task_helper import save_task_reference

logger: Final = logging.getLogger(__name__)


class XYScreensConnectionError(Exception):
    """
    XY Screens Connection Error.

    When an error occurs while connecting to the projector screen or lift.
    """


class XYScreensCommands:
    """The commands needed to move and stop the screen"""

    _PREFIX = b"\xff"
    _UP = b"\xdd"
    _STOP = b"\xcc"
    _DOWN = b"\xee"
    _MICRO_UP = b"\xc9"
    _MICRO_DOWN = b"\xe9"
    _PROGRAM = b"\xaa"

    def __init__(self, address: bytes):
        self._address = address

    @property
    def up(self) -> bytes:
        """Returns the command needed to start moving the screen up."""
        return XYScreensCommands._PREFIX + self._address + XYScreensCommands._UP

    @property
    def micro_up(self) -> bytes:
        """Returns the command needed to move the screen up one step."""
        return XYScreensCommands._PREFIX + self._address + XYScreensCommands._MICRO_UP

    @property
    def stop(self) -> bytes:
        """Returns the command needed for stopping the screen."""
        return XYScreensCommands._PREFIX + self._address + XYScreensCommands._STOP

    @property
    def down(self) -> bytes:
        """Returns the command needed to start moving the screen down."""
        return XYScreensCommands._PREFIX + self._address + XYScreensCommands._DOWN

    @property
    def micro_down(self) -> bytes:
        """Returns the command needed to move the screen down one step."""
        return XYScreensCommands._PREFIX + self._address + XYScreensCommands._MICRO_DOWN

    @property
    def program(self) -> bytes:
        """Returns the command needed for programming the screen address."""
        return XYScreensCommands._PREFIX + self._address + XYScreensCommands._PROGRAM


class XYScreensState(IntEnum):
    """The different states the screen can be."""

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

    @override
    def __str__(self) -> str:
        """Human readable states."""
        return {
            self.STOPPED: "Stopped",
            self.UP: "Up",
            self.UPWARD: "Upward",
            self.DOWNWARD: "Downward",
            self.DOWN: "Down",
        }[self]


class XYScreens:
    """XYScreens class for controlling XY Screens projector screens and projector lifts."""

    # pylint: disable=too-many-instance-attributes
    # The URL to the RS-485 interface where the screen is connected to.
    _url: str
    # The amount of time in seconds it takes the screen to close from the fully-open state.
    _up_duration: float
    # The amount of time in seconds it takes the screen to open up from the fully-closed state.
    _down_duration: float
    # The commands that apply for this screen
    _commands: XYScreensCommands
    # IO lock to prevent overlapping access to the serial port
    _io_lock: asyncio.Lock

    # Current state of the screen. Defaults to Up when object is created.
    _state: XYScreensState = XYScreensState.UP
    # Position of the screen where 0.0 is totally up and 100.0 is fully down.
    _position: float = 0.0
    # Target position of the screen
    _target_position: float = 0.0
    # The distance that the screen needs to travel
    _distance = 0
    # Timestamp when the position was last recomputed
    _last_recompute_time: int = 0

    # List of callbacks which need to be called when the screen status changes.
    _callbacks: list[Callable[[XYScreensState, float], None]] | None = None
    # The task that handles the set position functionality in async mode.
    _set_position_task: asyncio.Task[None] | None = None

    def __init__(
        self,
        url: str,  # URL to the interface where the screen is connected to.
        address: bytes,
        down_duration: float,  # Duration in seconds for the screen to go down.
        up_duration: (
            float | None
        ) = None,  # Duration in seconds for the screen to go up.
        position: float = 0.0,  # Position of the screen where 0.0 is totally up and 100.0 is
        # fully down.
    ) -> None:
        """Initialises the XYScreens object."""
        # pylint: disable=too-many-arguments

        # Validate the different arguments.
        if len(address) != 3:
            raise ValueError("address must contain exactly 3 bytes")

        if (
            math.isnan(down_duration)
            or math.isinf(down_duration)
            or down_duration <= 0.0
        ):
            raise ValueError("down_duration must be greater than 0")
        if up_duration is not None and (
            math.isnan(up_duration) or math.isinf(up_duration) or up_duration <= 0.0
        ):
            raise ValueError("up_duration must be greater than 0")

        if not 0.0 <= position <= 100.0:
            raise ValueError("position must be between 0.0 and 100.0")

        self._url = url
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

        self._commands = XYScreensCommands(address)
        self._io_lock = asyncio.Lock()

    def restore_position(self, position: float) -> None:
        """
        Restores the position of the screen, mainly introduced to restore the screen state in Home
        Assistant.

        Not to be used to move the screen to a position
        """
        if not 0.0 <= position <= 100.0:
            raise ValueError("position must be between 0.0 and 100.0")

        self._position = position
        self._target_position = position

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

        self._last_recompute_time = time.monotonic_ns()

    def add_callback(
        self, callback: Callable[[XYScreensState, float], None]
    ) -> Callable[[], None]:
        """
        Adds a callback.
        """
        if self._callbacks is None:
            self._callbacks = []

        self._callbacks.append(callback)

        return lambda: self.remove_callback(callback)

    def remove_callback(
        self, callback: Callable[[XYScreensState, float], None]
    ) -> None:
        """
        Removes a callback.
        """
        if self._callbacks is None:
            return

        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass

        if len(self._callbacks) == 0:
            self._callbacks = None

    def test_connection(self) -> bool:
        """
        Test if a connection can be established.
        """
        try:
            return self._send_command(None)
        except XYScreensConnectionError:
            pass

        return False

    async def async_test_connection(self) -> bool:
        """
        Test if a connection can be established.
        """
        try:
            return await self._async_send_command(None)
        except XYScreensConnectionError:
            pass

        return False

    def _send_command(self, command: bytes | None) -> bool:
        try:
            # Create the connection instance.
            with serialx.serial_for_url(
                self._url,
                baudrate=2400,
                byte_size=8,
                parity=Parity.NONE,
                stopbits=StopBits.ONE,
                write_timeout=1,
            ) as connection:
                logger.debug("Device %s connected", self._url)

                if command is not None:
                    # Send the command.
                    logger.debug("Sending: 0x%s", command.hex())
                    connection.write(command)
                    connection.flush()
                    logger.debug("Command successfully sent")

            return True
        except (OSError, serialx.SerialException) as ex:
            raise XYScreensConnectionError() from ex

    async def _async_send_command(self, command: bytes | None) -> bool:
        try:
            async with self._io_lock:
                async with serialx.async_serial_for_url(
                    self._url,
                    baudrate=2400,
                    byte_size=8,
                    parity=Parity.NONE,
                    stopbits=StopBits.ONE,
                    write_timeout=1,
                ) as connection:
                    logger.debug("Device %s connected", self._url)

                    if command is not None:
                        # Send the command.
                        logger.debug("Sending: 0x%s", command.hex())
                        await connection.write(command)
                        await connection.flush()
                        logger.debug("Command successfully sent")

                return True
        except (OSError, serialx.SerialException) as ex:
            raise XYScreensConnectionError() from ex

    def update_status(self) -> tuple[XYScreensState, float]:
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
            self._last_recompute_time = time.monotonic_ns()
            return (self._state, self._position)

        now = time.monotonic_ns()
        time_delta = now - self._last_recompute_time
        movement = direction * time_delta / (action_duration * 10_000_000)
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

    def _update_callbacks(self) -> None:
        if self._callbacks is None:
            return

        for callback in self._callbacks.copy():
            try:
                callback(self._state, self._position)
            # pylint: disable=broad-exception-caught
            except Exception:
                logger.exception("Exception in callback: %s", callback)

    def program(self) -> bool:
        """Program the address of the screen."""
        return self._send_command(self._commands.program)

    async def async_program(self) -> bool:
        """Program the address of the screen."""
        return await self._async_send_command(self._commands.program)

    def _post_up(self) -> bool:
        if self._state not in (XYScreensState.UPWARD, XYScreensState.UP):
            self.update_status()
            self._state = XYScreensState.UPWARD
            return True

        return False

    # pylint: disable=C0103
    def up(self) -> bool:
        """Move the screen up."""

        if not self._send_command(self._commands.up):
            return False

        self._post_up()

        return True

    async def async_up(self) -> bool:
        """Move the screen up."""

        return await self.async_set_position(0.0)

    def micro_up(self) -> bool:
        """Move the screen up one step."""

        return self._send_command(self._commands.micro_up)

    async def async_micro_up(self) -> bool:
        """Move the screen up one step."""

        return await self._async_send_command(self._commands.micro_up)

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
        """Stop the screen."""

        if not self._send_command(self._commands.stop):
            return False

        self._post_stop()

        return True

    async def async_stop(self) -> bool:
        """Stop the screen."""

        await self._cancel_set_position()

        if not await self._async_send_command(self._commands.stop):
            return False

        self._post_stop()
        self._update_callbacks()

        return True

    def _post_down(self) -> bool:
        if self._state not in (XYScreensState.DOWNWARD, XYScreensState.DOWN):
            self.update_status()
            self._state = XYScreensState.DOWNWARD
            return True

        return False

    def down(self) -> bool:
        """Move the screen down."""

        if not self._send_command(self._commands.down):
            return False

        self._post_down()

        return True

    async def async_down(self) -> bool:
        """Move the screen down."""

        return await self.async_set_position(100.0)

    def micro_down(self) -> bool:
        """Move the screen down one step."""

        return self._send_command(self._commands.micro_down)

    async def async_micro_down(self) -> bool:
        """Move the screen down one step."""

        return await self._async_send_command(self._commands.micro_down)

    def _target_position_reached(self) -> bool:
        """Calculates if the target position has been reached."""
        self.update_status()

        if self._state == XYScreensState.DOWNWARD:
            return self._position >= self._target_position
        if self._state == XYScreensState.UPWARD:
            return self._position <= self._target_position

        # Target position has been reached
        return True

    def set_position(self, target_position: float) -> bool:
        """Initiates the screen to move to a given position."""
        if not 0.0 <= target_position <= 100.0:
            raise ValueError("target_position must be between 0.0 and 100.0")

        self.update_status()

        distance = target_position - self._position

        if target_position not in [0.0, 100.0] and round(distance, 1) == 0.0:
            return self.stop()

        self._target_position = target_position

        time_needed = 0.0
        if target_position == 100.0 or distance > 0.0:
            time_needed = distance * self._down_duration / 100.0
            if not self.down():
                return False
        elif target_position == 0.0 or distance < 0.0:
            time_needed = -distance * self._up_duration / 100.0
            if not self.up():
                return False

        time.sleep(time_needed)

        if target_position not in [0.0, 100.0]:
            return self.stop()

        return True

    async def async_set_position(self, target_position: float) -> bool:
        """Initiates the screen to move to a given position."""
        if not 0.0 <= target_position <= 100.0:
            raise ValueError("target_position must be between 0.0 and 100.0")

        if self._callbacks is None:
            await self._cancel_set_position()

        self.update_status()

        distance = target_position - self._position

        if target_position not in [0.0, 100.0] and round(distance, 1) == 0.0:
            return await self.async_stop()

        self._target_position = target_position
        self._distance = distance

        if target_position == 100.0 or distance > 0.0:
            if not await self._async_send_command(self._commands.down):
                return False
            self._post_down()
        elif target_position == 0.0 or distance < 0.0:
            if not await self._async_send_command(self._commands.up):
                return False
            self._post_up()

        if (
            self._set_position_task is None
            or self._set_position_task.done()
            or self._set_position_task.cancelled()
        ):
            self._set_position_task = asyncio.create_task(
                self._set_position_coroutine()
            )

            save_task_reference(self._set_position_task)

        return True

    async def _cancel_set_position(self) -> bool:
        if self._set_position_task is not None:
            self._set_position_task.cancel()
            _, pending = await asyncio.wait({self._set_position_task}, timeout=1)
            if pending:
                logger.error("Failed to cancel set position task")
                logger.debug("Set position task: %s", self._set_position_task)
            else:
                self._set_position_task = None

        return self._set_position_task is None

    async def _set_position_coroutine(self) -> None:
        try:
            sleep_duration = 0.1
            target_position_reached = False
            if self._callbacks is None:
                time_needed = 0.0
                if self._distance < 0.0:
                    time_needed = -self._distance * self._up_duration / 100.0
                elif self._distance > 0.0:
                    time_needed = self._distance * self._down_duration / 100.0

                await asyncio.sleep(time_needed)
                target_position_reached = True
            else:
                sleep_duration = min(self._up_duration, self._down_duration) / 1000.0
                sleep_duration = max(sleep_duration, 0.1)

            connection_error_count = 0
            while True:
                if not target_position_reached:
                    target_position_reached = self._target_position_reached()

                if target_position_reached:
                    if self._target_position in [0.0, 100.0]:
                        self._update_callbacks()
                        break

                    try:
                        if await self._async_send_command(self._commands.stop):
                            self._post_stop()
                            self._update_callbacks()
                            break
                    except XYScreensConnectionError:
                        if connection_error_count == 0:
                            logger.exception("Connection error")
                        connection_error_count += 1
                        if connection_error_count == 5:
                            logger.error(
                                "Could not stop the screen at %.1f%%; giving up",
                                self._target_position,
                            )
                            break

                self._update_callbacks()

                await asyncio.sleep(sleep_duration)
        except asyncio.CancelledError:
            logger.debug("Set position task was canceled")

    def state(self) -> XYScreensState:
        """Returns the current state of the screen."""
        state, _ = self.update_status()

        return state

    def position(self) -> float:
        """
        Returns the current position of the screen where 0.0 is totally up and 100.0 is fully down.
        """
        _, position = self.update_status()

        return position
