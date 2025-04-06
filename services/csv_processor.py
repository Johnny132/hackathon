import pandas as pd

def load_courses_csv(file_path):
    """
    Load courses directly from the CSV file without any additional processing
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Pandas DataFrame with the raw course data
    """
    try:
        # Try to read with UTF-8 encoding
        df = pd.read_csv(file_path)
    except UnicodeDecodeError:
        # If UTF-8 fails, try with cp1252 encoding (Windows default)
        df = pd.read_csv(file_path, encoding='cp1252')
        
    # Print the columns to verify structure
    print(f"CSV columns: {df.columns.tolist()}")
    print(f"Total courses loaded: {len(df)}")
    
    return df

def recommend_courses(df, career=None, subject=None, max_courses=5):
    """
    Simple function to recommend courses based on career or subject interest.
    Only uses data that's actually in the CSV.
    
    Args:
        df: Pandas DataFrame with course data
        career: Career interest (used to match against title/description)
        subject: Subject interest (used to match against department)
        max_courses: Maximum number of courses to recommend
        
    Returns:
        List of recommended courses with details
    """
    # Make a copy to avoid modifying the original
    courses = df.copy()
    
    # Filter by career interest if provided
    if career and career.strip():
        career_lower = career.lower()
        
        # Try to match career against title or description
        mask = courses['title'].str.lower().str.contains(career_lower, na=False)
        
        # Also check description if available
        if 'description' in courses.columns:
            mask = mask | courses['description'].str.lower().str.contains(career_lower, na=False)
            
        courses = courses[mask]
    
    # Filter by subject interest if provided
    if subject and subject.strip() and 'department' in courses.columns:
        subject_lower = subject.lower()
        courses = courses[courses['department'].str.lower().str.contains(subject_lower, na=False)]
    
    # If no matches, return the first max_courses from the original DataFrame
    if len(courses) == 0:
        courses = df.head(max_courses)
        recommendations = []
        for _, row in courses.iterrows():
            recommendations.append({
                'course_id': row['course_id'],
                'title': row['title'],
                'credits': row.get('credits', 3),
                'reason': "General education requirement"
            })
        return recommendations
    
    # Sort by course_id to get a stable ordering
    courses = courses.sort_values('course_id').head(max_courses)
    
    # Format recommendations
    recommendations = []
    for _, row in courses.iterrows():
        # Create the reason based on available data
        if career and career.strip():
            reason = f"Relevant for {career} career path"
        elif subject and subject.strip():
            reason = f"Matches your interest in {subject}"
        else:
            reason = "General education requirement"
            
        recommendations.append({
            'course_id': row['course_id'],
            'title': row['title'],
            'credits': row.get('credits', 3),
            'reason': reason
        })
    
    return recommendations

def get_all_courses(df, max_courses=100):
    """
    Get a list of all courses in the CSV file
    
    Args:
        df: Pandas DataFrame with course data
        max_courses: Maximum number of courses to return
        
    Returns:
        List of courses with basic details
    """
    courses = []
    
    # Get a sample of courses up to max_courses
    sample_df = df.head(max_courses)
    
    for _, row in sample_df.iterrows():
        courses.append({
            'course_id': row['course_id'],
            'title': row['title'],
            'credits': row.get('credits', 3),
            'department': row.get('department', ''),
            'level': row.get('level', '')
        })
    
    return courses

# Example usage
if __name__ == "__main__":
    # Load courses from CSV
    courses_df = load_courses_csv("courses.csv")
    
    # Print some example courses
    print("\nSample courses:")
    for _, row in courses_df.head(5).iterrows():
        print(f"{row['course_id']}: {row['title']}")
    
    # Get recommendations for a Computer Science student
    cs_recommendations = recommend_courses(courses_df, career="Computer Science")
    
    # Print recommendations
    print("\nRecommended Computer Science courses:")
    for rec in cs_recommendations:
        print(f"{rec['course_id']}: {rec['title']} ({rec['credits']} credits)")
        print(f"   Reason: {rec['reason']}")
        print()