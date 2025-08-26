from enum import IntEnum, StrEnum
from typing import TypeVar, Generic, Type


TService = TypeVar("TService", bound=StrEnum)
TBit = TypeVar("TBit", bound=IntEnum)


class ServiceBitMaskCodec(Generic[TService, TBit]):
    def __init__(self, service_enum: Type[TService], bit_enum: Type[TBit]):
        self.service_enum = service_enum
        self.bit_enum = bit_enum

    def encode_bit_mask(self, data: dict[TService, list[TBit]]) -> list[int]:
        result = []
        for service in self.service_enum:
            bits = data.get(service, []) or []
            mask = 0
            for bit in bits:
                mask |= 1 << bit
            result.append(mask)
        return result

    def decode_bit_mask(self, mask: list[int]) -> dict[TService, list[TBit] | None]:
        result = {}
        for i, value in enumerate(mask):
            service = list(self.service_enum)[i]
            bits = []
            for bit in self.bit_enum:
                if value & (1 << bit):
                    bits.append(bit)
            result[service] = bits if bits else None
        return result

    def encode_int_mask(self, data: dict[TService, int]) -> list[int]:
        return [data[s] for s in self.service_enum]

    def decode_int_mask(self, mask: list[float] | list[int]) -> dict[TService, float]:
        return {self.service_enum(s): mask[i] for i, s in enumerate(self.service_enum)}


# Human-readable labels for display information that the controller returns
MODE_LABELS: dict[int, str] = {
    0x00: "Логотип",
    0x01: "Очікування оплати",
    0x02: "Двері відкриті",
    0x03: "Блокування",
    0x04: "Сервісний режим 0",
    0x05: "Сервісний режим 1",
    0x06: "Сервісний режим 2",
    0x07: "Продажа готівкою",
    0x08: "Подяка",
    0x09: "Оплата PayPass 0",
    0x0A: "Оплата PayPass 1",
    0x0B: "Продажа карткою 0",
    0x0C: "Продажа карткою 1",
    0x0D: "Продажа карткою 2",
    0x0E: "Продажа карткою 3",
    0x0F: "Інкасація",
    0x10: "Перевірка при старі",
    0x80: "Реклама",
}
