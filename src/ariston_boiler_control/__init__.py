"""
Module for the control of a Wifi-enabled Ariston boiler through the Web API.

At the moment, this module only works with the default boiler specificed in the web interface.

Features:
    - read the current temperature
    - read and set the target temperature
    - read and set the operation mode (Green, Comfort, Fast, Auto, HCHP)
    - read the HP state (on/off)
    - read and set the boost mode (on/off)

Example:
    >>> from ariston_boiler_control import AristonBoilerControl, OperationMode
    >>> abc = AristonBoilerControl('email@email.com', 'password')
    >>> # executes the login with the username and password provided
    >>> # it is actually optional: it is done automatically when needed
    >>> abc.login()
    >>> # get the current temperature
    >>> temperature = abc.get_current_temperature()
    >>> # set the operation mode to comfort
    >>> abc.set_operation_mode(OperationMode.COMFORT)
    >>> # set the target temperature to 60 degrees
    >>> abc.set_target_temperature(60)

Copyright (c) 2023 Francesco Santini <francesco.santini@gmail.com>
"""

from ._boiler_control import AristonBoilerControl, AuthenticationError, HPState, OperationMode

__all__ = ['AristonBoilerControl', 'AuthenticationError', 'HPState', 'OperationMode']

VERSION = "0.0.5"
__version__ = VERSION

