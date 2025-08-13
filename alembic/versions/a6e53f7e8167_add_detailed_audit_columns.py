"""add_detailed_audit_columns

Revision ID: a6e53f7e8167
Revises: cd8752e735e5
Create Date: 2025-08-13 16:25:02.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6e53f7e8167'
down_revision: Union[str, Sequence[str], None] = 'cd8752e735e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add detailed audit logging columns for comprehensive compliance tracking"""
    
    # Add missing columns for detailed audit logging
    op.add_column('audit_logs', sa.Column('details', sa.Text(), nullable=True))
    op.add_column('audit_logs', sa.Column('compliance_data', sa.Text(), nullable=True))
    op.add_column('audit_logs', sa.Column('created_at', sa.DateTime(timezone=True), nullable=True))
    
    # Update existing records to have created_at from timestamp
    op.execute("UPDATE audit_logs SET created_at = timestamp WHERE created_at IS NULL")
    
    # Add indices for better audit query performance
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_institution_id', 'audit_logs', ['institution_id'])


def downgrade() -> None:
    """Remove detailed audit logging columns"""
    
    # Drop indices
    op.drop_index('idx_audit_logs_action', 'audit_logs')
    op.drop_index('idx_audit_logs_resource_type', 'audit_logs')
    op.drop_index('idx_audit_logs_user_id', 'audit_logs')
    op.drop_index('idx_audit_logs_created_at', 'audit_logs')
    op.drop_index('idx_audit_logs_institution_id', 'audit_logs')
    
    # Drop columns
    op.drop_column('audit_logs', 'details')
    op.drop_column('audit_logs', 'compliance_data')
    op.drop_column('audit_logs', 'created_at')