# app.py
from flask import Flask, render_template, request, jsonify, session
import os
import sys
import logging

# Import services and models
from services.AIProcessor import AIProcessor
from services.courseSelector import CourseSelector
from services.dataLoader import load_courses_from_csv, load_students_from_csv  
from models.base import Course
from models.student import StudentProfile
from services.course_enhancement import enhance_course_data

# Rest of your app.py file...

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'  # Append mode
)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)

# Global variables for the selector and API
selector = None
api = None

def initialize_system():
    """Initialize the course selection system"""
    global selector, api
    
    try:
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Initialize course selector
        selector = CourseSelector()
        
        # Load courses from CSV
        courses_path = 'data/courses.csv'
        if os.path.exists(courses_path):
            courses = load_courses_from_csv(courses_path)
            
            # Enhance course data
            logging.info(f"Enhancing {len(courses)} courses with career relevance and skills data...")
            enhanced_courses = [enhance_course_data(course) for course in courses]
            
            # Add courses to selector
            for course in enhanced_courses:
                selector.add_course(course)
                
            logging.info(f"Loaded and enhanced {len(courses)} courses")
        else:
            logging.error(f"Courses file not found: {courses_path}")
            return False
        
        # Create the API layer
        api = CourseRecommendationAPI(selector)
        
        return True
    
    except Exception as e:
        logging.error(f"Error initializing system: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

@app.before_first_request
def setup_app():
    """Initialize the system before the first request"""
    if not initialize_system():
        logging.error("Failed to initialize the course selection system")

@app.route('/')
def home():
    """Render the home page"""
    return render_template('index.html')

@app.route('/chatbot')
def chatbot():
    """Render the chatbot interface"""
    return render_template('chatbot.html')

@app.route('/api/chatbot/process', methods=['POST'])
def process_chatbot_input():
    """Process the chatbot input and generate recommendations"""
    if not api:
        return jsonify({"error": "System not initialized"}), 500
    
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400
        
        user_message = data['message']
        
        # Generate recommendations based on user input
        result = api.generate_recommendations(user_message)
        
        # Format a conversational response
        response = format_chatbot_response(result)
        
        return jsonify({
            "response": response,
            "extracted_info": result['extracted_info']
        })
    
    except Exception as e:
        logging.error(f"Error processing chatbot input: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def format_chatbot_response(result):
    """Format the API result into a conversational response"""
    response_parts = []
    
    # Acknowledge understanding
    career_goals = result['extracted_info']['career_goals']
    preferred_subjects = result['extracted_info']['preferred_subjects']
    
    if career_goals:
        response_parts.append(f"Based on your interest in {', '.join(career_goals)}, ")
    elif preferred_subjects:
        response_parts.append(f"Based on your interest in {', '.join(preferred_subjects)}, ")
    else:
        response_parts.append("Based on your input, ")
    
    # Add recommendations
    recommendations = result['recommendations']
    if recommendations:
        response_parts.append("here are some courses that would be beneficial for you:\n\n")
        response_parts.append("**RECOMMENDED COURSES:**\n\n")
        
        for rec in recommendations:
            course_id = rec['course_id']
            title = rec['title']
            credits = rec['credits']
            reason = rec['reason']
            
            response_parts.append(f"• **{course_id}** - {title} ({credits} credits)\n")
            response_parts.append(f"  *Why:* {reason}\n\n")
        
        total_credits = result['total_credits']
        response_parts.append(f"These recommendations total {total_credits} credits.\n\n")
        
        # Add follow-up question
        response_parts.append("Would you like more specific details about any of these courses, or would you like to explore courses in a different area?")
    else:
        response_parts.append("I couldn't find specific course recommendations based on your input. Could you please provide more details about your academic interests or career goals?")
    
    return "".join(response_parts)

@app.route('/api/courses/search', methods=['GET'])
def search_courses():
    """Search for courses based on query parameters"""
    if not api:
        return jsonify({"error": "System not initialized"}), 500
    
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "No search query provided"}), 400
        
        courses = api.selector.search_courses(query)
        
        results = [
            {
                'course_id': course.course_id,
                'title': course.title,
                'credits': course.credits,
                'department': course.department,
                'level': course.level,
                'description': course.description,
                'skills_taught': course.skills_taught,
                'career_relevance': course.career_relevance
            }
            for course in courses[:10]  # Limit to 10 results
        ]
        
        return jsonify(results)
    
    except Exception as e:
        logging.error(f"Error searching courses: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/courses/<course_id>', methods=['GET'])
def get_course_details(course_id):
    """Get details for a specific course"""
    if not api:
        return jsonify({"error": "System not initialized"}), 500
    
    try:
        course = api.get_course_by_id(course_id)
        if not course:
            return jsonify({"error": f"Course not found: {course_id}"}), 404
        
        return jsonify(course)
    
    except Exception as e:
        logging.error(f"Error getting course details: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommend', methods=['POST'])
def recommend_courses():
    """Generate course recommendations based on provided criteria"""
    if not api:
        return jsonify({"error": "System not initialized"}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract recommendation parameters from request
        career_goals = data.get('career_goals', [])
        preferred_subjects = data.get('preferred_subjects', [])
        completed_courses = data.get('completed_courses', [])
        current_semester = int(data.get('current_semester', 1))
        enrollment_status = data.get('enrollment_status', 'Full-time')
        min_credits = int(data.get('min_credits', 12))
        max_credits = int(data.get('max_credits', 18))
        max_recommendations = int(data.get('max_recommendations', 5))
        
        # Generate recommendations
        recommendations = api.selector.recommend_courses(
            career_goals=career_goals,
            preferred_subjects=preferred_subjects,
            completed_courses=completed_courses,
            current_semester=current_semester,
            enrollment_status=enrollment_status,
            min_credits=min_credits,
            max_credits=max_credits,
            max_recommendations=max_recommendations
        )
        
        # Calculate total credits
        total_credits = sum(rec['credits'] for rec in recommendations)
        
        return jsonify({
            'recommendations': recommendations,
            'total_credits': total_credits,
            'parameters': {
                'career_goals': career_goals,
                'preferred_subjects': preferred_subjects,
                'current_semester': current_semester,
                'enrollment_status': enrollment_status
            }
        })
    
    except Exception as e:
        logging.error(f"Error generating recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Ensure the system is initialized
    if initialize_system():
        logging.info("Course selection system initialized successfully")
        
        # Run the Flask application
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        logging.error("Failed to initialize the course selection system")