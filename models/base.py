from dataclasses import dataclass
from typing import List, Dict, Optional

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
    
    prerequisites: Optional[List[str]] = None
    terms_offered: Optional[List[str]] = None
    available_slots: Optional[Dict[str, int]] = None
    
    def is_eligible(self, completed_courses: List[str]) -> bool:
        if not self.prerequisites:
            return True
        return all(prereq in completed_courses for prereq in self.prerequisites)