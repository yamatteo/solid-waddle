"""User.is_editor not nullable

Revision ID: fbc079b4cb52
Revises: 637c9d1295da
Create Date: 2023-05-15 17:46:45.317387

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fbc079b4cb52'
down_revision = '637c9d1295da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.execute("UPDATE user SET is_editor = true")
        batch_op.alter_column('is_editor',
               existing_type=sa.BOOLEAN(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('is_editor',
               existing_type=sa.BOOLEAN(),
               nullable=True)

    # ### end Alembic commands ###