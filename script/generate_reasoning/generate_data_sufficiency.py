"""
Data Sufficiency Question Generator
Generates questions using OpenAI API in batches
"""

import os
import time
from datetime import datetime
from openai_utils import create_openai_client, generate_questions_openai, test_openai_connection
from utils import (
    calculate_batch_distribution,
    validate_json_output,
    save_to_json,
    log_error,
    calculate_cost,
    get_timestamp_filename
)


# ============================================================================
# CONFIGURATION - MODIFY THESE VALUES
# ============================================================================

# OpenAI API Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("❌ Please set OPENAI_API_KEY environment variable")
MODEL_NAME = "gpt-4o"

# Question Generation Configuration
TOTAL_QUESTIONS = 30

# Difficulty Distribution (percentage-based)
DIFFICULTY_WEIGHTS = {
    "Easy": 20,      # 20% = 6 questions
    "Medium": 40,    # 40% = 12 questions
    "Hard": 40       # 40% = 12 questions
}

# Batch Configuration
BATCH_SIZE = 5
MAX_RETRIES_PER_BATCH = 3

# API Parameters
TEMPERATURE = 0.9
MAX_TOKENS = 8192

# Cost Configuration (GPT-4o pricing per million tokens)
INPUT_COST_PER_MILLION = 2.50
OUTPUT_COST_PER_MILLION = 10.00

# Output Configuration
OUTPUT_BASE_DIR = "data/generated"

# Question Metadata
TOPIC_NAME = "Data Sufficiency"
REASONING_TOPIC = "Data Sufficiency"
MAIN_CATEGORY = "Analytical & Critical Reasoning"
SUBJECT = "Reasoning"
EXAM_NAME = "RBI Grade B Phase 1"

# ============================================================================
# PROMPT TEMPLATE (Under 80 lines)
# ============================================================================

PROMPT_TEMPLATE = """# TASK: DATA SUFFICIENCY QUESTION GENERATOR

## CONTEXT
You are an expert in analytical reasoning and critical thinking, tasked with creating high-quality Data Sufficiency questions. These questions test the ability to evaluate whether given statements provide sufficient information to answer a specific question, requiring skills in logical analysis, information adequacy assessment, and distinguishing between necessary and redundant data.

## YOUR TASK
Please generate {batch_size} Data Sufficiency questions.

**Key Guidelines for Logical Rigor:**
As an expert in data sufficiency analysis, your primary goal is to ensure every question accurately tests the concept of information sufficiency. Please follow this internal verification process for each question you create:
1. First, clearly define what information is needed to answer the main question definitively.
2. Second, analyze Statement I alone: does it provide sufficient information? Then analyze Statement II alone.
3. Third, if neither alone is sufficient, determine whether combining both statements provides sufficiency.
4. Finally, verify that your answer choice accurately reflects the sufficiency analysis and that the explanation clearly justifies the conclusion.
5. Please ensure each statement is meaningful, non-redundant, and that the correct answer option is unambiguous.

## DIFFICULTY DISTRIBUTION
Please generate the following distribution:
- {easy_count} Easy question(s)
- {medium_count} Medium question(s)
- {hard_count} Hard question(s)

Total: {batch_size} questions

## DIFFICULTY PARAMETERS

### EASY
**Question Structure:**
- Simple arithmetic, basic relationships, or straightforward logical scenarios
- Clear, direct statements with obvious sufficiency or insufficiency
- Statement I alone OR Statement II alone typically sufficient
- Minimal calculation or logical steps required
- Topics: basic ages, simple comparisons, direct values, elementary statistics

### MEDIUM
**Question Structure:**
- Moderate complexity involving equations, ratios, percentages, or multi-variable problems
- Statements require 2-3 steps of reasoning or calculation to assess sufficiency
- Often requires BOTH statements together for sufficiency
- May involve: time-work problems, profit-loss, averages, sequence problems, coded relationships
- Some interdependence between statements

### HARD
**Question Structure:**
- High complexity with multiple variables, abstract relationships, or conditional logic
- Statements require multi-step reasoning, algebraic manipulation, or advanced analytical thinking
- May involve: complex word problems, multiple constraints, probability, set theory, advanced number properties
- Requires careful analysis to avoid trap answers (e.g., statements that seem sufficient but aren't)
- High interdependence or subtle relationships between statements
- May test recognition of redundant vs. essential information

## STANDARD ANSWER OPTIONS (Use these EXACT options for consistency)

**Option A:** Statement I alone is sufficient, but Statement II alone is not sufficient to answer the question.
**Option B:** Statement II alone is sufficient, but Statement I alone is not sufficient to answer the question.
**Option C:** Both statements I and II together are sufficient to answer the question, but neither statement alone is sufficient.
**Option D:** Each statement alone is sufficient to answer the question.
**Option E:** Statements I and II together are not sufficient to answer the question, and additional information is needed.

## QUESTION DOMAINS (Use variety across difficulties)
- **Quantitative:** Age problems, distance-speed-time, profit-loss, ratios, percentages, averages, number properties
- **Logical:** Ordering, rankings, comparisons, sequences, code/symbol relationships
- **Relational:** Blood relations combined with data, family trees with missing info
- **Spatial:** Seating arrangements, directions with incomplete data
- **Set-Based:** Group memberships, Venn diagram scenarios, counting problems

## QUESTION ID FORMAT
Use this format for question IDs:
- data_sufficiency_001
- data_sufficiency_002
- And so on...

Start from ID: data_sufficiency_{start_id:03d}

## OUTPUT FORMAT
Please return a valid JSON object with a "questions" array. Structure:

{{
  "questions": [
    {{
      "question_id": "data_sufficiency_001",
      "question": "[Main question]\n\nStatement I: [First statement]\nStatement II: [Second statement]",
      "options": {{
        "A": "Statement I alone is sufficient, but Statement II alone is not sufficient to answer the question.",
        "B": "Statement II alone is sufficient, but Statement I alone is not sufficient to answer the question.",
        "C": "Both statements I and II together are sufficient to answer the question, but neither statement alone is sufficient.",
        "D": "Each statement alone is sufficient to answer the question.",
        "E": "Statements I and II together are not sufficient to answer the question, and additional information is needed."
      }},
      "correct_answer": "A",
      "explanation": "[Detailed analysis: (1) What is needed to answer the question, (2) Analysis of Statement I alone, (3) Analysis of Statement II alone, (4) Analysis of both together if needed, (5) Final conclusion]",
      "difficulty": "Easy",
      "topic": "{topic}",
      "reasoning_topic": "{reasoning_topic}",
      "main_category": "{main_category}",
      "subject": "{subject}",
      "exam": "{exam}",
      "metadata": {{
        "generated_by": "{model}",
        "generation_date": "{date}",
        "reviewed": false
      }}
    }}
  ]
}}

**IMPORTANT**: Output ONLY the JSON object. Do NOT include any text before or after the JSON.
"""


# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================

def generate_data_sufficiency_questions():
    """
    Main function to generate data sufficiency questions
    """
    
    print("=" * 80)
    print("DATA SUFFICIENCY QUESTION GENERATOR")
    print("=" * 80)
    print(f"Model: {MODEL_NAME}")
    print(f"Target: {TOTAL_QUESTIONS} questions")
    print(f"Distribution: Easy={DIFFICULTY_WEIGHTS['Easy']}%, Medium={DIFFICULTY_WEIGHTS['Medium']}%, Hard={DIFFICULTY_WEIGHTS['Hard']}%")
    print(f"Batch Size: {BATCH_SIZE}")
    print("=" * 80)
    
    # Create output directory
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
    
    # Generate filenames with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_BASE_DIR, f"data_sufficiency_questions_{timestamp}.json")
    error_log_file = os.path.join(OUTPUT_BASE_DIR, f"data_sufficiency_errors_{timestamp}.log")
    metadata_file = os.path.join(OUTPUT_BASE_DIR, f"data_sufficiency_metadata_{timestamp}.json")
    
    print(f"\n📁 Output Files:")
    print(f"   Questions: {output_file}")
    print(f"   Errors: {error_log_file}")
    print(f"   Metadata: {metadata_file}")
    print()
    
    # Initialize OpenAI client
    print("🔑 Initializing OpenAI client...")
    client = create_openai_client(OPENAI_API_KEY)
    
    if not client:
        print("❌ Failed to create OpenAI client. Please check your API key.")
        return
    
    # Test connection
    test_result = test_openai_connection(client, MODEL_NAME)
    if not test_result["success"]:
        print(f"❌ API connection test failed: {test_result['error']}")
        return
    
    print()
    
    # Calculate batch distribution
    print("📊 Calculating batch distribution...")
    batches = calculate_batch_distribution(TOTAL_QUESTIONS, BATCH_SIZE, DIFFICULTY_WEIGHTS)
    print()
    
    # Initialize tracking variables
    all_questions = []
    total_input_tokens = 0
    total_output_tokens = 0
    total_time = 0
    successful_batches = 0
    failed_batches = 0
    start_time = time.time()
    
    # Process each batch
    for batch_info in batches:
        batch_num = batch_info["batch_num"]
        batch_total = batch_info["total"]
        batch_easy = batch_info["Easy"]
        batch_medium = batch_info["Medium"]
        batch_hard = batch_info["Hard"]
        
        print(f"{'=' * 80}")
        print(f"BATCH {batch_num}/{len(batches)}")
        print(f"{'=' * 80}")
        print(f"Generating {batch_total} questions: Easy={batch_easy}, Medium={batch_medium}, Hard={batch_hard}")
        
        # Calculate starting question ID
        start_id = len(all_questions) + 1
        
        # Build prompt
        prompt = PROMPT_TEMPLATE.format(
            batch_size=batch_total,
            easy_count=batch_easy,
            medium_count=batch_medium,
            hard_count=batch_hard,
            start_id=start_id,
            topic=TOPIC_NAME,
            reasoning_topic=REASONING_TOPIC,
            main_category=MAIN_CATEGORY,
            subject=SUBJECT,
            exam=EXAM_NAME,
            model=MODEL_NAME,
            date=datetime.now().strftime('%Y-%m-%d')
        )
        
        # Generate questions
        result = generate_questions_openai(
            client=client,
            prompt=prompt,
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            max_retries=MAX_RETRIES_PER_BATCH
        )
        
        # Handle result
        if result["success"]:
            questions = result["questions"]
            
            # Validate
            validation = validate_json_output(questions, batch_total)
            
            if validation["valid"]:
                print(f"   ✅ Batch successful!")
                
                # Update question IDs to ensure consistency
                for idx, q in enumerate(questions):
                    expected_id = f"data_sufficiency_{start_id + idx:03d}"
                    q["question_id"] = expected_id
                
                all_questions.extend(questions)
                successful_batches += 1
                
                # Track tokens and cost
                total_input_tokens += result["tokens_input"]
                total_output_tokens += result["tokens_output"]
                total_time += result["time_taken"]
                
                cost_info = calculate_cost(
                    result["tokens_input"],
                    result["tokens_output"],
                    INPUT_COST_PER_MILLION,
                    OUTPUT_COST_PER_MILLION
                )
                
                print(f"   💰 Batch Cost: ${cost_info['total_cost']:.4f}")
                
            else:
                print(f"   ❌ Validation failed!")
                for error in validation["errors"]:
                    print(f"      • {error}")
                
                failed_batches += 1
                error_msg = f"Batch {batch_num} validation failed: {validation['errors']}"
                log_error(error_msg, error_log_file)
                
                if validation["warnings"]:
                    print(f"   ⚠️  Warnings:")
                    for warning in validation["warnings"]:
                        print(f"      • {warning}")
        
        else:
            print(f"   ❌ Batch failed: {result['error']}")
            failed_batches += 1
            error_msg = f"Batch {batch_num} generation failed: {result['error']}"
            log_error(error_msg, error_log_file)
        
        print()
        
        # Save progress after each batch
        if all_questions:
            save_to_json(all_questions, output_file)
            print(f"   💾 Progress saved ({len(all_questions)} questions so far)")
            print()
        
        # Wait between batches (except last one)
        if batch_num < len(batches):
            time.sleep(3)
    
    # Calculate final statistics
    end_time = time.time()
    total_generation_time = end_time - start_time
    
    total_cost_info = calculate_cost(
        total_input_tokens,
        total_output_tokens,
        INPUT_COST_PER_MILLION,
        OUTPUT_COST_PER_MILLION
    )
    
    # Create metadata
    metadata = {
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_used": MODEL_NAME,
        "total_questions_requested": TOTAL_QUESTIONS,
        "total_questions_generated": len(all_questions),
        "difficulty_distribution": {
            "Easy": sum(1 for q in all_questions if q.get("difficulty") == "Easy"),
            "Medium": sum(1 for q in all_questions if q.get("difficulty") == "Medium"),
            "Hard": sum(1 for q in all_questions if q.get("difficulty") == "Hard")
        },
        "batch_configuration": {
            "total_batches": len(batches),
            "batch_size": BATCH_SIZE,
            "successful_batches": successful_batches,
            "failed_batches": failed_batches
        },
        "token_usage": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens
        },
        "cost": {
            "input_cost": total_cost_info["input_cost"],
            "output_cost": total_cost_info["output_cost"],
            "total_cost": total_cost_info["total_cost"]
        },
        "time": {
            "total_time_seconds": round(total_generation_time, 2),
            "api_time_seconds": round(total_time, 2)
        },
        "output_files": {
            "questions": output_file,
            "errors": error_log_file,
            "metadata": metadata_file
        }
    }
    
    # Save metadata
    save_to_json(metadata, metadata_file)
    
    # Print final summary
    print("=" * 80)
    print("GENERATION COMPLETE!")
    print("=" * 80)
    print(f"✅ Total Questions Generated: {len(all_questions)}/{TOTAL_QUESTIONS}")
    print(f"✅ Successful Batches: {successful_batches}/{len(batches)}")
    if failed_batches > 0:
        print(f"❌ Failed Batches: {failed_batches}/{len(batches)}")
    print()
    print(f"📊 Difficulty Distribution:")
    print(f"   Easy: {metadata['difficulty_distribution']['Easy']}")
    print(f"   Medium: {metadata['difficulty_distribution']['Medium']}")
    print(f"   Hard: {metadata['difficulty_distribution']['Hard']}")
    print()
    print(f"🎯 Token Usage:")
    print(f"   Input: {total_input_tokens:,}")
    print(f"   Output: {total_output_tokens:,}")
    print(f"   Total: {total_input_tokens + total_output_tokens:,}")
    print()
    print(f"💰 Total Cost: ${total_cost_info['total_cost']:.4f}")
    print(f"   Input Cost: ${total_cost_info['input_cost']:.4f}")
    print(f"   Output Cost: ${total_cost_info['output_cost']:.4f}")
    print()
    print(f"⏱️  Time: {total_generation_time:.1f}s ({total_generation_time/60:.1f} minutes)")
    print()
    print(f"📁 Output saved to:")
    print(f"   {output_file}")
    print("=" * 80)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    generate_data_sufficiency_questions()