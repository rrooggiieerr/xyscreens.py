import logging
import time

import serial

logger = logging.getLogger(__name__)

_COMMAND_UP = bytearray.fromhex("FFAAEEEEDD")
_COMMAND_STOP = bytearray.fromhex("FFAAEEEECC")
_COMMAND_DOWN = bytearray.fromhex("FFAAEEEEEE")


class XYScreens:
    STATE_STOPPED = 0
    STATE_UP = 1
    STATE_UPWARD = 2
    STATE_DOWNWARD = 3
    STATE_DOWN = 4

    _serial_port = None
    _time_up = None
    _time_down = None

    _state = STATE_UP
    _position = 0.0
    _timestamp = None

    def __init__(
        self,
        serial_port: str,
        time_down: float | None = None,
        time_up: float | None = None,
        position: float = 0.0,
    ):
        assert serial_port is not None
        assert time_down is None or time_down > 0.0
        assert time_up is None or time_up > 0.0
        assert position >= 0.0 and position <= 100.0

        self._serial_port = serial_port
        self._time_down = time_down
        if time_up is not None:
            self._time_up = time_up
        else:
            self._time_up = self._time_down
        self._position = position

        if self._position == 0.0:
            self._state = self.STATE_UP
        elif self._position == 100.0:
            self._state = self.STATE_DOWN
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
        if self._state == self.STATE_DOWNWARD and self._time_down is not None:
            self._position = ((time.time() - self._timestamp) / self._time_down) * 100.0
            if self._position >= 100.0:
                self._state = self.STATE_DOWN
                self._position = 100.0
            logger.debug("update() position: %s", self._position)
        elif self._state == self.STATE_UPWARD and self._time_up is not None:
            self._position = ((time.time() - self._timestamp) / self._time_up) * 100.0
            self._position = 100 - self._position
            logger.debug("update() position: %s", self._position)
            if self._position <= 0.0:
                self._state = self.STATE_UP
                self._position = 0.0
            logger.debug("update() position: %s", self._position)

    def up(self) -> bool:
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
        self._update()

        return self._state

    def position(self) -> float:
        self._update()

        return self._position
