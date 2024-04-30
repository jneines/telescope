#!/usr/bin/env python3
import asyncio
import time
import functools
from pathlib import Path

import click
import gpiozero
from gpiozero.pins.pigpio import PiGPIOFactory

from async_app.app import AsyncApp
import async_app.messenger as app_messenger
from async_app.logger import logger
from async_app.app_factory import async_app_options

from motor import Motor


@click.command()
@async_app_options
def main(**kwargs):

    app = AsyncApp(**kwargs)
    motor = Motor()
    task_descriptions = [
        {
            "kind": "continuous",
            "function": app_messenger.listener,
            "args": ("motor:command", motor.command),
        }
    ]

    for task_description in task_descriptions:
        app.add_task_description(task_description)

    asyncio.run(app.run(), debug=True)


if __name__ == "__main__":
    main()
