##Get CGM information from our Sugarmate Account
##When Dexcom login isn't working
##Need to enable API access through the Sugarmate app

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

log = logging.getLogger(__file__)
log.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
log.addHandler(ch)

#Process command line arguments
ArgParser=argparse.ArgumentParser(description="Handle Command Line Arguments")
ArgParser.add_argument("--apikey", '-a', help="Set your Sugarmate API Key (6 digit code from your Sugarmate Account)")
ArgParser.add_argument("--polling_interval", help="Polling interval for getting updates from Sugarmate")
ArgParser.add_argument("--time_ago_interval", help="Polling interval for updating the \"Time Ago\" detail")
args=ArgParser.parse_args()

if args.apikey != None:
    API_KEY = args.apikey
else:
    sys.exit("No Sugarmate API key defined.  Exiting")

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

def display_reading(reading):

    if not platform.platform().find("arm") >= 0:
        log.debug("Skipping display.  Not on Raspberry Pi")
        return
    global pygame, lcd
    log.debug("Getting ready to display on the LCD panel")

    log.debug("Displaying with Reading of " + str(reading))
    now = datetime.datetime.utcnow()
    reading_time = datetime.datetime.utcfromtimestamp(reading["x"]) # Sugarmate puts the posix timstamp in the 'x' attribute
    difference = round((now - reading_time).total_seconds()/60)
    log.debug("Time difference since last good reading is: " + str(difference))
    print("Time difference since last good reading is: " + str(difference))
    if difference == 0:
        str_difference = "Just Now"
    elif difference == 1:
        str_difference = str(difference) + " Minute Ago"
    else:
        str_difference = str(difference) + " Minutes Ago"
    log.info("About to update Time Ago Display with reading from " + str_difference)

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

        font_big = pygame.font.SysFont("dejavusans", 200)

        if reading["trend_words"] == "DOUBLE_UP":
            trend_arrow = chr(int("0x21D1",16))
        elif reading["trend_words"] == "DOUBLE_DOWN":
            trend_arrow = chr(int("0x21D3",16))
        else:
            trend_arrow = reading["reading"].split()[1]
        str_reading = reading["reading"].split()[0] + trend_arrow
        log.debug("About to push: " + str_reading + " to the display")
        text_surface = font_big.render(str_reading, True, font_color)
        rect = text_surface.get_rect(center=(240,155))
        lcd.blit(text_surface, rect)

        font_medium = pygame.font.Font(None, 135)
        text_surface = font_medium.render(reading["reading"].split()[2],True,font_color)
        rect = text_surface.get_rect(center=(240, 275))
        lcd.blit(text_surface, rect)

        log.debug("About to update the LCD display")
        pygame.display.update()
        pygame.mouse.set_visible(False)
    finally:
        log.debug("Done with display")

def no_connection():

    log.info("Displaying connection failure")
    if not platform.platform().find("arm") >= 0:
        log.debug("Skipping display.  Not on Raspberry Pi")
        return
    global pygame, lcd

    now = datetime.datetime.utcnow()
    try:
        if isNightTime():
           log.debug("Setting to Nighttime mode")
           lcd.fill(Defaults.BLACK)
           font_color=Defaults.GREY
        else:
           log.debug("Setting to Daylight mode")
           lcd.fill(Defaults.BLUE)
           font_color=Defaults.WHITE

        font_big = pygame.font.SysFont("dejavusans", 150)
        text_surface = font_big.render("net failure", True, font_color)
        rect = text_surface.get_rect(center=(240,155))
        lcd.blit(text_surface, rect)

        log.debug("About to update the LCD display")
        pygame.display.update()
        pygame.mouse.set_visible(False)
    finally:
        log.debug("Done with display")

i=0
while True:
    i += 1
    try:
        log.info("Getting Reading from Sugarmate - Loop #" + str(i))
        r=requests.get("https://sugarmate.io/api/v1/"+API_KEY+"/latest.json")
        log.info("Got Status Code: " + str(r.status_code))
        log.info("Data: " + str(r.json()))
        j=r.json()
        display_reading(j)

    except Exception as e:
        log.info("Exception processing The Reading, Sleeping and trying again....")
        log.info(e)
        no_connection()
    sleep(CHECK_INTERVAL)
