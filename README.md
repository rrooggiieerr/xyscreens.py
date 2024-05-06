# Python library to control XY Screens projector screens and projector lifts.

[![GitHub Release][releases-shield]][releases]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]

# Introduction

This python library lets you control XY Screens projector screens and projector lifts over the RS-485 interface.

XY Screens is an OEM manufacturer of projector screens and projector lifts.

## Features

- Synchronous and asynchronous methods
- Calculates screen position

## Hardware
I use a cheap USB RS-485 controller from eBay to talk to the projector screen where position 5 of the RJ25
connector is connected to D+ and position 6 to the D-.

See the documentation of your specific device on how to wire yours correctly.

## Protocol

This are the protocol details:\
2400 baud 8N1\
Up command  : 0xFFAAEEEEDD\
Down command: 0xFFAAEEEEEE\
Stop command: 0xFFAAEEEECC

## Known to work

* iVisions Electro M Series

Not tested but uses the same protocol according to the documentation:
* iVisions Electro L/XL/Pro/HD Series
* iVisions PL Series projector lift
* Elite Screens
* KIMEX
* DELUXX

Please let me know if your projector screen or projector lift works with this library so I can improve the overview of supported devices.

## Installation

You can install the Python XY Screens library using the Python package manager PIP:\
`pip3 install xyscreens`

## xyscreens CLI
You can use the Python XY Screens library directly from the command line to move your screen up or down or to stop the screen using the following syntax:

Move the screen down: `python3 -m xyscreens <serial port> down`\
Stop the screen: `python3 -m xyscreens <serial port> stop`\
Move the screen up: `python3 -m xyscreens <serial port> up`

If you add the arguments `--wait <time>` to the down and up commands where
`<time>` is the time in seconds to move the screen down, respectively up, the
process will wait till the screen is down/up and show the progress.

Do you enjoy using this Python library? Then consider supporting my work:\
[<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >](https://www.buymeacoffee.com/rrooggiieerr)  

---

[buymecoffee]: https://www.buymeacoffee.com/rrooggiieerr
[buymecoffee-shield]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate?style=for-the-badge
[releases-shield]: https://img.shields.io/github/v/release/rrooggiieerr/xyscreens.py?style=for-the-badge
[releases]: https://github.com/rrooggiieerr/xyscreens.py/releases
