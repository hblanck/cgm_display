"""Dexcom Share API client for CGM display.

Fetches CGM readings from Dexcom Share servers.

Credentials are loaded in this order of precedence:
1. Command-line arguments (--username, --password)
2. Environment variables (DEXCOM_USERNAME, DEXCOM_PASSWORD)
3. None (will raise error if not provided)
"""

from __future__ import annotations

import datetime
import os
import re
from typing import Any, Optional

from . import http_general
from .Defaults import Defaults
from .logger import log


class DexcomDataSource:
    """Fetches CGM readings from Dexcom Share API.

    Credentials resolved in order: command-line args > environment variables.
    """

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, polling_interval: int = 180):
        # Resolve credentials from args, environment, or raise error
        self.username = username or os.environ.get("DEXCOM_USERNAME")
        self.password = password or os.environ.get("DEXCOM_PASSWORD")

        if not self.username or not self.password:
            raise ValueError(
                "Dexcom credentials not provided. Use --username/--password arguments, "
                "or set DEXCOM_USERNAME and DEXCOM_PASSWORD environment variables."
            )

        self.polling_interval = polling_interval
        self.session_id: Optional[str] = None
        self._create_opts()

    def _create_opts(self) -> None:
        """Create options object for http_general functions."""
        self.opts = Defaults
        self.opts.accountName = self.username
        self.opts.password = self.password
        self.opts.sessionID = None
        self.opts.applicationId = Defaults.applicationId

    def fetch(self) -> dict[str, Any]:
        """Fetch latest CGM reading from Dexcom.

        Returns dict with keys: bg, trend, trend_english, reading_lag, last_reading_time, last_reading_lag
        """
        try:
            # Get session if needed
            if not self.opts.sessionID:
                self.opts.sessionID = http_general.get_sessionID(self.opts)
                log.debug(f"Got Dexcom session token")

            # Fetch reading
            response = http_general.fetch(self.opts)
            if not response or response.status_code >= 400:
                raise Exception(f"Dexcom API error: {response.status_code if response else 'No response'}")

            return self._parse_response(response)

        except Exception as e:
            # Clear session on error
            self.opts.sessionID = None
            self.session_id = None
            log.error(f"Dexcom fetch failed: {e}")
            raise

    def _parse_response(self, response: Any) -> dict[str, Any]:
        """Parse Dexcom API response into standardized format."""
        try:
            data = response.json()
            if not data or len(data) == 0:
                raise Exception("Empty response from Dexcom")

            reading_data = data[0]

            # Extract timestamp
            st_str = reading_data.get("ST", "")
            last_reading_time = int(re.search(r"\d+", st_str).group()) / 1000 if st_str else 0

            # Calculate lag
            epoch_now = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
            reading_lag = epoch_now - last_reading_time

            # Get BG value and trend
            bg = reading_data.get("Value", 0)
            trend = reading_data.get("Trend", 0)

            # Lookup trend name
            trend_english = Defaults.DIRECTIONS.get(trend, "Unknown")

            # Check if reading is stale
            last_reading_lag = reading_lag > (60 * 7.5)  # 7.5 minutes

            log.info(
                f"Dexcom reading: {bg} trending {trend_english} ({trend}), "
                f"lag: {int(reading_lag)} seconds, stale: {last_reading_lag}"
            )

            return {
                "bg": bg,
                "trend": trend,
                "trend_english": trend_english,
                "reading_lag": reading_lag,
                "last_reading_time": last_reading_time,
                "last_reading_lag": last_reading_lag,
            }

        except Exception as e:
            log.error(f"Failed to parse Dexcom response: {e}")
            log.error(f"Response data: {response.json() if hasattr(response, 'json') else response}")
            raise
