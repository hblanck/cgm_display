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
#ArgParser.add_argument("--apikey", '-a', help="Set your Sugarmate API Key (6 digit code from your Sugarmate Account)")
ArgParser.add_argument("--nightscoutserver", '-ns', help="Set the base URL for your Nightscout server e.g. https://mynighscout.domain.com")
ArgParser.add_argument("--polling_interval", help="Polling interval for getting updates from Sugarmate")
ArgParser.add_argument("--time_ago_interval", help="Polling interval for updating the \"Time Ago\" detail")
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

if args.polling_interval != None:
    CHECK_INTERVAL = int(args.polling_interval)
else:
    CHECK_INTERVAL = 60

if args.time_ago_interval != None:
    TIME_AGO_INTERVAL = int(args.time_ago_interval)
else:
    TIME_AGO_INTERVAL = 30

if  platform.platform().find("arm") >= 0:
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    import pygame
    global pygame, lcd
    os.putenv('SDL_FBDEV', '/dev/fb1')
    pygame.init()
    lcd=pygame.display.set_mode((480, 320))

def isNightTime():
    now = datetime.datetime.now()
    if now.hour in Defaults.NIGHTMODE:
        return True
    else:
        return False

def display_reading(reading, last_reading):

    display = True
    if not platform.platform().find("arm") >= 0:
        display = False

    if display:
        #log.debug("Skipping display.  Not on Raspberry Pi")
        #return
        global pygame, lcd
        log.debug("Getting ready to display on the LCD panel")

    log.debug("Displaying with Reading of " + str(reading))
    now = datetime.datetime.utcnow()
    reading_time = datetime.datetime.utcfromtimestamp(int(str(reading["date"])[0:10]))
    difference = round((now - reading_time).total_seconds()/60)
    log.debug("Time difference since last good reading is: " + str(difference))
    #print("Time difference since last good reading is: " + str(difference))
    if difference == 0:
        str_difference = "Just Now"
    elif difference == 1:
        str_difference = str(difference) + " Minute Ago"
    else:
        str_difference = str(difference) + " Minutes Ago"
    log.info("About to update Time Ago Display with reading from " + str_difference)


    trend_arrow = Defaults.ARROWS[str(Defaults.DIRECTIONS[reading["direction"]])]
    log.debug("The arrow direction is: " + trend_arrow)

    # if reading["direction"] == "DoubleUp":
    #     trend_arrow = chr(int("0x21D1",16))
    # elif reading["direction"] == "DoubleDown":
    #     trend_arrow = chr(int("0x21D3",16))
    # else:
    #     trend_arrow = reading["reading"].split()[1]
    str_reading = str(reading["sgv"]) + trend_arrow
    log.debug("About to push: " + str_reading + " to the display")

    try:        
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

            #TODO -Logic for handling difference from last reading    
            # font_medium = pygame.font.Font(None, 135)
            # if len(reading["reading"].split()) > 2:
            #     text_surface = font_medium.render(reading["reading"].split()[2],True,font_color)
            # else:
            #     text_surface = font_medium.render("--",True,font_color)
            # rect = text_surface.get_rect(center=(240, 275))
            # lcd.blit(text_surface, rect)
    
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
last_reading = None
while True:
    i += 1
    try:
        log.info("Getting Reading from Nightscout - Loop #" + str(i))
        response=requests.get(NIGHTSCOUT+"/api/v1/entries/sgv?count=1",headers={'Accept': 'application/json'})
        r=response.text.strip("[]") #Nightscout API returns as an array, so Python converts it to a list instead of a dict.  Stripping the brackets allows it to load as a dict.
        log.info("Got Status Code: " + str(response.status_code))
        log.info("Data: " + r)
        j=json.loads(r.strip("[]"))
        last_reading = display_reading(j, last_reading)

    except Exception as e:
        log.error(e,exc_info=True)
        log.info("Exception processing The Reading, Sleeping and trying again....")
    sleep(CHECK_INTERVAL)
