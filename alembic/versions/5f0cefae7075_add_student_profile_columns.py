"""Add missing student profile columns

Revision ID: 5f0cefae7075
Revises: 9626b5d9eb1d
Create Date: 2025-11-06 18:47:42.901895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
# revision identifiers, used by Alembic.
revision: str = '5f0cefae7075'
down_revision: Union[str, Sequence[str], None] = '9626b5d9eb1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('students', sa.Column('name', sa.String(length=255), nullable=True))
    op.add_column('students', sa.Column('current_gpa', sa.Float(), nullable=True))
    op.add_column('students', sa.Column('previous_gpa', sa.Float(), nullable=True))
    op.add_column('students', sa.Column('attendance_rate', sa.Float(), nullable=True))
    op.add_column('students', sa.Column('study_hours_week', sa.Integer(), nullable=True))
    op.add_column('students', sa.Column('extracurricular', sa.Integer(), nullable=True))
    op.add_column('students', sa.Column('parent_education', sa.Integer(), nullable=True))
    op.add_column('students', sa.Column('socioeconomic_status', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_students_name'), 'students', ['name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_students_name'), table_name='students')
    op.drop_column('students', 'socioeconomic_status')
    op.drop_column('students', 'parent_education')
    op.drop_column('students', 'extracurricular')
    op.drop_column('students', 'study_hours_week')
    op.drop_column('students', 'attendance_rate')
    op.drop_column('students', 'previous_gpa')
    op.drop_column('students', 'current_gpa')
    op.drop_column('students', 'name')
