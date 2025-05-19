from dash.services.carwash.dto import RelayBit


def encode_relay_mask(data: dict[str, list[RelayBit]]) -> list[int]:
    result = []
    for i in range(1, 9):
        relay_bits = data.get(f"relay_{i}", None) or []
        mask = 0
        for bit in relay_bits:
            mask |= 1 << bit
        result.append(mask)
    return result


def decode_relay_mask(mask: list[int]) -> dict[str, list[RelayBit]]:
    relays = {}
    for i, value in enumerate(mask, start=1):
        bits = []
        for bit in RelayBit:
            if value & (1 << bit):
                bits.append(bit)
        relays[f"relay_{i}"] = bits if bits else None
    return relays
