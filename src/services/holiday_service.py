"""External HTTP integration: looks up public holidays for a given year and
country from the free, no-auth Nager.Date API. Used by Reports/Leave to
flag when a requested leave period overlaps a public holiday.

This is a genuine network call, not a stub — it is deliberately opt-in
(only called when the user explicitly asks for it from a menu) so the
rest of the application works fully offline. Network failures (no
internet, DNS blocked, timeout, non-200 response) are caught and turned
into an empty result with a logged warning rather than crashing the
application — a public-holiday lookup is a nice-to-have, not something
that should ever take the whole app down.
"""

import os
import sys

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger  # noqa: E402

logger = get_logger("services.holiday")

BASE_URL = "https://date.nager.at/api/v3/PublicHolidays"
DEFAULT_TIMEOUT_SECONDS = 5


class HolidayService:
    def __init__(self, country_code: str = "AU", timeout: int = DEFAULT_TIMEOUT_SECONDS):
        self.country_code = country_code
        self.timeout = timeout

    def get_holidays(self, year: int) -> list[dict]:
        """Returns a list of {"date": "YYYY-MM-DD", "name": str} dicts, or an
        empty list if the service can't be reached — never raises."""
        url = f"{BASE_URL}/{year}/{self.country_code}"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            holidays = [{"date": item["date"], "name": item.get("localName", item.get("name", ""))}
                        for item in data]
            logger.info("Fetched %d public holidays for %s %d", len(holidays), self.country_code, year)
            return holidays
        except requests.RequestException as e:
            logger.warning("Could not fetch public holidays (%s) — continuing without them", e)
            return []
        except (ValueError, KeyError) as e:
            logger.warning("Unexpected response format from holiday API: %s", e)
            return []

    def is_public_holiday(self, date: str, year: int = None) -> str | None:
        """Returns the holiday name if `date` (YYYY-MM-DD) is a public
        holiday, else None. Fetches the whole year and checks locally
        rather than hitting the API once per date."""
        year = year or int(date[:4])
        holidays = self.get_holidays(year)
        for h in holidays:
            if h["date"] == date:
                return h["name"]
        return None
