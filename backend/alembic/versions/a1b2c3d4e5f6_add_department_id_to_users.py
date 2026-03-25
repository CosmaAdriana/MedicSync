"""Add department_id to users

Revision ID: a1b2c3d4e5f6
Revises: 3a4b5c6d7e8f
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '3a4b5c6d7e8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('department_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'department_id')
