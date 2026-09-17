"""
XY Screens Unit Tests.
"""

import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(filename)s:%(lineno)d %(message)s",
    level=logging.DEBUG,
)

URL = "/dev/cu.some_port"
ADDRESS = b"\xaa\xee\xee"
