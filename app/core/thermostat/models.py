#!/usr/bin/python
"""
    Author: Fabio Hellmann <info@fabio-hellmann.de>
"""

from attr import s, ib
from attr.validators import instance_of
from enum import Enum, unique
from datetime import datetime


@unique
class ThermostatManufacturer(Enum):
    COMET_BLUE = "comet blue"


@s(frozen=True)
class ThermostatEntry(object):
    thermostat_name = ib(validator=instance_of(str), type=str)
    type = ib(validator=instance_of(ThermostatManufacturer), type=ThermostatManufacturer)
    timestamp = ib(validator=instance_of(datetime), type=datetime)
    current_temp = ib(validator=instance_of(float), type=float)
    manual_temp = ib(validator=instance_of(float), type=float)
    target_temp_low = ib(validator=instance_of(float), type=float)
    target_temp_high = ib(validator=instance_of(float), type=float)
    offset_temp = ib(validator=instance_of(float), type=float)
    window_open_detection = ib(validator=instance_of(int), type=int)
    window_open_minutes = ib(validator=instance_of(int), type=int)
