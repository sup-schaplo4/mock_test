"""
Quadratic Equations Prompts for Question Generation
Simple and straightforward prompts for generating quadratic equation questions
"""

def get_quadratic_system_prompt() -> str:
    """System prompt for quadratic equations generation"""
    return """You are an expert in creating Quadratic Equations questions for competitive exams like CAT, XAT, SNAP, etc.

Your questions should:
- Test understanding of quadratic equations, roots, and relationships
- Cover factorization, discriminant, sum/product of roots, and word problems
- Include varied question types
- Provide detailed step-by-step solutions
- Have 4 answer options with only one correct answer

Generate questions in valid JSON format."""


def get_quadratic_generation_prompt(
    num_questions: int = 5,
    difficulty_distribution: dict = None
) -> str:
    """
    Generate prompt for quadratic equation questions
    
    Args:
        num_questions: Number of questions to generate
        difficulty_distribution: Dict with Easy, Medium, Hard counts
    
    Returns:
        str: Generation prompt
    """
    
    if difficulty_distribution is None:
        difficulty_distribution = {"Easy": 2, "Medium": 2, "Hard": 1}
    
    return f"""Generate {num_questions} Quadratic Equations questions with the following distribution:
- Easy: {difficulty_distribution.get('Easy', 0)} questions
- Medium: {difficulty_distribution.get('Medium', 0)} questions
- Hard: {difficulty_distribution.get('Hard', 0)} questions

**Difficulty Guidelines:**

**Easy:**
- Simple factorization: x² + 5x + 6 = 0
- Finding roots by factoring
- Sum or product of roots (straightforward)
- Basic discriminant questions
- Simple substitution in formulas

**Medium:**
- Equations requiring formula method
- Relationship between roots (one root is twice the other, etc.)
- Nature of roots based on discriminant
- Forming equations from given roots
- Word problems with quadratic applications
- Equations with parameters

**Hard:**
- Complex relationships between roots
- System of quadratic equations
- Conditions on coefficients for specific root relationships
- Advanced word problems
- Roots with multiple constraints
- Maximum/minimum value problems

**Question Types to Include:**
1. Solve quadratic equations
2. Find sum/product of roots
3. Nature of roots (real, equal, imaginary)
4. Form equation from given roots
5. Find relationship between roots
6. Discriminant-based questions
7. Word problems (age, motion, area, etc.)
8. Maximum/minimum value problems
9. Roots with conditions (one root = k times other)
10. Parameter-based questions

**JSON Output Format:**
{{
    "questions": [
        {{
            "question_id": "QE_001",
            "question_text": "Find the sum of roots of the equation 2x² - 7x + 3 = 0",
            "options": {{
                "A": "3.5",
                "B": "7",
                "C": "1.5",
                "D": "2"
            }},
            "correct_answer": "A",
            "solution": "For equation ax² + bx + c = 0, sum of roots = -b/a. Here a=2, b=-7, so sum = -(-7)/2 = 7/2 = 3.5",
            "difficulty": "Easy",
            "topic": "Quadratic Equations",
            "subtopic": "Sum of Roots"
        }}
    ]
}}

Ensure variety in question types and concepts. All calculations should be accurate."""


def get_quadratic_validation_prompt(questions: list) -> str:
    """Validation prompt for quadratic equation questions"""
    return f"""Validate these {len(questions)} Quadratic Equations questions:

Questions: {questions}

Check:
1. Mathematical accuracy of equation and solution
2. Only one correct answer
3. All options are distinct and reasonable
4. Solution shows clear step-by-step working
5. Difficulty matches the complexity
6. Discriminant calculations are correct (if applicable)

Return validation results in JSON format."""
