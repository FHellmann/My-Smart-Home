"""
    Author: Fabio Hellmann <info@fabio-hellmann.de>

    Sending and receiving 433/315Mhz signals with low-cost GPIO RF Modules on a Raspberry Pi.

    Original: https://github.com/milaq/rpi-radiofrequency
"""

import logging
import time
from datetime import datetime

from RPi import GPIO

from .models import Signal, ProtocolType

MAX_CHANGES = 67

_LOGGER = logging.getLogger(__name__)


class Device:
    """Representation of a GPIO RF device."""

    # pylint: disable=too-many-instance-attributes,too-many-arguments
    def __init__(self, gpio,
                 tx_proto=ProtocolType.PL_350.value, tx_pulse_length=None, tx_repeat=10, tx_length=24, rx_tolerance=80):
        """Initialize the RF device."""
        self.gpio = gpio
        self.tx_enabled = False
        self.tx_proto = tx_proto
        if tx_pulse_length:
            self.tx_pulse_length = tx_pulse_length
        else:
            self.tx_pulse_length = tx_proto.pulse_length
        self.tx_repeat = tx_repeat
        self.tx_length = tx_length
        self.rx_enabled = False
        self.rx_tolerance = rx_tolerance
        # internal values
        self._rx_timings = [0] * (MAX_CHANGES + 1)
        self._rx_last_timestamp = 0
        self._rx_change_count = 0
        self._rx_repeat_count = 0
        # successful RX values
        self._rx_listener = None

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        _LOGGER.info("Using GPIO " + str(gpio))

    def cleanup(self):
        """Disable TX and RX and clean up GPIO."""
        if self.tx_enabled:
            self.disable_tx()
        if self.rx_enabled:
            self.disable_rx()
        _LOGGER.info("Cleanup")
        GPIO.cleanup()

    def enable_tx(self):
        """Enable TX, set up GPIO."""
        if self.rx_enabled:
            _LOGGER.error("RX is enabled, not enabling TX")
            return False
        if not self.tx_enabled:
            self.tx_enabled = True
            GPIO.setup(self.gpio, GPIO.OUT)
            _LOGGER.info("TX enabled")
        return True

    def disable_tx(self):
        """Disable TX, reset GPIO."""
        if self.tx_enabled:
            # set up GPIO pin as input for safety
            GPIO.setup(self.gpio, GPIO.IN)
            self.tx_enabled = False
            _LOGGER.info("TX disabled")
        return True

    def tx_code(self, signal):
        """
        Send a decimal code.
        Optionally set protocol and pulselength.
        When none given reset to default protocol and pulselength.
        """
        if signal.protocol:
            self.tx_proto = signal.protocol
        else:
            self.tx_proto = ProtocolType.PL_350.value
        if signal.pulse_length:
            self.tx_pulse_length = signal.pulse_length
        else:
            self.tx_pulse_length = self.tx_proto.pulse_length
        rawcode = format(signal.code, '#0{}b'.format(self.tx_length + 2))[2:]
        _LOGGER.info("TX code: " + str(signal.code))
        return self.tx_bin(rawcode)

    def tx_bin(self, rawcode):
        """Send a binary code."""
        _LOGGER.info("TX bin: " + str(rawcode))
        for _ in range(0, self.tx_repeat):
            for byte in range(0, self.tx_length):
                if rawcode[byte] == '0':
                    if not self.tx_l0():
                        return False
                else:
                    if not self.tx_l1():
                        return False
            if not self.tx_sync():
                return False
        return True

    def tx_l0(self):
        """Send a '0' bit."""
        return self.tx_waveform(self.tx_proto.zero_high,
                                self.tx_proto.zero_low)

    def tx_l1(self):
        """Send a '1' bit."""
        return self.tx_waveform(self.tx_proto.one_high,
                                self.tx_proto.one_low)

    def tx_sync(self):
        """Send a sync."""
        return self.tx_waveform(self.tx_proto.sync_high,
                                self.tx_proto.sync_low)

    def tx_waveform(self, highpulses, lowpulses):
        """Send basic waveform."""
        if not self.tx_enabled:
            _LOGGER.error("TX is not enabled, not sending data")
            return False
        GPIO.output(self.gpio, GPIO.HIGH)
        time.sleep((highpulses * self.tx_pulse_length) / 1000000)
        GPIO.output(self.gpio, GPIO.LOW)
        time.sleep((lowpulses * self.tx_pulse_length) / 1000000)
        return True

    def enable_rx(self):
        """Enable RX, set up GPIO and add event detection."""
        if self.tx_enabled:
            _LOGGER.error("TX is enabled, not enabling RX")
            return False
        if not self.rx_enabled:
            self.rx_enabled = True
            GPIO.setup(self.gpio, GPIO.IN)
            GPIO.add_event_detect(self.gpio, GPIO.BOTH)
            GPIO.add_event_callback(self.gpio, self.rx_callback)
            _LOGGER.info("RX enabled")
        return True

    def disable_rx(self):
        """Disable RX, remove GPIO event detection."""
        if self.rx_enabled:
            GPIO.remove_event_detect(self.gpio)
            self.rx_enabled = False
            _LOGGER.info("RX disabled")
        return True

    def add_rx_listener(self, listener):
        self._rx_listener = listener

    # pylint: disable=unused-argument
    def rx_callback(self, gpio):
        """RX callback for GPIO event detection. Handle basic signal detection."""
        timestamp = int(time.perf_counter() * 1000000)
        duration = timestamp - self._rx_last_timestamp

        if duration > 5000:
            if duration - self._rx_timings[0] < 200:
                self._rx_repeat_count += 1
                self._rx_change_count -= 1
                if self._rx_repeat_count == 2:
                    for name, protocol in ProtocolType.__members__.items():
                        if self._rx_waveform(protocol.value, self._rx_change_count):
                            break
                    self._rx_repeat_count = 0
            self._rx_change_count = 0

        if self._rx_change_count >= MAX_CHANGES:
            self._rx_change_count = 0
            self._rx_repeat_count = 0
        self._rx_timings[self._rx_change_count] = duration
        self._rx_change_count += 1
        self._rx_last_timestamp = timestamp

    def _rx_waveform(self, protocol, change_count):
        """Detect waveform and format code."""
        code = 0
        delay = int(self._rx_timings[0] / protocol.sync_low)
        delay_tolerance = delay * self.rx_tolerance / 100

        for i in range(1, change_count, 2):
            if (self._rx_timings[i] - delay * protocol.zero_high < delay_tolerance and
                    self._rx_timings[i + 1] - delay * protocol.zero_low < delay_tolerance):
                code <<= 1
            elif (self._rx_timings[i] - delay * protocol.one_high < delay_tolerance and
                  self._rx_timings[i + 1] - delay * protocol.one_low < delay_tolerance):
                code <<= 1
                code |= 1
            else:
                return False

        if self._rx_change_count > 6 and code != 0:
            _LOGGER.info("RX code " + str(code))
            if not(self._rx_listener is None):
                signal = Signal(code=code, pulse_length=delay, bit_length=int(change_count / 2), protocol=protocol,
                                timestamp=datetime.utcnow())
                self._rx_listener(signal)
            return True

        return False
