#!/usr/bin/env python3
"""

Needs 

dtoverlay=pwm,pin=18,func=5,pin2=19,func2=2

in /boot/config.txt

"""
import asyncio
import time
import functools
from pathlib import Path
import atexit

import numpy as np

import gpiozero
from rpi_hardware_pwm import HardwarePWM

from async_app.logger import logger


class Motor(object):
    motor_pins = {
        1: {
            "enable": 12,
            "direction": 13,
            # "step": 19,  # defined by dt-overlay
            "mode": (16, 17, 20),
        },
        0: {
            "enable": 4,
            "direction": 24,
            # "step": 18, # defined by dt-overlay
            "mode": (21, 22, 27),
        },
    }

    def __init__(self, motor_id=1, frequency=100):
        self.motor_id = motor_id
        self.frequency = frequency
        self.pwm = HardwarePWM(pwm_channel=motor_id, hz=60, chip=0)

        logger.info(f"Initializing Motor {motor_id}")

        self.enable_pin = gpiozero.DigitalOutputDevice(
            self.motor_pins[motor_id]["enable"]
        )

        self.direction_pin = gpiozero.DigitalOutputDevice(
            self.motor_pins[motor_id]["direction"]
        )
        max_frequency = 45_000
        self.current_frequency = 1

        self.speed_mapper = functools.partial(
            np.interp,
            xp=[-100, 0, 100],
            fp=[max_frequency, self.current_frequency, max_frequency],
        )

        self.is_active = False

        atexit.register(self.disable)



    def enable(self):
        logger.info("Enabling motor")

        self.pwm.start(100)
        self.pwm.change_duty_cycle(50)
        self.enable_pin.on()

        self.is_active = True

    def disable(self):
        logger.info("Disabling motor")

        self.enable_pin.off()
        self.pwm.stop()

        self.is_active = False

    def toggle_active_state(self):
        self.disable() if self.is_active else self.enable()

    def set_direction(self, direction="forward"):
        logger.info(f"Setting {direction=}")

        if direction == "forward":
            self.direction_pin.off()
        elif direction == "backward":
            self.direction_pin.on()

    def set_frequency(self, frequency):
        logger.info(f"Setting PWM {frequency=}")
        self.pwm.change_frequency(frequency)
        self.current_frequency = frequency

    def fine_tune_speed(self, delta_speed):
        new_frequency = max(1, self.current_frequency + delta_speed)
        self.set_frequency(new_frequency)

    def set_speed(self, speed):
        frequency = int(self.speed_mapper(speed))
        self.set_frequency(frequency)

        if speed < 0:
            self.set_direction("backward")
        else:
            self.set_direction("forward")

    def command(self, record):
        """command dispatcher"""

        logger.debug(f"{record=}")
        command = record["command"]

        if command == "toggle_active_state":
            self.toggle_active_state()

        elif command == "set_speed":
            self.set_speed(record["speed"])

        elif command == "fine_tune_speed":
            self.fine_tune_speed(record["delta_speed"])

        elif command == "stop":
            self.disable()


if __name__ == "__main__":
    import atexit

    motor = Motor()
    atexit.register(motor.disable)

    motor.set_frequency(35_000)
    while True:
        motor.enable()
        motor.set_direction("forward")

        time.sleep(2)
        motor.disable()

        time.sleep(0.5)

        motor.enable()
        motor.set_direction("backward")
        time.sleep(2)
        motor.disable()

        time.sleep(0.5)
