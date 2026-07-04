# CGM Display
CGM Display Project

Always on CGM Display.  Designed for Raspberry Pi using Adafruit's PiTFT Plus 3.5" display (parts list I used below).
This depends on Dexcom CGM data from the Dexcom server or from an active Sugarmate account using the Sugarmate API.

![Alt text](assets/images/IMG_0440.jpeg?raw=true "CGM Display")
![Alt text](assets/images/IMG_2247.jpeg?raw=true "e-Ink Display")

**Quick Links**: [Installation](#installation) • [Running](#running-cgm_display) • [Changelog](CHANGELOG.md) • [Directory Structure](#project-directory-structure)

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

## Basic Raspberry Pi Setup
I am not going to cover basic Raspberry Pi setup and configuration.  Minimum requirement is to have your Pi built, current Raspian OS installed and configured and connected to your WiFi network.  You should be able to login to your Pi with the standard pi user account via Desktop or Command Line.  Good getting started information can be found here: https://projects.raspberrypi.org/en/projects/raspberry-pi-getting-started

## PiTFT LCD Display Hardware Installation
The PiTFT Plus 3.5" display requires proper hardware setup and software installation:

1. **Physical Assembly**
   - Connect the PiTFT display to the GPIO pins on your Raspberry Pi
   - If using Pi Zero W, solder or use a solderless header connector (Hammer Header recommended)
   - Mount in case if desired (PiTFT Pibow+ case works well)

2. **Software Installation**
   - Follow the Adafruit PiTFT software installation instructions: https://learn.adafruit.com/adafruit-pitft-3-dot-5-touch-screen-for-raspberry-pi/easy-install-2
   - This installs the necessary kernel drivers and framebuffer support at `/dev/fb1`

3. **Clone CGM Display Application**
   - Download this repo: `git clone https://github.com/hblanck/cgm_display /home/pi/cgm_display`
   - Or download zip file: https://github.com/hblanck/cgm_display/archive/master.zip
   - Extract to `/home/pi/cgm_display` directory

4. **Install Python Dependencies**
   ```bash
   cd /home/pi/cgm_display
   python3 -m pip install -r requirements.txt
   ```

# Running cgm_display

The unified `cgm_display.py` entry point supports both Nightscout and Dexcom data sources via subcommands.

## Nightscout Mode

To run with a Nightscout server:
```bash
python3 cgm_display.py nightscout --nightscoutserver https://your-nightscout-server.com
```

Optional arguments:
- `--logging INFO|DEBUG` - Set logging level (default: INFO)
- `--polling_interval N` - How often to fetch new readings in seconds (default: 60)
- `--time_ago_interval N` - How often to update the "time ago" display in seconds (default: 30)

To run at boot automatically, add to `/etc/rc.local`:
```bash
sudo python3 /home/pi/cgm_display/cgm_display.py nightscout --nightscoutserver https://your-nightscout.com --logging=INFO > /var/log/cgm_display.log 2>&1 &
```

## Dexcom Mode

Credentials are resolved in this order (first found wins):
1. Command-line arguments: `--username` and `--password`
2. Environment variables: `DEXCOM_USERNAME` and `DEXCOM_PASSWORD`

### Using Command-Line Arguments
```bash
python3 cgm_display.py dexcom --username YOUR_USERNAME --password YOUR_PASSWORD
```

### Using Environment Variables (Recommended)
Set environment variables and run without credentials in the command:
```bash
export DEXCOM_USERNAME=your_username
export DEXCOM_PASSWORD=your_password
python3 cgm_display.py dexcom
```

### Using Systemd Service
Create `/etc/systemd/system/cgm-display.service`:
```ini
[Unit]
Description=CGM Display
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/cgm_display
Environment="DEXCOM_USERNAME=your_username"
Environment="DEXCOM_PASSWORD=your_password"
ExecStart=/usr/bin/python3 /home/pi/cgm_display/cgm_display.py dexcom --logging=INFO
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Using Docker

**Quick Start with .env file**:
```bash
# Copy example and fill in your credentials
cp .env.example .env
# Edit .env with your credentials

# Run with Docker using .env file
docker run --env-file .env cgm-display cgm_display.py dexcom
```

**With inline environment variables**:
```bash
docker run \
  -e DEXCOM_USERNAME=your_username \
  -e DEXCOM_PASSWORD=your_password \
  cgm-display cgm_display.py dexcom
```

**With Docker Compose**:
Create a `docker-compose.yml`:
```yaml
version: '3.8'
services:
  cgm-display:
    build: .
    env_file: .env
    environment:
      - CGM_LOG_LEVEL=INFO
    stdin_open: true
    tty: true
```

Then run:
```bash
docker-compose up -d
```

**Environment Variables Available** (see `.env.example`):
- `DEXCOM_USERNAME` — Dexcom Share username
- `DEXCOM_PASSWORD` — Dexcom Share password
- `NIGHTSCOUT_SERVER` — Nightscout server URL
- `CGM_POLLING_INTERVAL` — Fetch interval in seconds (optional)
- `CGM_TIME_AGO_INTERVAL` — Display update interval in seconds (optional)
- `CGM_LOG_LEVEL` — INFO or DEBUG (optional)

### Optional Arguments
- `--logging INFO|DEBUG` - Set logging level (default: INFO)
- `--polling_interval N` - How often to fetch new readings in seconds (default: 180)
- `--time_ago_interval N` - How often to update the "time ago" display in seconds (default: 30)

# Project Directory Structure

```
cgm_display/
├── src/                          # Python source modules
│   ├── __init__.py
│   ├── cgm_args.py              # Command-line argument parsing
│   ├── cgm_display.py            # (entry point also in root)
│   ├── Defaults.py               # Configuration constants
│   ├── dexcom_data.py            # Dexcom API client
│   ├── http_general.py           # Dexcom HTTP utilities
│   ├── logger.py                 # Logging configuration
│   ├── nightscout_data.py        # Nightscout API client
│   └── pygame_display.py         # Display rendering
│
├── assets/                       # Images and resources
│   ├── images/                   # Documentation/display images
│   │   ├── IMG_0440.jpeg        # PiTFT display example
│   │   ├── IMG_2247.jpeg        # e-Ink display example
│   │   └── IMG_5750.png         # Another display image
│   ├── loop-status/              # Loop status indicator icons
│   │   ├── loop-aging@38mm.png
│   │   ├── loop-fresh@38mm.png
│   │   └── loop-stale@38mm.png
│   └── nightscout_large.png      # Nightscout icon (downloaded at runtime)
│
├── docs/                         # Documentation files
│   └── THIRD_PARTY_NOTICES.md   # License attributions
│
├── archive/                      # Archived/obsolete code (preserved for reference)
│   ├── cgm_display_2displays.py  # Old: dual-display variant
│   ├── cgm_display_legacy.py     # Old: legacy Dexcom implementation
│   ├── e-ink_display.py          # Old: Waveshare e-ink support
│   └── sugarmate_display.py      # Old: Sugarmate API variant
│
├── cgm_display.py                # Main entry point
├── Dockerfile                    # Container configuration
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── .gitignore                    # Git exclusions
```

## Directory Organization

- **`src/`** — All Python source code organized as a package
- **`assets/`** — Static resources (images, icons)
  - `images/` — Documentation images (screenshots, diagrams)
  - `loop-status/` — Loop device status indicator images
- **`docs/`** — Project documentation files
- **`archive/`** — Obsolete/unmaintained code (preserved in git history for reference)
- **Root files** — Configuration files and main entry point

# Archived Display Options

The following display options are no longer actively maintained and have been archived to the `archive/` directory (see git history for reference):

- **cgm_display_legacy.py** - Original Dexcom Share implementation
- **sugarmate_display.py** - Sugarmate API integration (alternative to Dexcom)
- **e-ink_display.py** - Waveshare e-ink display support
- **cgm_display_2displays.py** - Dual-display variant (monitoring two users)

Use the modern unified **cgm_display.py** entry point instead, which supports both Nightscout and Dexcom data sources.
