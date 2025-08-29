"""Add unique constraint on students institution_id and student_id

Revision ID: 9626b5d9eb1d
Revises: 4025f415202a
Create Date: 2025-08-28 17:41:24.174259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9626b5d9eb1d'
down_revision: Union[str, Sequence[str], None] = '4025f415202a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint on students (institution_id, student_id)."""
    # Add unique constraint for institution_id and student_id combination
    op.create_unique_constraint(
        'uq_students_institution_student_id',  # constraint name
        'students',  # table name
        ['institution_id', 'student_id']  # columns
    )


def downgrade() -> None:
    """Remove unique constraint on students (institution_id, student_id)."""
    # Drop the unique constraint
    op.drop_constraint(
        'uq_students_institution_student_id',  # constraint name
        'students',  # table name
        type_='unique'
    )
