"""Add User entity

Revision ID: 984b2f7e745a
Revises: 
Create Date: 2021-09-15 03:37:33.462937

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '984b2f7e745a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=False),
    sa.Column('email', sa.VARCHAR(), nullable=False),
    sa.Column('password', sa.LargeBinary(), nullable=False),
    sa.Column('avatar', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    # ### end Alembic commands ###
