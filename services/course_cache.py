from typing import Dict, Any, List, Optional

class CourseRecommendationCache:
    """
    A simple cache for storing and retrieving course recommendations.
    
    This is a basic implementation that can be expanded later.
    """
    _cache: Dict[str, List[Dict[str, Any]]] = {}
    
    @classmethod
    def get_cached_recommendations(cls, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached recommendations for a given key.
        
        Args:
            key (str): The cache key (e.g., career goal or subject)
        
        Returns:
            List of cached recommendations or None if not found
        """
        return cls._cache.get(key)
    
    @classmethod
    def cache_recommendations(cls, key: str, recommendations: List[Dict[str, Any]]):
        """
        Store recommendations in the cache.
        
        Args:
            key (str): The cache key
            recommendations (List[Dict]): Recommendations to store
        """
        cls._cache[key] = recommendations
    
    @classmethod
    def clear_cache(cls):
        """
        Clear the entire cache.
        """
        cls._cache.clear()