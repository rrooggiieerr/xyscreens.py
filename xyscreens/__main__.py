"""
Created on 18 Nov 2022

@author: rogier
"""
import argparse
import logging
import time

from xyscreens.XYScreens import XYScreens

logger = logging.getLogger(__name__)
loglevel = logging.INFO


if __name__ == "__main__":
    # Read command line arguments
    argparser = argparse.ArgumentParser()
    argparser.add_argument("port")
    argparser.add_argument("action", choices=["up", "stop", "down"])
    argparser.add_argument("--wait", dest="wait", action="store_true")
    argparser.add_argument("--debug", dest="debugLogging", action="store_true")

    args = argparser.parse_args()

    if args.debugLogging:
        loglevel = logging.DEBUG
        logging.basicConfig(
            format="%(asctime)s %(levelname)-8s %(message)s", level=loglevel
        )
    else:
        logging.basicConfig(format="%(message)s", level=loglevel)

    screen = XYScreens(args.port)

    if args.action == "up":
        screen.set_position(100.0)
        if screen.up():
            if args.wait:
                while True:
                    state = screen.state()
                    position = screen.position()
                    if not args.debugLogging:
                        print(f"{screen.STATES[state]:8}: {position:5.1f} %", end="\r")
                    else:
                        logger.info("%s: %5.1f %%", screen.STATES[state], position)
                    if state == screen.STATE_UP:
                        if not args.debugLogging:
                            print()
                        break
                    time.sleep(0.1)
    elif args.action == "stop":
        screen.stop()
    elif args.action == "down":
        screen.set_position(0.0)
        if screen.down():
            if args.wait:
                while True:
                    state = screen.state()
                    position = screen.position()
                    if not args.debugLogging:
                        print(f"{screen.STATES[state]:8}: {position:5.1f} %", end="\r")
                    else:
                        logger.info("%s: %5.1f %%", screen.STATES[state], position)
                    if state == screen.STATE_DOWN:
                        if not args.debugLogging:
                            print()
                        break
                    time.sleep(0.1)
