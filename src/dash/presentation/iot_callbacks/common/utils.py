from datetime import datetime, timedelta, timezone


def dt_naive_to_zone_aware(dt: datetime, tz_offset: int) -> datetime:
    tz = timezone(timedelta(hours=tz_offset))
    return dt.replace(tzinfo=tz)
