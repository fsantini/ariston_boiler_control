[![Documentation Status](https://readthedocs.org/projects/ariston-boiler-control/badge/?version=latest)](https://ariston-boiler-control.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/ariston-boiler-control.svg)](https://badge.fury.io/py/ariston-boiler-control)
![License - Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-brightgreen)

## ariston_boiler_control

Module for the control of a Wifi-enabled Ariston boiler through the Web API.

At the moment, this module only works with the default boiler specificed in the web interface.

Features:
* read the current temperature
* read and set the target temperature
* read and set the operation mode (Green, Comfort, Fast, Auto, HCHP)
* read the HP state (on/off)
* read and set the boost mode (on/off)

Example:
```python
    >>> from ariston_boiler_control import AristonBoilerControl, OperationMode
    >>> abc = AristonBoilerControl('email@email.com', 'password')
    >>> # alternatively, you can use the option `quiet_login` to avoid the 'Login successful' message
    >>> abc = AristonBoilerControl('email@email.com', 'password', quiet_login=True)
    >>> # executes the login with the username and password provided
    >>> # it is actually optional: it is done automatically when needed
    >>> abc.login()
    >>> # get the current temperature
    >>> temperature = abc.get_current_temperature()
    >>> # set the operation mode to comfort
    >>> abc.set_operation_mode(OperationMode.COMFORT)
    >>> # set the target temperature to 60 degrees
    >>> abc.set_target_temperature(60)
```
Copyright (c) 2023 Francesco Santini <francesco.santini@gmail.com>