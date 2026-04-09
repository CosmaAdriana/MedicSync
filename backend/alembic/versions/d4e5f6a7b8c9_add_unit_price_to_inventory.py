"""Add unit_price to inventory_items

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-07
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'inventory_items',
        sa.Column('unit_price', sa.Float(), nullable=False, server_default='0.0'),
    )


def downgrade() -> None:
    op.drop_column('inventory_items', 'unit_price')
