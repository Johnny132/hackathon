import os
import sys
from models import databaseSetup, student
from services import courseSelector
from services.dataLoader import load_courses_from_csv, load_students_from_csv
from services.AIProcessor import AIProcessor

def main():
    sys.dont_write_bytecode = True
    """Main entry point for the Smart Course Selector application"""
    print("Starting Smart Course Selector...")
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Initialize selector as None first
    selector = None
    
    # Check if data files exist
    if not all(os.path.exists(f) for f in ['data/courses.csv', 'data/students.csv']):
        print("Error: Required CSV files not found in the data directory.")
        print("Please make sure 'data/courses.csv' and 'data/students.csv' exist.")
        print("Exiting program.")
        return
    
    try:
        # Initialize course selector
        selector = courseSelector.CourseSelector()
        
        # Load courses
        courses = load_courses_from_csv('data/courses.csv')
        if not courses:
            print("Error: No courses loaded from 'data/courses.csv'.")
            print("Exiting program.")
            return
            
        for course in courses:
            selector.add_course(course)
        print(f"Loaded {len(courses)} courses from data/courses.csv")
        
        # Load students
        students = load_students_from_csv('data/students.csv')
        if not students:
            print("Warning: No students loaded from 'data/students.csv'.")
            print("Continuing with courses only.")
        else:
            for student in students:
                selector.add_student(student)
            print(f"Loaded {len(students)} student profiles from data/students.csv")
    
    except Exception as e:
        print(f"Error initializing data: {str(e)}")
        print("Exiting program.")
        return
      
    ai_processor = AIProcessor(model="llama3:latest")
    
    # Interactive interface
    print("\nWelcome to the Smart Course Selector!")
    print("Tell us about your career goals, preferred subjects, and time constraints.")
    
    while True:
        print("\nOptions:")
        print("1. Returning User")
        print("2. New User - Get Course Recommendations")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == "1":
            student_id = input("Enter student ID: ")
            if student_id in selector.students:
                try:
                    recommendations = selector.recommend_courses(student_id)
                    
                    print(f"\nRecommended courses for student {student_id}:")
                    if recommendations:
                        for i, course in enumerate(recommendations, 1):
                            print(f"{i}. {course.title} ({course.course_id}) - {course.credits} credits")
                            print(f"   Description: {course.description}")
                            print(f"   Skills taught: {', '.join(course.skills_taught)}")
                            print()
                    else:
                        print("No recommendations available for this student.")
                except Exception as e:
                    print(f"Error generating recommendations: {str(e)}")
            else:
                print(f"Student with ID {student_id} not found.")
                available_ids = list(selector.students.keys())
                if available_ids:
                    print(f"Available student IDs: {', '.join(available_ids)}")
        
        elif choice == "2":
            if ai_processor is None:
                print("AI processor is not available. Cannot process natural language input.")
                continue
                
            text = input("Tell us about your preferences: ")
            try:
                extracted_info = ai_processor.process_student_input(text)
                
                print("\nExtracted information:")
                print(f"Career goals: {', '.join(extracted_info['career_goals']) if extracted_info['career_goals'] else 'None detected'}")
                print(f"Preferred subjects: {', '.join(extracted_info['preferred_subjects']) if extracted_info['preferred_subjects'] else 'None detected'}")
                print(f"Time constraints: {', '.join(extracted_info['time_constraints']) if extracted_info['time_constraints'] else 'None detected'}")
                
                # Ask if user wants AI-generated recommendations
                if extracted_info['career_goals']:
                    proceed = input("\nWould you like AI-generated course recommendations? (y/n): ")
                    if proceed.lower() == 'y':
                        try:
                            # Get completed courses
                            completed_input = input("Enter completed courses (comma-separated): ")
                            completed_courses = [c.strip() for c in completed_input.split(',') if c.strip()]
                            
                            # Get current semester
                            try:
                                current_semester = int(input("Enter current semester (1-8): "))
                            except ValueError:
                                current_semester = 1
                                print("Invalid input. Using semester 1 as default.")
                            
                            # Get enrollment status
                            enrollment_status = input("Enter enrollment status (Full-time/Part-time): ")
                            if enrollment_status.lower() not in ['full-time', 'part-time']:
                                enrollment_status = 'Full-time'
                                print("Invalid input. Using Full-time as default.")
                            
                            # Get credit limits
                            try:
                                min_credits = int(input("Enter minimum credits: "))
                            except ValueError:
                                min_credits = 12 if enrollment_status.lower() == 'full-time' else 6
                                print(f"Invalid input. Using {min_credits} as default.")
                                
                            try:
                                max_credits = int(input("Enter maximum credits: "))
                            except ValueError:
                                max_credits = 18 if enrollment_status.lower() == 'full-time' else 9
                                print(f"Invalid input. Using {max_credits} as default.")
                            
                            # Create a temporary student profile with the extracted info
                            temp_student = {
                                'student_id': 'temp_id',
                                'completed_courses': completed_courses,
                                'current_semester': current_semester,
                                'career_goals': extracted_info['career_goals'],
                                'preferred_subjects': extracted_info['preferred_subjects'],
                                'time_constraints': {},  # Initialize as empty dict
                                'enrollment_status': enrollment_status,
                                'min_credits': min_credits,
                                'max_credits': max_credits
                            }
                            
                            # Convert time constraints to the correct format
                            for constraint in extracted_info['time_constraints']:
                                temp_student['time_constraints'][constraint] = True
                            
                            # Convert eligible courses to dict for AI processing
                            eligible_courses = []
                            for course in selector.courses.values():
                                eligible_courses.append({
                                    'course_id': course.course_id,
                                    'title': course.title,
                                    'credits': course.credits,
                                    'skills_taught': course.skills_taught,
                                    'career_relevance': course.career_relevance
                                })
                            
                            # Get career paths info for AI processing
                            career_paths = []
                            for goal in extracted_info['career_goals']:
                                relevant_courses = [
                                    course['course_id'] for course in eligible_courses 
                                    if goal in course['career_relevance']
                                ]
                                career_paths.append({
                                    'name': goal,
                                    'description': f"Career path for {goal}",
                                    'core_courses': relevant_courses[:5]  # Take first 5 relevant courses as core
                                })
                            
                            # Generate AI recommendations
                            ai_recommendations = ai_processor.generate_course_recommendations(
                                temp_student, eligible_courses, career_paths
                            )
                            
                            # Display recommendations
                            print("\nAI-Generated Course Recommendations:")
                            if ai_recommendations:
                                for i, rec in enumerate(ai_recommendations, 1):
                                    print(f"{i}. {rec['title']} ({rec['course_id']}) - {rec.get('credits', 'N/A')} credits")
                                    print(f"   Reason: {rec['reason']}")
                                    print()
                            else:
                                print("No recommendations generated. Try different preferences or career goals.")
                        except Exception as e:
                            print(f"Error generating AI recommendations: {str(e)}")
                else:
                    print("No career goals detected. Please provide more specific information about your career interests.")
            except Exception as e:
                print(f"Error processing input: {str(e)}")
        
        elif choice == "3":
            print("Thank you for using the Smart Course Selector!")
            break
        
        else:
            print("Invalid choice. Please try again.")
    
def ensure_data_directory():
    """Make sure the data directory exists"""
    os.makedirs('data', exist_ok=True)

if __name__ == "__main__":
    main()