from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Course:
    course_id: str
    title: str
    description: str
    credits: int
    department: str
    level: int
    skills_taught: List[str]
    career_relevance: List[str]
    
    prerequisites: List[str] = None
    terms_offered: List[str] = None
    available_slots: Dict[str, int] = None
    
    def is_eligible(self, completed_courses: List[str]) -> bool:
        if self.prerequisites is None:
            return True
        return all(prereq in completed_courses for prereq in self.prerequisites)