import functools
import time
import requests
import urllib.parse
from Defaults import Defaults
from logger import log

def login_payload(opts):
    """ Build payload for the auth api query """
    body = {
        "password": opts.password,
        "applicationId": opts.applicationId,
        "accountName": opts.accountName
        }
    return body


def handle_http_exceptions(retries: int = 0, backoff: float = 1.0, return_on_error=None):
    """Decorator to wrap HTTP calls and handle `requests` exceptions.

    - retries: number of retry attempts after the first failure
    - backoff: base delay in seconds (exponential backoff applied)
    - return_on_error: value to return if all attempts fail (default: None)

    The wrapped function is expected to return a `requests.Response` on success.
    On exceptions (e.g., ConnectionError, Timeout) the error is logged and
    the function will retry up to `retries` times before returning
    `return_on_error`.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    attempt += 1
                    log.error(f"HTTP request failed in {func.__name__}: {e}")
                    if attempt > retries:
                        log.debug(f"Exceeded retries ({retries}) for {func.__name__}")
                        return return_on_error
                    sleep_time = backoff * (2 ** (attempt - 1))
                    log.info(f"Retrying {func.__name__} in {sleep_time} seconds (attempt {attempt}/{retries})")
                    time.sleep(sleep_time)
        return wrapper
    return decorator

@handle_http_exceptions(retries=2, backoff=1.0, return_on_error=None)
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

@handle_http_exceptions(retries=2, backoff=1.0, return_on_error=None)
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
    #print(headers)
    #print(url)
    return requests.post(url, json=body, headers=headers)

def get_sessionID(opts):
    authfails = 0
    while not opts.sessionID:
        res = authorize(opts)
        if res is not None and getattr(res, 'status_code', None) == 200:
            opts.sessionID = res.text.strip('"')
#            log.debug("Got auth token {}".format(opts.sessionID))
        else:
            status = getattr(res, 'status_code', None)
            if authfails > int(MAX_AUTHFAILS):
                raise AuthError(status, res)
            else:
                log.warning(f"Auth failed with: {status}")
                time.sleep(AUTH_RETRY_DELAY_BASE**authfails)
                authfails += 1
    return opts.sessionID

