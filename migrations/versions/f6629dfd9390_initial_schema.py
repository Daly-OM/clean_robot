"""initial schema

Revision ID: f6629dfd9390
Revises: 88fc1fdd1ed7
Create Date: 2025-06-26 14:06:09.930851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6629dfd9390'
down_revision: Union[str, None] = '88fc1fdd1ed7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
