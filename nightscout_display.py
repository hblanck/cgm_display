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


def _is_night_time() -> bool:
    now = datetime.datetime.now()
    return now.hour in Defaults.NIGHTMODE


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


def _nightscout_icon_path() -> str:
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_dir, "assets", "nightscout_large.png")


def _ensure_nightscout_icon_downloaded(dest_path: str) -> None:
    """Download the official Nightscout icon if it isn't present locally."""

    if os.path.exists(dest_path):
        return

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    # Official source (Nightscout CGM Remote Monitor repo).
    url = "https://raw.githubusercontent.com/nightscout/cgm-remote-monitor/master/static/images/large.png"

    try:
        import requests
    except Exception as e:
        raise RuntimeError("requests is required to download the Nightscout icon") from e

    response = requests.get(url, timeout=15)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(response.content)


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


class _PygameDisplay:
    def __init__(self) -> None:
        os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
        # On Raspberry Pi targets, pygame typically renders to a framebuffer device.
        # On desktop platforms, this is ignored and pygame opens a normal window.
        if sys.platform.startswith("linux"):
            os.putenv(
                "SDL_FBDEV", "/dev/fb1"
            )  # May need adjustment for different framebuffer devices.
        import pygame  # local import: optional dependency

        self._pygame = pygame
        pygame.init()
        self._lcd = pygame.display.set_mode((480, 320))
        self._nightscout_icon_base: Optional["pygame.Surface"] = None
        self._connection_error_icon: Optional["pygame.Surface"] = None
        try:
            icon_path = _nightscout_icon_path()
            _ensure_nightscout_icon_downloaded(icon_path)
            icon_surface = pygame.image.load(icon_path).convert_alpha()
            self._nightscout_icon_base = icon_surface
            self._connection_error_icon = pygame.transform.smoothscale(icon_surface, (96, 96))
        except Exception:
            # If loading the PNG fails for any reason, we'll fall back to a drawn icon.
            self._nightscout_icon_base = None
            self._connection_error_icon = None
        log.debug("Initialized pygame display")

    def render(
        self,
        *,
        difference: str,
        reading: str,
        change: str,
        loop_image_path: Optional[str],
        connection_ok: bool,
    ) -> None:
        pygame = self._pygame
        lcd = self._lcd
        width, height = lcd.get_size()

        the_platform = platform.platform().lower()
        if "linux" in the_platform:
            font_to_use = Defaults.Linux_font
        elif "macos" in the_platform:
            font_to_use = Defaults.Mac_font
        else:
            font_to_use = ""

        if _is_night_time():
            lcd.fill(Defaults.BLACK)
            font_color = Defaults.GREY
        else:
            lcd.fill(Defaults.BLUE)
            font_color = Defaults.WHITE

        font_time = pygame.font.Font(None, 75)
        time_surface = font_time.render(difference, True, font_color)
        lcd.blit(time_surface, time_surface.get_rect(center=(240, 20)))

        font_big = pygame.font.SysFont(font_to_use, 200)
        reading_surface = font_big.render(reading, True, font_color)
        lcd.blit(reading_surface, reading_surface.get_rect(center=(240, 155)))

        font_medium = pygame.font.Font(None, 135)
        change_surface = font_medium.render(change, True, font_color)
        lcd.blit(change_surface, change_surface.get_rect(center=(240, 275)))

        if loop_image_path:
            loop_surface = pygame.image.load(loop_image_path)
            lcd.blit(loop_surface, loop_surface.get_rect(center=(450, 290)))

        # Connection status badge (bottom-right): Nightscout icon + indicator.
        if self._nightscout_icon_base is not None:
            icon_size = 52
            margin = 8
            icon = pygame.transform.smoothscale(self._nightscout_icon_base, (icon_size, icon_size))
            x = width - icon_size - margin
            y = height - icon_size - margin
            lcd.blit(icon, (x, y))

            indicator_r = 10
            indicator_center = (x + icon_size - 8, y + icon_size - 8)
            ok_color = (0, 200, 0)
            bad_color = (255, 80, 80)
            indicator_color = ok_color if connection_ok else bad_color
            pygame.draw.circle(lcd, indicator_color, indicator_center, indicator_r)
            pygame.draw.circle(lcd, (255, 255, 255), indicator_center, indicator_r, 2)

            if connection_ok:
                # Check mark
                cx, cy = indicator_center
                pygame.draw.lines(
                    lcd,
                    (255, 255, 255),
                    False,
                    [(cx - 5, cy + 0), (cx - 1, cy + 4), (cx + 6, cy - 4)],
                    3,
                )
            else:
                # X mark
                cx, cy = indicator_center
                pygame.draw.line(lcd, (255, 255, 255), (cx - 5, cy - 5), (cx + 5, cy + 5), 3)
                pygame.draw.line(lcd, (255, 255, 255), (cx - 5, cy + 5), (cx + 5, cy - 5), 3)

        pygame.display.update()
        pygame.mouse.set_visible(False)

    def render_connection_error(self, *, title: str = "Connection Error", detail: str = "") -> None:
        """Render a full-screen connection error message."""

        pygame = self._pygame
        lcd = self._lcd
        width, height = lcd.get_size()

        lcd.fill(Defaults.BLUE)
        font_color = Defaults.WHITE

        # PNG icon preferred; fall back to a simple drawn icon.
        if self._connection_error_icon is not None:
            icon = self._connection_error_icon
            icon_pos = (int(width * 0.08), int(height * 0.14))
            lcd.blit(icon, icon_pos)
        else:
            icon_center = (int(width * 0.15), int(height * 0.30))
            icon_radius = int(min(width, height) * 0.12)
            icon_rect = pygame.Rect(
                icon_center[0] - icon_radius,
                icon_center[1] - icon_radius,
                icon_radius * 2,
                icon_radius * 2,
            )

            stroke = 5
            for r in (icon_radius, int(icon_radius * 0.72), int(icon_radius * 0.44)):
                rect = pygame.Rect(
                    icon_center[0] - r,
                    icon_center[1] - r,
                    r * 2,
                    r * 2,
                )
                pygame.draw.arc(lcd, font_color, rect, 3.4, 5.98, stroke)
            pygame.draw.circle(lcd, font_color, (icon_center[0], icon_center[1] + int(icon_radius * 0.70)), 8)

            pygame.draw.line(
                lcd,
                (255, 80, 80),
                (icon_rect.left, icon_rect.top + 5),
                (icon_rect.right, icon_rect.bottom - 5),
                8,
            )

        def wrap_lines(text: str, font, max_width: int, max_lines: int) -> list[str]:
            words = (text or "").strip().replace("\n", " ").split()
            if not words:
                return []
            lines: list[str] = []
            current: list[str] = []
            for word in words:
                candidate = (" ".join(current + [word])).strip()
                if font.size(candidate)[0] <= max_width or not current:
                    current.append(word)
                else:
                    lines.append(" ".join(current))
                    current = [word]
                if len(lines) >= max_lines:
                    break
            if len(lines) < max_lines and current:
                lines.append(" ".join(current))
            if len(lines) >= max_lines and words:
                # Add an ellipsis if we truncated.
                last = lines[-1]
                while last and font.size(last + "...")[0] > max_width:
                    last = last[:-1]
                lines[-1] = (last + "...") if last else "..."
            return lines

        # Layout: icon on left, wrapped text on right.
        left_margin = 20
        top_margin = 18
        icon_width = 96
        icon_height = 96
        text_left = left_margin + icon_width + 18
        text_right_margin = 18
        max_text_width = max(10, width - text_left - text_right_margin)

        font_title = pygame.font.Font(None, 56)
        font_detail = pygame.font.Font(None, 32)

        title_lines = wrap_lines(title, font_title, max_text_width, max_lines=2)
        y = top_margin
        for line in title_lines:
            surf = font_title.render(line, True, font_color)
            lcd.blit(surf, (text_left, y))
            y += surf.get_height() + 2

        y += 10
        for line in wrap_lines("Couldn't reach Nightscout.", font_detail, max_text_width, max_lines=2):
            surf = font_detail.render(line, True, font_color)
            lcd.blit(surf, (text_left, y))
            y += surf.get_height() + 2

        # Exception detail: wrap and limit to remaining space.
        detail = (detail or "").strip().replace("\n", " ")
        if detail:
            y += 6
            remaining_lines = max(1, (height - y - 12) // (font_detail.get_height() + 2))
            for line in wrap_lines(detail, font_detail, max_text_width, max_lines=min(4, remaining_lines)):
                surf = font_detail.render(line, True, font_color)
                lcd.blit(surf, (text_left, y))
                y += surf.get_height() + 2

        pygame.display.update()
        pygame.mouse.set_visible(False)


def display_reading(
    readings: Any,
    devicestatus: Any,
    *,
    display: Optional[_PygameDisplay],
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
    display: Optional[_PygameDisplay] = None
    try:
        display = _PygameDisplay()
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
