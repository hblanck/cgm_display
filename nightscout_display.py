##Get CGM information from our Nightscout Server
##When Dexcom and Sugarmate aren't working
##

import os
import sys
import platform
from time import sleep
import argparse
import datetime
import logging
import threading
import urllib
import urllib.parse #Python3 requires this
import requests
import json
from Defaults import Defaults
#from builtins import None

#Process command line arguments
ArgParser=argparse.ArgumentParser(description="Handle Command Line Arguments")
ArgParser.add_argument("--logging", '-l', default="INFO", help="Logging level: INFO (Default) or DEBUG")
ArgParser.add_argument("--nightscoutserver", '-ns', help="Set the base URL for your Nightscout server e.g. https://mynighscout.domain.com")
ArgParser.add_argument("--polling_interval", default=60, help="Polling interval for getting updates from Sugarmate")
ArgParser.add_argument("--time_ago_interval", default=30, help="Polling interval for updating the \"Time Ago\" detail")
args=ArgParser.parse_args()

log = logging.getLogger(__file__)
log.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
log.addHandler(ch)
if args.logging == "DEBUG":
    log.setLevel(logging.DEBUG)

if args.nightscoutserver != None:
    NIGHTSCOUT = args.nightscoutserver
else:
    sys.exit("No Nighscout URL defined.  Exiting")

log.debug(f'Using Arguments: {args}')

CHECK_INTERVAL = int(args.polling_interval)
TIME_AGO_INTERVAL = int(args.time_ago_interval)

log.debug(f"Platform we're running on is: {platform.platform()}")
if  platform.platform().find("arm") >= 0:
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" #Doesn't seem to work.  Still get prompt when running foreground
    import pygame
    global pygame, lcd
    os.putenv('SDL_FBDEV', '/dev/fb1') #This may need to change to accomodate a different type of disolay using different device frame buffer.
    pygame.init()
    lcd=pygame.display.set_mode((480, 320))

def isNightTime():
    now = datetime.datetime.now()
    if now.hour in Defaults.NIGHTMODE:
        return True
    else:
        return False


def display_reading(readings,devicestatus):

    reading=readings[0] #Current Reading
    last_reading=readings[1] #Previous reading
    log.debug(f"Current Reading: {readings[0]}")
    log.debug(f"Previous Reading: {readings[1]}")

    display = True
    if not platform.platform().find("arm") >= 0:
        display = False

    if display:
        global pygame, lcd
        log.debug("Getting ready to display on the LCD panel")

    log.debug(f"Displaying with Reading of {reading}")
    now = datetime.datetime.utcnow()
    reading_time = datetime.datetime.utcfromtimestamp(int(str(reading["date"])[0:10]))
    difference = round((now - reading_time).total_seconds()/60)
    log.debug(f"Time difference since last good reading is: {difference}")
    if difference == 0:
        str_difference = "Just Now"
    elif difference == 1:
        str_difference = str(difference) + " Minute Ago"
    else:
        str_difference = str(difference) + " Minutes Ago"

    if "direction" in reading:
        trend_arrow = Defaults.ARROWS[str(Defaults.DIRECTIONS[reading["direction"]])]
    else:
        trend_arrow = ""
    log.debug(f"The arrow direction is: {trend_arrow}")

    if difference < 7:
        str_reading = str(reading["sgv"]) + trend_arrow
    else:
        str_reading = "---"
    log.debug(f"About to push: {str_reading} to the display")

    change = reading["sgv"] - last_reading["sgv"]
    str_change=str(change)
    if change > 0: str_change = "+"+str(change)
    log.debug(f"Change from last reading is: {change}")

    loop_time = datetime.datetime.strptime(devicestatus[0]['loop']['timestamp'],'%Y-%m-%dT%H:%M:%SZ')
    loop_time_difference = round((now - loop_time).total_seconds()/60)
    if 0 <= loop_time_difference <= 5:
        loop_image = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),Defaults.Loop_Fresh)
    elif (6 <= loop_time_difference <= 10):
        loop_image = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),Defaults.Loop_Aging)
    else:
        loop_image = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),Defaults.Loop_Stale)

    log.info(f"Loop Age:{loop_time_difference} Minutes, Loop Image Used:{loop_image}")

    try:        
        log.debug(f"Displaying:\n\t {str_difference}\n\t{str_reading}\n\t{str_change}")
        if display:
            if isNightTime():
               log.debug("Setting to Nighttime mode")
               lcd.fill(Defaults.BLACK)
               font_color=Defaults.GREY
            else:
               log.debug("Setting to Daylight mode")
               lcd.fill(Defaults.BLUE)
               font_color=Defaults.WHITE

            log.debug("Setting up Difference Display")
            font_time = pygame.font.Font(None, 75)
            text_surface = font_time.render(str_difference, True, font_color)
            rect = text_surface.get_rect(center=(240,20))
            lcd.blit(text_surface, rect)

            log.debug("Setting up Reading Display")
            font_big = pygame.font.SysFont("dejavusans", 200)
    
            text_surface = font_big.render(str_reading, True, font_color)
            rect = text_surface.get_rect(center=(240,155))
            lcd.blit(text_surface, rect)

            font_medium = pygame.font.Font(None, 135)
            text_surface = font_medium.render(str_change,True,font_color)
            rect = text_surface.get_rect(center=(240, 275))
            lcd.blit(text_surface, rect)

            log.debug(f'Using Loop Image file: {loop_image}')
            text_surface = pygame.image.load(loop_image)
            rect = text_surface.get_rect(center=(450,290))
            lcd.blit(text_surface, rect)
    
            log.debug("About to update the LCD display")
            pygame.display.update()
            pygame.mouse.set_visible(False)
        else:
            log.info("Skipped display, not on Raspberry Pi")
    except Exception as e:
        log.info("Caught an Exception processing the display")
        log.error(e,exc_info=True)
    finally:
        log.debug("Done with display")
    return reading

i=0
while True:
    i += 1
    try:
        log.info(f"Getting Reading and Device Status from Nightscout - Loop #{i}")
        response=requests.get(NIGHTSCOUT+"/api/v1/entries/sgv?count=2",headers={'Accept': 'application/json'}) #Get the last two readings
        log.info(f"Got Status Code: {response.status_code}\nData: {response.text}")
        devicestatus_response=requests.get("https://nightscout.blanckfamily.net/api/v1/devicestatus",headers={'Accept': 'application/json'})
        log.info(f"DeviceStatus Status Code: {devicestatus_response.status_code}")
        log.debug(f"DeviceStatus: {devicestatus_response.text}")
        display_reading(response.json(),devicestatus_response.json())

    except Exception as e:
        log.error(e,exc_info=True)
        log.info("Exception processing The Reading, Sleeping and trying again....")
    sleep(CHECK_INTERVAL)
