# tests/ — Test Suite

## Files

| File | Role |
|---|---|
| `test_xyscreens.py` | Main test suite — constructor, state, position, sync + async operations |
| `test_tcp_connection.py` | TCP-specific tests — endpoint parsing, mock TCP server, routing |
| `test_all_commands.py` | Hardware brute-force test — iterates all 256 command bytes (requires real device) |
| `settings.json` | Test config: `serial_port` and `address` for hardware tests |

## Patterns

- All test classes extend `unittest.TestCase` or `unittest.IsolatedAsyncioTestCase`
- `test_xyscreens.py` reads connection settings from `tests/settings.json` in `asyncSetUp`
- `test_tcp_connection.py` uses `MockTCPServer` (threaded) for integration tests and `unittest.mock.patch` for unit tests
- Time-dependent tests use `time.sleep()` / `asyncio.sleep()` with `assertAlmostEqual(delta=0.3)` for position checks
- `test_all_commands.py` requires a physical RS-485 device — not suitable for CI

## Running Tests

```bash
# All tests (some require hardware or settings.json)
python -m unittest discover -s tests

# TCP tests only (no hardware needed)
python -m unittest tests.test_tcp_connection

# Skip hardware-dependent tests in CI by not providing settings.json
```

## Adding Tests

1. Create test class extending `unittest.IsolatedAsyncioTestCase` for async tests
2. Use `MockTCPServer` from `test_tcp_connection.py` for TCP integration tests
3. Use `unittest.mock.patch` for serial port mocking
4. Position assertions: use `assertAlmostEqual(expected, actual, delta=0.3)` for time-based values
