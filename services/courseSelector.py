from typing import List, Dict, Set, Optional, Tuple
from models.base import Course
from models.student import StudentProfile
import json
from services.AIProcessor import AIProcessor
import requests

class CourseSelector:
    def __init__(self):
        self.courses: Dict[str, Course] = {}
        self.career_goal_mapping: Dict[str, Set[str]] = {}
        self.subject_mapping: Dict[str, Set[str]] = {}

    # Add this to your CourseSelector class in services/courseSelector.py

    def analyze_course_relevance_with_ai(self, courses, user_interest):
        """Use AI to analyze and score courses based on relevance to user interest"""
        ai_processor = AIProcessor(model="llama3:latest")
        
        # Prepare the prompt for analyzing relevance
        prompt = f"""
        I need to find courses relevant to a student interested in {user_interest}.
        
        Here are some courses to analyze. For each course, rate its relevance to {user_interest} on a scale of 0-10, 
        where 10 is extremely relevant and 0 is not relevant at all.
        
        Provide your response as a JSON array of objects with course_id and relevance_score fields:
        
        Courses to analyze:
        """
        
        # Add course details to the prompt (limit to 10-15 courses for efficiency)
        sample_courses = courses[:15] if len(courses) > 15 else courses
        for i, course in enumerate(sample_courses):
            prompt += f"""
            {i+1}. {course.course_id}: {course.title}
            Department: {course.department}
            Level: {course.level}
            Description: {course.description}
            Skills: {', '.join(course.skills_taught) if course.skills_taught else "None"}
            Career relevance: {', '.join(course.career_relevance) if course.career_relevance else "None"}
            
            """
        
        # Call the AI to analyze the courses
        data = {
            "model": ai_processor.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }
        
        try:
            response = requests.post(ai_processor.generate_url, json=data, timeout=60)
            response.raise_for_status()
            response_data = response.json()
            content = response_data.get('response', '{}')
            
            # Extract the JSON from the response
            import re
            json_pattern = r'\[.*\]'
            match = re.search(json_pattern, content, re.DOTALL)
            if not match:
                print("Failed to extract JSON from AI response")
                return []
                
            json_content = match.group(0)
            try:
                relevance_scores = json.loads(json_content)
                
                # Map the scores back to the courses
                scored_courses = []
                for score_item in relevance_scores:
                    course_id = score_item.get('course_id')
                    relevance_score = score_item.get('relevance_score', 0)
                    
                    # Find the matching course
                    for course in courses:
                        if course.course_id == course_id:
                            scored_courses.append((course, relevance_score))
                            break
                
                # Sort by relevance score
                scored_courses.sort(key=lambda x: x[1], reverse=True)
                return scored_courses
                
            except json.JSONDecodeError:
                print("Failed to parse AI response as JSON")
                return []
        
        except Exception as e:
            print(f"Error in AI course analysis: {e}")
            return []

    def get_candidate_courses_for_interest(self, interest):
        """Get a smaller set of potential relevant courses for AI analysis"""
        candidates = []
        interest_lower = interest.lower()
        
        # Initial filtering based on simple rules
        for course in self.courses.values():
            # Check department, title, and description for matches
            if (interest_lower in course.department.lower() or
                interest_lower in course.title.lower() or
                any(interest_lower in skill.lower() for skill in course.skills_taught) or
                any(interest_lower in career.lower() for career in course.career_relevance)):
                candidates.append(course)
        
        # If we don't have enough candidates, add some broader matches
        if len(candidates) < 15:
            for course in self.courses.values():
                if course not in candidates and interest_lower in course.description.lower():
                    candidates.append(course)
                    if len(candidates) >= 20:
                        break
    
    def add_course(self, course: Course):
        """Add a course to the catalog and update mappings"""
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
            
            # Update subject mapping
            if course.skills_taught:
                for skill in course.skills_taught:
                    skill_key = skill.lower().strip()
                    if skill_key:
                        if skill_key not in self.subject_mapping:
                            self.subject_mapping[skill_key] = set()
                        self.subject_mapping[skill_key].add(course.course_id)

    def _match_career_goals(self, career_goals: List[str]) -> Set[str]:
        """Find course IDs matching career goals"""
        matching_courses = set()
        
        for goal in career_goals:
            goal_lower = goal.lower().strip()
            
            # Direct matching
            if goal_lower in self.career_goal_mapping:
                matching_courses.update(self.career_goal_mapping[goal_lower])
            
            # Partial matching
            for mapped_goal, course_ids in self.career_goal_mapping.items():
                if goal_lower in mapped_goal or mapped_goal in goal_lower:
                    matching_courses.update(course_ids)
            
            # Additional matching through course objects directly
            for course_id, course in self.courses.items():
                if any(goal_lower in career.lower() for career in course.career_relevance):
                    matching_courses.add(course_id)
        
        return matching_courses

    def _match_preferred_subjects(self, preferred_subjects: List[str]) -> Set[str]:
        """Find course IDs matching preferred subjects with better keyword matching"""
        matching_courses = set()
        
        # Create a mapping of common subjects to related keywords
        subject_keywords = {
    'business': ['business', 'management', 'marketing', 'finance', 'accounting', 
                 'economics', 'entrepreneurship', 'commerce', 'strategy', 'leadership'],
    'computer science': ['programming', 'software', 'algorithm', 'data structure', 
                         'coding', 'development', 'computation', 'computer systems', 'networking'],
    'data science': ['data', 'statistics', 'analysis', 'machine learning', 
                     'analytics', 'visualization', 'data mining', 'big data', 'AI'],
    'mathematics': ['calculus', 'algebra', 'geometry', 'trigonometry', 
                    'probability', 'statistics', 'mathematical reasoning', 'number theory'],
    'physics': ['mechanics', 'optics', 'thermodynamics', 'quantum mechanics', 
                'relativity', 'astrophysics', 'electrodynamics', 'nuclear physics'],
    'biology': ['genetics', 'evolution', 'molecular biology', 'cell biology', 
                'ecology', 'anatomy', 'physiology', 'biochemistry'],
    'chemistry': ['organic chemistry', 'inorganic chemistry', 'biochemistry', 
                  'physical chemistry', 'chemical engineering', 'laboratory techniques'],
    'history': ['ancient history', 'modern history', 'world wars', 'cultural history', 
                'political history', 'economic history', 'historical analysis'],
    'psychology': ['cognitive psychology', 'behavioral science', 'mental health', 
                   'neuroscience', 'developmental psychology', 'personality psychology'],
    'engineering': ['civil engineering', 'mechanical engineering', 
                    'electrical engineering', 'chemical engineering', 'robotics', 'design'],
    'music': ['music theory', 'notation', 'composition', 'performance', 
              'classical music', 'instrumentation', 'genres', 'orchestration'],
    'philosophy': ['ethics', 'logic', 'epistemology', 'metaphysics', 
                   'existentialism', 'aesthetics', 'philosophical analysis'],
    'art': ['painting', 'sculpture', 'digital art', 'art history', 
            'visual arts', 'design', 'illustration'],
    'astronomy': ['stars', 'galaxies', 'cosmology', 'telescopes', 
                  'space exploration', 'astrophysics', 'solar system', 'black holes']
}

        
        for subject in preferred_subjects:
            subject_lower = subject.lower().strip()
            
            # Direct matching in subject mappings
            if subject_lower in self.subject_mapping:
                matching_courses.update(self.subject_mapping[subject_lower])
            
            # Use expanded keywords for better matching
            if subject_lower in subject_keywords:
                keywords = subject_keywords[subject_lower]
                for keyword in keywords:
                    # Match in title
                    for course_id, course in self.courses.items():
                        if (keyword in course.title.lower() or 
                            keyword in course.department.lower() or
                            keyword in course.description.lower()):
                            matching_courses.add(course_id)
            
            # Partial matching in existing mappings
            for mapped_subject, course_ids in self.subject_mapping.items():
                if subject_lower in mapped_subject or mapped_subject in subject_lower:
                    matching_courses.update(course_ids)
        
        return matching_courses

    def rank_courses_by_relevance(self, 
                                 courses: List[Course], 
                                 career_goals: List[str], 
                                 preferred_subjects: List[str]) -> List[Tuple[Course, float]]:
        """Rank courses by relevance to career goals and subjects"""
        # Get matching course IDs
        career_matched = self._match_career_goals(career_goals)
        subject_matched = self._match_preferred_subjects(preferred_subjects)
        
        # Score and rank courses
        ranked_courses = []
        for course in courses:
            score = 0
            
            # Career goal relevance (higher weight)
            if course.course_id in career_matched:
                score += 5
            
            # Subject relevance 
            if course.course_id in subject_matched:
                score += 3
            
            # Level-based bonus (higher level = more specialized)
            score += min(course.level / 100, 4) / 2
            
            # Only include courses with meaningful scores
            if score > 0:
                ranked_courses.append((course, score))
        
        # Sort by score in descending order
        ranked_courses.sort(key=lambda x: x[1], reverse=True)
        return ranked_courses
    
    def recommend_courses(self, 
                        career_goals=None, 
                        preferred_subjects=None, 
                        completed_courses=None, 
                        current_semester=1,
                        enrollment_status='Full-time',
                        min_credits=12,
                        max_credits=18,
                        max_recommendations=5):
        """Generate course recommendations with better fallback mechanism"""
        if career_goals is None:
            career_goals = []
        if preferred_subjects is None:
            preferred_subjects = []
        if completed_courses is None:
            completed_courses = []
            
        # Get all courses
        all_courses = list(self.courses.values())
        
        # Filter out completed courses
        eligible_courses = [c for c in all_courses if c.course_id not in completed_courses]
        
        # Rank by relevance
        ranked_courses = self.rank_courses_by_relevance(
            eligible_courses, career_goals, preferred_subjects
        )
        
        # If we don't have enough relevant courses, implement a fallback strategy
        if len(ranked_courses) < max_recommendations:
            print(f"Not enough relevant courses found, using fallback strategy")
            
            # First try: Look for courses with department names matching subjects
            if preferred_subjects:
                for course in eligible_courses:
                    # Check if course isn't already in our recommendations
                    if not any(course.course_id == rc[0].course_id for rc in ranked_courses):
                        for subject in preferred_subjects:
                            if subject.lower() in course.department.lower():
                                # Add with a lower score but still relevant
                                ranked_courses.append((course, 1.0))
            
            # Second fallback: Add some introductory courses for the subject
            if preferred_subjects and len(ranked_courses) < max_recommendations:
                for course in eligible_courses:
                    if not any(course.course_id == rc[0].course_id for rc in ranked_courses):
                        # Look for intro courses (usually 100-level)
                        if course.level <= 200:
                            for subject in preferred_subjects:
                                if subject.lower() in course.title.lower():
                                    ranked_courses.append((course, 0.5))
        
        # Re-sort with any new additions
        ranked_courses.sort(key=lambda x: x[1], reverse=True)
        
        # Format recommendations
        recommendations = []
        total_credits = 0
        
        for course, score in ranked_courses:
            # Check if adding this course would exceed max credits
            if total_credits + course.credits > max_credits:
                continue
                
            # Generate reason based on score components
            reason = self._generate_recommendation_reason(
                course, career_goals, preferred_subjects
            )
            
            recommendations.append({
                'course_id': course.course_id,
                'title': course.title,
                'credits': course.credits,
                'reason': reason
            })
            
            total_credits += course.credits
            
            # Stop once we have enough recommendations
            if len(recommendations) >= max_recommendations:
                break
        
        return recommendations
    

    def _generate_recommendation_reason(self, course, career_goals, preferred_subjects):
        """Generate a more specific personalized reason for recommendations"""
        reasons = []
        
        # For business specifically
        if any(subject.lower() == 'business' for subject in preferred_subjects):
            if 'business' in course.department.lower():
                reasons.append(f"Core business course that will help build your foundation in business")
            elif any('business' in skill.lower() for skill in course.skills_taught):
                reasons.append(f"Teaches business skills that will be valuable for your minor")
            elif any('business' in career.lower() for career in course.career_relevance):
                reasons.append(f"Relevant for business career paths")
        
        # Career goal match
        for goal in career_goals:
            if any(goal.lower() in cr.lower() for cr in course.career_relevance):
                reasons.append(f"Aligns with your {goal} career goal")
                break
        
        # Subject match
        for subject in preferred_subjects:
            if subject.lower() in course.title.lower():
                reasons.append(f"Directly covers {subject} which you're interested in")
                break
            elif any(subject.lower() in skill.lower() for skill in course.skills_taught):
                reasons.append(f"Teaches skills in {subject} which match your interests")
                break
        
        # Default reason if no specific matches
        if not reasons:
            # Better default reason
            if course.level < 200:
                reasons.append("This introductory course provides a strong foundation")
            elif course.level < 300:
                reasons.append("This intermediate course develops important skills")
            else:
                reasons.append("This advanced course explores specialized topics")
        
        return " and ".join(reasons) + "."