import requests
from logger import log

class Nightscout:
    def __init__(self, server) -> None:
        self._server = server
        self._Readings_url = self._server + "/api/v1/entries/sgv?count=2"
        self._DeviceStatus_url = self._server + "/api/v1/devicestatus"
        self._urlheaders = {'Accept': 'application/json'}

    def getReading(self):
        response = requests.get(self._Readings_url, headers=self._urlheaders)  # Get the last two readings
        log.info(f"Got Status Code: {response.status_code}\nData: {response.text}")
        return response.json()

    def getDeviceStatus(self):
        devicestatus_response = requests.get(self._DeviceStatus_url, headers=self._urlheaders)
        log.debug(f"DeviceStatus: {devicestatus_response.text}")
        return devicestatus_response.json()
