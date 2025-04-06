from dataclasses import dataclass
from typing import List, Dict
from models.base import Course

@dataclass
class StudentProfile:
    student_id: str
    completed_courses: List[str]
    current_semester: int
    career_goals: List[str]
    preferred_subjects: List[str]
    time_constraints: Dict[str, bool]
    enrollment_status: str
    min_credits: int
    max_credits: int
    
    def can_take_course(self, course: Course) -> bool:
        prereq_met = course.is_eligible(self.completed_courses)
        time_available = any(
            course.available_slots.get(slot, 0) > 0 and self.time_constraints.get(slot, False)
            for slot in self.time_constraints
        ) if course.available_slots else True
        return prereq_met and time_available