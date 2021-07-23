"""empty message

Revision ID: 8d03f21b6003
Revises: a1e746f130ed
Create Date: 2021-07-23 20:31:07.006092

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d03f21b6003'
down_revision = 'a1e746f130ed'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ab_user', schema=None) as batch_op:
        batch_op.create_foreign_key('None', 'company', ['company_id'], ['id'])

    with op.batch_alter_table('document_template', schema=None) as batch_op:
        batch_op.drop_column('tmpl')

    with op.batch_alter_table('pos_config', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_multiple_payment', sa.Boolean(), nullable=True))

    with op.batch_alter_table('product_product', schema=None) as batch_op:
        batch_op.drop_column('categ_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('product_product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('categ_id', sa.INTEGER(), nullable=True))

    with op.batch_alter_table('pos_config', schema=None) as batch_op:
        batch_op.drop_column('is_multiple_payment')

    with op.batch_alter_table('document_template', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tmpl', sa.TEXT(), nullable=True))

    with op.batch_alter_table('ab_user', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    # ### end Alembic commands ###