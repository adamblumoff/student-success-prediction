"""fix_audit_logs_user_id_datatype

Revision ID: 4025f415202a
Revises: a6e53f7e8167
Create Date: 2025-08-13 16:27:32.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4025f415202a'
down_revision: Union[str, Sequence[str], None] = 'a6e53f7e8167'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix user_id column to support string identifiers for audit logging"""
    
    # Drop the foreign key constraint first
    op.drop_constraint('audit_logs_user_id_fkey', 'audit_logs', type_='foreignkey')
    
    # Change user_id from integer to varchar to support string user identifiers
    op.alter_column('audit_logs', 'user_id', 
                   existing_type=sa.Integer(), 
                   type_=sa.String(length=100),
                   existing_nullable=True)
    
    # Note: We don't recreate the foreign key since user_id will now be a string identifier
    # that doesn't reference another table


def downgrade() -> None:
    """Revert user_id column back to integer"""
    
    # Note: This may fail if there are string user_ids in the database
    op.alter_column('audit_logs', 'user_id', 
                   existing_type=sa.String(length=100), 
                   type_=sa.Integer(),
                   existing_nullable=True)