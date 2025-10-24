"""
Number Series Prompts for Question Generation
Simple and straightforward prompts for generating number series questions
"""

def get_number_series_system_prompt() -> str:
    """System prompt for number series generation"""
    return """You are an expert in creating Number Series questions for competitive exams like CAT, XAT, SNAP, etc.

Your questions should:
- Test pattern recognition and logical thinking
- Have clear, unambiguous patterns
- Include varied series types (arithmetic, geometric, mixed, squares, cubes, prime-based, etc.)
- Provide detailed solutions with pattern explanation
- Have 4 answer options with only one correct answer

Generate questions in valid JSON format."""


def get_number_series_generation_prompt(
    num_questions: int = 5,
    difficulty_distribution: dict = None
) -> str:
    """
    Generate prompt for number series questions
    
    Args:
        num_questions: Number of questions to generate
        difficulty_distribution: Dict with Easy, Medium, Hard counts
    
    Returns:
        str: Generation prompt
    """
    
    if difficulty_distribution is None:
        difficulty_distribution = {"Easy": 2, "Medium": 2, "Hard": 1}
    
    return f"""Generate {num_questions} Number Series questions with the following distribution:
- Easy: {difficulty_distribution.get('Easy', 0)} questions
- Medium: {difficulty_distribution.get('Medium', 0)} questions  
- Hard: {difficulty_distribution.get('Hard', 0)} questions

**Difficulty Guidelines:**

**Easy:**
- Simple arithmetic progressions (add/subtract constant)
- Basic geometric progressions (multiply/divide by constant)
- Square or cube series
- Alternating simple patterns

**Medium:**
- Combined operations (add then multiply)
- Fibonacci-like series
- Prime number based patterns
- Difference of differences patterns
- Multiple alternating patterns

**Hard:**
- Complex nested patterns
- Three or more interleaved series
- Advanced mathematical relationships
- Patterns involving squares, cubes, and primes together
- Non-obvious logical patterns

**Series Types to Include:**
1. Arithmetic Progression (AP)
2. Geometric Progression (GP)
3. Square/Cube series
4. Prime number series
5. Fibonacci-type series
6. Alternating patterns
7. Difference series
8. Mixed operations

**Question Format:**
Each question should have:
- A series with one missing number (marked with ?)
- 4 answer options
- Clear pattern explanation in solution

**JSON Output Format:**
{{
    "questions": [
        {{
            "question_id": "NS_001",
            "question_text": "Find the missing number in the series: 2, 6, 12, 20, 30, ?",
            "options": {{
                "A": "40",
                "B": "42",
                "C": "44",
                "D": "46"
            }},
            "correct_answer": "B",
            "solution": "The pattern is n(n+1): 1×2=2, 2×3=6, 3×4=12, 4×5=20, 5×6=30, 6×7=42",
            "difficulty": "Easy",
            "topic": "Number Series",
            "subtopic": "Product Pattern"
        }}
    ]
}}

Generate diverse and interesting number series patterns. Ensure all patterns are mathematically sound and unambiguous."""


def get_number_series_validation_prompt(questions: list) -> str:
    """Validation prompt for number series questions"""
    return f"""Validate these {len(questions)} Number Series questions:

Questions: {questions}

Check:
1. Pattern is clear and unambiguous
2. Only one correct answer
3. All options are distinct
4. Solution correctly explains the pattern
5. Difficulty matches the pattern complexity

Return validation results in JSON format."""
