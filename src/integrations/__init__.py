"""
LMS Integration package for Student Success Prediction System

Provides seamless integration with Learning Management Systems including:
- Canvas LMS
- Blackboard Learn  
- Moodle
- Google Classroom
"""

from .canvas import CanvasIntegration
from .base import BaseLMSIntegration

__all__ = [
    'CanvasIntegration',
    'BaseLMSIntegration'
]