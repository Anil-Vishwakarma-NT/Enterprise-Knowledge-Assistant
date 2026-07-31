"""
Google Calendar tools exposed to the ADK calendar_agent.
"""

import datetime as dt
from zoneinfo import ZoneInfo

from auth.google_auth import get_calendar_service
from src.tools.datetime_tools import get_current_datetime, DEFAULT_TIMEZONE


def _ensure_tz_offset(iso_str: str, timezone: str = DEFAULT_TIMEZONE) -> str:
    """Google's Calendar API requires timeMin/timeMax to include a UTC offset
    (e.g. "2026-07-30T00:00:00+05:30"), but a local LLM will often produce a
    bare datetime with no offset. If one is missing, attach the offset for
    the given IANA timezone so the request doesn't get rejected as malformed.
    """
    if not iso_str:
        return iso_str
    if iso_str.endswith("Z") or iso_str[-6] in ("+", "-"):
        return iso_str  # already has an offset
    try:
        naive = dt.datetime.fromisoformat(iso_str)
        aware = naive.replace(tzinfo=ZoneInfo(timezone))
        return aware.isoformat()
    except Exception:
        return iso_str  # let the API surface a clear error if this is still malformed


def get_todays_events(max_results: int = 10) -> dict:
    """Returns every event on the user's calendar for today (the real,
    current day — this is computed in code, not guessed). Prefer this tool
    whenever the user asks what's on their calendar "today".

    Args:
        max_results: Maximum number of events to return (default 10, max 50).

    Returns:
        Same shape as list_events: {"status": "success", "count": int,
            "events": [...]} or {"status": "error", "error_message": str}
    """
    start_of_day = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + dt.timedelta(days=1)
    return list_events(
        time_min=start_of_day.isoformat(),
        time_max=end_of_day.isoformat(),
        max_results=max_results,
    )


def list_events(time_min: str = "", time_max: str = "", max_results: int = 10) -> dict:
    """Lists upcoming events on the user's primary calendar.

    Args:
        time_min: Start of the search window in ISO format, e.g. "2026-07-30T00:00:00".
            Leave empty to default to right now.
        time_max: End of the search window in ISO format. Leave empty for no upper bound.
        max_results: Maximum number of events to return (default 10, max 50).

    Returns:
        dict: {"status": "success", "count": int, "events": [
            {"id": str, "summary": str, "start": str, "end": str,
             "attendees": [str], "location": str}
        ]} or {"status": "error", "error_message": str}
    """
    try:
        service = get_calendar_service()
        max_results = min(int(max_results), 50)

        time_min = time_min or dt.datetime.utcnow().isoformat() + "Z"
        time_min = _ensure_tz_offset(time_min)
        params = {
            "calendarId": "primary",
            "timeMin": time_min,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if time_max:
            params["timeMax"] = _ensure_tz_offset(time_max)

        result = service.events().list(**params).execute()
        raw_events = result.get("items", [])

        events = []
        for e in raw_events:
            events.append(
                {
                    "id": e.get("id"),
                    "summary": e.get("summary", "(no title)"),
                    "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date", "")),
                    "end": e.get("end", {}).get("dateTime", e.get("end", {}).get("date", "")),
                    "attendees": [a.get("email") for a in e.get("attendees", [])],
                    "location": e.get("location", ""),
                }
            )

        return {"status": "success", "count": len(events), "events": events}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def create_event(
    summary: str,
    start_time: str,
    end_time: str,
    attendees: str = "",
    description: str = "",
    location: str = "",
    timezone: str = DEFAULT_TIMEZONE,
) -> dict:
    """Creates a calendar event and sends invites to attendees.

    Args:
        summary: Title of the event.
        start_time: Start time in ISO format, e.g. "2026-08-05T15:00:00".
        end_time: End time in ISO format, e.g. "2026-08-05T15:30:00".
        attendees: Comma-separated attendee email addresses. Leave empty for none.
        description: Optional event description/agenda.
        location: Optional event location (physical or a meeting link).
        timezone: IANA timezone name, e.g. "Asia/Kolkata" or "America/New_York".

    Returns:
        dict: {"status": "success", "event_id": str, "html_link": str} or
            {"status": "error", "error_message": str}
    """
    try:
        service = get_calendar_service()

        attendee_list = [
            {"email": email.strip()} for email in attendees.split(",") if email.strip()
        ]

        event_body = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start_time, "timeZone": timezone},
            "end": {"dateTime": end_time, "timeZone": timezone},
            "attendees": attendee_list,
        }

        created = (
            service.events()
            .insert(calendarId="primary", body=event_body, sendUpdates="all")
            .execute()
        )

        return {
            "status": "success",
            "event_id": created["id"],
            "html_link": created.get("htmlLink", ""),
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
