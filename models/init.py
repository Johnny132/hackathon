# models/__init__.py
from models.base import Course
from models.student import StudentProfile

# This makes the imports available directly from 'models'
Course = Course
StudentProfile = StudentProfile

__all__ = ['Course', 'StudentProfile']