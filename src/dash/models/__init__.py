from .admin_user import AdminUser
from .base import Base
from .company import Company
from .controllers import CarwashController, Controller, WaterVendingController
from .customer import Customer
from .encashment import Encashment
from .location import Location
from .location_admin import LocationAdmin
from .payment import Payment
from .transactions import (
    CarwashTransaction,
    Transaction,
    TransactionType,
    VacuumTransaction,
    WaterVendingTransaction,
)

__all__ = [
    "AdminUser",
    "Base",
    "CarwashController",
    "CarwashTransaction",
    "Company",
    "Controller",
    "Customer",
    "Location",
    "LocationAdmin",
    "Payment",
    "Transaction",
    "TransactionType",
    "VacuumTransaction",
    "WaterVendingController",
    "WaterVendingTransaction",
    "Encashment",
]
from adaptix.type_tools import exec_type_checking

from . import (
    admin_user,
    company,
    customer,
    encashment,
    location,
    location_admin,
    payment,
)
from .controllers import carwash as carwash_c
from .controllers import controller
from .controllers import vacuum as vacuum_c
from .controllers import water_vending as water_vending_c
from .transactions import carwash as carwash_t
from .transactions import transaction
from .transactions import vacuum as vacuum_t
from .transactions import water_vending as water_vending_t

exec_type_checking(admin_user)
exec_type_checking(company)
exec_type_checking(controller)
exec_type_checking(water_vending_c)
exec_type_checking(carwash_c)
exec_type_checking(vacuum_c)
exec_type_checking(customer)
exec_type_checking(location)
exec_type_checking(location_admin)
exec_type_checking(payment)
exec_type_checking(transaction)
exec_type_checking(water_vending_t)
exec_type_checking(carwash_t)
exec_type_checking(vacuum_t)
exec_type_checking(encashment)
