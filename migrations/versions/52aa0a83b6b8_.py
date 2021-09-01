"""empty message

Revision ID: 52aa0a83b6b8
Revises: 91c66e84c6d9
Create Date: 2021-08-15 09:30:57.060834

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52aa0a83b6b8'
down_revision = '91c66e84c6d9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pos_order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sync', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pos_order', schema=None) as batch_op:
        batch_op.drop_column('sync')

    # ### end Alembic commands ###
