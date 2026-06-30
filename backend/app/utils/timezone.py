"""Timezone helpers for consistent IST handling."""

from datetime import date, datetime, time

import pytz

IST = pytz.timezone("Asia/Kolkata")


def get_ist_now() -> datetime:
    """Return the current timezone-aware datetime in IST."""
    return datetime.now(IST)


def get_ist_today() -> date:
    """Return today's date in IST."""
    return get_ist_now().date()


def make_ist_datetime(day: date, hour: float) -> datetime:
    """Build a timezone-aware IST datetime for the given day and hour."""
    hour_value = int(hour)
    minutes = int(round((float(hour) - hour_value) * 60))
    naive_datetime = datetime.combine(day, time(hour=hour_value, minute=minutes))
    return IST.localize(naive_datetime)


def ensure_ist(dt: datetime | None) -> datetime | None:
    """Convert an aware datetime to IST, or localize naive values as IST."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return IST.localize(dt)
    return dt.astimezone(IST)
