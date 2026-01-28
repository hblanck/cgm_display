"""Nightscout CGM display.

Fetches CGM readings and device status from a Nightscout server and displays them.
On Raspberry Pi (Linux/ARM), uses pygame to render to a PiTFT framebuffer.
"""

from __future__ import annotations

import datetime
import logging
import os
import platform
import sys
from time import sleep
from typing import Any, Optional

from Defaults import Defaults
from cgm_args import cgm_args
from logger import log
from nightscout_data import Nightscout
from pygame_display import PygameDisplay

def _epoch_to_utc_datetime(epoch: Any) -> datetime.datetime:
    """Convert seconds-or-milliseconds epoch to an aware UTC datetime."""

    try:
        value = int(epoch)
    except Exception:
        value = int(str(epoch)[0:10])

    # Nightscout "date" is commonly ms since epoch.
    if value > 1_000_000_000_000:
        value = value // 1000
    return datetime.datetime.fromtimestamp(value, datetime.timezone.utc)


def _format_time_ago(minutes: int) -> str:
    if minutes <= 0:
        return "Just Now"
    if minutes == 1:
        return "1 Minute Ago"
    return f"{minutes} Minutes Ago"


def _get_loop_image_path(devicestatus: Any, now_utc: datetime.datetime) -> Optional[str]:
    if not devicestatus or not isinstance(devicestatus, list) or not devicestatus[0]:
        log.info("No Loop Data, No Loop status Image Used")
        return None

    loop = devicestatus[0].get("loop")
    if not loop or "timestamp" not in loop:
        log.info("No Loop Data, No Loop status Image Used")
        return None

    try:
        loop_time = datetime.datetime.strptime(loop["timestamp"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc
        )
    except Exception:
        log.info("No Loop Data, No Loop status Image Used")
        return None

    loop_age_minutes = round((now_utc - loop_time).total_seconds() / 60)
    if 0 <= loop_age_minutes <= 5:
        loop_image = Defaults.Loop_Fresh
    elif 6 <= loop_age_minutes <= 10:
        loop_image = Defaults.Loop_Aging
    else:
        loop_image = Defaults.Loop_Stale

    loop_image_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), loop_image)
    log.info(f"Loop Age:{loop_age_minutes} Minutes, Loop Image Used:{loop_image_path}")
    return loop_image_path


def display_reading(
    readings: Any,
    devicestatus: Any,
    *,
    display: Optional[PygameDisplay],
    connection_ok: bool,
) -> Optional[dict[str, Any]]:
    if not readings or not isinstance(readings, list) or len(readings) < 2:
        log.warning("No readings (or not enough readings) returned from Nightscout")
        return None

    reading = readings[0]
    last_reading = readings[1]
    if not isinstance(reading, dict) or not isinstance(last_reading, dict):
        log.warning("Unexpected readings format returned from Nightscout")
        return None

    if "date" not in reading or "sgv" not in reading or "sgv" not in last_reading:
        log.warning("Nightscout reading missing required fields")
        return None

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    reading_time = _epoch_to_utc_datetime(reading["date"])
    difference_minutes = round((now_utc - reading_time).total_seconds() / 60)
    str_difference = _format_time_ago(difference_minutes)

    direction = reading.get("direction")
    if direction in Defaults.DIRECTIONS:
        trend_arrow = Defaults.ARROWS[str(Defaults.DIRECTIONS[direction])]
    else:
        trend_arrow = ""

    if difference_minutes < 7:
        str_reading = f"{reading['sgv']}{trend_arrow}"
    else:
        str_reading = "---"

    change_value = reading["sgv"] - last_reading["sgv"]
    str_change = f"+{change_value}" if change_value > 0 else str(change_value)

    loop_image_path = _get_loop_image_path(devicestatus, now_utc)

    log.debug(f"Displaying:\n\t{str_difference}\n\t{str_reading}\n\t{str_change}")
    if display is None:
        log.info("Skipped display, not on Raspberry Pi")
        return reading

    try:
        display.render(
            difference=str_difference,
            reading=str_reading,
            change=str_change,
            loop_image_path=loop_image_path,
            connection_ok=connection_ok,
        )
    except Exception as e:
        log.info("Caught an Exception processing the display")
        log.error(e, exc_info=True)
    return reading


def main() -> int:
    args = cgm_args()
    if args.logging == "DEBUG":
        log.setLevel(logging.DEBUG)

    if not args.night_scout_server:
        log.error("No Nightscout URL defined. Exiting")
        return 2

    log.debug(f"Using Arguments: {args}")

    polling_interval = int(args.polling_interval)
    time_ago_interval = int(args.time_ago_interval)
    tick_interval = max(1, min(polling_interval, time_ago_interval))

    log.debug(f"Platform we're running on is: {platform.platform()}")

    # Per user preference: always attempt pygame display initialization regardless of platform,
    # and fail fast if it can't initialize.
    try:
        display = PygameDisplay()
    except Exception as e:
        log.error("pygame not initialized; there will be no video device")
        log.error("Failed to initialize pygame display; exiting")
        log.error(e, exc_info=True)
        return 3

    nightscout = Nightscout(args.night_scout_server)

    loop_count = 0
    last_fetch: Optional[datetime.datetime] = None
    last_readings: Any = None
    last_devicestatus: Any = None
    last_fetch_ok = False

    while True:
        loop_count += 1
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            should_fetch = last_fetch is None or (now - last_fetch).total_seconds() >= polling_interval
            if should_fetch:
                log.info(f"Getting Reading and Device Status from Nightscout - Loop #{loop_count}")
                try:
                    last_readings = nightscout.getReading()
                    last_devicestatus = nightscout.getDeviceStatus()
                    last_fetch = now
                    last_fetch_ok = True
                except Exception as e:
                    last_fetch_ok = False
                    # If we have never successfully fetched data, show a full-screen connection error.
                    if last_fetch is None:
                        log.error("Initial Nightscout connection failed")
                        log.error(e, exc_info=True)
                        display.render_connection_error(detail=str(e))
                        sleep(tick_interval)
                        continue

                    # Otherwise, keep the last displayed reading and try again next poll.
                    log.error("Nightscout fetch failed; keeping last known readings")
                    log.error(e, exc_info=True)

            display_reading(last_readings, last_devicestatus, display=display, connection_ok=last_fetch_ok)

        except KeyboardInterrupt:
            log.info("Exiting on KeyboardInterrupt")
            return 0
        except Exception as e:
            log.error(e, exc_info=True)
            log.info("Exception processing the reading, sleeping and trying again....")

        sleep(tick_interval)


if __name__ == "__main__":
    raise SystemExit(main())
