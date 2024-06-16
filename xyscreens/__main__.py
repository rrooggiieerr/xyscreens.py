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


async def main(port: str, address: bytes, wait: int, action: str):
    "The main function."

    if wait <= 0:
        down_duration = 1
    else:
        down_duration = wait

    try:
        if action == "up":
            screen = XYScreens(port, address, down_duration, position=100.0)
            if not await screen.async_up():
                return

            while wait > 0:
                (state, position) = screen.update_status()
                _print_status(state, position)
                if state == XYScreensState.UP:
                    if _LOGGER.level <= logging.DEBUG:
                        print()
                    break
                await asyncio.sleep(0.1)
        elif action == "down":
            screen = XYScreens(port, address, down_duration, position=0.0)
            if not await screen.async_down():
                return

            while wait > 0:
                (state, position) = screen.update_status()
                _print_status(state, position)
                if state == XYScreensState.DOWN:
                    if _LOGGER.level <= logging.DEBUG:
                        print()
                    break
                await asyncio.sleep(0.1)
        else:
            screen = XYScreens(port, address, 1)
            match action:
                case "stop":
                    await screen.async_stop()
                case "micro_up":
                    await screen.async_micro_up()
                case "micro_down":
                    await screen.async_micro_down()
                case "program":
                    await screen.async_program()
    except KeyboardInterrupt:
        # Handle keyboard interrupt
        pass


if __name__ == "__main__":
    # Read command line arguments
    argparser = argparse.ArgumentParser()
    argparser.add_argument("port")
    argparser.add_argument("address")
    argparser.add_argument(
        "action", choices=["up", "stop", "down", "micro_up", "micro_down", "program"]
    )
    argparser.add_argument("wait", nargs="?", type=int, default=0)
    argparser.add_argument("--debug", dest="debugLogging", action="store_true")

    args = argparser.parse_args()

    if args.debugLogging:
        logging.basicConfig(
            format="%(asctime)s %(levelname)-8s %(filename)s:%(lineno)d %(message)s", level=logging.DEBUG
        )
    else:
        logging.basicConfig(format="%(message)s", level=logging.INFO)

    loop = asyncio.new_event_loop()
    try:
        main_task = loop.run_until_complete(
            main(args.port, bytes.fromhex(args.address), args.wait, args.action)
        )
    finally:
        loop.close()
