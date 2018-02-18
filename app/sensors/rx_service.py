#!/usr/bin/python
"""
    Author: Fabio Hellmann <info@fabio-hellmann.de>
"""

import threading
import time
import logging
from datetime import datetime

from ..hardware.rf_rpi import Device
from ..hardware.gpio import RaspberryPi3 as GPIO_PI

_LOGGER = logging.getLogger(__name__)


class RxService:
    def __init__(self):
        self.rx_device = Device(GPIO_PI.GPIO_27)
        self.result = None

    def __del__(self):
        self.rx_device.cleanup()

    def search_verified_signals(self, time_to_search_sec):
        threading.Thread(target=self._listening, args=time_to_search_sec).start()

    def get_result(self):
        return self.result

    def _listening(self, time_to_search_sec):
        self.rx_device.enable_rx()
        rf_signal_counter = {}
        rf_signal_dict = {}
        self.result = []
        start_time = datetime.now()

        timestamp = None
        while datetime.now() - start_time < time_to_search_sec:
            if self.rx_device.rx_signal.time != timestamp:
                rf_signal = self.rx_device.rx_signal
                timestamp = rf_signal.time

                rf_signal_dict[str(rf_signal.code)] = rf_signal
                rf_signal_counter[str(rf_signal.code)] += 1

                # Signal found -> filter only the signals we would like to see
                if rf_signal_counter[str(rf_signal.code)] >= 3:
                    self.result.append(rf_signal)

            time.sleep(0.01)

        self.rx_device.disable_rx()