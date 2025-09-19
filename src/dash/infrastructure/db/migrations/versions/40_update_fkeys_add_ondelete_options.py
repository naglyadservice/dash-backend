"""update fkeys, add ondelete options

Revision ID: 40
Revises: 39
Create Date: 2025-09-19 18:15:55.578039
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "40"
down_revision: Union[str, None] = "39"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # car_cleaner
    op.drop_constraint(
        "car_cleaner_controllers_controller_id_fkey",
        "car_cleaner_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "car_cleaner_controllers_controller_id_fkey",
        "car_cleaner_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "car_cleaner_transactions_transaction_id_fkey",
        "car_cleaner_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "car_cleaner_transactions_transaction_id_fkey",
        "car_cleaner_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # carwash
    op.drop_constraint(
        "carwash_controllers_controller_id_fkey",
        "carwash_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "carwash_controllers_controller_id_fkey",
        "carwash_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "carwash_transactions_transaction_id_fkey",
        "carwash_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "carwash_transactions_transaction_id_fkey",
        "carwash_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # companies
    op.alter_column("companies", "owner_id", existing_type=sa.UUID(), nullable=True)
    op.drop_constraint("companies_owner_id_fkey", "companies", type_="foreignkey")
    op.create_foreign_key(
        "companies_owner_id_fkey",
        "companies",
        "admin_users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # controllers
    op.drop_constraint(
        "controllers_location_id_fkey", "controllers", type_="foreignkey"
    )
    op.create_foreign_key(
        "controllers_location_id_fkey",
        "controllers",
        "locations",
        ["location_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # customers
    op.drop_constraint("customers_company_id_fkey", "customers", type_="foreignkey")
    op.create_foreign_key(
        "customers_company_id_fkey",
        "customers",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # daily_energy_states
    op.drop_constraint(
        "daily_energy_states_controller_id_fkey",
        "daily_energy_states",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "daily_energy_states_controller_id_fkey",
        "daily_energy_states",
        "controllers",
        ["controller_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # dummy_controllers
    op.drop_constraint(
        "dummy_controllers_controller_id_fkey", "dummy_controllers", type_="foreignkey"
    )
    op.create_foreign_key(
        "dummy_controllers_controller_id_fkey",
        "dummy_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # encashments
    op.drop_constraint(
        "encashments_controller_id_fkey", "encashments", type_="foreignkey"
    )
    op.create_foreign_key(
        "encashments_controller_id_fkey",
        "encashments",
        "controllers",
        ["controller_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # fiscalizer
    op.drop_constraint(
        "fiscalizer_controllers_controller_id_fkey",
        "fiscalizer_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fiscalizer_controllers_controller_id_fkey",
        "fiscalizer_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fiscalizer_transactions_transaction_id_fkey",
        "fiscalizer_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fiscalizer_transactions_transaction_id_fkey",
        "fiscalizer_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # laundry
    op.drop_constraint(
        "laundry_controllers_controller_id_fkey",
        "laundry_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "laundry_controllers_controller_id_fkey",
        "laundry_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "laundry_transactions_transaction_id_fkey",
        "laundry_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "laundry_transactions_transaction_id_fkey",
        "laundry_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # locations
    op.drop_constraint("locations_company_id_fkey", "locations", type_="foreignkey")
    op.create_foreign_key(
        "locations_company_id_fkey",
        "locations",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # payments + transactions
    op.alter_column("payments", "controller_id", existing_type=sa.UUID(), nullable=True)
    op.alter_column(
        "transactions", "controller_id", existing_type=sa.UUID(), nullable=True
    )

    # vacuum
    op.drop_constraint(
        "vacuum_controllers_controller_id_fkey",
        "vacuum_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "vacuum_controllers_controller_id_fkey",
        "vacuum_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "vacuum_transactions_transaction_id_fkey",
        "vacuum_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "vacuum_transactions_transaction_id_fkey",
        "vacuum_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # water_vending
    op.drop_constraint(
        "water_vending_controllers_controller_id_fkey",
        "water_vending_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "water_vending_controllers_controller_id_fkey",
        "water_vending_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "water_vending_transactions_transaction_id_fkey",
        "water_vending_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "water_vending_transactions_transaction_id_fkey",
        "water_vending_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # water_vending
    op.drop_constraint(
        "water_vending_transactions_transaction_id_fkey",
        "water_vending_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "water_vending_transactions_transaction_id_fkey",
        "water_vending_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
    )
    op.drop_constraint(
        "water_vending_controllers_controller_id_fkey",
        "water_vending_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "water_vending_controllers_controller_id_fkey",
        "water_vending_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
    )

    # vacuum
    op.drop_constraint(
        "vacuum_transactions_transaction_id_fkey",
        "vacuum_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "vacuum_transactions_transaction_id_fkey",
        "vacuum_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
    )
    op.drop_constraint(
        "vacuum_controllers_controller_id_fkey",
        "vacuum_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "vacuum_controllers_controller_id_fkey",
        "vacuum_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
    )

    # payments + transactions
    op.alter_column(
        "transactions", "controller_id", existing_type=sa.UUID(), nullable=False
    )
    op.alter_column(
        "payments", "controller_id", existing_type=sa.UUID(), nullable=False
    )

    # locations
    op.drop_constraint("locations_company_id_fkey", "locations", type_="foreignkey")
    op.create_foreign_key(
        "locations_company_id_fkey",
        "locations",
        "companies",
        ["company_id"],
        ["id"],
    )

    # laundry
    op.drop_constraint(
        "laundry_transactions_transaction_id_fkey",
        "laundry_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "laundry_transactions_transaction_id_fkey",
        "laundry_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
    )
    op.drop_constraint(
        "laundry_controllers_controller_id_fkey",
        "laundry_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "laundry_controllers_controller_id_fkey",
        "laundry_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
    )

    # fiscalizer
    op.drop_constraint(
        "fiscalizer_transactions_transaction_id_fkey",
        "fiscalizer_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fiscalizer_transactions_transaction_id_fkey",
        "fiscalizer_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
    )
    op.drop_constraint(
        "fiscalizer_controllers_controller_id_fkey",
        "fiscalizer_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fiscalizer_controllers_controller_id_fkey",
        "fiscalizer_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
    )

    # encashments
    op.drop_constraint(
        "encashments_controller_id_fkey", "encashments", type_="foreignkey"
    )
    op.create_foreign_key(
        "encashments_controller_id_fkey",
        "encashments",
        "controllers",
        ["controller_id"],
        ["id"],
    )

    # dummy_controllers
    op.drop_constraint(
        "dummy_controllers_controller_id_fkey", "dummy_controllers", type_="foreignkey"
    )
    op.create_foreign_key(
        "dummy_controllers_controller_id_fkey",
        "dummy_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
    )

    # daily_energy_states
    op.drop_constraint(
        "daily_energy_states_controller_id_fkey",
        "daily_energy_states",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "daily_energy_states_controller_id_fkey",
        "daily_energy_states",
        "controllers",
        ["controller_id"],
        ["id"],
    )

    # customers
    op.drop_constraint("customers_company_id_fkey", "customers", type_="foreignkey")
    op.create_foreign_key(
        "customers_company_id_fkey",
        "customers",
        "companies",
        ["company_id"],
        ["id"],
    )

    # controllers
    op.drop_constraint(
        "controllers_location_id_fkey", "controllers", type_="foreignkey"
    )
    op.create_foreign_key(
        "controllers_location_id_fkey",
        "controllers",
        "locations",
        ["location_id"],
        ["id"],
    )

    # companies
    op.drop_constraint("companies_owner_id_fkey", "companies", type_="foreignkey")
    op.create_foreign_key(
        "companies_owner_id_fkey",
        "companies",
        "admin_users",
        ["owner_id"],
        ["id"],
    )
    op.alter_column("companies", "owner_id", existing_type=sa.UUID(), nullable=False)

    # carwash
    op.drop_constraint(
        "carwash_transactions_transaction_id_fkey",
        "carwash_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "carwash_transactions_transaction_id_fkey",
        "carwash_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
    )
    op.drop_constraint(
        "carwash_controllers_controller_id_fkey",
        "carwash_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "carwash_controllers_controller_id_fkey",
        "carwash_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
    )

    # car_cleaner
    op.drop_constraint(
        "car_cleaner_transactions_transaction_id_fkey",
        "car_cleaner_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "car_cleaner_transactions_transaction_id_fkey",
        "car_cleaner_transactions",
        "transactions",
        ["transaction_id"],
        ["id"],
    )
    op.drop_constraint(
        "car_cleaner_controllers_controller_id_fkey",
        "car_cleaner_controllers",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "car_cleaner_controllers_controller_id_fkey",
        "car_cleaner_controllers",
        "controllers",
        ["controller_id"],
        ["id"],
    )
    # ### end Alembic commands ###
