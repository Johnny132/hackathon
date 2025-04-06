import requests
import json
import os
import re
from typing import Dict, List, Any, Optional
import time

class AIProcessor:
    def __init__(self, model: str = "llama3:current", base_url: str = "http://127.0.0.1:11434"):
        """
        Initialize the AI processor using Ollama.
        
        Args:
            model: The name of the Ollama model to use (e.g., "llama3", "mistral", "gemma")
            base_url: The base URL for the Ollama API, defaults to localhost
        """
        self.model = model
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
        
        # Check if Ollama is running and model is available
        self.is_available = False
        self.model_loaded = False
        
        try:
            # Check if Ollama API is available
            version_response = requests.get(f"{base_url}/api/version", timeout=5)
            version_response.raise_for_status()
            self.is_available = True
            print(f"Ollama API available: {version_response.json()}")
            
            # Check if model is loaded
            models_response = requests.get(f"{base_url}/api/tags", timeout=5)
            models_response.raise_for_status()
            
            models = models_response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            if model in model_names:
                self.model_loaded = True
                print(f"Model '{model}' is available")
            else:
                print(f"Model '{model}' not found. Available models: {', '.join(model_names)}")
                print(f"Please run 'ollama pull {model}' to download the model")
                
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama API: {e}")
            print("Ensure Ollama is running with 'ollama serve' command")
    
    def _check_model_availability(self):
        """Try to load the model if it's not already loaded"""
        if not self.is_available:
            print("Ollama API is not available. Please ensure Ollama is running.")
            return False
            
        if not self.model_loaded:
            print(f"Attempting to load model '{self.model}'...")
            try:
                # Use a simple request with a timeout to check model availability
                test_data = {
                    "model": self.model,
                    "prompt": "Hello",
                    "stream": False
                }
                response = requests.post(self.generate_url, json=test_data, timeout=20)
                if response.status_code == 200:
                    self.model_loaded = True
                    print(f"Successfully loaded model '{self.model}'")
                    return True
                else:
                    error_message = response.json().get('error', 'Unknown error')
                    print(f"Error loading model: {error_message}")
                    return False
            except requests.exceptions.RequestException as e:
                print(f"Network error checking model: {e}")
                return False
        return True
        
    def process_student_input(self, text: str) -> Dict[str, List[str]]:
        """Process student input with better extraction of majors and minors"""
        prompt = f"""
        Extract the following information from the student's input text:
        
        1. Career goals: What profession or job roles do they want to pursue?
        2. Preferred subjects: What academic subjects or topics are they interested in?
        3. Major/Minor interests: Are they asking about specific majors or minors?
        4. Time constraints: Any scheduling preferences?
        
        Student input: "{text}"
        
        Format your response as a JSON object. If they mention wanting to major or minor in a subject,
        be sure to include that subject in the preferred_subjects array.
        
        Example format:
        {{
            "career_goals": ["Data Scientist", "Machine Learning Engineer"],
            "preferred_subjects": ["Statistics", "Computer Science", "Business"],
            "time_constraints": ["Available mornings"]
        }}
        """
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1}
        }
        
        try:
            response = requests.post(self.generate_url, json=data, timeout=60)
            response.raise_for_status()
            response_data = response.json()
            content = response_data.get('response', '{}').strip()
            
            # Clean and parse response
            if content.startswith("```json"):
                content = content.strip("```json").strip()
            elif content.startswith("```"):
                content = content.strip("```").strip()
            
            try:
                extracted_info = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_pattern = r'\{[\s\S]*\}'
                match = re.search(json_pattern, content)
                if match:
                    try:
                        extracted_info = json.loads(match.group(0))
                    except json.JSONDecodeError:
                        extracted_info = {}
                else:
                    extracted_info = {}
            
            # Ensure expected keys
            for key in ["career_goals", "preferred_subjects", "time_constraints"]:
                if key not in extracted_info:
                    extracted_info[key] = []
            
            return extracted_info
                
        except Exception as e:
            print(f"API request error: {e}")
        
        return {
            "career_goals": [],
            "preferred_subjects": [],
            "time_constraints": []
        }
    
    def format_course_recommendations(self, recommendations):
        """
        Format course recommendations for better display in chat responses
        
        Args:
            recommendations: List of recommended course dictionaries
            
        Returns:
            Formatted string for display in chat
        """
        if not recommendations:
            return "No recommendations available."
        
        # Start with an intro line
        formatted = "**RECOMMENDED COURSES:**\n\n"
        
        # Add each course recommendation
        for rec in recommendations:
            course_id = rec.get('course_id', 'Unknown')
            title = rec.get('title', 'Unknown')
            credits = rec.get('credits', 0)
            reason = rec.get('reason', 'Aligns with your interests')
            
            # Format each course as a clean bullet point
            formatted += f"• **{course_id}** - {title} ({credits} credits)\n"
            formatted += f"  *Why:* {reason}\n\n"
        
        return formatted

    def generate_course_recommendations(self, 
                                        student_profile: Dict[str, Any], 
                                        courses: List[Dict[str, Any]], 
                                        career_paths: List[Dict[str, Any]], 
                                        max_recommendations: int = 5) -> List[Dict[str, Any]]:
        """
        Generate recommendations using a simple matching algorithm
        """
        recommendations = []
        
        # Extract student's interests
        career_goals = student_profile.get('career_goals', [])
        preferred_subjects = student_profile.get('preferred_subjects', [])
        
        # Search through all courses
        for course in courses:
            score = 0
            
            # Check career goals alignment
            for goal in career_goals:
                if goal.lower() in [cr.lower() for cr in course.get('career_relevance', [])]:
                    score += 3
            
            # Check preferred subjects
            for subject in preferred_subjects:
                # Match in title, skills, or description
                if (subject.lower() in course.get('title', '').lower() or
                    subject.lower() in course.get('description', '').lower() or
                    any(subject.lower() in skill.lower() for skill in course.get('skills_taught', []))):
                    score += 2
            
            # Add course if it has a positive score
            if score > 0:
                recommendations.append({
                    'course_id': course['course_id'],
                    'title': course['title'],
                    'credits': course.get('credits', 3),
                    'reason': f"Matches your interest in {', '.join(career_goals or preferred_subjects)} (Score: {score})"
                })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: int(x.get('score', 0)), reverse=True)
        
        return recommendations[:max_recommendations]
    
    # Define simplified prompts for the course selector chatbot
    SIMPLIFIED_PROMPTS = {
        # Initial greeting
        'greeting': "Hi! I'll help you find the right courses. What's your academic interest or career goal?",
        
        # Follow-up questions
        'ask_career': "What career are you aiming for?",
        'ask_subjects': "What subjects interest you most?",
        'ask_completed': "Which courses have you already taken?",
        'ask_semester': "What semester are you in?",
        'ask_time': "Any scheduling preferences?",
        
        # Recommendations
        'recommend_intro': "Based on your interests, here are some courses to consider:",
        'no_recommendations': "I need more details about your interests to recommend courses.",
        'ask_more_info': "Can you tell me more about your academic goals?",
        
        # Confirmation
        'confirm_understanding': "Got it. You're interested in {career_goals}.",
        'offer_recommendations': "Want to see course recommendations?",
        
        # Help messages
        'help_message': "I can help with course selection, prerequisites, or career path planning.",
        'missing_ai': "I'll recommend courses based on what you've shared.",
    }
    
    def generate_concise_response(self, response_type, **kwargs):
        """
        Generate more concise responses using predefined templates
        
        Args:
            response_type: Type of response from SIMPLIFIED_PROMPTS
            kwargs: Format arguments for the template
        
        Returns:
            Formatted response string
        """
        template = self.SIMPLIFIED_PROMPTS.get(response_type, self.SIMPLIFIED_PROMPTS['help_message'])
        
        # Format the template with any provided arguments
        try:
            formatted_response = template.format(**kwargs)
        except KeyError:
            # If formatting fails, just return the template
            formatted_response = template
        
        return formatted_response
    
    def _generate_basic_recommendations(self, 
                                    extracted_info: Dict[str, List[str]], 
                                    courses: List[Dict[str, Any]],
                                    max_recommendations: int = 3) -> List[Dict[str, Any]]:
        """Generate basic course recommendations based on extracted information with better relevance"""
        scored_courses = []
        
        # Score all courses based on relevance
        for course in courses:
            score = 0
            
            # Career goals matching
            if extracted_info['career_goals']:
                for goal in extracted_info['career_goals']:
                    goal_lower = goal.lower()
                    for career_relevance in course.get('career_relevance', []):
                        if goal_lower in career_relevance.lower():
                            score += 3
                        elif career_relevance.lower() in goal_lower:  # Partial match
                            score += 1
            
            # Subject matching
            if extracted_info['preferred_subjects']:
                for subject in extracted_info['preferred_subjects']:
                    subject_lower = subject.lower()
                    
                    # Title match
                    if subject_lower in course['title'].lower():
                        score += 2
                    
                    # Skills match
                    for skill in course.get('skills_taught', []):
                        if subject_lower in skill.lower():
                            score += 2
                            break
            
            # Only include courses with a meaningful score
            if score >= 2:
                scored_courses.append((course, score))
        
        # Sort by score
        scored_courses.sort(key=lambda x: x[1], reverse=True)
        
        # Format recommendations with reasons
        recommendations = []
        for course, score in scored_courses[:max_recommendations]:
            # Create a more specific reason based on matches
            reason = "This course "
            
            # Add career goal reason if relevant
            if extracted_info['career_goals'] and score >= 3:
                goals = ", ".join(extracted_info['career_goals'][:2])
                reason += f"aligns with your {goals} career goal"
                
                # Add subject reason if also relevant
                if extracted_info['preferred_subjects'] and score > 3:
                    subjects = ", ".join(extracted_info['preferred_subjects'][:2])
                    reason += f" and covers {subjects} which you're interested in"
                reason += "."
            # Just subject reason if no career match
            elif extracted_info['preferred_subjects']:
                subjects = ", ".join(extracted_info['preferred_subjects'][:2])
                reason += f"covers {subjects} which you're interested in."
            else:
                reason = "This is a highly recommended course in the curriculum."
            
            recommendations.append({
                'course_id': course['course_id'],
                'title': course['title'],
                'credits': course.get('credits', 3),
                'reason': reason
            })
        
        return recommendations
    
    def _generate_formatted_recommendations(self, extracted_info, context):
        """Generate and format course recommendations"""
        
        # Get courses from context
        courses = context.get('courses', [])
        
        # Generate recommendations
        recommendations = self._generate_basic_recommendations(
            extracted_info, courses, max_recommendations=3
        )
        
        if recommendations:
            return self.generate_concise_response('recommend_intro') + "\n\n" + \
                   self.format_course_recommendations(recommendations)
        else:
            return self.generate_concise_response('no_recommendations')
    
    def should_ask_career_again(self, student_question, context, conversation_history):
        """
        Determine if we should ask about career goals again or use existing information
        
        Args:
            student_question: The student's question
            context: Context with previous information
            conversation_history: Previous conversation
            
        Returns:
            Boolean indicating if we should ask about career again
        """
        # If conversation history is short, it's reasonable to ask
        if len(conversation_history) < 2:
            return True
        
        # Check if we've already asked about careers
        has_asked_career = any("career" in msg.lower() for msg in conversation_history)
        
        # Check if the student has mentioned a career goal in their question
        career_mentioned = any(career.lower() in student_question.lower() 
                            for career in ["data science", "software", "engineering", 
                                          "manager", "management", "developer", "analyst"])
        
        # If we've already asked about careers or the student has mentioned a career, 
        # we shouldn't ask again
        if has_asked_career or career_mentioned:
            return False
            
        return True
    
    def generate_chatbot_response(self, 
                                 student_question: str, 
                                 context: Dict[str, Any],
                                 conversation_history: List[str] = None) -> str:
        """
        Generate a conversational response with improved memory of the conversation
        
        Args:
            student_question: The student's question
            context: Dictionary with relevant context (courses, career paths, etc.)
            conversation_history: List of previous conversation turns
            
        Returns:
            String response from the chatbot
        """
        # Initialize conversation history if None
        if conversation_history is None:
            conversation_history = []
        
        # Process the input to extract information
        extracted_info = self.process_student_input(student_question)
        
        # Check for specific course recommendation request
        is_asking_for_recommendations = any(term in student_question.lower() 
                                         for term in ["recommend", "suggest", "course", "show", "classes"])
        
        # Check for specific requests about computer science + business
        is_cs_business_query = ("computer science" in student_question.lower() and 
                               "business" in student_question.lower())
        
        # Look for major/minor mentions
        is_major_minor_query = ("major" in student_question.lower() or 
                               "minor" in student_question.lower())
        
        # Extract career goals from conversation history
        known_career_goals = []
        for message in conversation_history:
            # Skip user messages
            if message.startswith("I ") or message.startswith("What "):
                continue
                
            # Check for career goals mention in previous bot responses
            if "Career goals:" in message:
                try:
                    goals_text = message.split("Career goals:")[1].split("\n")[0].strip()
                    known_career_goals = [g.strip() for g in goals_text.split(",")]
                    # Add to extracted info if not already there
                    if not extracted_info['career_goals']:
                        extracted_info['career_goals'] = known_career_goals
                except:
                    pass
        
        # If this is a CS + Business query, generate a specific response
        if is_cs_business_query and is_major_minor_query:
            return """Based on your interest in majoring in Computer Science with a minor in Business, here's what I recommend for your sophomore year:

For Computer Science major (Fall semester):
- CS 240: Data Structures & Algorithms
- CS 270: Systems Programming 
- MATH 231: Calculus II (if not completed)

For Business minor:
- BUS 101: Introduction to Business
- ECON 201: Principles of Microeconomics

This balanced schedule gives you core CS classes while starting your business foundation. The CS courses are prerequisites for advanced work, and the business courses will introduce fundamental business concepts."""
        
        # For a standard recommendation request
        if is_asking_for_recommendations and extracted_info['career_goals']:
            career_goals = extracted_info['career_goals']
            response = f"Based on your interest in {', '.join(career_goals)}, I recommend the following courses: "
            
            # Add course recommendations based on career goals
            if "Business" in career_goals:
                response += "Introduction to Business (BUS 101) * Principles of Marketing (MKTG 201) * Financial Accounting (ACCT 202) These courses will give you a solid foundation in business principles and prepare you for more advanced studies."
            
            if "Computer Science" in career_goals:
                if "Business" in career_goals:
                    response += " For Computer Science, consider: Data Structures (CS 240) * Computer Organization (CS 230) * Discrete Mathematics (MATH 215)"
                else:
                    response += "Introduction to Programming (CS 101) * Data Structures (CS 240) * Computer Organization (CS 230) * Discrete Mathematics (MATH 215) These courses build the foundation for advanced computer science topics."
                    
            response += " Would you like me to suggest more courses or explore related career paths?"
            return response
            
        # Build the conversation history string
        history_str = ""
        if conversation_history:
            # Only use the last 5 turns to avoid token limits
            recent_history = conversation_history[-10:]
            for i, message in enumerate(recent_history):
                role = "Student" if i % 2 == 0 else "Advisor"
                history_str += f"{role}: {message}\n"
        
        # Prepare context information
        courses_info = "\n".join([
            f"- {c['course_id']}: {c['title']} ({c['credits']} credits)"
            for c in context.get('courses', [])[:7]
        ])
        
        # Create prompt with memory of the conversation
        prompt = f"""
        You are a helpful academic advisor chatbot for a university course selection system.
        Keep your responses brief, clear, and focused on helping the student.
        
        AVAILABLE COURSES:
        {courses_info}
        
        CONVERSATION HISTORY:
        {history_str}
        
        Student: {student_question}
        
        Advisor: 
        """
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 800  # Limit response length for conciseness
            }
        }
        
        try:
            response = requests.post(self.generate_url, json=data, timeout=60)
            response.raise_for_status()
            response_data = response.json()
            
            content = response_data.get('response', '')
            return content.strip()
            
        except requests.exceptions.RequestException as e:
            print(f"API request error: {e}")
            return "I'm having trouble connecting to my knowledge base. Please try again later."
        except ValueError as e:
            print(f"Error processing AI response: {e}")
            return "I encountered an error processing your question. Could you rephrase it?"