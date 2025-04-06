import os
from typing import Dict, Any, List
from models.base import Course
import json

DEFAULT_SKILLS = ["Critical Thinking", "Problem Solving"]
DEFAULT_CAREER_PATHS = ["Professional Development"]

class CourseEnhancementCache:
    CACHE_FILE = 'data/course_enhancements_cache.json'
    _cache = {}
    
    @classmethod
    def load_cache(cls) -> Dict[str, Dict[str, Any]]:
        """
        Load existing course enhancements cache with extensive logging
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(cls.CACHE_FILE), exist_ok=True)
            
            if os.path.exists(cls.CACHE_FILE):
                with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cls._cache = json.load(f)
            else:
                cls._cache = {}
            
            return cls._cache
        except Exception as e:
            print(f"Error loading course enhancement cache: {e}")
            return {}
    
    @classmethod
    def save_cache(cls):
        """
        Save course enhancements to cache file
        """
        try:
            # Explicitly create directory
            os.makedirs(os.path.dirname(cls.CACHE_FILE), exist_ok=True)
            
            with open(cls.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cls._cache, f, indent=2)
        except Exception as e:
            print(f"Error saving course enhancement cache: {e}")
    
    @classmethod
    def get_enhancement(cls, course_id: str) -> Dict[str, Any]:
        """
        Retrieve enhancement for a specific course
        """
        # Ensure cache is loaded
        if not cls._cache:
            cls.load_cache()
        
        # Return enhancement or empty dict
        return cls._cache.get(course_id, {})
    
    @classmethod
    def update_enhancement(cls, course_id: str, enhancement_data: Dict[str, Any]):
        """
        Update enhancement for a specific course
        """
        # Ensure cache is loaded
        if not cls._cache:
            cls.load_cache()
        
        # Update the specific course
        cls._cache[course_id] = enhancement_data
        
        # Save updated cache
        cls.save_cache()

def enhance_course_data(course: Course) -> Course:
    """
    Enhance course data with caching mechanism and infinite loop prevention
    """
    # Check if we've already enhanced this course
    cached_enhancement = CourseEnhancementCache.get_enhancement(course.course_id)
    
    if cached_enhancement:
        # Use cached data
        course.skills_taught = cached_enhancement.get('skills_taught', DEFAULT_SKILLS)
        course.career_relevance = cached_enhancement.get('career_relevance', DEFAULT_CAREER_PATHS)
        return course
    
    # No cache hit - use defaults
    if not course.skills_taught:
        course.skills_taught = DEFAULT_SKILLS
    
    if not course.career_relevance:
        course.career_relevance = DEFAULT_CAREER_PATHS
    
    # Update cache with new enhancement
    CourseEnhancementCache.update_enhancement(course.course_id, {
        'skills_taught': course.skills_taught,
        'career_relevance': course.career_relevance
    })
    
    return course


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