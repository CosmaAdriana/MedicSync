"""Add indexes on foreign key columns for performance

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-25
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_users_department_id', 'users', ['department_id'])
    op.create_index('ix_patients_department_id', 'patients', ['department_id'])
    op.create_index('ix_vital_signs_patient_id', 'vital_signs', ['patient_id'])
    op.create_index('ix_clinical_alerts_patient_id', 'clinical_alerts', ['patient_id'])
    op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('ix_order_items_inventory_item_id', 'order_items', ['inventory_item_id'])
    op.create_index('ix_shifts_user_id', 'shifts', ['user_id'])
    op.create_index('ix_shifts_department_id', 'shifts', ['department_id'])
    op.create_index('ix_daily_patient_flow_department_id', 'daily_patient_flow', ['department_id'])
    op.create_index('ix_inventory_items_department_id', 'inventory_items', ['department_id'])


def downgrade() -> None:
    op.drop_index('ix_users_department_id', table_name='users')
    op.drop_index('ix_patients_department_id', table_name='patients')
    op.drop_index('ix_vital_signs_patient_id', table_name='vital_signs')
    op.drop_index('ix_clinical_alerts_patient_id', table_name='clinical_alerts')
    op.drop_index('ix_order_items_order_id', table_name='order_items')
    op.drop_index('ix_order_items_inventory_item_id', table_name='order_items')
    op.drop_index('ix_shifts_user_id', table_name='shifts')
    op.drop_index('ix_shifts_department_id', table_name='shifts')
    op.drop_index('ix_daily_patient_flow_department_id', table_name='daily_patient_flow')
    op.drop_index('ix_inventory_items_department_id', table_name='inventory_items')
