"""
Shared date/time tool. Local LLMs have no reliable notion of "today" — this
gives any sub-agent a single, real source of truth to call instead of
guessing, so the mistake doesn't have to be fixed separately in every agent.
"""

import datetime as dt

DEFAULT_TIMEZONE = "Asia/Kolkata"


def get_current_datetime(timezone: str = DEFAULT_TIMEZONE) -> dict:
    """Returns the current real-world date and time. ALWAYS call this first
    before interpreting relative dates like "today", "tomorrow", "this Friday",
    or "next week" — never guess the current date from memory.

    Args:
        timezone: IANA timezone name, e.g. "Asia/Kolkata". Defaults to the
            assistant's configured timezone.

    Returns:
        dict: {"status": "success", "current_datetime_iso": str,
            "date": str, "time": str, "weekday": str, "timezone": str}
    """
    now = dt.datetime.now()
    return {
        "status": "success",
        "current_datetime_iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": now.strftime("%A"),
        "timezone": timezone,
    }
