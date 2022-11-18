"""
Created on 18 Nov 2022

@author: rogier
"""
import argparse
import logging

from xyscreens.XYScreens import XYScreens

logger = logging.getLogger(__name__)
loglevel = logging.INFO


if __name__ == "__main__":
    # Read command line arguments
    argparser = argparse.ArgumentParser()
    argparser.add_argument("port")
    argparser.add_argument("action", choices=["up", "stop", "down"])
    argparser.add_argument("--debug", dest="debugLogging", action="store_true")

    args = argparser.parse_args()

    if args.debugLogging:
        loglevel = logging.DEBUG

    screen = XYScreens(args.port)

    if args.action == "up":
        screen.up()
    elif args.action == "stop":
        screen.stop()
    elif args.action == "down":
        screen.down()
