import csv
import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

class CourseDataManager:
    """
    Manager for loading, enhancing, and saving course data
    """
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.courses_file = os.path.join(data_dir, 'courses.csv')
        self.students_file = os.path.join(data_dir, 'students.csv')
        self.enhanced_courses_file = os.path.join(data_dir, 'enhanced_courses.json')
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=os.path.join(data_dir, 'data_loader.log'),
            filemode='a'
        )
    
    def load_courses_from_csv(self) -> List[Dict]:
        """
        Load courses from CSV file
        
        Returns:
            List of course dictionaries
        """
        courses = []
        
        if not os.path.exists(self.courses_file):
            logging.error(f"Courses file not found: {self.courses_file}")
            return courses
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(self.courses_file, 'r', newline='', encoding=encoding) as csvfile:
                        reader = csv.DictReader(csvfile)
                        
                        for row in reader:
                            try:
                                # Process course data
                                course = {
                                    'course_id': row['course_id'],
                                    'title': row['title'],
                                    'description': row.get('description', ''),
                                    'credits': self._parse_credits(row.get('credits', '3')),
                                    'department': row.get('department', ''),
                                    'level': self._parse_level(row.get('level', '100')),
                                    'prerequisites': [p.strip() for p in row.get('prerequisites', '').split(',') if p.strip()],
                                    'terms_offered': [t.strip() for t in row.get('terms_offered', '').split(',') if t.strip()]
                                }
                                
                                courses.append(course)
                            except Exception as e:
                                logging.error(f"Error processing course row: {str(e)}")
                                logging.error(f"Problem row: {row}")
                    
                    # If we loaded courses successfully, break out of the encoding loop
                    if courses:
                        break
                except UnicodeDecodeError:
                    # Try the next encoding
                    continue
            
            if not courses:
                logging.error(f"Failed to load courses with any encoding")
            else:
                logging.info(f"Successfully loaded {len(courses)} courses from {self.courses_file}")
            
            return courses
        
        except Exception as e:
            logging.error(f"Unexpected error loading courses: {str(e)}")
            return []
    
    def load_students_from_csv(self) -> List[Dict]:
        """
        Load students from CSV file
        
        Returns:
            List of student dictionaries
        """
        students = []
        
        if not os.path.exists(self.students_file):
            logging.warning(f"Students file not found: {self.students_file}")
            return students
        
        try:
            with open(self.students_file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    try:
                        # Process student data
                        student = {
                            'student_id': row['student_id'],
                            'completed_courses': [c.strip() for c in row.get('completed_courses', '').split(',') if c.strip()],
                            'current_semester': int(row.get('current_semester', 1)),
                            'career_goals': [g.strip() for g in row.get('career_goals', '').split(',') if g.strip()],
                            'preferred_subjects': [s.strip() for s in row.get('preferred_subjects', '').split(',') if s.strip()],
                            'enrollment_status': row.get('enrollment_status', 'Full-time'),
                            'min_credits': int(row.get('min_credits', 12)),
                            'max_credits': int(row.get('max_credits', 18))
                        }
                        
                        # Process time constraints
                        time_constraints = {}
                        constraints_str = row.get('time_constraints', '')
                        if constraints_str:
                            for constraint in constraints_str.split(';'):
                                parts = constraint.strip().split(':')
                                if len(parts) == 2:
                                    slot = parts[0].strip()
                                    available = parts[1].lower() == 'true'
                                    time_constraints[slot] = available
                        
                        student['time_constraints'] = time_constraints
                        students.append(student)
                    except Exception as e:
                        logging.error(f"Error processing student row: {str(e)}")
            
            logging.info(f"Successfully loaded {len(students)} students from {self.students_file}")
            return students
        
        except Exception as e:
            logging.error(f"Error loading students: {str(e)}")
            return []
    
    def enhance_courses(self, courses: List[Dict]) -> List[Dict]:
        """
        Enhance course data with skills and career relevance.
        First checks if enhanced data is already cached.
        
        Args:
            courses: List of course dictionaries
            
        Returns:
            List of enhanced course dictionaries
        """
        # Check if enhanced courses file exists
        if os.path.exists(self.enhanced_courses_file):
            try:
                # Load enhanced courses from cache
                with open(self.enhanced_courses_file, 'r', encoding='utf-8') as f:
                    enhanced_courses_dict = json.load(f)
                
                # Convert to list if needed
                if isinstance(enhanced_courses_dict, dict):
                    enhanced_courses = list(enhanced_courses_dict.values())
                else:
                    enhanced_courses = enhanced_courses_dict
                
                logging.info(f"Loaded {len(enhanced_courses)} enhanced courses from cache")
                
                if len(enhanced_courses) >= len(courses):
                    return enhanced_courses
            except Exception as e:
                logging.error(f"Error loading enhanced courses from cache: {str(e)}")
        
        # Enhance courses
        enhanced_courses = []
        
        # Department to skills and careers mapping
        department_mapping = {
            'computer science': {
                'skills': ['Programming', 'Algorithms', 'Problem Solving', 'Computational Thinking'],
                'careers': ['Software Engineering', 'Data Science', 'Web Development']
            },
            'cs': {
                'skills': ['Programming', 'Algorithms', 'Problem Solving', 'Computational Thinking'],
                'careers': ['Software Engineering', 'Data Science', 'Web Development']
            },
            'mathematics': {
                'skills': ['Analytical Thinking', 'Quantitative Analysis', 'Problem Solving'],
                'careers': ['Data Science', 'Finance', 'Research']
            },
            'math': {
                'skills': ['Analytical Thinking', 'Quantitative Analysis', 'Problem Solving'],
                'careers': ['Data Science', 'Finance', 'Research']
            },
            'business': {
                'skills': ['Strategic Thinking', 'Analysis', 'Communication', 'Management'],
                'careers': ['Business Analytics', 'Management', 'Consulting', 'Entrepreneurship']
            },
            'psychology': {
                'skills': ['Research Methods', 'Critical Thinking', 'Data Analysis', 'Human Behavior Analysis'],
                'careers': ['Counseling', 'Human Resources', 'UX Research', 'Healthcare']
            },
            'engineering': {
                'skills': ['Problem Solving', 'Design Thinking', 'Technical Analysis', 'Project Management'],
                'careers': ['Engineering', 'Product Management', 'Research and Development']
            },
            'english': {
                'skills': ['Writing', 'Analysis', 'Communication', 'Critical Thinking'],
                'careers': ['Content Creation', 'Journalism', 'Education', 'Marketing']
            },
            'communication': {
                'skills': ['Public Speaking', 'Writing', 'Media Analysis', 'Persuasion'],
                'careers': ['Marketing', 'Public Relations', 'Journalism', 'Social Media Management']
            }
        }
        
        # Keywords to skills and careers mapping
        keyword_mapping = {
            'programming': {
                'skills': ['Coding', 'Software Development', 'Debugging', 'Testing'],
                'careers': ['Software Engineering', 'Web Development', 'Mobile Development']
            },
            'data': {
                'skills': ['Data Analysis', 'Statistical Thinking', 'Data Visualization'],
                'careers': ['Data Science', 'Data Engineering', 'Business Analytics']
            },
            'algorithm': {
                'skills': ['Algorithm Design', 'Computational Thinking', 'Optimization'],
                'careers': ['Software Engineering', 'Data Science', 'Research']
            },
            'database': {
                'skills': ['Database Design', 'SQL', 'Data Management'],
                'careers': ['Database Administrator', 'Data Engineer', 'Backend Developer']
            },
            'web': {
                'skills': ['Web Development', 'Frontend', 'Backend', 'UI/UX'],
                'careers': ['Web Developer', 'Frontend Engineer', 'Full Stack Developer']
            },
            'design': {
                'skills': ['Design Thinking', 'User Experience', 'Visual Communication'],
                'careers': ['UX Designer', 'Product Designer', 'Graphic Designer']
            },
            'ai': {
                'skills': ['Machine Learning', 'Data Analysis', 'Algorithm Design'],
                'careers': ['AI Engineer', 'Machine Learning Engineer', 'Data Scientist']
            },
            'network': {
                'skills': ['Network Administration', 'Security', 'System Configuration'],
                'careers': ['Network Engineer', 'Security Specialist', 'System Administrator']
            },
            'security': {
                'skills': ['Cybersecurity', 'Threat Analysis', 'Security Protocols'],
                'careers': ['Security Analyst', 'Penetration Tester', 'Security Engineer']
            },
            'mobile': {
                'skills': ['Mobile Development', 'App Design', 'Cross-platform Development'],
                'careers': ['Mobile Developer', 'App Developer', 'iOS/Android Developer']
            },
            'management': {
                'skills': ['Leadership', 'Project Management', 'Team Coordination'],
                'careers': ['Project Manager', 'Product Manager', 'Team Lead']
            },
            'finance': {
                'skills': ['Financial Analysis', 'Budgeting', 'Investment Analysis'],
                'careers': ['Financial Analyst', 'Investment Banker', 'Financial Planner']
            },
            'marketing': {
                'skills': ['Market Research', 'Campaign Planning', 'Digital Marketing'],
                'careers': ['Marketing Specialist', 'Digital Marketer', 'Brand Manager']
            },
            'research': {
                'skills': ['Research Methods', 'Data Collection', 'Analysis'],
                'careers': ['Researcher', 'Analyst', 'Scientist', 'Academic']
            },
            'intro': {
                'skills': ['Foundational Knowledge', 'Basic Concepts', 'Terminology'],
                'careers': ['Entry-level Positions', 'Professional Development']
            },
            'advanced': {
                'skills': ['Advanced Techniques', 'Specialized Knowledge', 'Expert Skills'],
                'careers': ['Senior Positions', 'Specialist Roles', 'Advanced Practitioner']
            }
        }
        
        # Check if there are courses to enhance
        if not courses:
            logging.warning("No courses to enhance")
            return []
        
        # Enhance each course
        for course in courses:
            # Default skills and careers
            skills = ["Critical Thinking", "Problem Solving"]
            careers = ["Professional Development"]
            
            # Get department and normalize
            dept = course.get('department', '').lower()
            
            # Try to find department in mappings
            for key, mapping in department_mapping.items():
                if key in dept:
                    skills.extend(mapping['skills'])
                    careers.extend(mapping['careers'])
                    break
            
            # Check for keywords in title and description
            title_desc = (course.get('title', '') + " " + course.get('description', '')).lower()
            for keyword, mapping in keyword_mapping.items():
                if keyword in title_desc:
                    skills.extend(mapping['skills'])
                    careers.extend(mapping['careers'])
            
            # Remove duplicates while preserving order
            unique_skills = []
            seen_skills = set()
            for skill in skills:
                if skill.lower() not in seen_skills:
                    seen_skills.add(skill.lower())
                    unique_skills.append(skill)
            
            unique_careers = []
            seen_careers = set()
            for career in careers:
                if career.lower() not in seen_careers:
                    seen_careers.add(career.lower())
                    unique_careers.append(career)
            
            # Add enhanced data to course
            course['skills_taught'] = unique_skills[:5]  # Limit to 5 skills
            course['career_relevance'] = unique_careers[:5]  # Limit to 5 careers
            
            # Add to enhanced courses list
            enhanced_courses.append(course)
        
        # Save enhanced courses to cache
        try:
            with open(self.enhanced_courses_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced_courses, f, indent=2)
            
            logging.info(f"Saved {len(enhanced_courses)} enhanced courses to cache")
        except Exception as e:
            logging.error(f"Error saving enhanced courses to cache: {str(e)}")
        
        return enhanced_courses
    
    def _parse_credits(self, credits_str: str) -> int:
        """
        Parse credits string to integer
        
        Args:
            credits_str: Credits as string
            
        Returns:
            Credits as integer
        """
        try:
            # Remove non-numeric characters except decimal point
            credits_str = re.sub(r'[^\d.]', '', credits_str)
            
            # Parse as float and round to integer
            credits = int(round(float(credits_str)))
            
            # Ensure credits are in a reasonable range
            if credits < 0 or credits > 12:
                logging.warning(f"Unusual credit value: {credits}. Limiting to range 1-6.")
                credits = max(1, min(credits, 6))
            
            return credits
        except Exception as e:
            logging.warning(f"Error parsing credits '{credits_str}': {str(e)}. Using default of 3.")
            return 3
    
    def _parse_level(self, level_str: str) -> int:
        """
        Parse course level to integer
        
        Args:
            level_str: Level as string
            
        Returns:
            Level as integer
        """
        try:
            # Remove non-numeric characters
            level_str = re.sub(r'\D', '', level_str)
            
            # If empty after stripping, use default
            if not level_str:
                return 100
            
            # Parse as integer
            level = int(level_str)
            
            # Normalize to standard course levels
            if level < 100:
                # Might be 1, 2, 3, 4 for year level
                level = level * 100
            elif level > 700:
                # Unusual course level
                logging.warning(f"Unusual course level {level}. Using default level 100.")
                level = 100
            
            return level
        except Exception as e:
            logging.warning(f"Error parsing level '{level_str}': {str(e)}. Using default of 100.")
            return 100
    
    def generate_sample_data(self):
        """
        Generate sample course and student data if none exists
        
        Returns:
            Tuple of (courses, students)
        """
        if not os.path.exists(self.courses_file):
            self._generate_sample_courses()
        
        if not os.path.exists(self.students_file):
            self._generate_sample_students()
        
        return self.load_courses_from_csv(), self.load_students_from_csv()