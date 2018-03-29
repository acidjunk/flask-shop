"""empty message

Revision ID: a4370c451013
Revises: 276a4f355c8f
Create Date: 2018-03-27 08:51:23.980485

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a4370c451013'
down_revision = '276a4f355c8f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('categories', 'name',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.alter_column('customers', 'name',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.add_column('products', sa.Column('usp1', sa.String(length=255), nullable=True))
    op.add_column('products', sa.Column('usp2', sa.String(length=255), nullable=True))
    op.add_column('products', sa.Column('usp3', sa.String(length=255), nullable=True))
    op.alter_column('products', 'content',
               existing_type=sa.TEXT(),
               nullable=False)
    op.alter_column('products', 'detail_image',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.alter_column('products', 'list_image',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.alter_column('products', 'name',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.alter_column('products', 'price',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=False)
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.alter_column('users', 'password',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'password',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.alter_column('products', 'price',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               nullable=True)
    op.alter_column('products', 'name',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.alter_column('products', 'list_image',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.alter_column('products', 'detail_image',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.alter_column('products', 'content',
               existing_type=sa.TEXT(),
               nullable=True)
    op.drop_column('products', 'usp3')
    op.drop_column('products', 'usp2')
    op.drop_column('products', 'usp1')
    op.alter_column('customers', 'name',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.alter_column('categories', 'name',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    # ### end Alembic commands ###
