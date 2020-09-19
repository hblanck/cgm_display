#First implementation of using an e-ink display.  Using this one:  https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT
#Need to install the waveshare raspberrypi/python libraries this depends on.  These are included in their sample code.  https://github.com/waveshare/e-Paper, (sudo git clone https://github.com/waveshare/e-Paper) to install on your Pi
#Copy the libraries into the directory where this application is located.  I will assume here that this is /home/pi/cgm_display
# To copy where you need it:
#    mkdir /home/pi/cgm_display/lib
#    cp /home/pi/e-Paper-master/RaspberryPi\&JetsonNano/python/lib/* /home/pi/cgm_display/lib


import sys
import argparse
import time
import datetime
import requests
import json
import logging

log = logging.getLogger(__file__)
log.setLevel(logging.ERROR)
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

#sys.path.append("./lib") #This assumes you have placed the waveshare_epd libraries in ./lib (subdirectory of where this file is)
log.info("The path is: " + Path().absolute())
sys.path.append(Path().absolute()+"/lib")
font_file="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_font_s = 20
_font_m = 45
_font_l = 75

from waveshare_epd import epd2in7
from PIL import Image, ImageDraw, ImageFont

epd = epd2in7.EPD() # get the display
epd.init()           # initialize the display
epd.Clear(0xFF)      # clear the display

def printToDisplay(reading):

    now = datetime.datetime.utcnow()
    reading_time = datetime.datetime.utcfromtimestamp(reading["x"]) # Sugarmate puts the posix timstamp in the 'x' attribute
    difference = round((now - reading_time).total_seconds()/60)
    if difference == 0:
        str_difference = "Just Now"
    elif difference == 1:
        str_difference = str(difference) + " Minute Ago"
    else:
        str_difference = str(difference) + " Minutes Ago"
    str_difference += "-"+reading["time"]

    HBlackImage = Image.new('1', (epd2in7.EPD_HEIGHT, epd2in7.EPD_WIDTH), 255)
    draw = ImageDraw.Draw(HBlackImage) # Create draw object and pass in the image layer we want to work with (HBlackImage)

    font_s = ImageFont.truetype(font_file, _font_s)
    font_m = ImageFont.truetype(font_file, _font_m)
    font_l = ImageFont.truetype(font_file, _font_l)

    draw.text((10, 5), str_difference, font = font_s, fill = 0)
    draw.text((20, 40), str(reading["value"]) + reading["trend_symbol"], font = font_l, fill = 0)
    draw.text((90, 120), reading["reading"].split()[2], font = font_m, fill = 0)
    epd.display(epd.getbuffer(HBlackImage))

i=0
while True:
    i += 1
    try:
        log.info("Getting Reading from Sugarmate - Loop #" + str(i))
        r=requests.get("https://sugarmate.io/api/v1/"+API_KEY+"/latest.json")
        j=r.json()
        printToDisplay(j)

    except Exception as e:
        print("Exception processing The Reading, Sleeping and trying again....")
        print(e)
    time.sleep(CHECK_INTERVAL)