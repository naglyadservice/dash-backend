from datetime import datetime, timedelta, timezone


def dt_naive_to_zone_aware(dt: datetime | str, tz_offset: int) -> datetime:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)

    tz = timezone(timedelta(hours=tz_offset))
    return dt.replace(tzinfo=tz)


SIMPLE_STATUSES = {
    0x10: "Power Up",
    0x11: "Power Up with Bill in Validator",
    0x12: "Power Up with Bill in Stacker",
    0x13: "Initialize",
    0x14: "Idling",
    0x15: "Accepting",
    0x17: "Stacking",
    0x18: "Returning",
    0x19: "Unit Disabled",
    0x1A: "Holding",
    0x41: "Drop Cassette Full",
    0x42: "Drop Cassette out of position",
    0x43: "Validator Jammed",
    0x44: "Drop Cassette Jammed",
    0x45: "Cheated",
    0x46: "Pause",
}

REJECT_REASONS = {
    0x60: "Rejecting due to Insertion",
    0x61: "Rejecting due to Magnetic",
    0x62: "Rejecting due to Remained bill",
    0x63: "Rejecting due to Multiplying",
    0x64: "Rejecting due to Conveying",
    0x65: "Rejecting due to Identification",
    0x66: "Rejecting due to Verification",
    0x67: "Rejecting due to Optic",
    0x68: "Rejecting due to Inhibit",
    0x69: "Rejecting due to Capacity",
    0x6A: "Rejecting due to Operation",
    0x6C: "Rejecting due to Length",
    0x92: "Rejecting due to unrecognised barcode",
    0x6D: "Rejecting due to UV",
    0x93: "Rejecting due to incorrect barcode characters",
    0x94: "Rejecting due to unknown barcode start sequence",
    0x95: "Rejecting due to unknown barcode stop sequence",
}

FAILURE_REASONS = {
    0x50: "Stack Motor Failure",
    0x51: "Transport Motor Speed Failure",
    0x52: "Transport Motor Failure",
    0x53: "Aligning Motor Failure",
    0x54: "Initial Cassette Status Failure",
    0x55: "Optic Canal Failure",
    0x56: "Magnetic Canal Failure",
    0x5F: "Capacitance Canal Failure",
}

EVENTS_WITH_CREDIT = {
    0x80: "Escrow position",
    0x81: "Bill stacked",
    0x82: "Bill returned",
}


def parse_bill_state(value: int) -> str:
    if value == 0:
        return "Bill disconnected"

    if value <= 0xFF and value in SIMPLE_STATUSES:
        return SIMPLE_STATUSES[value]

    z1 = (value >> 8) & 0xFF
    z2 = value & 0xFF

    if z1 in EVENTS_WITH_CREDIT:
        return f"{EVENTS_WITH_CREDIT[z1]}: bill type {z2}"

    unknown_status_msg = f"Unknown status: 0x{z1}{z2:02X}"

    if z1 == 0x1C:
        reason = REJECT_REASONS.get(z2, unknown_status_msg)
        return f"Rejecting: {reason}"

    if z1 == 0x47:
        reason = FAILURE_REASONS.get(z2, unknown_status_msg)
        return f"Failure: {reason}"

    if z1 == 0x1B:
        return f"Device Busy (wait {z2 * 100}) ms"

    return unknown_status_msg


def parse_card_uid(card_uid: str) -> str:
    stripped = card_uid.rstrip("0")
    
    if len(stripped) % 2 != 0:
        stripped += "0"
    
    return stripped
