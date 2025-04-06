# services/dataLoader.py
import csv
import os
import re
import logging
from typing import List, Dict
from models.base import Course
from models.student import StudentProfile
from services.courseSelector import CourseSelector
from services.AIProcessor import AIProcessor
from services.course_enhancement import enhance_course_data, add_ai_response_method

def clean_credits_string(credits_str: str) -> int:
    """
    Clean and parse credits string, handling various edge cases
    
    Args:
        credits_str (str): Raw credits string from CSV
    
    Returns:
        int: Parsed credits value
    """
    try:
        # Remove any weird characters
        credits_str = re.sub(r'[^\d.]+', '', credits_str)
        
        # Convert to float first to handle decimal credits
        credits_float = float(credits_str)
        
        # Round to nearest integer
        return round(credits_float)
    except (ValueError, TypeError):
        # Fallback to default credits
        logging.warning(f"Could not parse credits from '{credits_str}'. Using default of 3 credits.")
        return 3

def parse_course_level(level_str: str) -> int:
    """
    Parse course level with robust handling
    
    Args:
        level_str (str): Raw level string from CSV
    
    Returns:
        int: Parsed course level
    """
    try:
        # Strip any non-digit characters
        level_str = re.sub(r'\D', '', level_str)
        
        # If empty after stripping, use default
        if not level_str:
            logging.warning(f"Could not parse level from '{level_str}'. Using default level 100.")
            return 100
        
        # Parse as integer
        level = int(level_str)
        
        # Validate level is in a reasonable range
        if level < 100 or level > 700:
            logging.warning(f"Unusual course level {level}. Using default level 100.")
            return 100
        
        return level
    except (ValueError, TypeError):
        # Fallback to default level
        logging.warning(f"Could not parse level from '{level_str}'. Using default level 100.")
        return 100

import csv
import os
from typing import List
from models.base import Course

def load_courses_from_csv(file_path: str) -> List[Course]:
    """Load course data from CSV with detailed error handling"""
    print(f"Loading courses from: {file_path}")
    courses = []
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return courses
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            print(f"CSV headers: {reader.fieldnames}")
            
            row_count = 0
            for row in reader:
                try:
                    row_count += 1
                    
                    # Parse credits
                    try:
                        credits = int(row.get('credits', '3'))
                    except (ValueError, TypeError):
                        credits = 3
                    
                    # Parse level
                    try:
                        level = int(row.get('level', '100'))
                    except (ValueError, TypeError):
                        level = 100
                    
                    # Parse lists
                    prerequisites = row.get('prerequisites', '').split(',') if row.get('prerequisites') else []
                    prerequisites = [p.strip() for p in prerequisites if p.strip()]
                    
                    skills = row.get('skills_taught', '').split(',') if row.get('skills_taught') else ['Problem Solving']
                    skills = [s.strip() for s in skills if s.strip()]
                    
                    careers = row.get('career_relevance', '').split(',') if row.get('career_relevance') else ['Professional Development']
                    careers = [c.strip() for c in careers if c.strip()]
                    
                    course = Course(
                        course_id=row['course_id'],
                        title=row['title'],
                        description=row.get('description', ''),
                        credits=credits,
                        department=row.get('department', ''),
                        level=level,
                        prerequisites=prerequisites,
                        skills_taught=skills,
                        career_relevance=careers
                    )
                    courses.append(course)
                except Exception as e:
                    print(f"Error processing row {row_count}: {e}")
            
            print(f"Successfully loaded {len(courses)} courses out of {row_count} rows")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    
    return courses

def load_students_from_csv(file_path: str) -> List[StudentProfile]:
    """
    Load student profile data from a CSV file
    
    Args:
        file_path (str): Path to the students CSV
    
    Returns:
        List[StudentProfile]: List of loaded student profiles
    """
    students = []
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return students
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Convert string representations to appropriate types
                    completed_courses = row.get('completed_courses', '').split(',') if row.get('completed_courses') else []
                    career_goals = row.get('career_goals', '').split(',') if row.get('career_goals') else []
                    preferred_subjects = row.get('preferred_subjects', '').split(',') if row.get('preferred_subjects') else []
                    
                    # Parse time constraints
                    time_constraints = {}
                    constraints_str = row.get('time_constraints', '')
                    if constraints_str:
                        for constraint in constraints_str.split(';'):
                            # Use regex to split on the LAST colon only
                            match = re.match(r'(.+):(\w+)$', constraint.strip())
                            if match:
                                slot = match.group(1).strip()
                                available = match.group(2).lower() == 'true'
                                time_constraints[slot] = available
                    
                    student = StudentProfile(
                        student_id=row['student_id'],
                        completed_courses=completed_courses,
                        current_semester=int(row.get('current_semester', 1)),
                        career_goals=career_goals,
                        preferred_subjects=preferred_subjects,
                        time_constraints=time_constraints,
                        enrollment_status=row.get('enrollment_status', 'Full-time'),
                        min_credits=int(row.get('min_credits', 12)),
                        max_credits=int(row.get('max_credits', 18))
                    )
                    students.append(student)
                except Exception as e:
                    print(f"Error processing student row: {str(e)}")
                    print(f"Problem row: {row}")
                    # Continue with the next row
    
    except Exception as e:
        print(f"Error reading students from {file_path}: {str(e)}")
        return []
    
    return students

def load_data_from_csv(ai_processor=None):
    """
    Load data from separate CSV files for courses and students,
    and initialize the course selector with this data.
    
    Args:
        ai_processor (AIProcessor, optional): AI processor for enhancing course data
    
    Returns:
        CourseSelector: Initialized course selector with loaded data
    """
    selector = CourseSelector()
    
    # Load courses with optional AI enhancement
    courses = load_courses_from_csv('data/courses.csv', ai_processor)
    if courses:
        for course in courses:
            selector.add_course(course)
        print(f"Loaded {len(courses)} courses from data/courses.csv")
    else:
        print("No courses loaded.")
        return None
    
    # Load students
    students = load_students_from_csv('data/students.csv')
    if students:
        for student in students:
            selector.add_student(student)
        print(f"Loaded {len(students)} student profiles from data/students.csv")
    else:
        print("No students loaded.")
        # We can still continue with just courses loaded
    
    return selector