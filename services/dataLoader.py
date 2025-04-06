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

def load_courses_from_csv(file_path: str, ai_processor=None) -> List[Course]:
    """
    Load course data from a CSV file with robust error handling
    
    Args:
        file_path (str): Path to the courses CSV
        ai_processor (AIProcessor, optional): AI processor for enhancing course data
    
    Returns:
        List[Course]: List of loaded and potentially enhanced courses
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='course_loading.log',
        filemode='w'
    )
    
    courses = []
    
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return courses
    
    try:
        # Try different encodings
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', newline='', encoding=encoding) as csvfile:
                    reader = csv.DictReader(csvfile)
                    
                    for row in reader:
                        try:
                            # Clean and parse credits 
                            credits = clean_credits_string(row['credits'])
                            
                            # Parse level with robust method
                            level = parse_course_level(row['level'])
                            
                            # Clean description
                            description = row.get('description', '').replace('Course Description: ', '').strip()
                            
                            # Parse terms offered
                            terms_offered = row.get('terms_offered', '').replace('Typically Offered: ', '').split(', ') if row.get('terms_offered') else []
                            
                            # Try to parse prerequisites if exists
                            prerequisites = row.get('prerequisites', '').split(',') if row.get('prerequisites') else []
                            
                            # Create course object with default empty lists for optional fields
                            course = Course(
                                course_id=row['course_id'],
                                title=row['title'],
                                description=description,
                                credits=credits,
                                department=row['department'],
                                level=level,
                                terms_offered=terms_offered,
                                skills_taught=['Problem Solving'],  # Default skills
                                career_relevance=['Professional Development'],  # Default career relevance
                                prerequisites=prerequisites
                            )
                            
                            courses.append(course)
                        
                        except Exception as e:
                            logging.error(f"Error processing course row: {str(e)}")
                            logging.error(f"Problem row: {row}")
                            # Continue with the next row
                
                # If we successfully read the file, break the encoding loop
                if courses:
                    break
            
            except UnicodeDecodeError:
                # Try next encoding if current one fails
                continue
        
        # Enhance courses with AI if processor is available
        if ai_processor and courses:
            # Ensure AI response method exists
            add_ai_response_method(AIProcessor)
            
            # Enhance each course individually
            enhanced_courses = []
            for course in courses:
                try:
                    enhanced_course = enhance_course_data(course, ai_processor)
                    enhanced_courses.append(enhanced_course)
                except Exception as e:
                    logging.error(f"Error enhancing course {course.course_id}: {str(e)}")
                    # Fall back to original course if enhancement fails
                    enhanced_courses.append(course)
            
            courses = enhanced_courses
        
        logging.info(f"Successfully loaded {len(courses)} courses")
        return courses
    
    except Exception as e:
        logging.error(f"Unexpected error reading courses from {file_path}: {str(e)}")
        return []

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