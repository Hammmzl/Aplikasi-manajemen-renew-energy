"""Add role column to users

Revision ID: 9f7a3c1d2b10
Revises: bf762bd32f09
Create Date: 2026-04-02 22:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f7a3c1d2b10'
down_revision = 'bf762bd32f09'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.String(length=20), nullable=False, server_default='user'))

    connection = op.get_bind()
    first_user_id = connection.execute(sa.text('SELECT id FROM users ORDER BY id ASC LIMIT 1')).scalar()
    if first_user_id is not None:
        connection.execute(
            sa.text("UPDATE users SET role = 'admin' WHERE id = :user_id"),
            {'user_id': first_user_id},
        )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'role',
            existing_type=sa.String(length=20),
            existing_nullable=False,
            server_default=None,
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('role')
