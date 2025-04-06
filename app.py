# app.py
from typing import Dict, Any, List, Optional
from flask import Flask, render_template, request, jsonify, session
import os
import sys
import logging
import traceback

# Import services and models
from services.course_cache import CourseRecommendationCache
from services.AIProcessor import AIProcessor
from services.courseSelector import CourseSelector
from services.dataLoader import load_courses_from_csv
from models.base import Course
from models.student import StudentProfile
from services.course_enhancement import enhance_course_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Create app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)

# Global variables for the selector and API
selector = None
api = None
ai_processor = None


class CourseRecommendationAPI:
    def __init__(self, selector, ai_processor=None):
        """
        Initialize the Course Recommendation API
        
        Args:
            selector (CourseSelector): The course selector instance
            ai_processor (AIProcessor, optional): AI processor for generating recommendations
        """
        self.selector = selector
        self.ai_processor = ai_processor
        self.logger = logging.getLogger(__name__)
    
    def generate_recommendations(self, user_message: str) -> Dict[str, Any]:
        """
        Generate course recommendations based on user message
        
        Args:
            user_message (str): User's input message
        
        Returns:
            Dict containing recommendations and extracted information
        """
        try:
            # First, ensure we have an AI processor
            if not self.ai_processor:
                self.logger.warning("No AI processor available. Using fallback recommendation method.")
                return {
                    'recommendations': self._generate_general_recommendations(),
                    'extracted_info': {},
                    'total_credits': 0
                }
            
            # Extract information from user message
            try:
                extracted_info = self.ai_processor.process_student_input(user_message)
            except Exception as e:
                self.logger.error(f"Error processing student input: {e}")
                extracted_info = {}
            
            # Determine primary interest
            primary_interest = (
                extracted_info.get('career_goals', [None])[0] or 
                extracted_info.get('preferred_subjects', [None])[0] or
                'general'
            )
            
            # Check cache first
            cached_recommendations = CourseRecommendationCache.get_cached_recommendations(primary_interest)
            if cached_recommendations:
                return {
                    'recommendations': cached_recommendations,
                    'extracted_info': extracted_info,
                    'total_credits': sum(rec.get('credits', 3) for rec in cached_recommendations)
                }
            
            # Generate recommendations
            recommendations = self._generate_smart_recommendations(extracted_info)
            
            # Format recommendations
            formatted_recommendations = [
                {
                    'course_id': course.course_id,
                    'title': course.title,
                    'credits': course.credits,
                    'reason': self._generate_recommendation_reason(course, extracted_info)
                } for course in recommendations
            ]
            
            # Cache recommendations
            CourseRecommendationCache.cache_recommendations(primary_interest, formatted_recommendations)
            
            return {
                'recommendations': formatted_recommendations,
                'extracted_info': extracted_info,
                'total_credits': sum(rec.get('credits', 3) for rec in formatted_recommendations)
            }
        
        except Exception as e:
            self.logger.error(f"Unexpected error generating recommendations: {e}")
            self.logger.error(traceback.format_exc())
            return {
                'recommendations': self._generate_general_recommendations(),
                'extracted_info': {},
                'total_credits': 0
            }
    
    def _generate_smart_recommendations(self, extracted_info: Dict[str, Any]) -> List[Course]:
        """
        Generate smart recommendations based on extracted information
        
        Args:
            extracted_info (Dict): Extracted user interests
        
        Returns:
            List of recommended courses
        """
        # Check career goals and preferred subjects
        goals = extracted_info.get('career_goals', [])
        subjects = extracted_info.get('preferred_subjects', [])
        
        # Combine goals and subjects for matching
        search_terms = goals + subjects
        
        # If no search terms, generate general recommendations
        if not search_terms:
            return self._generate_general_recommendations()
        
        # Score courses based on relevance
        course_scores = {}
        for course in self.selector.courses.values():
            score = 0
            
            # Check against goals and subjects
            for term in search_terms:
                term_lower = term.lower()
                
                # Check career relevance
                if any(term_lower in cr.lower() for cr in course.career_relevance):
                    score += 3
                
                # Check skills
                if any(term_lower in skill.lower() for skill in course.skills_taught):
                    score += 2
                
                # Check title and description
                if (term_lower in course.title.lower() or 
                    term_lower in course.description.lower()):
                    score += 1
            
            if score > 0:
                course_scores[course] = score
        
        # Sort courses by score and take top recommendations
        recommended_courses = sorted(
            course_scores.keys(), 
            key=lambda c: course_scores[c], 
            reverse=True
        )[:5]
        
        return recommended_courses or self._generate_general_recommendations()
    
    def _generate_general_recommendations(self) -> List[Course]:
        """
        Generate general course recommendations
        
        Returns:
            List of recommended courses
        """
        # Take a mix of courses from different levels
        levels = [100, 200, 300]
        general_recommendations = []
        
        for level in levels:
            level_courses = [
                course for course in self.selector.courses.values() 
                if course.level == level
            ]
            
            # Add up to 2 courses from each level
            general_recommendations.extend(level_courses[:2])
            
            # Break if we have 5 or more recommendations
            if len(general_recommendations) >= 5:
                break
        
        # If not enough recommendations, fill with remaining courses
        if len(general_recommendations) < 5:
            general_recommendations.extend(
                list(self.selector.courses.values())[:5 - len(general_recommendations)]
            )
        
        return general_recommendations[:5]
    
    def _generate_recommendation_reason(self, course: Course, extracted_info: Dict[str, Any]) -> str:
        """
        Generate a reason for recommending a course
        
        Args:
            course (Course): Recommended course
            extracted_info (Dict): Extracted user interests
        
        Returns:
            str: Reason for recommending the course
        """
        # Check career goals
        if extracted_info.get('career_goals'):
            for goal in extracted_info['career_goals']:
                if any(goal.lower() in cr.lower() for cr in course.career_relevance):
                    return f"Aligns with your {goal} career goal"
        
        # Check preferred subjects
        if extracted_info.get('preferred_subjects'):
            for subject in extracted_info['preferred_subjects']:
                if (subject.lower() in course.title.lower() or 
                    subject.lower() in course.description.lower() or
                    any(subject.lower() in skill.lower() for skill in course.skills_taught)):
                    return f"Matches your interest in {subject}"
        
        # Fallback reason
        return "Recommended based on your academic interests"
    
    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """
        Get a specific course by its ID
        
        Args:
            course_id (str): Course ID to retrieve
        
        Returns:
            Course or None if not found
        """
        return self.selector.courses.get(course_id)
    
    def search_courses(self, query: str, max_results: int = 10) -> List[Course]:
        """
        Search for courses based on a query string
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results to return
        
        Returns:
            List of matching courses
        """
        query_lower = query.lower()
        
        matching_courses = [
            course for course in self.selector.courses.values()
            if (query_lower in course.title.lower() or
                query_lower in course.description.lower() or
                query_lower in course.department.lower() or
                any(query_lower in skill.lower() for skill in course.skills_taught) or
                any(query_lower in career.lower() for career in course.career_relevance))
        ]
        
        return matching_courses[:max_results]
def initialize_system():
    """Initialize the course selection system"""
    global selector, api, ai_processor
    
    try:
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Initialize course selector
        selector = CourseSelector()
        
        # Initialize AI Processor
        try:
            ai_processor = AIProcessor(model="llama3:latest")
            logger.info(f"AI Processor initialized with model: {ai_processor.model}")
        except Exception as e:
            logger.error(f"Failed to initialize AI Processor: {e}")
            ai_processor = None
        
        # Load courses from CSV
        courses_path = 'data/courses.csv'
        logger.info(f"Looking for courses file at: {os.path.abspath(courses_path)}")
        
        if os.path.exists(courses_path):
            courses = load_courses_from_csv(courses_path)
            
            if not courses:
                logger.warning("No courses loaded from CSV file. Creating test courses.")
                
            
            # Enhance course data
            logger.info(f"Enhancing {len(courses)} courses...")
            enhanced_courses = [enhance_course_data(course) for course in courses]
            
            # Add courses to selector
            for course in enhanced_courses:
                selector.add_course(course)
            
            logger.info(f"Added {len(enhanced_courses)} courses to selector")
        else:
            logger.error(f"Courses file not found: {courses_path}")
            return False
        
        # Create the API layer
        api = CourseRecommendationAPI(selector, ai_processor)
        logger.info("Course recommendation API initialized")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing system: {e}")
        logger.error(traceback.format_exc())
        return False

def format_chatbot_response(result):
    """Format the API result into a conversational response"""
    response_parts = []
    
    # Safely extract extracted info
    extracted_info = result.get('extracted_info', {}) or {}
    recommendations = result.get('recommendations', [])
    
    # Acknowledge understanding
    career_goals = extracted_info.get('career_goals', [])
    preferred_subjects = extracted_info.get('preferred_subjects', [])
    
    if career_goals:
        response_parts.append(f"Based on your interest in {', '.join(career_goals)}, ")
    elif preferred_subjects:
        response_parts.append(f"Based on your interest in {', '.join(preferred_subjects)}, ")
    else:
        response_parts.append("Based on your input, ")
    
    # Add recommendations
    if recommendations:
        response_parts.append("here are some courses that would be beneficial for you:\n\n")
        response_parts.append("**RECOMMENDED COURSES:**\n\n")
        
        for rec in recommendations:
            # Handle both Course objects and dictionaries
            if hasattr(rec, 'course_id'):
                # Course object
                course_id = rec.course_id
                title = rec.title
                credits = rec.credits
                reason = "Matches your interests"
                
                # Try to get skills or career relevance for a more specific reason
                if hasattr(rec, 'skills_taught') and rec.skills_taught:
                    reason = f"Teaches {', '.join(rec.skills_taught[:2])}"
                elif hasattr(rec, 'career_relevance') and rec.career_relevance:
                    reason = f"Relevant for {', '.join(rec.career_relevance[:2])}"
            else:
                # Dictionary 
                course_id = rec.get('course_id', rec.get('id', 'Unknown Course'))
                title = rec.get('title', 'Course Title')
                credits = rec.get('credits', rec.get('credit', 3))
                reason = rec.get('reason', 'Matches your interests')
            
            response_parts.append(f"• **{course_id}** - {title} ({credits} credits)\n")
            response_parts.append(f"  *Why:* {reason}\n\n")
        
        # Try to calculate total credits
        try:
            if hasattr(recommendations[0], 'credits'):
                total_credits = sum(rec.credits for rec in recommendations)
            else:
                total_credits = sum(rec.get('credits', rec.get('credit', 3)) for rec in recommendations)
            
            response_parts.append(f"These recommendations total {total_credits} credits.\n\n")
        except:
            # If credit calculation fails, skip
            pass
        
        # Add follow-up question
        response_parts.append("Would you like more specific details about any of these courses, or would you like to explore courses in a different area?")
    else:
        response_parts.append("I couldn't find specific course recommendations based on your input. Could you please provide more details about your academic interests or career goals?")
    
    return "".join(response_parts)

# Flask Routes
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
            "extracted_info": result.get('extracted_info', {})
        })
    
    except Exception as e:
        logger.error(f"Error processing chatbot input: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/courses/search', methods=['GET'])
def search_courses():
    """Search for courses based on query parameters"""
    if not api:
        return jsonify({"error": "System not initialized"}), 500
    
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "No search query provided"}), 400
        
        # Assuming selector has a search_courses method
        try:
            courses = api.selector.search_courses(query)
        except AttributeError:
            # Fallback search if method doesn't exist
            courses = [
                course for course in api.selector.courses.values()
                if query.lower() in course.title.lower() 
                or query.lower() in course.description.lower()
            ]
        
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
        logger.error(f"Error searching courses: {str(e)}")
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
        
        return jsonify({
            'course_id': course.course_id,
            'title': course.title,
            'credits': course.credits,
            'department': course.department,
            'level': course.level,
            'description': course.description,
            'skills_taught': course.skills_taught,
            'career_relevance': course.career_relevance
        })
    
    except Exception as e:
        logger.error(f"Error getting course details: {str(e)}")
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
        
        # Use the CourseSelector to generate recommendations
        recommendations = api.selector.recommend_courses(
            student_profile={
                'career_goals': career_goals,
                'preferred_subjects': preferred_subjects,
                'completed_courses': completed_courses,
                'current_semester': current_semester,
                'enrollment_status': enrollment_status,
                'min_credits': min_credits,
                'max_credits': max_credits
            }
        )
        
        # Format recommendations
        formatted_recommendations = [
            {
                'course_id': course.course_id,
                'title': course.title,
                'credits': course.credits,
                'reason': f"Matches your {career_goals[0] if career_goals else 'interests'}"
            } for course in recommendations
        ]
        
        # Calculate total credits
        total_credits = sum(rec.get('credits', 3) for rec in formatted_recommendations)
        
        return jsonify({
            'recommendations': formatted_recommendations,
            'total_credits': total_credits,
            'parameters': {
                'career_goals': career_goals,
                'preferred_subjects': preferred_subjects,
                'current_semester': current_semester,
                'enrollment_status': enrollment_status
            }
        })
    
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500

# Initialize the system at startup
with app.app_context():
    if not initialize_system():
        logger.error("Failed to initialize the course selection system")

if __name__ == '__main__':
    # Ensure the system is initialized
    if initialize_system():
        logger.info("Course selection system initialized successfully")
        
        # Run the Flask application
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        logger.error("Failed to initialize the course selection system")