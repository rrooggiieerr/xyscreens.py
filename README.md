# Python library to control XY Screens projector screens and projector lifts.
Python library to control XY Screens projector screens and projector lifts
over the RS-485 interface.

XY Screens is an OEM manufacturer of projector screens and projector lifts.

## Hardware
I use a cheap USB RS-485 controler from eBay to talk to the projector screen
where position 5 of the RJ25 connector is connected to D+ and position 6 to
the D-.

See the documentation of your specific device on how to wire yours correctly.

## Protocol
This are the protocol details:\
2400 baud 8N1\
Up command  : 0xFF 0xAA 0xEE 0xEE 0xDD\
Down command: 0xFF 0xAA 0xEE 0xEE 0xEE\
Stop command: 0xFF 0xAA 0xEE 0xEE 0xCC

## Known to work
* iVisions Electro M Series

Not tested but uses the same protocol according to the documentation:
* iVisions Electro L/XL/Pro/HD Series
* iVisions PL Series projector lift
* Elite Screens
* KIMEX
* DELUXX

Please let me know if your projector screen or projector lift works with this
library so I can improve the overview of supported devices.

## Installation
You can install the Python XY Screens library using the Python package manager
PIP:\
`pip3 install xyscreens`

## xyscreens CLI
You can use the Python XY Screens library directly from the command line to
move your screen up or down or to stop the screen using the follwoing syntax:

Move the screen down: `python3 -m xyscreens <serial port> down`\
Stop the screen: `python3 -m xyscreens <serial port> stop`\
Move the screen up: `python3 -m xyscreens <serial port> up`

If you add the arguments `--wait <time>` to the down and up commands where
`<time>` is the time in seconds to move the screen down, respectively up, the
process will wait till the screen is down/up and show the progress.