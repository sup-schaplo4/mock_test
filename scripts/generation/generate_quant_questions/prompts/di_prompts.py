"""
Data Interpretation Prompts
============================

This module contains all prompt templates for generating Data Interpretation (DI) questions
for RBI Grade B Phase 1 exam.

Available DI Types:
    - Table
    - Bar Chart
    - Line Chart
    - Pie Chart
    - Mixed Charts
    - Caselet
"""

from typing import Dict, List, Optional

# ============================================================================
# DI TYPES AND TOPICS
# ============================================================================

DI_TYPES = [
    "Table",
    "Bar Chart", 
    "Line Chart",
    "Pie Chart",
    "Mixed Charts",
    "Caselet"
]

DI_TOPICS = [
    "Sales & Revenue Analysis",
    "Population & Demographics",
    "Production & Manufacturing",
    "Import & Export",
    "Budget & Expenditure",
    "Profit & Loss Analysis",
    "Market Share Analysis",
    "Employee & HR Statistics",
    "Agriculture & Crop Production",
    "Banking & Finance",
    "Education Statistics",
    "Healthcare Data",
    "Transportation & Logistics",
    "Energy & Power",
    "Sports Statistics"
]

# ============================================================================
# SYSTEM PROMPT
# ============================================================================

def get_di_system_prompt() -> str:
    """
    Get the system prompt for DI generation
    
    Returns:
        str: System prompt for OpenAI API
    """
    
    return """You are an expert question generator for Data Interpretation (DI) sets for the RBI Grade B Phase 1 examination.

Your expertise includes:
- Creating realistic and exam-relevant data scenarios
- Designing tables, charts, and caselets with appropriate complexity
- Crafting questions that test analytical and calculation skills
- Ensuring questions are solvable within 2-3 minutes each
- Following RBI Grade B difficulty standards and patterns

Key Requirements:
1. Data must be realistic and internally consistent
2. Questions should require 2-3 calculation steps
3. Difficulty should match the specified level (Easy/Medium/Hard)
4. All calculations must be verifiable
5. Options should be plausible but distinct
6. Explanations must show complete solution steps

Output Format:
- Always respond with valid JSON only
- No additional text or explanations outside JSON
- Follow the exact schema provided in the prompt"""


# ============================================================================
# MAIN DI GENERATION PROMPT
# ============================================================================

def get_di_generation_prompt(
    di_type: str,
    topic: str,
    difficulty: str,
    num_questions: int = 5,
    additional_instructions: Optional[str] = None
) -> str:
    """
    Generate the main prompt for DI set creation
    
    Args:
        di_type: Type of DI (Table, Bar Chart, etc.)
        topic: Topic/theme for the DI set
        difficulty: Difficulty level (Easy, Medium, Hard)
        num_questions: Number of questions to generate (default: 5)
        additional_instructions: Optional additional requirements
    
    Returns:
        str: Complete prompt for DI generation
    """
    
    # Get specific instructions based on DI type
    type_instructions = _get_type_specific_instructions(di_type)
    
    # Get difficulty-specific guidelines
    difficulty_guidelines = _get_difficulty_guidelines(difficulty)
    
    # Build the prompt
    prompt = f"""Generate a Data Interpretation (DI) set for RBI Grade B Phase 1 exam.

**Specifications:**
- DI Type: {di_type}
- Topic: {topic}
- Difficulty: {difficulty}
- Number of Questions: {num_questions}

**Data Source Requirements:**
{type_instructions}

**Difficulty Guidelines ({difficulty}):**
{difficulty_guidelines}

**Question Requirements:**
1. Each question should be solvable in 2-3 minutes
2. Questions should test different aspects of the data
3. Include a mix of:
   - Direct value questions (20%)
   - Percentage/ratio questions (40%)
   - Comparison questions (20%)
   - Complex calculation questions (20%)
4. All calculations must be accurate and verifiable
5. Avoid questions that are too similar to each other

**Options Guidelines:**
- Provide exactly 5 options (A, B, C, D, E)
- Options should be distinct and plausible
- Include common calculation errors as distractors
- Ensure only one option is unambiguously correct
- Format numbers consistently (use commas for thousands when appropriate)

**Explanation Requirements:**
- Show step-by-step calculations
- Explain the reasoning clearly
- Highlight key data points used
- Calculate the final answer explicitly
- Keep explanations concise but complete (50-150 words)
"""

    if additional_instructions:
        prompt += f"\n**Additional Instructions:**\n{additional_instructions}\n"

    # Add JSON schema
    prompt += _get_di_json_schema(di_type, num_questions)
    
    return prompt


# ============================================================================
# TYPE-SPECIFIC INSTRUCTIONS
# ============================================================================

def _get_type_specific_instructions(di_type: str) -> str:
    """Get specific instructions based on DI type"""
    
    instructions = {
        "Table": """
Create a well-structured table with:
- 4-6 columns (including row headers)
- 5-8 rows of data
- Clear column headers with units (if applicable)
- Realistic and consistent numerical data
- A descriptive title
- Data should allow for multiple calculation types

Example structure:
{
  "type": "table",
  "title": "Production of Widgets by Company (2019-2023)",
  "data": {
    "headers": ["Year", "Company A", "Company B", "Company C", "Company D"],
    "rows": [
      ["2019", "450", "380", "520", "410"],
      ["2020", "480", "420", "540", "450"],
      ...
    ]
  },
  "units": "in thousands"
}
""",
        
        "Bar Chart": """
Create a bar chart with:
- 2-3 groups/categories
- 4-6 bars per group
- Clear axis labels
- Descriptive title
- Values that allow meaningful comparisons

Example structure:
{
  "type": "bar_chart",
  "title": "Sales Revenue by Product Category (Q1-Q4)",
  "data": {
    "categories": ["Q1", "Q2", "Q3", "Q4"],
    "series": [
      {
        "name": "Electronics",
        "values": [450, 520, 480, 610]
      },
      {
        "name": "Clothing",
        "values": [380, 420, 450, 520]
      }
    ]
  },
  "units": "Revenue in Lakhs (₹)"
}
""",
        
        "Line Chart": """
Create a line chart showing trends with:
- 2-4 lines (series)
- 5-8 data points per line
- Clear time periods or sequential categories
- Descriptive title and axis labels
- Data showing meaningful trends (increasing, decreasing, fluctuating)

Example structure:
{
  "type": "line_chart",
  "title": "Monthly Profit Trend for Three Branches (Jan-Aug)",
  "data": {
    "x_axis": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
    "series": [
      {
        "name": "Branch A",
        "values": [45, 52, 48, 55, 60, 58, 65, 70]
      },
      {
        "name": "Branch B",
        "values": [38, 42, 45, 43, 50, 52, 55, 58]
      }
    ]
  },
  "units": "Profit in Thousands (₹)"
}
""",
        
        "Pie Chart": """
Create a pie chart with:
- 5-8 segments
- Percentages that sum to 100%
- Clear segment labels
- Descriptive title
- Optional: provide absolute values alongside percentages

Example structure:
{
  "type": "pie_chart",
  "title": "Market Share of Smartphone Brands in 2023",
  "data": {
    "segments": [
      {"label": "Brand A", "percentage": 28, "value": 560},
      {"label": "Brand B", "percentage": 22, "value": 440},
      {"label": "Brand C", "percentage": 18, "value": 360},
      {"label": "Brand D", "percentage": 15, "value": 300},
      {"label": "Others", "percentage": 17, "value": 340}
    ]
  },
  "total": 2000,
  "units": "Units Sold (in thousands)"
}
""",
        
        "Mixed Charts": """
Create a combination of 2-3 different chart types with:
- Related but distinct datasets
- Common theme or context
- Clear labels for each chart
- Data that allows cross-chart analysis

Example structure:
{
  "type": "mixed_charts",
  "title": "Company Performance Analysis (2023)",
  "charts": [
    {
      "type": "bar_chart",
      "title": "Quarterly Revenue",
      "data": {...}
    },
    {
      "type": "pie_chart",
      "title": "Expense Breakdown",
      "data": {...}
    }
  ]
}
""",
        
        "Caselet": """
Create a textual caselet with:
- 150-250 words of descriptive text
- 8-12 specific numerical data points embedded in the text
- Clear context and scenario
- Information about multiple entities/categories
- Data relationships that enable various calculations

Example structure:
{
  "type": "caselet",
  "title": "ABC Corporation Performance Report",
  "text": "ABC Corporation operates three manufacturing plants located in Delhi, Mumbai, and Bangalore. In the financial year 2023, the Delhi plant produced 45,000 units with a production cost of ₹450 per unit and selling price of ₹620 per unit. The Mumbai plant manufactured 38,000 units at ₹480 per unit and sold them at ₹640 per unit. The Bangalore plant had the highest production of 52,000 units with costs of ₹420 per unit and selling price of ₹600 per unit. The company's total administrative expenses were ₹85 lakhs, distributed equally among the three plants. Additionally, the company spent 8% of its total revenue on marketing activities..."
}
"""
    }
    
    return instructions.get(di_type, instructions["Table"])


# ============================================================================
# DIFFICULTY GUIDELINES
# ============================================================================

def _get_difficulty_guidelines(difficulty: str) -> str:
    """Get difficulty-specific guidelines"""
    
    guidelines = {
        "Easy": """
- Questions should require 1-2 simple calculation steps
- Direct reading from data (30-40% of questions)
- Simple percentage calculations
- Basic comparisons and differences
- Straightforward ratios
- Minimal complex arithmetic
- Clear and obvious solution paths
Example: "What is the total production in 2020?" or "Which company had the highest sales in Q3?"
""",
        
        "Medium": """
- Questions require 2-3 calculation steps
- Percentage increase/decrease calculations
- Average and ratio problems
- Multiple data point comparisons
- Some analytical thinking required
- Mix of direct and derived values
- May involve one level of inference
Example: "What is the percentage increase in revenue from 2020 to 2023?" or "What is the ratio of Product A sales to Product B sales in 2022?"
""",
        
        "Hard": """
- Questions require 3-4 calculation steps
- Complex percentage problems (percentage of percentage)
- Weighted averages
- Multiple ratios and proportions
- Cross-referencing multiple data points
- Analytical reasoning required
- May involve compound calculations
- Time-consuming but solvable in 2-3 minutes
Example: "If the company increases production by 15% next year while maintaining the same cost structure, what will be the percentage change in profit?" or "What is the compound annual growth rate (CAGR) over the period?"
"""
    }
    
    return guidelines.get(difficulty, guidelines["Medium"])


# ============================================================================
# JSON SCHEMA
# ============================================================================

def _get_di_json_schema(di_type: str, num_questions: int) -> str:
    """Get the JSON schema for the response"""
    
    schema = f"""
**Output Format (JSON):**

Return ONLY a valid JSON object with this exact structure:

{{
  "di_set_id": "DI_[TYPE]_XXX",
  "topic": "{di_type} - [Specific Topic]",
  "difficulty": "[Easy/Medium/Hard]",
  "data_source": {{
    // Structure depends on DI type - see type-specific instructions above
  }},
  "questions": [
    {{
      "question_id": "DI_[TYPE]_XXX_Q1",
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text",
        "E": "Option E text"
      }},
      "correct_answer": "A",
      "explanation": "Step-by-step solution explaining how to arrive at the answer.",
      "difficulty": "Easy"
    }}
    // ... {num_questions} questions total
  ]
}}

**Important:**
- Generate exactly {num_questions} questions
- Ensure all JSON is valid and properly formatted
- Do not include any text outside the JSON object
- All numerical values should be realistic and consistent
- Questions should cover different aspects of the data
- Maintain difficulty progression (easier questions first if mixed difficulty)
"""
    
    return schema


# ============================================================================
# SPECIFIC DI TYPE PROMPTS (Optional - for fine-tuned generation)
# ============================================================================

def get_table_di_prompt(topic: str, difficulty: str, num_questions: int = 5) -> str:
    """Generate prompt specifically for Table-based DI"""
    return get_di_generation_prompt("Table", topic, difficulty, num_questions)


def get_bar_chart_di_prompt(topic: str, difficulty: str, num_questions: int = 5) -> str:
    """Generate prompt specifically for Bar Chart DI"""
    return get_di_generation_prompt("Bar Chart", topic, difficulty, num_questions)


def get_line_chart_di_prompt(topic: str, difficulty: str, num_questions: int = 5) -> str:
    """Generate prompt specifically for Line Chart DI"""
    return get_di_generation_prompt("Line Chart", topic, difficulty, num_questions)


def get_pie_chart_di_prompt(topic: str, difficulty: str, num_questions: int = 5) -> str:
    """Generate prompt specifically for Pie Chart DI"""
    return get_di_generation_prompt("Pie Chart", topic, difficulty, num_questions)


def get_mixed_chart_di_prompt(topic: str, difficulty: str, num_questions: int = 5) -> str:
    """Generate prompt specifically for Mixed Charts DI"""
    return get_di_generation_prompt("Mixed Charts", topic, difficulty, num_questions)


def get_caselet_di_prompt(topic: str, difficulty: str, num_questions: int = 5) -> str:
    """Generate prompt specifically for Caselet DI"""
    return get_di_generation_prompt("Caselet", topic, difficulty, num_questions)


# ============================================================================
# VALIDATION PROMPT (for checking generated DI sets)
# ============================================================================

def get_di_validation_prompt(di_set: dict) -> str:
    """
    Generate prompt for validating a DI set
    
    Args:
        di_set: The DI set dictionary to validate
    
    Returns:
        str: Validation prompt
    """
    
    prompt = f"""Review the following Data Interpretation set for quality and accuracy.

**DI Set to Review:**
```json
{di_set}
Check for:

Data Consistency: Are all values internally consistent?
Calculation Accuracy: Are all answers mathematically correct?
Question Quality: Are questions clear and unambiguous?
Option Plausibility: Are incorrect options reasonable distractors?
Explanation Completeness: Do explanations show all necessary steps?
Difficulty Appropriateness: Does difficulty match the specifications?
Provide feedback in JSON format: {{ "overall_quality": "Excellent/Good/Fair/Poor", "data_consistency": {{ "status": "Pass/Fail", "issues": [] }}, "calculation_accuracy": {{ "status": "Pass/Fail", "errors": [] }}, "question_quality": {{ "status": "Pass/Fail", "suggestions": [] }}, "improvements": [] }} """

    return prompt

# ============================================================================

# ENHANCEMENT PROMPTS (for improving existing DI sets)

# ============================================================================

def get_di_enhancement_prompt(di_set: dict, enhancement_type: str) -> str: 
    """ Generate prompt for enhancing an existing DI set

        Args:
            di_set: The DI set to enhance
            enhancement_type: Type of enhancement (difficulty, variety, clarity)

        Returns:
            str: Enhancement prompt
    """

    enhancement_instructions = {
        "difficulty": """
    Increase the difficulty level of the questions while keeping the same data source.

    Add more calculation steps
    Introduce complex percentage calculations
    Include ratio and proportion problems
    Add analytical reasoning elements """,
    "variety": """
    Improve the variety of questions to cover more aspects of the data.

    Include different question types (direct, percentage, comparison, inference)
    Ensure questions test different data points
    Add questions requiring cross-referencing
    Avoid repetitive question patterns """,
    "clarity": """
    Improve the clarity and presentation of questions and options.

    Make question statements more precise
    Ensure options are clearly formatted
    Improve explanation clarity
    Remove any ambiguous language """ } 
    
    prompt = f"""Enhance the following Data Interpretation set.
                Current DI Set:

                {di_set}
                Enhancement Focus: {enhancement_type} {enhancement_instructions.get(enhancement_type, enhancement_instructions["variety"])}

                Requirements:

                Maintain the same data source structure
                Keep the same number of questions
                Preserve the JSON format
                Ensure all calculations remain accurate
                Return the enhanced DI set in the same JSON format. """
                
    return prompt

#============================================================================

# TOPIC-SPECIFIC PROMPT TEMPLATES

# ============================================================================

def get_banking_finance_di_prompt(di_type: str, difficulty: str, num_questions: int = 5) -> str: 
    """Generate DI prompt with banking/finance context"""

    banking_context = """
    Banking/Finance Context Requirements:

    Use realistic banking scenarios (deposits, loans, interest rates, etc.)
    Include relevant financial metrics (profit margins, ROI, NPAs, etc.)
    Use appropriate financial terminology
    Ensure data reflects realistic banking operations
    Include year-over-year growth patterns typical in banking """ 
    
    return get_di_generation_prompt( di_type=di_type, topic="Banking & Finance", difficulty=difficulty, num_questions=num_questions, additional_instructions=banking_context )


def get_sales_revenue_di_prompt(di_type: str, difficulty: str, num_questions: int = 5) -> str: 
    """Generate DI prompt with sales/revenue context"""

    sales_context = """
                    Sales/Revenue Context Requirements:

                    Include quarterly or monthly sales data
                    Show revenue trends across different products/regions
                    Include metrics like growth rate, market share
                    Use realistic sales figures and patterns
                    Consider seasonal variations if applicable """ 
    
    return get_di_generation_prompt( di_type=di_type, topic="Sales & Revenue Analysis", difficulty=difficulty, num_questions=num_questions, additional_instructions=sales_context )


def get_demographic_di_prompt(di_type: str, difficulty: str, num_questions: int = 5) -> str: 
    """Generate DI prompt with demographic/population context"""

    demographic_context = """
                        Demographic Context Requirements:

                        Use population data, age groups, gender distribution
                        Include growth rates, literacy rates, employment statistics
                        Use realistic demographic patterns
                        Consider urban/rural splits if relevant
                        Include time-based population changes """ 
    
    return get_di_generation_prompt( di_type=di_type, topic="Population & Demographics", difficulty=difficulty, num_questions=num_questions, additional_instructions=demographic_context )


#============================================================================
# BATCH GENERATION PROMPTS
# ============================================================================

def get_batch_di_generation_prompt( specifications: List[Dict[str, any]] ) -> str: 
    """ Generate prompt for creating multiple DI sets in one call

        Args:
            specifications: List of specs, each with di_type, topic, difficulty, num_questions

        Returns:
            str: Batch generation prompt
        """

    prompt = """Generate multiple Data Interpretation sets for RBI Grade B Phase 1 exam.
                Specifications for Each Set:

                """

    for idx, spec in enumerate(specifications, 1):
        prompt += f"""
    Set {idx}:

    DI Type: {spec['di_type']}
    Topic: {spec['topic']}
    Difficulty: {spec['difficulty']}
    Number of Questions: {spec.get('num_questions', 5)}
    """

    prompt += """
    General Requirements:

    Each set should be unique and independent
    Maintain consistent quality across all sets
    Follow all standard DI generation guidelines
    Ensure variety in question types within each set
    Output Format: Return a JSON array containing all DI sets:

    [
    {
        // DI Set 1
        "di_set_id": "...",
        "topic": "...",
        ...
    },
    {
        // DI Set 2
        "di_set_id": "...",
        "topic": "...",
        ...
    }
    // ... more sets
    ]
    """

    return prompt

#===========================================================================
# REGENERATION PROMPTS (for fixing issues)
#============================================================================

def get_di_regeneration_prompt( original_di_set: dict, issues: List[str], preserve_data: bool = True ) -> str: 
    """ Generate prompt for regenerating a DI set to fix issues

        Args:
            original_di_set: The original DI set with issues
            issues: List of issues to fix
            preserve_data: Whether to keep the same data source

        Returns:
            str: Regeneration prompt
        """

    prompt = f"""Regenerate the following Data Interpretation set to fix identified issues.
    Original DI Set:

    {original_di_set}
    Issues to Fix: """

    for idx, issue in enumerate(issues, 1):
        prompt += f"{idx}. {issue}\n"

    if preserve_data:
        prompt += """Important: Keep the same data source structure and values. Only modify the questions, options, and explanations as needed to fix the issues. """ 
    else: 
        prompt += """ Note: You may modify the data source if needed to create better questions. """

    prompt += """
    Requirements:

    Fix all identified issues
    Maintain the same JSON structure
    Ensure all calculations are correct
    Keep the same difficulty level
    Return the complete regenerated DI set
    Return the corrected DI set in JSON format. """

    return prompt

#============================================================================
# QUESTION-LEVEL PROMPTS (for individual question generation)
#============================================================================

def get_additional_question_prompt( di_set: dict, num_additional_questions: int = 2, question_types: Optional[List[str]] = None ) -> str: 
    """ Generate prompt for adding more questions to an existing DI set

        Args:
            di_set: Existing DI set
            num_additional_questions: Number of questions to add
            question_types: Optional list of specific question types to include

        Returns:
            str: Prompt for generating additional questions
        """

    prompt = f"""Generate {num_additional_questions} additional questions for the following Data Interpretation set.
    Existing DI Set:

    {di_set}
    Requirements:

    Use the same data source
    Ensure new questions don't duplicate existing ones
    Test different aspects of the data
    Maintain the same difficulty level
    Follow the same format as existing questions """ 
    
    
    if question_types: 
        prompt += f"\nFocus on these question types:\n" 
    for qt in question_types: 
        prompt += f"- {qt}\n" 
        prompt += """ Output Format: Return only the new questions as a JSON array:
    [
    {
        "question_id": "...",
        "question": "...",
        "options": {...},
        "correct_answer": "...",
        "explanation": "...",
        "difficulty": "..."
    }
    // ... more questions
    ]
    """

    return prompt

#============================================================================
#DIFFICULTY ADJUSTMENT PROMPTS
#============================================================================

def get_difficulty_adjustment_prompt( di_set: dict, target_difficulty: str ) -> str: 
    """ Generate prompt for adjusting difficulty of an existing DI set

        Args:
            di_set: Existing DI set
            target_difficulty: Target difficulty level (Easy/Medium/Hard)

        Returns:
            str: Difficulty adjustment prompt
        """

    prompt = f"""Adjust the difficulty level of the following Data Interpretation set to {target_difficulty}.
    Current DI Set:

    {di_set}
    Target Difficulty: {target_difficulty}

    """

    if target_difficulty == "Easy":
        prompt += """
        Adjustments for Easy Difficulty:

        Simplify calculation steps (1-2 steps maximum)
        Focus on direct data reading
        Use simple percentages and basic arithmetic
        Make questions more straightforward
        Reduce the number of data points to consider """ 

    elif target_difficulty == "Medium": 
        prompt += """ Adjustments for Medium Difficulty:
    Include 2-3 calculation steps
    Balance direct and derived values
    Include percentage and ratio calculations
    Require moderate analytical thinking
    Use multiple but manageable data points """ 
    
    else: # Hard 
        prompt += """ Requirements:
                Keep the same data source
                Maintain question count
                Adjust all questions to target difficulty
                Update the difficulty field in JSON
                Ensure calculations remain accurate
                Return the adjusted DI set in the same JSON format. """

    return prompt

#============================================================================
# UTILITY FUNCTIONS
#============================================================================


def format_di_prompt_with_examples( di_type: str, topic: str, difficulty: str, example_di_sets: List[dict], num_questions: int = 5 ) -> str: 
    """ Generate DI prompt with example DI sets for context

        Args:
            di_type: Type of DI
            topic: Topic for the DI set
            difficulty: Difficulty level
            example_di_sets: List of example DI sets to use as reference
            num_questions: Number of questions to generate

        Returns:
            str: Prompt with examples
        """

    base_prompt = get_di_generation_prompt(di_type, topic, difficulty, num_questions)

    examples_section = "\n\n**Example DI Sets for Reference:**\n\n"

    for idx, example in enumerate(example_di_sets, 1):
        examples_section += f"Example {idx}:\n```json\n{example}\n```\n\n"

    examples_section += "Generate a new DI set following similar quality and format.\n"

    return base_prompt + examples_section

def get_custom_di_prompt( di_type: str, topic: str, difficulty: str, num_questions: int, custom_requirements: Dict[str, any] ) -> str: 
    """ Generate a fully customized DI prompt

        Args:
            di_type: Type of DI
            topic: Topic for the DI set
            difficulty: Difficulty level
            num_questions: Number of questions
            custom_requirements: Dictionary of custom requirements

        Returns:
            str: Customized prompt
        """

    base_prompt = get_di_generation_prompt(di_type, topic, difficulty, num_questions)

    custom_section = "\n\n**Custom Requirements:**\n"

    for key, value in custom_requirements.items():
        custom_section += f"- {key}: {value}\n"

    return base_prompt + custom_section

#============================================================================
# TESTING AND DEBUG PROMPTS
#============================================================================

def get_di_test_prompt(di_type: str = "Table") -> str: 
    """ Get a simple test prompt for verifying DI generation

        Args:
            di_type: Type of DI to test

        Returns:
            str: Simple test prompt
        """

    return get_di_generation_prompt(
    di_type=di_type,
    topic="Sales Analysis",
    difficulty="Medium",
    num_questions=3,
    additional_instructions="This is a test generation. Focus on correctness over complexity."
)


if __name__ == "__main__": 
    print("✅ di_prompts.py loaded successfully") 
    print(f"📊 Available DI Types: {', '.join(DI_TYPES)}") 
    print(f"📚 Available Topics: {len(DI_TOPICS)} topics") 
    print("\n💡 Main functions:") 
    print(" - get_di_generation_prompt()") 
    print(" - get_di_system_prompt()") 
    print(" - get_di_validation_prompt()") 
    print(" - get_di_enhancement_prompt()") 
    print(" - get_batch_di_generation_prompt()")
    print(" - get_di_regeneration_prompt()") 
    print(" - get_additional_question_prompt()") 
    print(" - get_difficulty_adjustment_prompt()") 
    print(" - get_di_test_prompt()") 
    print("\n💡 Utility functions:") 
    print(" - format_di_prompt_with_examples()") 
    print(" - get_custom_di_prompt()")
    print("\n💡 Import this module in your scripts:")
    print("   from di_prompts import *")