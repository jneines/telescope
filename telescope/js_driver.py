import asyncio
import time
import functools
import signal
from collections import defaultdict

from evdev import InputDevice, list_devices, ecodes, categorize

import click
import async_timeout

import async_app.state as app_state
from async_app.logger import logger


class ButtonMapping(dict):
    def __missing__(self, key):
        # default setting is reflect key
        return key


class EventMapping(dict):
    def __missing__(self, key):
        return lambda v: print(f"Unbound {key=}: {v}")


class AsyncEventMapping(dict):
    def __missing__(self, key):
        return lambda v: asyncio.sleep(1e-6)


# def get_empty_event_mapping():
#    # The asyncio pass equivalent that can be awaited
#    return defaultdict(lambda: lambda ev_name, ev_value: Action(ev_name, ev_value))


# default_event_mapping = get_empty_event_mapping()
default_event_mapping = EventMapping()


class JSDriver(object):

    def __init__(self, number, button_mapping, event_mapping=default_event_mapping):
        self.button_mapping = button_mapping
        self.event_mapping = event_mapping
        js_devices = list_devices()
        logger.debug(f"{js_devices=}")

        self.js = InputDevice(js_devices[number])
        logger.info(f"Joystick in use: {self.js}")

    async def event_reader(self):

        while app_state.keep_running:
            try:
                async with async_timeout.timeout(0.05):
                    event = await self.js.async_read_one()
                    abs_event = categorize(event)
                    if event.type == ecodes.EV_ABS:
                        # axis event
                        axis_name = ecodes.bytype[abs_event.event.type][
                            abs_event.event.code
                        ]
                        await self.event_mapping[axis_name](event.value)
                    elif event.type == ecodes.EV_KEY:
                        # button event
                        btn_name = abs_event.keycode[0]
                        value = "pressed" if event.value == 1 else "released"
                        await self.event_mapping[btn_name](value)

            except asyncio.TimeoutError:
                pass


# Button Mapping for the speedlink controller
speedlink_button_mapping = ButtonMapping()
speedlink_button_mapping["BTN_NORTH"] = "BTN_X"
speedlink_button_mapping["BTN_WEST"] = "BTN_Y"


@click.command
@click.option(
    "-n",
    "--number",
    type=int,
    default=0,
    show_default=True,
    help="Joystick number to use",
)
def main(number):
    event_mapping = EventMapping()
    event_mapping["ABS_X"] = lambda v: print(v)

    js_driver = JSDriver(number, button_mapping, event_mapping)
    asyncio.run(js_driver.event_reader())


if __name__ == "__main__":
    main()
