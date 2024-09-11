import requests
from logger import log

class Nightscout:
    def __init__(self, server) -> None:
        self.server = server

    def getReading(self):
        response = requests.get(self.server+"/api/v1/entries/sgv?count=2",headers={'Accept': 'application/json'}) #Get the last two readings
        log.info(f"Got Status Code: {response.status_code}\nData: {response.text}")
        return response.json()

    def getDeviceStatus(self):
        devicestatus_response = requests.get(self.server+"/api/v1/devicestatus",headers={'Accept': 'application/json'})
        log.debug(f"DeviceStatus: {devicestatus_response.text}")
        return devicestatus_response.json()