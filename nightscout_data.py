import requests
from logger import log
from http_general import handle_http_exceptions

class Nightscout:
    def __init__(self, server) -> None:
        self._server = server
        self._Readings_url = self._server + "/api/v1/entries/sgv?count=2"
        self._DeviceStatus_url = self._server + "/api/v1/devicestatus"
        self._urlheaders = {'Accept': 'application/json'}

    @handle_http_exceptions(retries=2, backoff=1.0, return_on_error=None)
    def getReading(self):
        response = requests.get(self._Readings_url, headers=self._urlheaders)  # Get the last two readings
        if response is None:
            log.warning("Nightscout getReading: no response")
            return None
        log.info(f"Got Status Code: {response.status_code}\nData: {response.text}")
        try:
            return response.json()
        except ValueError:
            log.error("Nightscout getReading: response not JSON")
            return None

    @handle_http_exceptions(retries=2, backoff=1.0, return_on_error=None)
    def getDeviceStatus(self):
        devicestatus_response = requests.get(self._DeviceStatus_url, headers=self._urlheaders)
        if devicestatus_response is None:
            log.warning("Nightscout getDeviceStatus: no response")
            return None
        log.debug(f"DeviceStatus: {devicestatus_response.text}")
        try:
            return devicestatus_response.json()
        except ValueError:
            log.error("Nightscout getDeviceStatus: response not JSON")
            return None
