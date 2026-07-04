import configparser #Python3 version
import datetime
from logger import log
import os
import sys
import threading
import platform
import re
import time
import http_general
from time import sleep
from Defaults import Defaults, Error, AuthError, FetchError#
from Defaults import Defaults
from cgm_args import cgm_args

args = cgm_args()

# On Raspberry Pi with LCD display only
if  platform.platform().find("arm") >= 0:
    import pygame
    global pygame, lcd
    os.putenv('SDL_FBDEV', '/dev/fb1')
    pygame.init()
    lcd=pygame.display.set_mode((480, 320))

Config = configparser.SafeConfigParser()
Config.read(os.path.dirname(os.path.realpath(__file__))+"/cgm_display.ini")
log.setLevel(Config.get("logging", 'log_level').upper())
if args.logging == "DEBUG":
    log.setLevel("DEBUG")

log.debug(f"Running with command line: {sys.argv}")

global TheReading

if args.username:
    DEXCOM_ACCOUNT_NAME = args.username
else:
    DEXCOM_ACCOUNT_NAME = Config.get("dexcomshare", "dexcom_share_login")

if args.password:
    DEXCOM_PASSWORD = args.password
else:
    DEXCOM_PASSWORD = Config.get("dexcomshare", "dexcom_share_password")

if args.polling_interval:
    CHECK_INTERVAL = int(args.polling_interval)
else:
    CHECK_INTERVAL = int(Config.get("dexcomshare", "polling_interval"))

if args.time_ago_interval:
    TIME_AGO_INTERVAL = int(args.time_ago_interval)
else:
    TIME_AGO_INTERVAL = int(Config.get("dexcomshare","time_ago_interval"))

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
    log.debug(f'Parsing response: {res.json()}')
    epochtime = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
    try:
        last_reading_time = int(re.search('\d+', res.json()[0]['ST']).group())/1000
        reading_lag = epochtime - last_reading_time
        trend = res.json()[0]['Trend']
        mgdl = res.json()[0]['Value']
        
        #trend_english = DIRECTIONS.keys()[DIRECTIONS.values().index(trend)] # Python2 version
        #trend_english=list(Defaults.DIRECTIONS.keys())[list(Defaults.DIRECTIONS.values()).index(trend)] # Python3 version
        trend_english=Defaults.DIRECTIONS[trend]
        log.info(f"Last bg: {mgdl}  trending: {trend_english} ({trend})  last reading at: {reading_lag} seconds ago")
        if reading_lag > LAST_READING_MAX_LAG:
            log.warning(f"***WARN It has been {int(reading_lag/60)} minutes since DEXCOM got a new measurement")
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
        log.error(f"Caught IndexError: return code:{res.status_code} ... response output below")
        log.error(res.__dict__)
        return None

def monitor_dexcom():
    """ Main loop """
    opts = Defaults
    opts.accountName = os.getenv("DEXCOM_ACCOUNT_NAME", DEXCOM_ACCOUNT_NAME)
    opts.password = os.getenv("DEXCOM_PASSWORD", DEXCOM_PASSWORD)
    opts.interval = float(os.getenv("CHECK_INTERVAL", CHECK_INTERVAL))
    fetchfails = 0
    failures = 0
    #log.debug("RUNNING {}, failures: {}".format(runs, failures))
    try:
        if not opts.sessionID:
            authfails = 0
            opts.sessionID = http_general.get_sessionID(opts)
            log.debug(f"Got auth token {opts.sessionID}")
        res = http_general.fetch(opts)
        if res and res.status_code < 400:
            fetchfails = 0
            reading = parse_dexcom_response(opts, res)
            if reading:
                return reading
            else:
                opts.sessionID = None
                log.error("parse_dexcom_response returned None.  Investigate above logs")
                if run_once:
                    return None
        else:
            failures += 1
            opts.sessionID = None
            log.warning(f"Saw an error from the dexcom api, code: {res.status_code}.  details to follow")
            raise opts.FetchError(res.status_code, res)
            log.warning(f"Fetch failed on: {res.status_code}")
            return
            if fetchfails > (MAX_FETCHFAILS/2):
                log.warning("Trying to re-auth...")
                opts.sessionID = None
            else:
                log.warning("Trying again...")
            #time.sleep((FAIL_RETRY_DELAY_BASE**authfails))
            fetchfails += 1

    except ConnectionError:
        opts.sessionID = None
        raise log.warning("Cnnection Error.. sleeping for {} seconds and".format(RETRY_DELAY) + " trying again")
        time.sleep(RETRY_DELAY)
    except AuthError:
        log.error("Authentication error connecting to Dexcom share")
        return False
    except:
        log.debug("Caught exception communicating with Dexcom:  Returning False")
        return False

    return False

def display_reading(reading, bgdelta):
    log.debug("Displaying with Reading of " + str(reading) + " and a change of " + '{0:{1}}'.format(bgdelta, '+' if bgdelta else ''))
    #log.debug("Differeince is " + '{0:{1}}'.format(number, '+' if number else ''))
    # On Raspberry Pi with LCD display only
    thePlatform = platform.platform().lower()
    if not platform.platform().find("arm") >= 0:
        log.debug("Skipping display.  Not on Raspberry Pi")
        return
    global pygame, lcd
    log.debug("Getting ready to display on the LCD panel")
    if thePlatform.find("linux") >= 0:
        fonttouse = Defaults.Linux_font
    elif thePlatform.find("macos") >= 0:
        fonttouse = Defaults.Mac_font
    else:
        fonttouse = ""

    now = datetime.datetime.utcnow()
    reading_time = datetime.datetime.utcfromtimestamp(reading["last_reading_time"])
    difference = round((now - reading_time).total_seconds()/60)
    log.debug(f"Time difference since last good reading is: {difference}")
    if difference == 0:
        str_difference = "Just Now"
    elif difference == 1:
        str_difference = str(difference) + " Minute Ago"
    else:
        str_difference = str(difference) + " Minutes Ago"
    log.info(f"About to update Time Ago Display with reading from {str_difference}")
    log.debug(f"About to acquire lock with: {lock}")
    lock.acquire(blocking=True)
    log.debug(f"Acquired lock {lock}")

    try:
        if isNightTime():
           log.debug("Setting to Nighttime mode")
           lcd.fill(Defaults.BLACK)
           font_color=Defaults.GREY
        else:
           log.debug("Setting to Daylight mode")
           lcd.fill(Defaults.BLUE)
           font_color=Defaults.WHITE
        
        font_time = pygame.font.Font(None, 75)
        text_surface = font_time.render(str_difference, True, font_color)
        rect = text_surface.get_rect(center=(240,20))
        lcd.blit(text_surface, rect)

        #font_big = pygame.font.SysFont("dejavusans", 200)
        font_big = pygame.font.SysFont(fonttouse, 200)
        #trend_index = reading["trend"] - This was causing the line below using trend_index to fail all of a sudden.  Passing trend string instead of the index.  2/6/22
        trend_index = Defaults.DIRECTIONS[reading['trend']]  ## Added 2/5/22 to fix above problem.  Not sure how if ever worked...
        if (reading["last_reading_lag"] == True) or (difference > round(LAST_READING_MAX_LAG/60)):
           str_reading = "---"
        else:
           str_reading = str(reading["bg"])+Defaults.ARROWS[str(trend_index)]
        text_surface = font_big.render(str_reading, True, font_color)
        rect = text_surface.get_rect(center=(240,155))
        lcd.blit(text_surface, rect)
        
        font_medium = pygame.font.Font(None, 135)
        text_surface = font_medium.render('{0:{1}}'.format(bgdelta, '+' if bgdelta else ''),True,font_color)
        rect = text_surface.get_rect(center=(240, 275))
        lcd.blit(text_surface, rect)
        
        pygame.display.update()
        pygame.mouse.set_visible(False)
    finally:
        log.debug(f"About to release lock: {lock}")
        lock.release()
        log.debug(f"Lock released: {lock}")
   
def TimeAgoThread():
    global TheReading, BGDifference
    #log.debug("Differeince is " + '{0:{1}}'.format(number, '+' if number else ''))
    while True:
        display_reading(TheReading, BGDifference)
        sleep(TIME_AGO_INTERVAL)

if __name__ == '__main__':      
    lock = threading.RLock()
    log.debug(f"Created lock: {lock}")
    
    LastReading = 0
    BGDifference = 0
    TheReading = False
    
    TheReading=monitor_dexcom() #One initial reading to have data for the TimeAgo Thread before we get into the main loop
    i = 1

    TimeAgo = threading.Thread(target=TimeAgoThread)
    TimeAgo.setName("TimeAgoThread")
    TimeAgo.start()
    sleep(CHECK_INTERVAL)

    while True:
        i += 1
        try:
            LastReading = TheReading["bg"]
            LastReadingTime = TheReading["last_reading_time"]
            TheReading=monitor_dexcom()
            if (TheReading["last_reading_time"] != LastReadingTime):
                BGDifference = TheReading["bg"] - LastReading
            log.debug(f"Iteration #{i}-{TheReading}")
            log.debug(f"Difference of {BGDifference}")
        except:
            log.info("Exception processing The Reading, Sleeping and trying again....")
        sleep(CHECK_INTERVAL)
