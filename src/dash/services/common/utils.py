def unify_pan_mask(raw_mask: str) -> str | None:
    if not isinstance(raw_mask, str):
        return None

    mask = raw_mask.strip().replace("X", "*")

    parts = [p for p in mask.split("*") if p]

    first_digits = ""
    last_digits = ""

    if len(parts) == 2:
        first_digits, last_digits = parts

    elif len(parts) == 1 and mask.startswith("*"):
        last_digits = parts[0]

    else:
        return None

    if not first_digits.isdigit() or not last_digits.isdigit():
        return None

    padding_length = 16 - (len(first_digits) + len(last_digits))

    if padding_length < 0:
        return None

    padding = "*" * padding_length

    return f"{first_digits}{padding}{last_digits}"
