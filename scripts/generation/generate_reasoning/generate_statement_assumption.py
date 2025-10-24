"""
Statement & Assumption Question Generator
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
TOPIC_NAME = "Statement & Assumption"
REASONING_TOPIC = "Statement & Assumption"
MAIN_CATEGORY = "Analytical & Critical Reasoning"
SUBJECT = "Reasoning"
EXAM_NAME = "RBI Grade B Phase 1"

# ============================================================================
# PROMPT TEMPLATE (Under 80 lines)
# ============================================================================

PROMPT_TEMPLATE = """# TASK: STATEMENT & ASSUMPTION QUESTION GENERATOR

## CONTEXT
You are an expert in critical reasoning and logical analysis, tasked with creating high-quality Statement & Assumption questions. These questions present a statement followed by two assumptions, testing the ability to identify implicit beliefs or presuppositions that must be true for the statement to hold. This requires skills in recognizing unstated premises, distinguishing between assumptions and inferences, and evaluating logical dependencies.

## YOUR TASK
Please generate {batch_size} Statement & Assumption questions.

**Key Guidelines for Logical Validity:**
As an expert in critical reasoning, your primary goal is to ensure every question accurately tests assumption identification. Please follow this internal verification process for each question you create:
1. First, craft a statement that contains implicit assumptions (unstated premises necessary for the statement's validity or action).
2. Second, identify true assumptions—ideas that MUST be taken for granted for the statement to be meaningful or the proposed action to be logical.
3. Third, distinguish assumptions from inferences (conclusions drawn FROM the statement) and facts explicitly stated.
4. Fourth, create assumption options where one or both may be implicit, ensuring they are neither too obvious nor irrelevant.
5. Finally, verify your answer choice is defensible and that the explanation clearly articulates why each assumption is implicit or not.
6. Please ensure assumptions are logically sound, contextually relevant, and genuinely implicit in the statement.

## DIFFICULTY DISTRIBUTION
Please generate the following distribution:
- {easy_count} Easy question(s)
- {medium_count} Medium question(s)
- {hard_count} Hard question(s)

Total: {batch_size} questions

## DIFFICULTY PARAMETERS

### EASY
**Statement Structure:**
- Simple, direct statement with 1-2 clear implicit assumptions
- Context: everyday scenarios, straightforward policies, basic cause-effect
- Assumptions are closely tied to the statement's immediate meaning
- Answer: Typically one assumption is clearly implicit (Answer: A or B) OR both are clearly implicit (Answer: E)
- Limited ambiguity; assumptions are relatively obvious upon analysis
- Examples: advertisements, simple recommendations, basic announcements

### MEDIUM
**Statement Structure:**
- Moderately complex statement with 2-3 implicit assumptions, requiring careful analysis
- Context: business decisions, policy implementations, conditional scenarios, arguments
- Mix of direct and less obvious assumptions
- Answer: May require evaluating both assumptions carefully (Answer: C, D, or E)
- Requires distinguishing between core assumptions and peripheral ideas
- Examples: government policies, organizational decisions, causal arguments, problem-solution scenarios

### HARD
**Statement Structure:**
- Complex, nuanced statement with multiple layers of implicit reasoning
- Context: abstract policies, multi-stakeholder scenarios, philosophical arguments, conditional chains
- Subtle assumptions that require deep critical thinking
- Assumptions may involve: temporal assumptions, comparative assumptions, motivational assumptions, hidden value judgments
- Answer: Requires sophisticated analysis to determine which assumptions are truly implicit
- May include trap options that seem like assumptions but are inferences or unrelated
- Examples: strategic decisions, ethical dilemmas, theoretical proposals, multi-conditional statements

## WHAT IS AN ASSUMPTION? (Core Definition)
An **assumption** is an unstated premise or belief that:
- Is taken for granted by the statement maker
- Must be true for the statement to be valid, meaningful, or for the proposed action to be rational
- Is NOT explicitly mentioned in the statement
- Bridges a logical gap between the statement and its intended meaning or action
- Is foundational, not a conclusion

**NOT assumptions:**
- Explicit facts stated in the statement
- Inferences or conclusions drawn FROM the statement
- Unrelated or tangential ideas
- Overly general truths not specific to the statement's logic

## STANDARD ANSWER OPTIONS (Use these EXACT options)

**Option A:** Only Assumption I is implicit.
**Option B:** Only Assumption II is implicit.
**Option C:** Either Assumption I or II is implicit.
**Option D:** Neither Assumption I nor II is implicit.
**Option E:** Both Assumptions I and II are implicit.

## STATEMENT DOMAINS (Use variety)
- **Policy/Governance:** Government initiatives, regulations, public programs
- **Business:** Corporate decisions, market strategies, product launches
- **Social:** Public advisories, awareness campaigns, community actions
- **Education:** Academic policies, institutional decisions, learning initiatives
- **Health/Safety:** Medical advisories, safety protocols, preventive measures
- **Environment:** Conservation efforts, sustainability initiatives
- **Technology:** Digital initiatives, tech adoption, innovation strategies

## QUESTION ID FORMAT
Use this format for question IDs:
- statement_assumption_001
- statement_assumption_002
- And so on...

Start from ID: statement_assumption_{start_id:03d}

## OUTPUT FORMAT
Please return a valid JSON object with a "questions" array. Structure:

{{
  "questions": [
    {{
      "question_id": "statement_assumption_001",
      "question": "Statement: [The statement text]\n\nAssumptions:\nI. [First assumption]\nII. [Second assumption]",
      "options": {{
        "A": "Only Assumption I is implicit.",
        "B": "Only Assumption II is implicit.",
        "C": "Either Assumption I or II is implicit.",
        "D": "Neither Assumption I nor II is implicit.",
        "E": "Both Assumptions I and II are implicit."
      }},
      "correct_answer": "E",
      "explanation": "[Analysis: (1) Brief context of the statement, (2) Evaluation of Assumption I with reasoning, (3) Evaluation of Assumption II with reasoning, (4) Final conclusion about which assumptions are implicit and why]",
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

def generate_statement_assumption_questions():
    """
    Main function to generate statement & assumption questions
    """
    
    print("=" * 80)
    print("STATEMENT & ASSUMPTION QUESTION GENERATOR")
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
    output_file = os.path.join(OUTPUT_BASE_DIR, f"statement_assumption_questions_{timestamp}.json")
    error_log_file = os.path.join(OUTPUT_BASE_DIR, f"statement_assumption_errors_{timestamp}.log")
    metadata_file = os.path.join(OUTPUT_BASE_DIR, f"statement_assumption_metadata_{timestamp}.json")
    
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
                    expected_id = f"statement_assumption_{start_id + idx:03d}"
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
    generate_statement_assumption_questions()

