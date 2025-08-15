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

    def decode_int_mask(self, mask: list[float]) -> dict[TService, float]:
        return {self.service_enum(s): mask[i] for i, s in enumerate(self.service_enum)}
