# Python library to control XY Screens projector screens and lifts

![Python][python-shield]
[![GitHub Release][releases-shield]][releases]
[![Licence][license-badge]][license]\
[![Github Sponsors][github-shield]][github]
[![PayPal][paypal-shield]][paypal]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]
[![Patreon][patreon-shield]][patreon]

# Introduction

This python library lets you control XY Screens projector screens and lifts over the RS-485 interface.

XY Screens is an OEM manufacturer of projector screens and lifts, their devices are sold around the world under various brand names.

## Features

- Synchronous and asynchronous methods
- Calculates screen position

## Hardware

I use a cheap USB RS-485 controller from eBay to talk to the projector screen where position 5 of the RJ25
connector is connected to D+ and position 6 to the D-.

![image](usb-rs485.png)

See the documentation of your specific device on how to wire yours correctly.

## Supported protocol

If your devices follows the following protocol it's supported by this Python library:

2400 baud 8N1\
Up command  : 0xFFAAEEEEDD\
Down command: 0xFFAAEEEEEE\
Stop command: 0xFFAAEEEECC

## Known to work

The following device is known to work:

* iVisions Electro M Series

The following device are not tested but use the same protocol according to the documentation:

* iVisions Electro L/XL/Pro/HD Series
* iVisions PL Series projector lift
* Elite Screens
* KIMEX
* DELUXX

Please let me know if your projector screen or projector lift works with this Python library so I can improve the overview of supported devices.

## Installation

You can install the Python XY Screens library using the Python package manager PIP:

`pip3 install xyscreens`

## xyscreens CLI

You can use the Python XY Screens library directly from the command line to move your screen up or down or to stop the screen using the following syntax:

Move the screen down: `python3 -m xyscreens <serial port> down`\
Stop the screen: `python3 -m xyscreens <serial port> stop`\
Move the screen up: `python3 -m xyscreens <serial port> up`

If you add the arguments `--wait <time>` to the down and up commands where `<time>` is the time in seconds to move the screen down, respectively up, the
process will wait till the screen is down/up and show the progress.

## Support

Do you enjoy using this Python library? Then consider supporting my work using one of the following platforms:

[![Github Sponsors][github-shield]][github]
[![PayPal][paypal-shield]][paypal]
[![BuyMeCoffee][buymecoffee-shield]][buymecoffee]
[![Patreon][patreon-shield]][patreon]

---

[python-shield]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[releases]: https://github.com/rrooggiieerr/xyscreens.py/releases
[releases-shield]: https://img.shields.io/github/v/release/rrooggiieerr/xyscreens.py?style=for-the-badge
[license]: ./LICENSE
[license-badge]: https://img.shields.io/github/license/rrooggiieerr/xyscreens.py?style=for-the-badge
[paypal]: https://paypal.me/seekingtheedge
[paypal-shield]: https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white
[buymecoffee]: https://www.buymeacoffee.com/rrooggiieerr
[buymecoffee-shield]: https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black
[github]: https://github.com/sponsors/rrooggiieerr
[github-shield]: https://img.shields.io/badge/sponsor-30363D?style=for-the-badge&logo=GitHub-Sponsors&logoColor=ea4aaa
[patreon]: https://www.patreon.com/seekingtheedge/creators
[patreon-shield]: https://img.shields.io/badge/Patreon-F96854?style=for-the-badge&logo=patreon&logoColor=white
