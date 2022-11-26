"""
Implements the XYScreens class for controlling XY Screens projector screens
and projector lifts.

Created on 17 Nov 2022

@author: Rogier van Staveren
"""
import logging
import time

import serial

logger = logging.getLogger(__name__)

# The commands needed to move and stop she screen
_COMMAND_UP = bytearray.fromhex("FFAAEEEEDD")
_COMMAND_STOP = bytearray.fromhex("FFAAEEEECC")
_COMMAND_DOWN = bytearray.fromhex("FFAAEEEEEE")


class XYScreens:
    """
    XY Screens class for controlling XY Screens projector screens and
    projector lifts.
    """

    # The different states the screen can be.
    # Stopped, standing still in a position anywhere between up and down but
    # not up and down.
    STATE_STOPPED = 0
    # Up, stopped and totally retracted to the highest position.
    STATE_UP = 1
    # Upward, moving in an upwards direction.
    STATE_UPWARD = 2
    # Downward, moving in a downwards direction.
    STATE_DOWNWARD = 3
    # Down, stopped and totally extended to the lowest position.
    STATE_DOWN = 4

    # Human readable states
    STATES = {
        STATE_STOPPED: "Stopped",
        STATE_UP: "Up",
        STATE_UPWARD: "Upward",
        STATE_DOWNWARD: "Downward",
        STATE_DOWN: "Down",
    }

    # The serial port where the RS-485 interface and screen is connected to.
    _serial_port = None
    # Time in seconds for the screen to go up.
    _time_up = None
    # Time in seconds for the screen to go down.
    _time_down = None

    # Current state of the screen. Defaults to Up when object is created.
    _state = STATE_UP
    # Position of the screen where 0.0 is totally up and 100.0 is fully down.
    _position = 0.0
    # Timestamp when the up or down command has been executed.
    _timestamp = None

    def __init__(
        self,
        serial_port: str,  # The serial port where the RS-485 interface and
        # screen is connected to.
        time_down: float | None = None,  # Time in seconds for the screen to go
        # down.
        time_up: float | None = None,  # Time in seconds for the screen to go
        # up.
        position: float = 0.0,  # Position of the screen where 0.0 is totally
        # up and 100.0 is fully down.
    ):
        """
        Initialises the XYScreens object.
        """
        # Validate the different arguments.
        assert serial_port is not None
        assert time_down is None or time_down > 0.0
        assert time_up is None or time_up > 0.0

        self._serial_port = serial_port
        # Set the time for the screen to go down.
        if time_down is not None:
            self._time_down = time_down

        # Set the time for the screen to go up.
        if time_up is not None:
            self._time_up = time_up
        # If no time for the screen to go up is given use the same value as
        # the time for the screen to go down.
        elif time_down is not None:
            self._time_up = time_down

        # Set the initial position of the screen.
        self.set_position(position)

    def set_position(self, position: float) -> None:
        """
        Sets the initial position of the screen, just like in the constructor.

        Mainly introduced to restore the screen state in Home Assistant.

        Not to be used to move the screen to a position
        """
        # Make sure the given screen position is within the range of
        # 0.0% to 100.0%
        assert 0.0 <= position <= 100.0

        self._position = position

        # Define the current state of the screen based on the position of the
        # screen.
        # When the screen position is set it is unknown if the screen is
        # moving and in which direction
        # If screen position is 0.0% it's in a totally retracted position and
        # the state is Up
        if self._position == 0.0:
            self._state = self.STATE_UP
        # If screen position is 100.0% it's in a totally extended position and
        # the state is Down
        elif self._position == 100.0:
            self._state = self.STATE_DOWN
        # If screen position is anywhere in between 0.0% and 100.0% the state
        # is Stopped
        else:
            self._state = self.STATE_STOPPED

    def _send_command(self, command: str) -> bool:
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
        except serial.SerialException as e:
            logger.exception(
                "Unable to connect to the device %s: %s", self._serial_port, e
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
        except serial.SerialException as e:
            logger.exception("Error while writing device %s: %s", self._serial_port, e)
        else:
            return True

        return False

    def _update(self) -> None:
        """
        Calculates the position of the screen based on the direction the
        screen is moving.
        """
        if self._state == self.STATE_DOWNWARD and self._time_down is not None:
            self._position = ((time.time() - self._timestamp) / self._time_down) * 100.0
            if self._position >= 100.0:
                self._state = self.STATE_DOWN
                self._position = 100.0
        elif self._state == self.STATE_UPWARD and self._time_up is not None:
            self._position = ((time.time() - self._timestamp) / self._time_up) * 100.0
            self._position = 100 - self._position
            if self._position <= 0.0:
                self._state = self.STATE_UP
                self._position = 0.0

    # pylint: disable=C0103
    def up(self) -> bool:
        """
        Move the screen up.
        """
        logger.debug("up()")

        if self._send_command(_COMMAND_UP):
            if self._state is self.STATE_DOWNWARD:
                self._update()

            if (
                self._state not in (self.STATE_UPWARD, self.STATE_UP)
                and self._time_up is not None
            ):
                self._timestamp = time.time() - (
                    (100.0 - self._position) * (self._time_up / 100)
                )
                logger.debug("up() time stamp: %s", self._timestamp)
                logger.debug("up() position: %s", self._position)
                self._state = self.STATE_UPWARD
                return True

        return False

    def stop(self) -> bool:
        """
        Stop the screen.
        """
        logger.debug("stop()")
        if self._send_command(_COMMAND_STOP):
            if self._state not in (
                self.STATE_UP,
                self.STATE_DOWN,
                self.STATE_STOPPED,
            ):
                self._update()
                if self._state not in (self.STATE_UP, self.STATE_DOWN):
                    self._state = self.STATE_STOPPED
                return True

        return False

    def down(self) -> bool:
        """
        Move the screen down.
        """
        logger.debug("down()")

        if self._send_command(_COMMAND_DOWN):
            if self._state is self.STATE_UPWARD:
                self._update()

            if (
                self._state not in (self.STATE_DOWNWARD, self.STATE_DOWN)
                and self._time_down is not None
            ):
                self._timestamp = time.time() - (
                    self._position * (self._time_down / 100)
                )
                logger.debug("down() time stamp: %s", self._timestamp)
                logger.debug("down() position: %s", self._position)
                self._state = self.STATE_DOWNWARD
                return True

        return False

    def state(self) -> int:
        """
        Returns the current state of the screen.
        """
        self._update()

        return self._state

    def position(self) -> float:
        """
        Returns the current position of the screen where 0.0 is totally up and
        100.0 is fully down.
        """
        self._update()

        return self._position
