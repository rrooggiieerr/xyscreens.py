Python library to control XY Screens projector screens and projector lifts.
=
Python library to control XY Screens projector screens and projector lifts over the RS485 interface.

XY Screens is an OEM manufacturer of projector screen and projector lifts.

I use a cheap USB RS485 controler from eBay to talk to the projector screen where position 5 of the RJ25 connector is connected to D+ and position 6 to the D-.

See the documentation of your specific device on how to wire yours correctly.

This are the protocol details:\
2400 baud 8N1\
up command  : 0xFF 0xAA 0xEE 0xEE 0xDD\
down command: 0xFF 0xAA 0xEE 0xEE 0xEE\
stop command: 0xFF 0xAA 0xEE 0xEE 0xCC

Known to work:\
iVisions Electro M Series

Not tested but uses te same protocol according to the documentation:\
iVisions Electro L/XL/Pro/HD Series\
iVisions PL Series projector lift\
Elite Screens\
KIMEX\
DELUXX

Please let me know if your projector screen or projector lift works with this library so I can improve the overview of supported devices.