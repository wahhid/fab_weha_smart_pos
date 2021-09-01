"""empty message

Revision ID: 91c66e84c6d9
Revises: 6af5afca5b46
Create Date: 2021-08-06 16:32:54.011502

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '91c66e84c6d9'
down_revision = '6af5afca5b46'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pos_session', schema=None) as batch_op:
        batch_op.add_column(sa.Column('amount_total', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pos_session', schema=None) as batch_op:
        batch_op.drop_column('amount_total')

    # ### end Alembic commands ###
