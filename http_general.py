import requests
import urllib.parse
from Defaults import Defaults

def login_payload(opts):
    """ Build payload for the auth api query """
    body = {
        "password": opts.password,
        "applicationId": opts.applicationId,
        "accountName": opts.accountName
        }
    return body

def authorize(opts):
    """ Login to dexcom share and get a session token """ 
    url = Defaults.login_url
    body = login_payload(opts)
    headers = {
            'User-Agent': Defaults.agent,
            'Content-Type': Defaults.content_type,
            'Accept': Defaults.accept
            }
 
    return requests.post(url, json=body, headers=headers)

def fetch_query(opts):
    """ Build the api query for the data fetch
    """
    q = {
        "sessionID": opts.sessionID,
        "minutes":  1440,
        "maxCount": 1
        }
    url = Defaults.LatestGlucose_url + '?' + urllib.parse.urlencode(q)
    return url

def fetch(opts):
    """ Fetch latest reading from dexcom share
    """
    url = fetch_query(opts)
    body = {
            'applicationId': 'd89443d2-327c-4a6f-89e5-496bbb0317db'
            }

    headers = {
            'User-Agent': Defaults.agent,
            'Content-Type': Defaults.content_type,
            'Content-Length': "0",
            'Accept': Defaults.accept
            }

    return requests.post(url, json=body, headers=headers)
