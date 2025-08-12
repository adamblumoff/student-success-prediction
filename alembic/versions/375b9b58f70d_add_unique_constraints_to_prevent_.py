"""Add unique constraints to prevent duplicates

Revision ID: 375b9b58f70d
Revises: 1d63a289fd84
Create Date: 2025-08-12 10:36:53.598024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '375b9b58f70d'
down_revision: Union[str, Sequence[str], None] = '1d63a289fd84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add unique constraint for students.student_id within institution
    op.create_unique_constraint(
        'uq_students_student_id_institution',
        'students',
        ['institution_id', 'student_id']
    )
    
    # Add unique constraint for users.email
    op.create_unique_constraint(
        'uq_users_email',
        'users',
        ['email']
    )
    
    # Add unique constraint for institutions.code
    op.create_unique_constraint(
        'uq_institutions_code',
        'institutions',
        ['code']
    )
    
    # Add unique constraint for predictions per student (one prediction per student)
    op.create_unique_constraint(
        'uq_predictions_student',
        'predictions',
        ['student_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove unique constraints in reverse order
    op.drop_constraint('uq_predictions_student', 'predictions')
    op.drop_constraint('uq_institutions_code', 'institutions')
    op.drop_constraint('uq_users_email', 'users')
    op.drop_constraint('uq_students_student_id_institution', 'students')
