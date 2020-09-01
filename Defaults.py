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
    MIN_PASSPHRASE_LENGTH = 12
    last_seen = 0
    # Mapping friendly names to trend IDs from dexcom
    DIRECTIONS = {
        "nodir": 0,
        "DoubleUp": 1,
        "SingleUp": 2,
        "FortyFiveUp": 3,
        "FORTY_FIVE_UP": 3,
        "Flat": 4,
        "FortyFiveDown": 5,
        "SingleDown": 6,
        "DoubleDown": 7,
        "NOT COMPUTABLE": 8,
        "RATE OUT OF RANGE": 9,
    }

    #Arrow Characters based on ucs2 character set
    ARROWS = {
        "0":chr(int("0x32",16)),
        "1":chr(int("0x21D1",16)),
        "2":chr(int("0x2191",16)),
        "3":chr(int("0x2197",16)),
        "4":chr(int("0x2192",16)),
        "5":chr(int("0x2198",16)),
        "6":chr(int("0x2193",16)),
        "7":chr(int("0x21D3",16)),
        "8":"??",
        "9":"??"
    }

    #Colors we use
    WHITE=(255,255,255)
    BLACK=(0,0,0)
    GREY=(160,160,160)
    BLUE=(0,0,255)

    #Nighttime for Night Mode
    NIGHTMODE=(22,23,24,0,1,2,3,4,5,6) #Hours to use Night Mode


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
