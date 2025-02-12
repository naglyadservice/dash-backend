from enum import StrEnum


class WaterVendingServiceType(StrEnum):
    WATER_1 = "WATER_1"
    WATER_2 = "WATER_2"


class CarwashServiceType(StrEnum):
    WATER = "WATER"
    WARM_WATER = "WARM_WATER"
    FOAM = "FOAM"
    PINK_FOAM = "PINK_FOAM"
    WAX = "WAX"
    OSMOSIS = "OSMOSIS"
    WINTER_CLEANER = "WINTER_CLEANER"


class VacuumServiceType(StrEnum):
    VACUUM = "VACUUM"
    AIR_BLOWING = "AIR_BLOWING"
    TIRE_INFLATION = "TIRE_INFLATION"
    GLASS_WASHER = "GLASS_WASHER"
    RUBBER_BLACKENING = "RUBBER_BLACKENING"
