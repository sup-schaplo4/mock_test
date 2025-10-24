"""
Arithmetic Question Generation Prompts
Clean and simple prompts for 8 arithmetic topics
"""

from typing import Dict, List, Optional

# ============================================================================
# ARITHMETIC TOPICS
# ============================================================================

ARITHMETIC_TOPICS = [
    "Percentage",
    "Profit, Loss & Discount",
    "Simple & Compound Interest",
    "Ratio & Proportion",
    "Time, Speed & Distance",
    "Time & Work",
    "Averages",
    "Mixtures & Alligations"
]

# ============================================================================
# SYSTEM PROMPT
# ============================================================================

def get_arithmetic_system_prompt() -> str:
    """Get system prompt for arithmetic question generation"""
    
    return """You are an expert at creating high-quality Quantitative Aptitude questions for banking exams (RBI Grade B, SBI PO, IBPS PO).

Your expertise:
- Creating questions with precise calculations
- Designing realistic word problems
- Crafting plausible distractors based on common errors
- Writing clear, step-by-step explanations
- Following exam patterns and difficulty levels

Generate questions that:
✅ Have exactly 5 options (A, B, C, D, E)
✅ Have only ONE correct answer
✅ Include complete explanations with calculations
✅ Use realistic numbers (avoid overly complex decimals)
✅ Match the specified difficulty level
✅ Are solvable within 60-120 seconds

Return output in valid JSON format only."""


# ============================================================================
# MAIN GENERATION PROMPT
# ============================================================================

def get_arithmetic_generation_prompt(
    topic: str,
    num_questions: int = 15,
    difficulty_distribution: Dict[str, int] = None
) -> str:
    """
    Generate prompt for arithmetic questions
    
    Args:
        topic: Arithmetic topic name
        num_questions: Number of questions to generate (default: 15)
        difficulty_distribution: Dict with Easy, Medium, Hard counts
    
    Returns:
        str: Complete generation prompt
    """
    
    if difficulty_distribution is None:
        difficulty_distribution = {
            "Easy": 3,
            "Medium": 6,
            "Hard": 6
        }
    
    prompt = f"""Generate {num_questions} high-quality {topic} questions for RBI Grade B Phase 1 exam.

**Topic: {topic}**

**Difficulty Distribution:**
- Easy: {difficulty_distribution['Easy']} questions (direct formula application, 1-2 steps)
- Medium: {difficulty_distribution['Medium']} questions (2-3 steps, standard variations)
- Hard: {difficulty_distribution['Hard']} questions (multi-step, tricky scenarios)

**Requirements:**

1. **Question Quality:**
   - Realistic scenarios relevant to banking/business context
   - Clear and unambiguous wording
   - Solvable within 60-120 seconds
   - Use practical numbers (avoid unnecessary decimals)

2. **Options (A, B, C, D, E):**
   - Exactly 5 options for each question
   - Only ONE correct answer
   - Distractors based on common calculation errors:
     * Wrong formula application
     * Calculation mistakes
     * Unit conversion errors
     * Sign errors (+ instead of -)
   - Options should be reasonably close to correct answer

3. **Explanations:**
   - Step-by-step solution
   - Show all calculations clearly
   - Mention the formula used
   - Explain why the answer is correct

4. **Variety:**
   - Cover different sub-concepts within {topic}
   - Vary the question formats
   - Use different numerical ranges
   - Include both straightforward and tricky questions

**JSON Output Format:**

```json
[
  {{
    "question_id": "ARITH_{topic.upper().replace(' ', '_').replace(',', '').replace('&', '')}_001",
    "question": "Question text here...",
    "options": {{
      "A": "Option A value",
      "B": "Option B value",
      "C": "Option C value",
      "D": "Option D value",
      "E": "Option E value"
    }},
    "correct_answer": "C",
    "explanation": "Step-by-step solution with calculations...",
    "difficulty": "Medium",
    "topic": "{topic}",
    "sub_topic": "Specific sub-concept",
    "concept_tags": ["tag1", "tag2"],
    "main_category": "Quantitative Aptitude",
    "subject": "Arithmetic",
    "exam": "RBI Grade B Phase 1",
    "metadata": {{
      "generated_by": "gpt-4o",
      "generation_date": "2025-10-05",
      "reviewed": false,
      "estimated_time": "90 seconds"
    }}
  }}
]
Generate all {num_questions} questions following this exact format. Return ONLY the JSON array, no additional text."""

    # Add topic-specific guidelines
    topic_guidelines = get_topic_specific_guidelines(topic)
    if topic_guidelines:
        prompt += f"\n\n**Topic-Specific Guidelines:**\n{topic_guidelines}"

    return prompt

#============================================================================
#TOPIC-SPECIFIC GUIDELINES
#============================================================================

def get_topic_specific_guidelines(topic: str) -> str: 
    """Get specific guidelines for each arithmetic topic"""

    guidelines = {
    "Percentage": """
                    Basic percentage calculations (finding %, of a number)
                    Percentage increase/decrease
                    Successive percentage changes
                    Percentage point difference
                    Reverse percentage problems
                    Comparison of percentages """,
  "Profit, Loss & Discount": """
                    Basic profit/loss calculations (CP, SP, Profit%, Loss%)
                    Marked price and discount
                    Successive discounts
                    Dishonest dealer problems
                    Profit/loss with GST or tax
                    Break-even analysis """,
  "Simple & Compound Interest": """
                    Simple Interest (SI = PRT/100)
                    Compound Interest (annual, half-yearly, quarterly)
                    Difference between CI and SI
                    Finding principal, rate, or time
                    Compound interest with different compounding frequencies
                    Installment problems """,
  "Ratio & Proportion": """
                    Simple ratios and proportions
                    Ratio comparisons
                    Dividing amounts in given ratios
                    Fourth proportional
                    Mean proportional
                    Compound ratios
                    Age-based ratio problems """,
  "Time, Speed & Distance": """
                    Basic speed-distance-time problems
                    Relative speed (same/opposite direction)
                    Average speed
                    Train problems (crossing platforms, poles, other trains)
                    Boat and stream problems
                    Races and games """,
  "Time & Work": """
                    Work done by individuals/groups
                    Work efficiency comparisons
                    Pipes and cisterns
                    Work and wages
                    Alternate day work problems
                    Negative work (pipes emptying) """,
  "Averages": """
                    Simple average calculations
                    Weighted averages
                    Average of consecutive numbers
                    Average speed/age problems
                    Effect of adding/removing values
                    Average income/expenditure problems """,
  "Mixtures & Alligations": """
                    Basic mixture problems
                    Alligation method
                    Replacing mixtures
                    Repeated dilution
                    Mixing different quantities
                    Cost price mixture problems """ } 
    
    return guidelines.get(topic, "")

#============================================================================
#INDIVIDUAL TOPIC PROMPTS (Convenience Functions)
#============================================================================

def get_percentage_prompt(num_questions: int = 15) -> str: 
    """Get prompt for Percentage questions""" 
    return get_arithmetic_generation_prompt("Percentage", num_questions)

def get_profit_loss_prompt(num_questions: int = 15) -> str: 
    """Get prompt for Profit, Loss & Discount questions""" 
    return get_arithmetic_generation_prompt("Profit, Loss & Discount", num_questions)

def get_interest_prompt(num_questions: int = 15) -> str: 
    """Get prompt for Simple & Compound Interest questions""" 
    return get_arithmetic_generation_prompt("Simple & Compound Interest", num_questions)

def get_ratio_proportion_prompt(num_questions: int = 15) -> str: 
    """Get prompt for Ratio & Proportion questions""" 
    return get_arithmetic_generation_prompt("Ratio & Proportion", num_questions)

def get_time_speed_distance_prompt(num_questions: int = 15) -> str: 
    """Get prompt for Time, Speed & Distance questions""" 
    return get_arithmetic_generation_prompt("Time, Speed & Distance", num_questions)

def get_time_work_prompt(num_questions: int = 15) -> str: 
    """Get prompt for Time & Work questions""" 
    return get_arithmetic_generation_prompt("Time & Work", num_questions)

def get_averages_prompt(num_questions: int = 15) -> str: 
    """Get prompt for Averages questions""" 
    return get_arithmetic_generation_prompt("Averages", num_questions)

def get_mixtures_prompt(num_questions: int = 15) -> str: 
    """Get prompt for Mixtures & Alligations questions""" 
    return get_arithmetic_generation_prompt("Mixtures & Alligations", num_questions)


#============================================================================
#VALIDATION PROMPT
#============================================================================

def get_arithmetic_validation_prompt(questions: List[Dict]) -> str: 
    """Generate validation prompt for arithmetic questions"""

    return f"""Review and validate the following arithmetic questions for quality and correctness.
            Questions to Review:

            {questions}
            Check for:

            ✅ Calculation accuracy (verify all math)
            ✅ Correct answer is actually correct
            ✅ All 5 options are present and unique
            ✅ Distractors are plausible
            ✅ Explanation is clear and complete
            ✅ Difficulty level matches question complexity
            ✅ Question is clear and unambiguous
            ✅ Realistic numbers and scenarios
            
            Return:
            {{
                "valid_questions": [...],  // Questions that passed validation
                "invalid_questions": [     // Questions with issues
                    {{
                    "question_id": "...",
                    "issues": ["issue1", "issue2"],
                    "suggested_fix": "..."
                    }}
                ],
                "overall_quality": "Good/Fair/Poor",
                "recommendations": ["..."]
                }}
                ```"""
    
# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_arithmetic_topics() -> List[str]:
    """Get list of all arithmetic topics"""
    return ARITHMETIC_TOPICS.copy()


def get_topic_info() -> Dict[str, any]:
    """Get information about arithmetic prompt system"""
    
    return {
        "topics": ARITHMETIC_TOPICS,
        "default_questions_per_topic": 15,
        "default_difficulty_distribution": {
            "Easy": 3,
            "Medium": 6,
            "Hard": 6
        },
        "available_functions": [
            "get_arithmetic_generation_prompt",
            "get_arithmetic_system_prompt",
            "get_arithmetic_validation_prompt"
        ],
        "topic_specific_functions": [
            "get_percentage_prompt",
            "get_profit_loss_prompt",
            "get_interest_prompt",
            "get_ratio_proportion_prompt",
            "get_time_speed_distance_prompt",
            "get_time_work_prompt",
            "get_averages_prompt",
            "get_mixtures_prompt"
        ]
    }


# ============================================================================
# END OF ARITHMETIC PROMPTS
# ============================================================================

if __name__ == "__main__":
    print("✅ arithmetic_prompts.py loaded successfully")
    print(f"📚 Available Topics: {len(ARITHMETIC_TOPICS)} topics")
    print("\n💡 Topics:")
    for idx, topic in enumerate(ARITHMETIC_TOPICS, 1):
        print(f"   {idx}. {topic}")
    print("\n💡 Main function: get_arithmetic_generation_prompt(topic, num_questions)")
