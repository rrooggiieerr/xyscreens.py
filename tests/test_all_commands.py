import asyncio
import unittest

from xyscreens import XYScreens

from . import async_test

_SERIAL_PORT = "/dev/tty.wchusbserial110"
_ADDRESS = bytes.fromhex("AAEEEE")


class TestXYScreens(unittest.TestCase):
    """Unit test for the XYScreens library"""

    @async_test
    async def test_all_commands(self):
        screen = XYScreens(_SERIAL_PORT, _ADDRESS, 60)
        for i in range(256):
            print(f"Trying command {i.to_bytes(1).hex()}")
            command = b"\xFF" + _ADDRESS + i.to_bytes(1)
            await screen._async_send_command(command)
            await asyncio.sleep(5)
            await screen.async_stop()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testConstructor']
    unittest.main()
