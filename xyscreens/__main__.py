"""
Created on 18 Nov 2022

@author: Rogier van Staveren
"""
import argparse
import logging
import time

from xyscreens import XYScreens

_LOGGER = logging.getLogger(__name__)


if __name__ == "__main__":
    # Read command line arguments
    argparser = argparse.ArgumentParser()
    argparser.add_argument("port")
    argparser.add_argument("action", choices=["up", "stop", "down"])
    argparser.add_argument("--wait", dest="wait", type=int)
    argparser.add_argument("--debug", dest="debugLogging", action="store_true")

    args = argparser.parse_args()

    if args.debugLogging:
        logging.basicConfig(
            format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG
        )
    else:
        logging.basicConfig(format="%(message)s", level=logging.INFO)

    if args.action == "up":
        screen = XYScreens(args.port, time_up=args.wait, position=100.0)
        if screen.up():
            while True:
                state = screen.state()
                position = screen.position()
                if not args.debugLogging:
                    print(f"{screen.STATES[state]:8}: {position:5.1f} %", end="\r")
                else:
                    _LOGGER.info("%s: %5.1f %%", screen.STATES[state], position)
                if state == screen.STATE_UP:
                    if not args.debugLogging:
                        print()
                    break
                time.sleep(0.1)
    elif args.action == "stop":
        screen = XYScreens(args.port)
        screen.stop()
    elif args.action == "down":
        screen = XYScreens(args.port, time_down=args.wait, position=0.0)
        if screen.down():
            while True:
                state = screen.state()
                position = screen.position()
                if not args.debugLogging:
                    print(f"{screen.STATES[state]:8}: {position:5.1f} %", end="\r")
                else:
                    _LOGGER.info("%s: %5.1f %%", screen.STATES[state], position)
                if state == screen.STATE_DOWN:
                    if not args.debugLogging:
                        print()
                    break
                time.sleep(0.1)
