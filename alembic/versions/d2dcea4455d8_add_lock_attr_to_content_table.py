"""add lock attr to content table

Revision ID: d2dcea4455d8
Revises: c15f428fa233
Create Date: 2023-08-23 22:13:55.249659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2dcea4455d8'
down_revision: Union[str, None] = 'c15f428fa233'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
            "content",
            sa.Column(
                "locked",
                sa.Integer,
                ),
            )


def downgrade() -> None:
    op.drop_column("content", "locked")
