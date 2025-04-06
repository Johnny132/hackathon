from typing import List, Dict, Set, Optional
import logging
from models.base import Course
from models.student import StudentProfile

class CourseSelector:
    def __init__(self):
        self.courses: Dict[str, Course] = {}
        self.students: Dict[str, StudentProfile] = {}
        
        # Add mappings for career goals and subjects to course IDs
        self.career_goal_mapping: Dict[str, Set[str]] = {}
        self.subject_mapping: Dict[str, Set[str]] = {}
    
    def add_course(self, course: Course):
        """
        Add a course to the catalog and update mappings
        
        Args:
            course (Course): Course to be added
        """
        # Only add if course_id is unique and not empty
        if course.course_id and course.course_id not in self.courses:
            # Add course to main courses dictionary
            self.courses[course.course_id] = course
            
            # Update career goal mapping
            if course.career_relevance:
                for career in course.career_relevance:
                    career_key = career.lower().strip()
                    if career_key:
                        if career_key not in self.career_goal_mapping:
                            self.career_goal_mapping[career_key] = set()
                        self.career_goal_mapping[career_key].add(course.course_id)
            
            # Update subject mapping based on skills taught
            if course.skills_taught:
                for skill in course.skills_taught:
                    skill_key = skill.lower().strip()
                    if skill_key:
                        if skill_key not in self.subject_mapping:
                            self.subject_mapping[skill_key] = set()
                        self.subject_mapping[skill_key].add(course.course_id)
    
    def add_student(self, student: StudentProfile):
        """Add a student profile"""
        if student.student_id and student.student_id not in self.students:
            self.students[student.student_id] = student
    
    def _match_career_goals(self, career_goals: List[str]) -> Set[str]:
        """
        Find course IDs matching career goals with robust matching
        
        Args:
            career_goals (List[str]): List of career goals
        
        Returns:
            Set[str]: Set of course IDs matching the career goals
        """
        matching_courses = set()
        for goal in career_goals:
            # Normalize goal
            goal_key = goal.lower().strip()
            
            # Direct matching in career relevance
            matching_courses.update(
                self.career_goal_mapping.get(goal_key, set())
            )
            
            # Partial matching for broader coverage
            for mapped_goal, course_ids in self.career_goal_mapping.items():
                if goal_key in mapped_goal or mapped_goal in goal_key:
                    matching_courses.update(course_ids)
        
        return matching_courses
    
    def _match_preferred_subjects(self, preferred_subjects: List[str]) -> Set[str]:
        """
        Find course IDs matching preferred subjects with robust matching
        
        Args:
            preferred_subjects (List[str]): List of preferred subjects
        
        Returns:
            Set[str]: Set of course IDs matching the subjects
        """
        matching_courses = set()
        for subject in preferred_subjects:
            # Normalize subject
            subject_key = subject.lower().strip()
            
            # Direct matching in skills taught
            matching_courses.update(
                self.subject_mapping.get(subject_key, set())
            )
            
            # Partial matching for skills and titles
            for mapped_skill, course_ids in self.subject_mapping.items():
                if subject_key in mapped_skill or mapped_skill in subject_key:
                    matching_courses.update(course_ids)
            
            # Additional matching in course titles
            title_matches = [
                course_id for course_id, course in self.courses.items()
                if subject_key in course.title.lower()
            ]
            matching_courses.update(title_matches)
        
        return matching_courses
    
    def rank_courses_by_relevance(self, 
                                   courses: List[Course], 
                                   career_goals: List[str], 
                                   preferred_subjects: List[str]) -> List[tuple]:
        """
        Rank courses by relevance with a more nuanced scoring system
        
        Args:
            courses (List[Course]): List of courses to rank
            career_goals (List[str]): Career goals to match
            preferred_subjects (List[str]): Preferred subjects to match
        
        Returns:
            List[tuple]: Ranked courses with their relevance scores
        """
        # Find matching course IDs
        career_matched_courses = self._match_career_goals(career_goals)
        subject_matched_courses = self._match_preferred_subjects(preferred_subjects)
        
        # Rank courses
        ranked_courses = []
        for course in courses:
            score = 0
            
            # Score based on career goals
            if course.course_id in career_matched_courses:
                score += 3
            
            # Score based on preferred subjects
            if course.course_id in subject_matched_courses:
                score += 2
            
            # Bonus for higher-level courses
            score += min(course.level / 100, 1)  # Cap the level bonus
            
            # Ensure we don't include zero-score courses
            if score > 0:
                ranked_courses.append((course, score))
        
        # Sort by score in descending order
        ranked_courses.sort(key=lambda x: x[1], reverse=True)
        
        return ranked_courses
def filter_eligible_courses(self, student_id: str) -> List[Course]:
    """
    Filter courses based on eligibility criteria for a specific student.
    
    Args:
        student_id: Student ID to filter courses for
        
    Returns:
        List of eligible courses
    """
    if student_id not in self.students:
        return list(self.courses.values())  # Return all courses if student not found
        
    student = self.students[student_id]
    
    eligible_courses = []
    for course in self.courses.values():
        # Check prerequisites
        if course.is_eligible(student.completed_courses):
            # Check enrollment capacity
            if not hasattr(course, 'available_slots') or not course.available_slots:
                # No slot constraints, course is available
                eligible_courses.append(course)
            else:
                # Check time availability
                for slot, count in course.available_slots.items():
                    if count > 0 and student.time_constraints.get(slot, True):
                        eligible_courses.append(course)
                        break
    
    return eligible_courses    

def recommend_courses(self, student_id: str, max_recommendations: int = 5) -> List[Course]:
    """
    Generate course recommendations for a student with improved matching
    """
    if student_id not in self.students:
        return []
        
    student = self.students[student_id]
    eligible_courses = self.filter_eligible_courses(student_id)
    
    if not eligible_courses:
        return []
    
    recommendations = []
    
    # Extract student's interests
    career_goals = student.career_goals
    preferred_subjects = student.preferred_subjects
    
    # Search through eligible courses
    for course in eligible_courses:
        score = 0
        
        # Check career goals alignment
        for goal in career_goals:
            goal_lower = goal.lower()
            if any(goal_lower in cr.lower() for cr in course.career_relevance):
                score += 3
            # Check for partial matches too
            elif any(goal_lower in cr.lower() or cr.lower() in goal_lower for cr in course.career_relevance):
                score += 1
        
        # Check preferred subjects
        for subject in preferred_subjects:
            subject_lower = subject.lower()
            # Match in title, skills, or description
            if subject_lower in course.title.lower():
                score += 2
            elif subject_lower in course.description.lower():
                score += 1
            elif any(subject_lower in skill.lower() for skill in course.skills_taught):
                score += 2
        
        # Only add courses with a meaningful relevance score (threshold of 2)
        if score >= 2:
            recommendations.append((course, score))
    
    # Sort by score and return top recommendations
    recommendations.sort(key=lambda x: x[1], reverse=True)
    
    # If we don't have enough recommendations, lower the threshold and try again
    if len(recommendations) < max_recommendations:
        low_score_recommendations = []
        for course in eligible_courses:
            # Skip courses already recommended
            if any(rec[0].course_id == course.course_id for rec in recommendations):
                continue
                
            # Add with a minimal score
            low_score_recommendations.append((course, 1))
            
        # Add these additional courses until we reach the maximum
        additional_needed = max_recommendations - len(recommendations)
        recommendations.extend(low_score_recommendations[:additional_needed])
    
    return [course for course, _ in recommendations[:max_recommendations]]