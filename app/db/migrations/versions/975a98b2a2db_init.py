"""init

Revision ID: 975a98b2a2db
Revises: 
Create Date: 2023-08-29 20:19:03.957023

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '975a98b2a2db'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'author_contacts', ['uid'])
    op.create_unique_constraint(None, 'authors', ['uid'])
    op.add_column('content', sa.Column('locked', sa.Integer(), nullable=False))
    op.create_unique_constraint(None, 'content', ['uid'])
    op.create_unique_constraint(None, 'publications', ['uid'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'publications', type_='unique')
    op.drop_constraint(None, 'content', type_='unique')
    op.drop_column('content', 'locked')
    op.drop_constraint(None, 'authors', type_='unique')
    op.drop_constraint(None, 'author_contacts', type_='unique')
    # ### end Alembic commands ###