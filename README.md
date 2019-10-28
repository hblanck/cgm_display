# CGM Display
CGM Display Project

Always on CGM Display.  Designed for Raspberry Pi using Adafruit's PiTFT Plus 3.5" display (parts list I used below).
This depends on Dexcom CGM data from the Dexcom server.
![Alt text](IMG_0440.jpeg?raw=true "CGM Display")

# Credits

Thanks to jerm's Dexcom Tools project (https://github.com/jerm/dexcom_tools) for the core code used here.

# Parts List

- Raspberry Pi Zero W.  I got mine from Adafruit (https://www.adafruit.com/product/3400).  I chose the Pi Zero W because it is cheaper.  But this also works well, and you'll find the cases to fit better with the standard Pi 3.  If you are not comfortable with attaching the header for the GPIO pins, then I'd go with the standard Pi.
- Adafruit PiTFT Plus 3.5" Touchscreen display (https://www.adafruit.com/product/2441)
- Hammer Header Male - Solderless Raspberry Pi Connector (Only needed if using Pi Zero W) (https://www.adafruit.com/product/3662)
- PiTFT Pibow+ Case (Optional) - Not a perfect fit, but I made it work pretty easily. (https://www.adafruit.com/product/2779)
- If you don't have an SD card, AC Adapter or other cables required you can pick those up on Adafruit or Amazon pretty easily too.

NOTE:  I've also had success with one other LCD display.  The setup and configuration was a bit different.  This should work with any compatible display.  So feel free to experiment and let me know your results.

# Requirements
This is the version I developed on.  All required packages were included in the distribution below.  Except for the PiTFT install which is documented below.

NOTES:  It is much easier to use the full Raspian distribution (Raspian with desktop and recommended software).  I've recently built using Raspian Buster release successfully with no issues.

Raspberry Pi Version:

"Raspian"
pi@raspberrypi:~ $ cat /etc/debian_version
9.4

pi@raspberrypi:~ $ cat /etc/os-release
PRETTY_NAME="Raspbian GNU/Linux 9 (stretch)"
NAME="Raspbian GNU/Linux"
VERSION_ID="9"
VERSION="9 (stretch)"
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"

Python (Python 2 not supported)
pi@raspberrypi:~ $ sudo python3 --version
Python 3.5.3

# Installation
- I am not going to cover basic Raspberry Pi setup and configuration.  Minimum requirement is to have your Pi built, current Raspian OS installed and configured and connected to your WiFi network.  You should be able to login to your Pi with the standard pi user account via Desktop or Command Line.  Good getting started information can be found here: https://projects.raspberrypi.org/en/projects/raspberry-pi-getting-started
- PiTFT LCD display also needs to be installed and connected to the GPIO pins on your Pi.  
- Follow the PiTFT software installation instructions: https://learn.adafruit.com/adafruit-pitft-3-dot-5-touch-screen-for-raspberry-pi/easy-install-2
- Download this zip file (https://github.com/hblanck/cgm_display/archive/master.zip).  Unzip in your /home/pi directory (all instructions will assume this location).
- Modify /home/pi/cgm_display/cgm_display.ini and put your Login name and password.  These are the ones you use in your Dexcom share app (not follow).  Save the file.  If you don't want to store your credentials in a file you can use the --username and --password command line options.
- To run as a foreground application "cd ~/cgm_display ; sudo python3 cgm_display.py"
- To install it to run at boot up automatically add the following line to your startup script.  To edit /etc/rc.local, 'sudo nano /etc/rc.local'.
Add the following line: "sudo python3 /home/pi/cgm_display/cgm_display.py --username=USERNAME --password=PASSWORD --logging=INFO > /var/log/cgm_display.log 2>&1 &"
 (Note: use --logging=DEBUG for debug level logging)
