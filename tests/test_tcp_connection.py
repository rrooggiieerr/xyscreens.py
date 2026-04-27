"""
Unit tests for TCP connection functionality in XYScreens.

Created on 15 Oct 2025
@author: Claude Code
"""

import asyncio
import socket
import threading
import time
import unittest
from unittest.mock import AsyncMock, Mock, patch

from xyscreens import XYScreens, XYScreensConnectionError, XYScreensState, XYScreensTCP


class MockTCPServer:
    """Mock TCP server for testing TCP connections."""

    def __init__(self, host="127.0.0.1", port=0):
        self.host = host
        self.port = port
        self.server_socket = None
        self.server_thread = None
        self.running = False
        self.received_data = []
        self.response_data = b""

    def start(self):
        """Start the mock TCP server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))

        self.port = self.server_socket.getsockname()[1]

        self.server_socket.listen(5)
        self.running = True

        self.server_thread = threading.Thread(target=self._server_loop)
        self.server_thread.daemon = True
        self.server_thread.start()

        time.sleep(0.1)

    def stop(self):
        """Stop the mock TCP server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.server_thread:
            self.server_thread.join(timeout=1.0)

    def _server_loop(self):
        """Server loop that handles incoming connections."""
        while self.running:
            try:
                client_socket, _ = self.server_socket.accept()
                with client_socket:
                    data = client_socket.recv(1024)
                    if data:
                        self.received_data.append(data)
                    if self.response_data:
                        client_socket.send(self.response_data)
            except OSError:
                break


class TestXYScreensTCP(unittest.TestCase):
    """Unit tests for XYScreensTCP class."""

    def setUp(self):
        """Set up test fixtures."""
        self.address = b"\x01"
        self.down_duration = 30.0
        self.up_duration = 25.0

    def test_constructor(self):
        """Test XYScreensTCP constructor stores host and port."""
        screen = XYScreensTCP("192.168.1.100", 9997, self.address, self.down_duration)
        self.assertEqual(screen.host, "192.168.1.100")
        self.assertEqual(screen.port, 9997)
        self.assertEqual(screen.device, "192.168.1.100:9997")

    def test_constructor_with_all_args(self):
        """Test XYScreensTCP constructor with all arguments."""
        screen = XYScreensTCP(
            "192.168.1.100",
            9997,
            self.address,
            self.down_duration,
            self.up_duration,
            50.0,
        )
        self.assertEqual(screen.host, "192.168.1.100")
        self.assertEqual(screen.port, 9997)
        self.assertEqual(screen.device, "192.168.1.100:9997")
        self.assertIs(XYScreensState.STOPPED, screen.state())

    def test_send_command_with_mock_server(self):
        """Test sending command via TCP with a mock server."""
        server = MockTCPServer()
        server.start()

        try:
            screen = XYScreensTCP(
                server.host, server.port, self.address, self.down_duration
            )

            result = screen._send_command(screen._commands.up)
            self.assertTrue(result)

            time.sleep(0.1)
            self.assertEqual(len(server.received_data), 1)
            self.assertEqual(server.received_data[0], screen._commands.up)

        finally:
            server.stop()

    def test_send_command_connection_error(self):
        """Test TCP connection error handling."""
        screen = XYScreensTCP("127.0.0.1", 1, self.address, self.down_duration)

        with self.assertRaises(XYScreensConnectionError) as cm:
            screen._send_command(screen._commands.up)

        self.assertIn("Error while connecting to TCP endpoint", str(cm.exception))

    def test_constructor_rejects_invalid_port(self):
        """Test that invalid port values are rejected at construction."""
        with self.assertRaises(AssertionError):
            XYScreensTCP("127.0.0.1", 99999, self.address, self.down_duration)
        with self.assertRaises(AssertionError):
            XYScreensTCP("127.0.0.1", 0, self.address, self.down_duration)
        with self.assertRaises(AssertionError):
            XYScreensTCP("127.0.0.1", -1, self.address, self.down_duration)


class TestXYScreensTCPAsync(unittest.IsolatedAsyncioTestCase):
    """Unit tests for async XYScreensTCP functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.address = b"\x01"
        self.down_duration = 30.0
        self.up_duration = 25.0

    async def test_async_send_command_with_mock_server(self):
        """Test sending command via TCP asynchronously with a mock server."""
        server = MockTCPServer()
        server.start()

        try:
            screen = XYScreensTCP(
                server.host, server.port, self.address, self.down_duration
            )

            result = await screen._async_send_command(screen._commands.down)
            self.assertTrue(result)

            await asyncio.sleep(0.1)
            self.assertEqual(len(server.received_data), 1)
            self.assertEqual(server.received_data[0], screen._commands.down)

        finally:
            server.stop()

    async def test_async_send_command_connection_error(self):
        """Test async TCP connection error handling."""
        screen = XYScreensTCP("127.0.0.1", 1, self.address, self.down_duration)

        with self.assertRaises(XYScreensConnectionError) as cm:
            await screen._async_send_command(screen._commands.stop)

        self.assertIn("Error while connecting to TCP endpoint", str(cm.exception))

    async def test_async_send_command_timeout(self):
        """Test async TCP connection timeout handling."""
        screen = XYScreensTCP("192.0.2.1", 9999, self.address, self.down_duration)

        with self.assertRaises(XYScreensConnectionError) as cm:
            await screen._async_send_command(screen._commands.program)

        self.assertIn("Error while connecting to TCP endpoint", str(cm.exception))

    async def test_high_level_async_methods_tcp(self):
        """Test high-level async methods with TCP connection."""
        server = MockTCPServer()
        server.start()

        try:
            screen = XYScreensTCP(
                server.host,
                server.port,
                self.address,
                self.down_duration,
                position=50.0,
            )

            result = await screen.async_up()
            self.assertTrue(result)

            await asyncio.sleep(0.2)
            self.assertGreater(len(server.received_data), 0)

        finally:
            server.stop()


class TestSerialConnection(unittest.TestCase):
    """Test that XYScreens serial class works correctly."""

    def setUp(self):
        """Set up test fixtures."""
        self.address = b"\x01"
        self.down_duration = 30.0

    @patch("serial.Serial")
    def test_send_command_uses_serial(self, mock_serial):
        """Test that XYScreens._send_command uses serial transport."""
        mock_connection = Mock()
        mock_connection.is_open = False
        mock_serial.return_value = mock_connection

        screen = XYScreens("/dev/ttyUSB0", self.address, self.down_duration)
        screen._send_command(screen._commands.up)

        mock_serial.assert_called_once()
        mock_connection.open.assert_called_once()
        mock_connection.write.assert_called_once()

    def test_serial_port_property(self):
        """Test that XYScreens.serial_port returns the serial port."""
        screen = XYScreens.__new__(XYScreens)
        screen._serial_port = "/dev/ttyUSB0"
        self.assertEqual(screen.serial_port, "/dev/ttyUSB0")


class TestClassSeparation(unittest.TestCase):
    """Test that serial and TCP classes cannot be used interchangeably."""

    def setUp(self):
        """Set up test fixtures."""
        self.address = b"\x01"
        self.down_duration = 30.0

    def test_xyscreens_serial_does_not_accept_tcp_endpoint(self):
        """XYScreens (serial) must not be used with a TCP host:port string."""
        with self.assertRaises((ValueError, AssertionError)):
            XYScreens("192.168.0.133:8887", self.address, self.down_duration)

    def test_xyscreens_serial_does_not_accept_ip_address(self):
        """XYScreens (serial) must not be used with an IP-like string."""
        with self.assertRaises((ValueError, AssertionError)):
            XYScreens("10.0.0.1:9997", self.address, self.down_duration)

    def test_xyscreens_serial_accepts_device_path(self):
        """XYScreens (serial) accepts a valid device path."""
        screen = XYScreens("/dev/ttyUSB0", self.address, self.down_duration)
        self.assertEqual(screen.serial_port, "/dev/ttyUSB0")

    def test_xyscreens_serial_accepts_com_port(self):
        """XYScreens (serial) accepts a Windows COM port."""
        screen = XYScreens("COM3", self.address, self.down_duration)
        self.assertEqual(screen.serial_port, "COM3")

    def test_xyscreens_tcp_does_not_accept_device_path(self):
        """XYScreensTCP must not be used with a serial device path."""
        with self.assertRaises((ValueError, AssertionError)):
            XYScreensTCP("/dev/ttyUSB0", 9997, self.address, self.down_duration)


if __name__ == "__main__":
    unittest.main()
