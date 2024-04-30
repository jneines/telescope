import asyncio
import time
import functools
import signal

import click
import numpy as np

import async_app.messenger as app_messenger
import async_app.state as app_state
from async_app.app_factory import async_app_options
from async_app.app import AsyncApp
from async_app.logger import logger

from js_driver import JSDriver, speedlink_button_mapping, AsyncEventMapping

speed_mapper = functools.partial(
    np.interp,
    xp=[-32676, 0, 32767],
    fp=[-100, 0.08, 100],
)


async def set_speed(ev_value):
    speed = speed_mapper(ev_value)
    logger.debug(f"Requesting {speed=}")
    await app_messenger.publish(
        "motor:command", {"command": "set_speed", "speed": speed}
    )


async def fine_tune_speed(ev_value):
    logger.debug(f"Fine tuning motor speed: {ev_value}")
    await app_messenger.publish(
        "motor:command", {"command": "fine_tune_speed", "delta_speed": ev_value}
    )


async def toggle_active_state(ev_value):
    logger.debug("Toggle motor controller active state.")
    if ev_value == "pressed":
        await app_messenger.publish("motor:command", {"command": "toggle_active_state"})


@click.command
@async_app_options
@click.option(
    "-n",
    "--number",
    type=int,
    default=0,
    show_default=True,
    help="Joystick number to use.",
)
def main(number, **kwargs):

    event_mapping = AsyncEventMapping()
    event_mapping["BTN_A"] = lambda value: toggle_active_state(value)
    event_mapping["ABS_X"] = lambda value: set_speed(value)
    event_mapping["ABS_RX"] = lambda value: set_speed(value / 1250)
    event_mapping["ABS_HAT0X"] = lambda value: fine_tune_speed(value)

    app = AsyncApp(**kwargs)
    js = JSDriver(number, speedlink_button_mapping, event_mapping)

    task_descriptions = [
        {
            "kind": "continuous",
            "function": js.event_reader,
        },
    ]
    for task_description in task_descriptions:
        app.add_task_description(task_description)

    asyncio.run(app.run(), debug=True)


if __name__ == "__main__":
    main()
