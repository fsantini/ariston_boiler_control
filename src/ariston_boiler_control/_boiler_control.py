from datetime import datetime
import re
import time
from enum import IntEnum

import requests

BASE_URL = 'https://www.ariston-net.remotethermo.com'
LOGIN_URL = BASE_URL + '/R2/Account/Login?returnUrl=%2FR2%2FHome'
DATA_BASE_URL = BASE_URL + '/R2/PlantHomeSlp/GetData/'
DATA_SUFFIX = '?fetchSettings=true&fetchTimeProg=true&rnd='

SET_DATA_URL = BASE_URL + '/R2/PlantHomeSlp/SetData/'


class OperationMode(IntEnum):
    """
    Enum representing the operating mode of the boiler
    """
    UNKNOWN = -1
    GREEN = 0
    COMFORT = 1
    FAST = 2
    AUTO = 3
    HCHP = 4

    @classmethod
    def _missing_(cls, value):
        return OperationMode.UNKNOWN


class HPState(IntEnum):
    """
    Enum representing the state of the heating pump
    """
    UNKNOWN = -1
    OFF = 1
    ON = 2

    @classmethod
    def _missing_(cls, value):
        return HPState.UNKNOWN



class AuthenticationError(ConnectionError):
    """
    Exception raised when authentication fails
    """
    pass


class AristonBoilerControl:
    """
    Class to control an Ariston boiler

    Attributes:
        email (str): the email address used to login to the Ariston website
        password (str): the password used to login to the Ariston website
        poll_interval (int, optional): the interval in seconds between polling for new data (default 30)
    """
    def __init__(self, email, password, poll_interval=30, quiet_login: bool = False):
        self.email = email
        self.password = password
        self.session = requests.session()
        self.poll_interval = poll_interval
        self.quiet_login = quiet_login
        self.boiler_id = None
        self.last_data = None
        self.last_data_time = None

    def login(self):
        """
        Login to the Ariston website.

        Returns:
            None

        Raises:
            ConnectionError: if there is a problem connecting to the website
            AuthenticationError: if the login fails
        """
        login_request = self.session.post(LOGIN_URL, json={'email': self.email, 'password': self.password, 'rememberMe': False,
                                                'language': 'English_Us'}, allow_redirects=False)

        if login_request.status_code != 302 and login_request.status_code != 200:
            raise ConnectionError('Error connecting')

        login_result = login_request.json()
        if login_result['ok']:
            if not self.quiet_login:
                print('Login successful')
        else:
            raise AuthenticationError('Login failed')

        # Now we are logged in, we can get the data
        # first find out the boiler id
        # this is given by a redirect from /R2/Home

        home_request = self.session.get(BASE_URL + '/R2/Home', allow_redirects=False)
        if home_request.status_code != 302:
            raise ConnectionError('Error getting boiler id')

        self.boiler_id = re.search(r'/R2/Plant/Index/([A-Z0-9]+)?', home_request.headers['Location']).group(1)

    def get_data_raw(self, force :bool =False) -> dict:
        """
        Get the raw data from the boiler.

        Args:
            force (bool, optional): if polling for a new value is required. Defaults to False.

        Returns:
            dict: dictionary of the data

        Raises:
            ConnectionError: if there is a problem connecting to the website
            AuthenticationError: if a login is made and it fails
        """
        if not force and \
                self.last_data_time is not None and \
                time.time() - self.last_data_time < self.poll_interval:
            return self.last_data

        if self.boiler_id is None:
            self.login()

        data_url = DATA_BASE_URL + self.boiler_id + DATA_SUFFIX + str(int(time.time()))
        data_request = self.session.get(data_url)
        if data_request.status_code == 403:
            if not self.quiet_login:
                print('Not logged in - retrying login')
            self.login()
            data_request = self.session.get(data_url)

        if data_request.status_code != 200:
            raise ConnectionError('Error getting data')

        data = data_request.json()
        if not data['ok'] or 'data' not in data:
            raise ConnectionError('Error getting data')

        self.last_data = data_request.json()
        self.last_data_time = time.time()

        return self.last_data

    def get_current_temperature(self, force: bool = False) -> float:
        """
        Get the current water temperature

        Parameters
        ----------
        force : bool, optional
            if polling for a new value is required, by default False

        Returns
        -------
        float
            the current water temperature
        """
        return self.get_data_raw(force)['data']['plantData']['waterTemp']

    def get_target_temperature(self, force: bool = False) -> float:
        """
        Get the target water temperature

        Parameters
        ----------
        force : bool, optional
            if polling for a new value is required, by default False

        Returns
        -------
        float
            the target water temperature
        """
        return self.get_data_raw(force)['data']['plantData']['comfortTemp']

    def get_hp_state(self, force: bool = False) -> HPState:
        """
        Get the current state of the heat pump

        Parameters
        ----------
        force : bool, optional
            if polling for a new value is required, by default False

        Returns
        -------
        HPState
            A HPSate enum corresponding to the current state
        """
        return HPState(self.get_data_raw(force)['data']['plantData']['hpState'])

    def get_boost(self, force: bool = False) -> bool:
        """
        Get the current state of the boost

        Parameters
        ----------
        force : bool, optional
            if polling for a new value is required, by default False

        Returns
        -------
        bool
            A bool corresponding to the current state
        """
        return self.get_data_raw(force)['data']['plantData']['boostOn']

    def get_operation_mode(self, force: bool = False) -> OperationMode:
        """
        Get the current operation mode

        Parameters
        ----------
        force : bool, optional
            if polling for a new value is required, by default False

        Returns
        -------
        OperationMode
            A OperationMode enum corresponding to the current state
        """
        return OperationMode(self.get_data_raw(force)['data']['plantData']['opMode'])

    def _populate_set_object(self, **kwargs) -> dict:
        """
        Populate the set object with the data from the last get, because this is the format expected by the server.

        Parameters
        ----------
        kwargs : dict
            Dictionary of the data to set.

        Returns
        -------
        dict
            The populated set object in the form of a dictionary.
        """
        last_data = self.get_data_raw()

        payload = {"plantData": {"__type__": ["my.entities.entityiface", "my.entities.slpplantdata"],
                                 "gatewayId": self.boiler_id,
                                 "on": last_data['data']['plantData']['on'],
                                 "mode": last_data['data']['plantData']['mode'],
                                 "waterTemp": last_data['data']['plantData']['waterTemp'],
                                 "comfortTemp": last_data['data']['plantData']['comfortTemp'],
                                 "reducedTemp": last_data['data']['plantData']['reducedTemp'],
                                 "procReqTemp": last_data['data']['plantData']['procReqTemp'],
                                 "opMode": last_data['data']['plantData']['opMode'],
                                 "holidayUntil": last_data['data']['plantData']['holidayUntil'],
                                 "boostOn": last_data['data']['plantData']['boostOn'],
                                 "hpState": last_data['data']['plantData']['hpState'],
                                 "__lastUpdatedOn__": datetime.fromtimestamp(self.last_data_time).strftime(
                                     '%Y-%m-%dT%H:%M:%S')},
                   "viewModel": {"on": kwargs.get('on', last_data['data']['plantData']['on']),
                                 "plantMode": kwargs.get('mode', last_data['data']['plantData']['mode']),
                                 "opMode": kwargs.get('opMode', last_data['data']['plantData']['opMode']),
                                 "boostOn": kwargs.get('boostOn', last_data['data']['plantData']['boostOn']),
                                 "comfortTemp": kwargs.get('comfortTemp', last_data['data']['plantData']['comfortTemp']),
                                 "holidayUntil": kwargs.get('holidayUntil', last_data['data']['plantData']['holidayUntil'])}}

        return payload

    def _send_request(self, **kwargs):
        """
        Send a request to the server to set the data

        Parameters
        ----------
        kwargs : dict
            A dictionary of the data to set

        Returns
        -------
        None

        Raises
        ------
        ConnectionError
            If there is a problem connecting to the website
        """
        payload = self._populate_set_object(**kwargs)
        set_data_url = SET_DATA_URL + self.boiler_id
        set_data_request = self.session.post(set_data_url, json=payload)
        if set_data_request.status_code != 200:
            raise ConnectionError('Error setting data')

    def set_target_temperature(self, temperature: float):
        """
        Set the target water temperature

        Parameters
        ----------
        temperature : float
            The target water temperature

        Returns
        -------
        None

        Raises
        ------
        ConnectionError
            If there is a problem connecting to the website
        """
        self._send_request(comfortTemp=temperature)

    def set_onoff(self, on: bool):
        """
        Set the boiler on or off

        Parameters
        ----------
        on : bool
            True for on, False for off

        Returns
        -------
        None

        Raises
        ------
        ConnectionError
            If there is a problem connecting to the website
        """
        self._send_request(on=on)

    def set_operation_mode(self, mode: OperationMode):
        """
        Set the operation mode (Green, Comfort, etc.)

        Parameters
        ----------
        mode : OperationMode
            The operation mode

        Returns
        -------
        None

        Raises
        ------
        ConnectionError
            If there is a problem connecting to the website
        """
        self._send_request(opMode=mode.value)

    def set_boost(self, on: bool):
        """
        Set the boost on or off

        Parameters
        ----------
        on : bool
            True for on, False for off

        Returns
        -------
        None

        Raises
        ------
        ConnectionError
            If there is a problem connecting to the website
        """
        self._send_request(boostOn=on)
