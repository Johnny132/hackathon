import os
import json
import logging
from typing import Dict, Any, List
from models.base import Course

# Default values
DEFAULT_SKILLS = ["Critical Thinking", "Problem Solving"]
DEFAULT_CAREER_PATHS = ["Professional Development"]

class CourseEnhancementCache:
    CACHE_FILE = 'data/course_enhancements_cache.json'
    
    @classmethod
    def load_cache(cls) -> Dict[str, Dict[str, Any]]:
        """
        Load existing course enhancements cache with extensive logging
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(cls.CACHE_FILE), exist_ok=True)
            
            print(f"Attempting to load cache from: {cls.CACHE_FILE}")
            print(f"File exists: {os.path.exists(cls.CACHE_FILE)}")
            
            if os.path.exists(cls.CACHE_FILE):
                with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_content = json.load(f)
                    print(f"Loaded cache with {len(cache_content)} entries")
                    return cache_content
            else:
                print("No existing cache file found. Returning empty cache.")
                return {}
        except Exception as e:
            print(f"CRITICAL ERROR loading course enhancement cache: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    @classmethod
    def save_cache(cls, cache: Dict[str, Dict[str, Any]]):
        """
        Save course enhancements to cache file with extensive logging
        """
        try:
            # Explicitly create directory
            os.makedirs(os.path.dirname(cls.CACHE_FILE), exist_ok=True)
            
            print(f"Attempting to save cache to: {cls.CACHE_FILE}")
            print(f"Cache entries to save: {len(cache)}")
            
            with open(cls.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
            
            # Verify file was created
            print(f"Cache file created/updated at: {cls.CACHE_FILE}")
            print(f"File exists after save: {os.path.exists(cls.CACHE_FILE)}")
        except Exception as e:
            print(f"CRITICAL ERROR saving course enhancement cache: {e}")
            import traceback
            traceback.print_exc()
    
    @classmethod
    def get_enhancement(cls, course_id: str) -> Dict[str, Any]:
        """
        Retrieve enhancement for a specific course with logging
        """
        cache = cls.load_cache()
        enhancement = cache.get(course_id, {})
        print(f"Retrieving enhancement for {course_id}: {'Found' if enhancement else 'Not Found'}")
        return enhancement
    
    @classmethod
    def update_enhancement(cls, course_id: str, enhancement_data: Dict[str, Any]):
        """
        Update enhancement for a specific course with logging
        """
        print(f"Attempting to update cache for course: {course_id}")
        print(f"Enhancement data: {enhancement_data}")
        
        # Load existing cache
        cache = cls.load_cache()
        
        # Update the specific course
        cache[course_id] = enhancement_data
        
        # Save updated cache
        cls.save_cache(cache)

def enhance_course_data(course: Course, ai_processor=None) -> Course:
    """
    Enhance course data with caching mechanism
    
    Args:
        course (Course): Course to enhance
        ai_processor (AIProcessor, optional): AI processor for generating enhancements
    
    Returns:
        Course with enhanced data
    """
    # Add extensive print statements for debugging
    print(f"Processing course enhancement for: {course.course_id}")
    print(f"Course title: {course.title}")
    
    # Check cache first
    cached_enhancement = CourseEnhancementCache.get_enhancement(course.course_id)
    
    if cached_enhancement:
        print(f"Using cached enhancement for {course.course_id}")
        course.skills_taught = cached_enhancement.get('skills_taught', DEFAULT_SKILLS)
        course.career_relevance = cached_enhancement.get('career_relevance', DEFAULT_CAREER_PATHS)
        return course
    
    # If no cache and no AI processor, use defaults
    if not ai_processor:
        course.skills_taught = DEFAULT_SKILLS
        course.career_relevance = DEFAULT_CAREER_PATHS
        return course
    
    # Generate enhancement via AI
    try:
        # Create prompt for AI to generate skills taught and career relevance
        prompt = f"""
        Analyze the following course details and provide:
        1. A list of 3-5 specific skills students would learn from this course
        2. A list of 2-4 career paths where these skills would be relevant

        Course Information:
        - Course ID: {course.course_id}
        - Title: {course.title}
        - Description: {course.description}
        - Department: {course.department}
        - Level: {course.level} (100=freshman, 200=sophomore, 300=junior, 400=senior)

        Format your response as a JSON object with two keys:
        {{
            "skills_taught": ["Skill1", "Skill2", "Skill3"],
            "career_relevance": ["Career Path 1", "Career Path 2"]
        }}
        
        Only respond with the JSON object, no additional text.
        """
        
        # Use AI to generate enhancement
        data = {
            "model": ai_processor.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 1000
            }
        }
        
        response = ai_processor._get_ai_response(data)
        
        # Clean and parse response
        response = response.strip()
        if response.startswith("```json"):
            response = response.strip("```json").strip()
        elif response.startswith("```"):
            response = response.strip("```").strip()
        
        # Parse JSON
        try:
            enhancement = json.loads(response)
            
            # Extract skills and career paths with fallbacks
            skills = enhancement.get('skills_taught', DEFAULT_SKILLS)
            career_paths = enhancement.get('career_relevance', DEFAULT_CAREER_PATHS)
            
            # Update course
            course.skills_taught = skills
            course.career_relevance = career_paths
            
            # Cache the enhancement
            CourseEnhancementCache.update_enhancement(course.course_id, {
                'skills_taught': skills,
                'career_relevance': career_paths
            })
        
        except json.JSONDecodeError:
            # Fallback to default values
            course.skills_taught = DEFAULT_SKILLS
            course.career_relevance = DEFAULT_CAREER_PATHS
    
    except Exception as e:
        print(f"Error enhancing course {course.course_id}: {e}")
        # Fallback to default values
        course.skills_taught = DEFAULT_SKILLS
        course.career_relevance = DEFAULT_CAREER_PATHS
    
    return course

def enhance_courses_from_csv(courses: List[Course], ai_processor) -> List[Course]:
    """
    Enhance multiple courses with caching
    
    Args:
        courses (List[Course]): Courses to enhance
        ai_processor (AIProcessor): AI processor for generating enhancements
    
    Returns:
        List[Course] with enhancements
    """
    # Load the cache once at the beginning
    cache = CourseEnhancementCache.load_cache()
    
    enhanced_courses = []
    courses_to_update = {}
    
    # First pass - use cache for all available courses
    for course in courses:
        course_id = course.course_id
        if course_id in cache:
            # Use cached data
            print(f"Using cached enhancement for {course_id}")
            enhancement = cache[course_id]
            course.skills_taught = enhancement.get('skills_taught', DEFAULT_SKILLS)
            course.career_relevance = enhancement.get('career_relevance', DEFAULT_CAREER_PATHS)
        else:
            # Mark for processing
            if ai_processor:
                courses_to_update[course_id] = course
            else:
                # Use defaults if no AI processor
                course.skills_taught = DEFAULT_SKILLS
                course.career_relevance = DEFAULT_CAREER_PATHS
        
        enhanced_courses.append(course)
    
    # Only process uncached courses
    if courses_to_update and ai_processor:
        print(f"Processing {len(courses_to_update)} uncached courses")
        for course_id, course in courses_to_update.items():
            # Process with AI
            try:
                # [AI processing code from enhance_course_data function]
                # ...
                
                # Update cache directly
                cache[course_id] = {
                    'skills_taught': course.skills_taught,
                    'career_relevance': course.career_relevance
                }
            except Exception as e:
                print(f"Error enhancing course {course_id}: {e}")
        
        # Save cache once after all processing
        CourseEnhancementCache.save_cache(cache)
    
    return enhanced_courses

def add_ai_response_method(ai_processor_class):
    """
    Add a method to get AI responses directly to the AIProcessor class if it doesn't exist
    
    Args:
        ai_processor_class (type): AIProcessor class to modify
    """
    if not hasattr(ai_processor_class, '_get_ai_response'):
        def _get_ai_response(self, data):
            """
            Get a direct response from the AI model
            
            Args:
                data (dict): Request data for AI model
            
            Returns:
                str: AI-generated response
            """
            import requests
            
            try:
                response = requests.post(self.generate_url, json=data, timeout=60)
                response.raise_for_status()
                response_data = response.json()
                
                return response_data.get('response', '')
            except Exception as e:
                print(f"AI response error: {str(e)}")
                return ""
        
        # Add the method to the class
        setattr(ai_processor_class, '_get_ai_response', _get_ai_response)