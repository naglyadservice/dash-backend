from datetime import datetime, timedelta, timezone


def dt_naive_to_zone_aware(dt: datetime | str, tz_offset: int) -> datetime:
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")

    tz = timezone(timedelta(hours=tz_offset))
    return dt.replace(tzinfo=tz)
