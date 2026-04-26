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
from unittest.mock import Mock, patch, AsyncMock

from xyscreens import XYScreens, XYScreensConnectionError, XYScreensState


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

        # Get the actual port if 0 was specified
        self.port = self.server_socket.getsockname()[1]

        self.server_socket.listen(5)
        self.running = True

        self.server_thread = threading.Thread(target=self._server_loop)
        self.server_thread.daemon = True
        self.server_thread.start()

        # Wait a bit for server to start
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

    def get_endpoint(self):
        """Get the server endpoint as host:port string."""
        return f"{self.host}:{self.port}"


class TestTCPConnection(unittest.TestCase):
    """Unit tests for TCP connection functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.address = b"\x01"
        self.down_duration = 30.0
        self.up_duration = 25.0

    def test_is_tcp_connection_detection(self):
        """Test TCP connection detection."""
        # TCP connections
        screen_tcp = XYScreens("192.168.1.100:9997", self.address, self.down_duration)
        self.assertTrue(screen_tcp.is_tcp_connection)

        screen_tcp2 = XYScreens("localhost:8080", self.address, self.down_duration)
        self.assertTrue(screen_tcp2.is_tcp_connection)

        # Serial connections
        screen_serial = XYScreens("/dev/ttyUSB0", self.address, self.down_duration)
        self.assertFalse(screen_serial.is_tcp_connection)

        screen_serial2 = XYScreens("COM1", self.address, self.down_duration)
        self.assertFalse(screen_serial2.is_tcp_connection)

        # Edge cases
        screen_serial3 = XYScreens("/dev/tty:with:colons", self.address, self.down_duration)
        self.assertFalse(screen_serial3.is_tcp_connection)  # Starts with /

    def test_parse_tcp_endpoint(self):
        """Test TCP endpoint parsing."""
        screen = XYScreens("192.168.1.100:9997", self.address, self.down_duration)
        host, port = screen._parse_tcp_endpoint()
        self.assertEqual(host, "192.168.1.100")
        self.assertEqual(port, 9997)

        screen2 = XYScreens("localhost:8080", self.address, self.down_duration)
        host2, port2 = screen2._parse_tcp_endpoint()
        self.assertEqual(host2, "localhost")
        self.assertEqual(port2, 8080)

    def test_parse_tcp_endpoint_invalid(self):
        """Test TCP endpoint parsing with invalid formats."""
        screen = XYScreens("/dev/ttyUSB0", self.address, self.down_duration)
        with self.assertRaises(ValueError):
            screen._parse_tcp_endpoint()

        screen2 = XYScreens("invalid:port:format", self.address, self.down_duration)
        with self.assertRaises(ValueError):
            screen2._parse_tcp_endpoint()

        screen3 = XYScreens("host:invalid_port", self.address, self.down_duration)
        with self.assertRaises(ValueError):
            screen3._parse_tcp_endpoint()

        screen4 = XYScreens("host:99999", self.address, self.down_duration)
        with self.assertRaises(ValueError):
            screen4._parse_tcp_endpoint()

    def test_create_tcp_classmethod(self):
        """Test the create_tcp class method."""
        screen = XYScreens.create_tcp(
            "192.168.1.100", 9997, self.address, self.down_duration, self.up_duration
        )
        self.assertTrue(screen.is_tcp_connection)
        self.assertEqual(screen.device, "192.168.1.100:9997")
        self.assertEqual(screen.serial_port, "192.168.1.100:9997")  # Backward compatibility

    def test_create_serial_classmethod(self):
        """Test the create_serial class method."""
        screen = XYScreens.create_serial(
            "/dev/ttyUSB0", self.address, self.down_duration, self.up_duration
        )
        self.assertFalse(screen.is_tcp_connection)
        self.assertEqual(screen.device, "/dev/ttyUSB0")
        self.assertEqual(screen.serial_port, "/dev/ttyUSB0")

    def test_tcp_send_command_with_mock_server(self):
        """Test sending command via TCP with a mock server."""
        server = MockTCPServer()
        server.start()

        try:
            screen = XYScreens(server.get_endpoint(), self.address, self.down_duration)

            result = screen._send_command_tcp(screen._commands.up)
            self.assertTrue(result)

            time.sleep(0.1)
            self.assertEqual(len(server.received_data), 1)
            self.assertEqual(server.received_data[0], screen._commands.up)

        finally:
            server.stop()

    def test_tcp_send_command_connection_error(self):
        """Test TCP connection error handling."""
        screen = XYScreens("127.0.0.1:99999", self.address, self.down_duration)

        with self.assertRaises(XYScreensConnectionError) as cm:
            screen._send_command_tcp(screen._commands.up)

        self.assertIn("Error while connecting to TCP endpoint", str(cm.exception))

    def test_tcp_send_command_invalid_endpoint(self):
        """Test TCP command sending with invalid endpoint format."""
        screen = XYScreens("invalid:endpoint:format", self.address, self.down_duration)

        with self.assertRaises(XYScreensConnectionError) as cm:
            screen._send_command_tcp(screen._commands.up)

        self.assertIn("Error while connecting to TCP endpoint", str(cm.exception))


class TestTCPConnectionAsync(unittest.IsolatedAsyncioTestCase):
    """Unit tests for async TCP connection functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.address = b"\x01"
        self.down_duration = 30.0
        self.up_duration = 25.0

    async def test_async_tcp_send_command_with_mock_server(self):
        """Test sending command via TCP asynchronously with a mock server."""
        server = MockTCPServer()
        server.start()

        try:
            screen = XYScreens(server.get_endpoint(), self.address, self.down_duration)

            result = await screen._async_send_command_tcp(screen._commands.down)
            self.assertTrue(result)

            await asyncio.sleep(0.1)
            self.assertEqual(len(server.received_data), 1)
            self.assertEqual(server.received_data[0], screen._commands.down)

        finally:
            server.stop()

    async def test_async_tcp_send_command_connection_error(self):
        """Test async TCP connection error handling."""
        screen = XYScreens("127.0.0.1:99999", self.address, self.down_duration)

        with self.assertRaises(XYScreensConnectionError) as cm:
            await screen._async_send_command_tcp(screen._commands.stop)

        self.assertIn("Error while connecting to TCP endpoint", str(cm.exception))

    async def test_async_tcp_send_command_timeout(self):
        """Test async TCP connection timeout handling."""
        screen = XYScreens("192.0.2.1:9999", self.address, self.down_duration)

        with self.assertRaises(XYScreensConnectionError) as cm:
            await screen._async_send_command_tcp(screen._commands.program)

        self.assertIn("Error while connecting to TCP endpoint", str(cm.exception))

    async def test_high_level_async_methods_tcp(self):
        """Test high-level async methods with TCP connection."""
        server = MockTCPServer()
        server.start()

        try:
            screen = XYScreens(server.get_endpoint(), self.address, self.down_duration, position=50.0)

            result = await screen.async_up()
            self.assertTrue(result)

            await asyncio.sleep(0.2)
            self.assertGreater(len(server.received_data), 0)

        finally:
            server.stop()


class TestMixedConnections(unittest.TestCase):
    """Test mixed serial and TCP connection scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.address = b"\x01"
        self.down_duration = 30.0

    @patch('serial.Serial')
    def test_send_command_routes_to_serial(self, mock_serial):
        """Test that _send_command routes to serial for serial connections."""
        mock_connection = Mock()
        mock_connection.is_open = False
        mock_serial.return_value = mock_connection

        screen = XYScreens("/dev/ttyUSB0", self.address, self.down_duration)
        screen._send_command(screen._commands.up)

        mock_serial.assert_called_once()
        mock_connection.open.assert_called_once()
        mock_connection.write.assert_called_once()

    @patch('socket.socket')
    def test_send_command_routes_to_tcp(self, mock_socket_cls):
        """Test that _send_command routes to TCP for TCP connections."""
        mock_sock = Mock()
        mock_sock.__enter__ = Mock(return_value=mock_sock)
        mock_sock.__exit__ = Mock(return_value=False)
        mock_socket_cls.return_value = mock_sock

        screen = XYScreens("192.168.1.100:9997", self.address, self.down_duration)
        screen._send_command(screen._commands.down)

        mock_socket_cls.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_sock.connect.assert_called_once_with(("192.168.1.100", 9997))
        mock_sock.sendall.assert_called_once()


if __name__ == "__main__":
    unittest.main()
