import os
import sys
import platform
from time import sleep
import logging
import urllib
import urllib.parse #Python3 requires this
import requests
import json
from Defaults import Defaults


log = logging.getLogger(__file__)
log.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
log.addHandler(ch)

if  platform.platform().find("arm") >= 0:
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
    log.debug("Displaying with Reading of " + str(reading))
    if not platform.platform().find("arm") >= 0:
        log.debug("Skipping display.  Not on Raspberry Pi")
        return
    global pygame, lcd
    log.debug("Getting ready to display on the LCD panel")

    now = datetime.datetime.utcnow()
    reading_time = datetime.datetime.utcfromtimestamp(reading["timestamp"])
    difference = round((now - reading_time).total_seconds()/60)
    log.debug("Time difference since last good reading is: " + str(difference))
    if difference == 0:
        str_difference = "Just Now"
    elif difference == 1:
        str_difference = str(difference) + " Minute Ago"
    else:
        str_difference = str(difference) + " Minutes Ago"
    log.info("About to update Time Ago Display with reading from " + str_difference)
    log.debug("About to acquire lock with: "+str(lock))
    lock.acquire(blocking=True)
    log.debug("Acquired lock "+str(lock))

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

        font_big = pygame.font.Font(None, 250)
        #trend_index = reading["trend"]
#         if (reading["last_reading_lag"] == True) or (difference > round(LAST_READING_MAX_LAG/60)):
#            str_reading = "---"
#         else:
        #str_reading = str(reading["bg"])+Defaults.ARROWS[str(trend_index)]
        str_reading = reading["reading"]
        text_surface = font_big.render(str_reading, True, font_color)
        rect = text_surface.get_rect(center=(240,155))
        lcd.blit(text_surface, rect)
        
        font_medium = pygame.font.Font(None, 135)
        #text_surface = font_medium.render('{0:{1}}'.format(bgdelta, '+' if bgdelta else ''),True,font_color)
        text_surface = font_medium.render('{0:{1}}'.format(reading["delta"], '+' if bgdelta else ''),True,font_color)
        rect = text_surface.get_rect(center=(240, 275))
        lcd.blit(text_surface, rect)
        
        pygame.display.update()
        pygame.mouse.set_visible(False)
    finally:
        log.debug("About to release lock: "+str(lock))
        lock.release()
        log.debug("Lock released: "+str(lock))
   

i=0
while True:
    i += 1
    try:
        log.info("Getting Reading from Sugarmate")
        r=requests.get("https://sugarmate.io/api/v1/rva9fb/latest.json")
        log.info("Got Status Code: " + r.status_code.__str__())
        j=r.json()
        print(r.text)
        print(j["full"])
        display_reading(j)

    except:
        log.info("Exception processing The Reading, Sleeping and trying again....")
    sleep(120)
