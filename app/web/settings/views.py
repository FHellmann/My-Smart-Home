#!/usr/bin/python
"""
    Author: Fabio Hellmann <info@fabio-hellmann.de>
"""

from flask import render_template, request, redirect, url_for

from . import settings
from ...sensors.rx_service import RfController

rf_controller = RfController()


@settings.route('/')
def index():
    """
    Render the settings template on the / route
    """
    return render_template('settings/index.html', title="Settings")


@settings.route('/rf_devices')
def rf_devices():
    """
    Render the rf-device template on the /rf_devices route
    """
    return render_template('settings/rf_devices.html', title="Settings", devices=rf_controller.get_signals())


@settings.route('/rf_devices/test', methods=['POST'])
def rf_device_test():
    """
    Send the specific signal and return same site
    """
    rf_signal = request.form['rf_signal']
    rf_controller.send(rf_signal)
    return redirect(url_for('settings.rf_devices'))


@settings.route('/setup_assistant')
def setup_assistant():
    """
    Render the setup assistant on the /setup_assistant route
    """
    return render_template('settings/setup_assistant.html', title="Setup Assistant")