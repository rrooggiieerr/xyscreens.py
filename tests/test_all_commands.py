import asyncio
import unittest

from xyscreens import XYScreens

_SERIAL_PORT = "/dev/tty.wchusbserial110"
_ADDRESS = bytes.fromhex("AAEEEE")


class TestXYScreens(unittest.IsolatedAsyncioTestCase):
    """Unit test for the XYScreens library"""

    async def test_all_commands(self):
        screen = XYScreens(_SERIAL_PORT, _ADDRESS, 60)
        for i in range(256):
            print(f"Trying command {i.to_bytes(1).hex()}")
            command = b"\xff" + _ADDRESS + i.to_bytes(1)
            await screen._async_send_command(command)
            await asyncio.sleep(5)
            await screen.async_stop()
