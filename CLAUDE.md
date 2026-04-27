# xyscreens.py

Python library for controlling XY Screens and See Max projector screens/lifts via RS-485 (serial or TCP).

## Tech Stack

- **Language**: Python 3.11+
- **Build**: Hatchling + hatch-vcs (version from git tags)
- **Dependencies**: `pyserial`, `pyserial-asyncio-fast`
- **Linting**: pylint, isort (black profile), black, mypy
- **Tests**: unittest (stdlib), `unittest.IsolatedAsyncioTestCase` for async
- **CI**: GitHub Actions — publishes to PyPI on release

## Commands

```bash
# Install in dev mode
pip install -e .

# Run tests (from project root)
python -m pytest tests/
# Or with unittest directly
python -m unittest discover -s tests

# Type check
mypy xyscreens/

# CLI usage
python -m xyscreens <port> <address_hex> <action> [wait]
# Actions: up, stop, down, micro_up, micro_down, program
# Example: python -m xyscreens /dev/ttyUSB0 AAEEEE down 60
```

## Architecture

Single-class library (`XYScreens`) with sync and async APIs:

```
XYScreens.__init__(serial_port, address, down_duration, up_duration, position)
├── Serial connection: pyserial / pyserial-asyncio-fast
├── TCP connection:    stdlib socket / asyncio.open_connection
├── Position tracking: time-based interpolation (no feedback from hardware)
└── State machine:     UP ↔ UPWARD ↔ STOPPED ↔ DOWNWARD ↔ DOWN
```

Connection type is auto-detected from the endpoint string: paths starting with `/` or without `:` → serial; `host:port` → TCP.

## Conventions

- Dual API pattern: sync `method()` and async `async_method()` for every command
- Position: `0.0` = fully retracted (up), `100.0` = fully extended (down)
- Commands are 3-byte RS-485 frames: `0xFF` + address + command byte
- `_version.py` is auto-generated — excluded from linting/formatting
- Tests in `tests/` require `tests/settings.json` with `serial_port` and `address`

## Key Design Decisions

- Position is computed from elapsed time and configured durations (no encoder feedback)
- `task_helper.py` prevents garbage collection of fire-and-forget asyncio tasks
- `_send_command` opens and closes a connection per command (no persistent connection)
- `set_position` uses a polling loop to reach target, then auto-stops
