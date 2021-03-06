"""empty message

Revision ID: 5d92bd1458fa
Revises: 37cca9a97202
Create Date: 2018-04-06 10:40:23.874078

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d92bd1458fa'
down_revision = '37cca9a97202'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('seo_name', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_products_seo_name'), 'products', ['seo_name'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_products_seo_name'), table_name='products')
    op.drop_column('products', 'seo_name')
    # ### end Alembic commands ###
