class Defaults:
    applicationId = "d89443d2-327c-4a6f-89e5-496bbb0317db"
    agent = "Dexcom Share/3.0.2.11 CFNetwork/711.2.23 Darwin/14.0.0"
    login_url = "https://share1.dexcom.com/ShareWebServices/Services/" +\
        "General/LoginPublisherAccountByName"
    accept = 'application/json'
    content_type = 'application/json'
    LatestGlucose_url = "https://share1.dexcom.com/ShareWebServices/" +\
        "Services/Publisher/ReadPublisherLatestGlucoseValues"
    sessionID = None
    nightscout_upload = '/api/v1/entries.json'
    nightscout_battery = '/api/v1/devicestatus.json'
    MIN_PASSPHRASE_LENGTH = 12
    last_seen = 0

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class AuthError(Error):
    """Exception raised for errors when trying to Auth to Dexcome share
    """

    def __init__(self, status_code, message):
        self.expression = status_code
        self.message = message
        log.error(message.__dict__)

class FetchError(Error):
    """Exception raised for errors in the date fetch.
    """

    def __init__(self, status_code, message):
        self.expression = status_code
        self.message = message
        log.error(message.__dict__)
