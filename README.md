# CGM Display
CGM Display Project

Always on CGM Display.  Designed for Raspberry Pi using Adafruit's PiTFT Plus 3.5" display (parts list I used below).
This depends on Dexcom CGM data from the Dexcom server or from an active Sugarmate account using the Sugarmate API.

![Alt text](IMG_0440.jpeg?raw=true "CGM Display")
![Alt text](IMG_2247.jpeg?raw=true "e-Ink Display")

# Credits

Thanks to jerm's Dexcom Tools project (https://github.com/jerm/dexcom_tools) for the core code used here.

# Features
- Always on Display
- Configurable Polling interval for how often you check for updates from Dexcom
- Configurable Display refersh interval (time ago).
- Nightmode.  Between 10pm and 7am the display uses lighter gray colors instead of high contrast white on blue.

# Updated Features - 9/19/20
- Added beta support for an e-ink display (Only one specific display currently supported, see e-ink_display.py for details)
- Added support for getting CGM data from Sugarmate instead of directly from Dexcom share servers (due to some recent changes and issues with Dexcom servers).  You will need your unique Sugarmate JSON API key.  If you are a Sugarmate user, go to https://sugarmate.io from a browser (not the mobile or desktop apps), log into your account, and under settings the 'External JSON' information will be at the bottom of the page.  The six character identifier will be passed into the application per the documentation.  This hasn't been merged into the main code yet.  Use 'sugarmate_display.py' to enable this.
- Finally fixed the display of double-up and double-down arrows.  Using full utf-8 character set font (dejavusans) on all displays for sugarmate_display.py and e-ink_display.py.  TBD on cgm_display.py

# Not Features
- No visual or audio alerts.  No plans to add these features which already exist in Dexcom and other apps.

# Parts List

- Raspberry Pi Zero W.  I got mine from Adafruit (https://www.adafruit.com/product/3400).  I chose the Pi Zero W because it is cheaper.  But this also works well, and you'll find the cases to fit better with the standard Pi 3.  If you are not comfortable with attaching the header for the GPIO pins, then I'd go with the standard Pi.
- Adafruit PiTFT Plus 3.5" Touchscreen display (https://www.adafruit.com/product/2441)
- Hammer Header Male - Solderless Raspberry Pi Connector (Only needed if using Pi Zero W) (https://www.adafruit.com/product/3662)
- PiTFT Pibow+ Case (Optional) - Not a perfect fit, but I made it work pretty easily. (https://www.adafruit.com/product/2779)
- If you don't have an SD card, AC Adapter or other cables required you can pick those up on Adafruit or Amazon pretty easily too.

NOTE:  I've also had success with one other LCD display.  The setup and configuration was a bit different.  This should work with any compatible display.  So feel free to experiment and let me know your results.

# Updated Parts information 9/19/20
- As mentioned above, I have a working version using this e-ink display.  https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT.  I found it on Amazon for about $20.

# Requirements
This is the version I developed on.  All required packages were included in the distribution below.  Except for the PiTFT install which is documented below.

NOTES:  It is much easier to use the full Raspian distribution (Raspian with desktop and recommended software).  I've recently built using Raspian Buster release successfully with no issues.

Raspberry Pi Version:
- Tested with current Raspberry Pi OS (formerly Raspian) as of 9/1920.  Full version with all recommended packages

# Installation
- I am not going to cover basic Raspberry Pi setup and configuration.  Minimum requirement is to have your Pi built, current Raspian OS installed and configured and connected to your WiFi network.  You should be able to login to your Pi with the standard pi user account via Desktop or Command Line.  Good getting started information can be found here: https://projects.raspberrypi.org/en/projects/raspberry-pi-getting-started

# PiTFT LCD Display
- PiTFT LCD display also needs to be installed and connected to the GPIO pins on your Pi.
- Follow the PiTFT software installation instructions: https://learn.adafruit.com/adafruit-pitft-3-dot-5-touch-screen-for-raspberry-pi/easy-install-2
- Download this zip file (https://github.com/hblanck/cgm_display/archive/master.zip).  Unzip in your /home/pi directory (all instructions will assume this location).
- Modify /home/pi/cgm_display/cgm_display.ini and put your Login name and password.  These are the ones you use in your Dexcom share app (not follow).  Save the file.  If you don't want to store your credentials in a file you can use the --username and --password command line options.
- To run as a foreground application "cd ~/cgm_display ; sudo python3 cgm_display.py"
- To install it to run at boot up automatically add the following line to your startup script.  To edit /etc/rc.local, 'sudo nano /etc/rc.local'.
Add the following line: "sudo python3 /home/pi/cgm_display/cgm_display.py --username=USERNAME --password=PASSWORD --logging=INFO > /var/log/cgm_display.log 2>&1 &"
 (Note: use --logging=DEBUG for debug level logging)

# Sugarmate with LCD display Version (this won't fetch data directly from Dexcom)
- Same as above for PiTFT LCD Display
- Modiy /etc/rc.local to start the sugarmate_display.py application
- "sudo nano /etc/rc.local"
- The execution line should say "sudo python3 /home/pi/cgm_display/sugarmate_display.py --apikey [your sugarmate api key] --polling_interval 30 > /var/log/sugarmate_display.log 2>&1 &"

# Sugarmate with e-Ink display version (this won't fetch data directly from Dexcom)
- First we will need to download the e-ink drivers from waveshare.  From the pi home directoy "git clone https://github.com/waveshare/e-Paper"
- Copy the python libraries to our application directory for easier reference (this assumes the application is in /home/pi/cgm_display and waveshare libraries were cloned from get into /home/pi/e_Paper-master) "mkdir /home/pi/cgm_display/lib;cp -r /home/pi/e-Paper-master/RaspberryPi\&JetsonNano/python/lib/* /home/pi/cgm_display/lib/".
- Currently only supports the 2.7inch version.  May work with others, but different libraries would need to be called.  TBD to make this more flexible and extensible.
- Modify /etc/rc.local to start the e-ink_display.py application.
- "sudo nano /etc/rc.local"
- The execution line should say "sudo python3 /home/pi/cgm_display/e-ink_display.py --apikey [your sugarmate api key] --polling_interval 30 > /var/log/e-ink_display.log 2>%1 &"
