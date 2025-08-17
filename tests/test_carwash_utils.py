from dash.services.iot.carwash.dto import CarwashServiceEnum, CarwashRelayBit
from dash.services.iot.common.utils import ServiceBitMaskCodec

codec = ServiceBitMaskCodec(CarwashServiceEnum, CarwashRelayBit)


def test_bit_mask_encoding():
    services_realy_int_list = [1094, 1606, 2052, 2056, 2080, 2180, 2312, 32]
    services_relay_dict = {
        "foam": [1, 2, 6, 10],
        "foam_extra": [1, 2, 6, 9, 10],
        "water_pressured": [2, 11],
        "water_warm": [3, 11],
        "osmos": [5, 11],
        "wax": [2, 7, 11],
        "winter": [3, 8, 11],
        "blackening": [5],
    }
    assert codec.encode_bit_mask(services_relay_dict) == services_realy_int_list  # type: ignore
    assert codec.decode_bit_mask(services_realy_int_list) == services_relay_dict


def test_int_list_encoding():
    tariff_list = [1, 2, 3, 4, 5, 6, 7, 8]
    tariff_dict = {
        "foam": 1,
        "foam_extra": 2,
        "water_pressured": 3,
        "water_warm": 4,
        "osmos": 5,
        "wax": 6,
        "winter": 7,
        "blackening": 8,
    }
    assert codec.encode_int_mask(tariff_dict) == tariff_list  # type: ignore
    assert codec.decode_int_mask(tariff_list) == tariff_dict
