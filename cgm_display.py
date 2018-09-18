#!/usr/bin/env python

#import ConfigParser #Python2 version
import configparser #Python3 version
import datetime
import logging
import os
import threading
import platform
import re
import requests
import time
import urllib
import urllib.parse #Python3 requires this
import http_general
from time import sleep
from Defaults import Defaults, Error, AuthError, FetchError

# On Raspberry Pi with LCD display only
if  platform.platform().find("arm") >= 0:
    import pygame

log = logging.getLogger(__file__)
log.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
#ch.setLevel(logging.DEBUG)
log.addHandler(ch)

#Config = ConfigParser.SafeConfigParser()
Config = configparser.SafeConfigParser()
Config.read(os.path.dirname(os.path.realpath(__file__))+"/cgm_display.ini")
log.setLevel(Config.get("logging", 'log_level').upper())

global TheReading, lcd

DEXCOM_ACCOUNT_NAME = Config.get("dexcomshare", "dexcom_share_login")
DEXCOM_PASSWORD = Config.get("dexcomshare", "dexcom_share_password")
CHECK_INTERVAL = 60 * 2.5
AUTH_RETRY_DELAY_BASE = 2
FAIL_RETRY_DELAY_BASE = 2
MAX_AUTHFAILS = Config.get("dexcomshare", "max_auth_fails")
MAX_FETCHFAILS = 10
RETRY_DELAY = 60 # Seconds
LAST_READING_MAX_LAG = 60 * 7.5

def isNightTime():
    now = datetime.datetime.now()
    if now.hour in Defaults.NIGHTMODE:
        return True
    else:
        return False

def parse_dexcom_response(ops, res):
    log.debug(res.json())
    epochtime = int((
                datetime.datetime.utcnow() -
                datetime.datetime(1970, 1, 1)).total_seconds())
    try:
        last_reading_time = int(re.search('\d+', res.json()[0]['ST']).group())/1000
        reading_lag = epochtime - last_reading_time
        trend = res.json()[0]['Trend']
        mgdl = res.json()[0]['Value']
        
        #trend_english = DIRECTIONS.keys()[DIRECTIONS.values().index(trend)] # Python2 version
        trend_english=list(Defaults.DIRECTIONS.keys())[list(Defaults.DIRECTIONS.values()).index(trend)] # Python3 version
        log.info("Last bg: {}  trending: {} ({})  last reading at: {} seconds ago".format(mgdl, trend_english, trend, reading_lag))
        if reading_lag > LAST_READING_MAX_LAG:
            log.warning(
                "***WARN It has been {} minutes since DEXCOM got a" +
                "new measurement".format(int(reading_lag/60)))
            last_reading_lag = True
        else:
            last_reading_lag = False
        return {
                "bg": mgdl,
                "trend": trend,
                "trend_english": trend_english,
                "reading_lag": reading_lag,
                "last_reading_time": last_reading_time,
                "last_reading_lag": last_reading_lag
                }
    except IndexError:
        log.error(
                "Caught IndexError: return code:{} ... response output" +
                " below".format(res.status_code))
        log.error(res.__dict__)
        return None

def get_sessionID(opts):
    authfails = 0
    while not opts.sessionID:
        res = http_general.authorize(opts)
        if res.status_code == 200:
            opts.sessionID = res.text.strip('"')
            log.debug("Got auth token {}".format(opts.sessionID))
        else:
            if authfails > MAX_AUTHFAILS:
                raise AuthError(res.status_code, res)
            else:
                log.warning("Auth failed with: {}".format(res.status_code))
                time.sleep(AUTH_RETRY_DELAY_BASE**authfails)
                authfails += 1
    return opts.sessionID

def monitor_dexcom(run_once):
    """ Main loop """
    opts = Defaults
    opts.accountName = os.getenv("DEXCOM_ACCOUNT_NAME", DEXCOM_ACCOUNT_NAME)
    opts.password = os.getenv("DEXCOM_PASSWORD", DEXCOM_PASSWORD)
    opts.interval = float(os.getenv("CHECK_INTERVAL", CHECK_INTERVAL))

    runs = 0
    fetchfails = 0
    failures = 0
    while True:
        log.debug("RUNNING {}, failures: {}".format(runs, failures))
        runs += 1
        if not opts.sessionID:
            authfails = 0
            opts.sessionID = get_sessionID(opts)
        try:
            res = http_general.fetch(opts)
            if res and res.status_code < 400:
                fetchfails = 0
                reading = parse_dexcom_response(opts, res)
                if reading:
                    if run_once:
                        # On Raspberry Pi with LCD display only
                        if  platform.platform().find("arm") >= 0:
                            display_reading(reading)
                            #sleep(180)
                        return reading
                    else:
                        if reading['last_reading_time'] > opts.last_seen:
                            #report_glucose(reading)
                            opts.sessionID = "foo"
                            opts.last_seen = reading['last_reading_time']
                            try:
                                if HEALTHCHECK_URL:
                                    requests.get(HEALTHCHECK_URL)
                            except ConnectionError as e:
                                log.error("Error sending healthcheck: {}".format(e))

                else:
                    opts.sessionID = None
                    log.error("parse_dexcom_response returned None.  Investigate above logs")
                    if run_once:
                        return None
            else:
                failures += 1
                if run_once or fetchfails > MAX_FETCHFAILS:
                    opts.sessionID = None
                    log.warning("Saw an error from the dexcom api, code: {}.  details to follow".format(res.status_code))
                    raise FetchError(res.status_code, res)
                else:
                    log.warning("Fetch failed on: {}".format(res.status_code))
                    if fetchfails > (MAX_FETCHFAILS/2):
                        log.warning("Trying to re-auth...")
                        opts.sessionID = None
                    else:
                        log.warning("Trying again...")
                    time.sleep((FAIL_RETRY_DELAY_BASE**authfails))
                    #opts.interval)
                    fetchfails += 1
        except ConnectionError:
            opts.sessionID = None
            if run_once:
                raise
            log.warning(
                    "Cnnection Error.. sleeping for {} seconds and".format(RETRY_DELAY) +
                    " trying again")
            time.sleep(RETRY_DELAY)

        time.sleep(opts.interval)

def display_reading(reading):
    log.debug("Getting ready to display on the LCD panel")
    os.putenv('SDL_FBDEV', '/dev/fb1')
    pygame.init()
    global lcd
    lcd=pygame.display.set_mode((480, 320))
    if isNightTime():
       lcd.fill(Defaults.BLACK)
       font_color=Defaults.GREY
    else:
       lcd.fill(Defaults.BLUE)
       font_color=Defaults.WHITE

    font_time = pygame.font.Font(None, 75)
    lag_time = int(reading["reading_lag"]/60)
    if lag_time == 0:
        str_lag_time = "Just Now"
    elif lag_time == 1:
        str_lag_time = str(lag_time) + " Minute Ago"
    else:
        str_lag_time = str(lag_time) + " Minutes Ago"

    #str_reading_time = time.strftime("%b %e %I:%M%p", time.localtime(flt_time))
    text_surface = font_time.render(str_lag_time, True, font_color)
    rect = text_surface.get_rect(center=(240,20))
    lcd.blit(text_surface, rect)

    font_big = pygame.font.Font(None, 250)
    trend_index = reading["trend"]
    if reading["last_reading_lag"] == True:
       str_reading = "---"
    else:
       str_reading = str(reading["bg"])+Defaults.ARROWS[str(trend_index)]
    text_surface = font_big.render(str_reading, True, font_color)
    rect = text_surface.get_rect(center=(240,160))
    lcd.blit(text_surface, rect)
    pygame.display.update()
    pygame.mouse.set_visible(False)
    
def TimeAgoThread():
    # On Raspberry Pi with LCD display only
    if  platform.platform().find("arm") >= 0:
        global lcd, pygame
    global TheReading
 
    while True:
        now = datetime.datetime.utcnow()
        reading_time = datetime.datetime.utcfromtimestamp(TheReading["last_reading_time"])
        difference = round((now - reading_time).total_seconds()/60)
        if difference == 0:
            str_difference = "Just Now"
        elif difference == 1:
            str_difference = str(difference) + " Minute Ago"
        else:
            str_difference = str(difference) + " Minutes Ago"
        log.info("About to update Time Ago Display with reading from " + str_difference)
        # On Raspberry Pi with LCD display only
#         if  platform.platform().find("arm") >= 0:
#             if isNightTime():
#                #lcd.fill(Defaults.BLACK)
#                font_color=Defaults.GREY
#             else:
#                #lcd.fill(Defaults.BLUE)
#                font_color=Defaults.WHITE
#             global lcd, pygame
#             font_time = pygame.font.Font(None, 75)
#             text_surface = font_time.render(str_difference, True, font_color)
#             rect = text_surface.get_rect(center=(240,20))
#             lcd.blit(text_surface, rect)
#             pygame.display.update()
        sleep(15)

if __name__ == '__main__':      

    #One initial reading to have data for the TimeAgo Thread before we get into the main loop
    TheReading=monitor_dexcom(run_once=True)
    i = 1
    # Thread to update how long ago display every minute
    TimeAgo = threading.Thread(target=TimeAgoThread)
    TimeAgo.setName("TimeAgoThread")
    TimeAgo.start()
    sleep(180)

    while True:
        i += 1
        TheReading=monitor_dexcom(run_once=True)
        log.debug("Iteration #"+str(i) + "-" + str(TheReading))
        sleep(120)
