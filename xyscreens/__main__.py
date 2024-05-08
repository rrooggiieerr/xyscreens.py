"""
Created on 18 Nov 2022

@author: Rogier van Staveren
"""

import argparse
import asyncio
import logging

from xyscreens import XYScreens, XYScreensState

_LOGGER = logging.getLogger(__name__)


def _print_status(state: XYScreensState, position: float):
    if _LOGGER.isEnabledFor(logging.DEBUG):
        _LOGGER.info("%-8s: %5.1f %%", state, position)
    else:
        print(f"{state!s:8}: {position:5.1f} %", end="\r")


async def main(port: str, wait: int, action: str):
    "The main function."
    try:
        if action == "up":
            screen = XYScreens(port, wait, position=100.0)
            if not await screen.async_up():
                return

            while True:
                (state, position) = screen.update_status()
                _print_status(state, position)
                if state == XYScreensState.UP:
                    if _LOGGER.level <= logging.DEBUG:
                        print()
                    break
                await asyncio.sleep(0.1)
        elif action == "stop":
            screen = XYScreens(port, wait)
            await screen.async_stop()
        elif action == "down":
            screen = XYScreens(port, wait, position=0.0)
            if not await screen.async_down():
                return

            while True:
                (state, position) = screen.update_status()
                _print_status(state, position)
                if state == XYScreensState.DOWN:
                    if _LOGGER.level <= logging.DEBUG:
                        print()
                    break
                await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        # Handle keyboard interrupt
        pass


if __name__ == "__main__":
    # Read command line arguments
    argparser = argparse.ArgumentParser()
    argparser.add_argument("port")
    argparser.add_argument("wait", type=int)
    argparser.add_argument("action", choices=["up", "stop", "down"])
    argparser.add_argument("--debug", dest="debugLogging", action="store_true")

    args = argparser.parse_args()

    if args.debugLogging:
        logging.basicConfig(
            format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG
        )
    else:
        logging.basicConfig(format="%(message)s", level=logging.INFO)

    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(main(args.port, args.wait, args.action))
    finally:
        loop.close()
