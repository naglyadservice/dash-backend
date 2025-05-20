from dash.services.iot.carwash.dto import CarwashServiceEnum, RelayBit


def encode_service_bit_mask(
    data: dict[CarwashServiceEnum, list[RelayBit]],
) -> list[int]:
    result = []
    for service in CarwashServiceEnum:
        bits = data.get(service, []) or []
        mask = 0
        for bit in bits:
            mask |= 1 << bit
        result.append(mask)
    return result


def decode_service_bit_mask(
    mask: list[int],
) -> dict[CarwashServiceEnum, list[RelayBit] | None]:
    result = {}
    for i, value in enumerate(mask):
        service = list(CarwashServiceEnum)[i]
        bits = []
        for bit in RelayBit:
            if value & (1 << bit):
                bits.append(bit)
        result[service] = bits if bits else None
    return result


def encode_service_int_mask(data: dict[CarwashServiceEnum, int]) -> list[int]:
    return [data[s] for s in CarwashServiceEnum]


def decode_service_int_mask(mask: list[int]) -> dict[CarwashServiceEnum, int]:
    return {CarwashServiceEnum(s): mask[i] for i, s in enumerate(CarwashServiceEnum)}
