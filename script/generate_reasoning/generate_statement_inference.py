"""
Statement & Inference Question Generator
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
TOPIC_NAME = "Statement & Inference"
REASONING_TOPIC = "Statement & Inference"
MAIN_CATEGORY = "Analytical & Critical Reasoning"
SUBJECT = "Reasoning"
EXAM_NAME = "RBI Grade B Phase 1"

# ============================================================================
# PROMPT TEMPLATE (Under 80 lines)
# ============================================================================

PROMPT_TEMPLATE = """# TASK: STATEMENT & INFERENCE QUESTION GENERATOR

## CONTEXT
You are an expert in logical reasoning and critical thinking, tasked with creating high-quality Statement & Inference questions. These questions present a statement or passage followed by multiple inference options, testing the ability to draw logical conclusions based solely on the given information. This requires skills in distinguishing definite conclusions from assumptions, possibilities, or information beyond what is stated.

## YOUR TASK
Please generate {batch_size} Statement & Inference questions.

**Key Guidelines for Logical Validity:**
As an expert in deductive reasoning, your primary goal is to ensure every question accurately tests inference identification. Please follow this internal verification process for each question you create:
1. First, craft a statement/passage that contains sufficient information to support clear logical conclusions without ambiguity.
2. Second, identify inferences that are DEFINITELY TRUE (follow logically and necessarily from the statement) versus those that are POSSIBLY TRUE, DEFINITELY FALSE, or UNPROVABLE.
3. Third, distinguish valid inferences from assumptions (unstated premises), extrapolations (going beyond the data), or unrelated claims.
4. Fourth, create inference options where some are logically valid and others contain subtle flaws (unsupported generalizations, temporal assumptions, causal claims without evidence).
5. Finally, verify your answer is defensible using only the information in the statement, and that your explanation clearly traces the logical chain.
6. Please ensure all inferences are evaluated purely on logical necessity, not real-world knowledge or plausibility.

## DIFFICULTY DISTRIBUTION
Please generate the following distribution:
- {easy_count} Easy question(s)
- {medium_count} Medium question(s)
- {hard_count} Hard question(s)

Total: {batch_size} questions

## DIFFICULTY PARAMETERS

### EASY
**Statement Structure:**
- Short, direct statement (2-3 sentences) with clear factual information
- Context: simple scenarios, straightforward data, basic cause-effect
- Inferences are closely tied to explicit information
- 2-3 inference options: one is clearly valid (definitely true), others are clearly invalid (assumptions or unsupported)
- Limited ambiguity; valid inference follows directly from statement
- Examples: statistical reports, simple announcements, direct observations

### MEDIUM
**Statement Structure:**
- Moderate-length passage (3-5 sentences) with multiple related facts or a comparative scenario
- Context: policy statements, research findings, trend analyses, conditional scenarios
- 3-4 inference options: requires careful evaluation to distinguish valid from invalid
- Mix of definitely true, possibly true, and definitely false/unprovable inferences
- Requires recognizing subtle distinctions (correlation vs. causation, specific vs. general, necessary vs. possible)
- Examples: survey results, organizational reports, comparative data, expert statements

### HARD
**Statement Structure:**
- Complex passage (5-7 sentences) with layered information, conditional logic, or multiple interrelated facts
- Context: abstract arguments, multi-variable scenarios, statistical analyses, philosophical statements
- 4-5 inference options with subtle distinctions and potential logical traps
- Requires sophisticated reasoning: identifying scope limitations, temporal constraints, implicit qualifiers, logical dependencies
- May include inferences that are almost true but contain one unsupported element
- Examples: research abstracts, policy analyses, complex arguments, multi-conditional scenarios

## WHAT IS A VALID INFERENCE? (Core Definition)
A **valid inference** is a conclusion that:
- Is DEFINITELY TRUE based solely on the information provided in the statement
- Follows logically and necessarily from the given facts
- Does NOT go beyond the scope, timeframe, or context of the statement
- Does NOT assume information not explicitly stated or logically entailed
- Does NOT generalize beyond what the data supports
- Does NOT confuse correlation with causation without explicit causal language

**INVALID inferences include:**
- Assumptions (unstated premises needed to support the statement)
- Possibilities (might be true but not necessarily true)
- Extrapolations beyond the data
- Overgeneralizations
- Causal claims without causal evidence
- Temporal extensions without support

## STANDARD ANSWER OPTIONS (Choose appropriate format)

**Format 1 (Multiple Inferences):**
- A: Only inference I is valid
- B: Only inference II is valid
- C: Only inferences I and II are valid
- D: Only inferences II and III are valid
- E: All inferences are valid

**Format 2 (Single Best Inference):**
- A-E: Five different inference statements, choose the one that is definitely true

## STATEMENT DOMAINS (Use variety)
- **Statistics/Data:** Survey results, research findings, demographic data, performance metrics
- **Policy/Governance:** Government initiatives, regulatory changes, institutional decisions
- **Business/Economics:** Market trends, corporate reports, economic indicators, industry analyses
- **Science/Research:** Study results, experimental findings, scientific observations
- **Social/Behavioral:** Social trends, behavioral patterns, public opinion, cultural phenomena
- **Health/Safety:** Medical reports, safety data, health trends, risk assessments
- **Education/Skills:** Academic performance, learning outcomes, skill assessments

## QUESTION ID FORMAT
Use this format for question IDs:
- statement_inference_001
- statement_inference_002
- And so on...

Start from ID: statement_inference_{start_id:03d}

## OUTPUT FORMAT
Please return a valid JSON object with a "questions" array. Structure:

{{
  "questions": [
    {{
      "question_id": "statement_inference_001",
      "question": "Statement: [The statement/passage text]\n\nWhich of the following inference(s) can be definitely drawn from the above statement?\n\nI. [First inference]\nII. [Second inference]\nIII. [Third inference (if applicable)]",
      "options": {{
        "A": "[Option A text]",
        "B": "[Option B text]",
        "C": "[Option C text]",
        "D": "[Option D text]",
        "E": "[Option E text]"
      }},
      "correct_answer": "C",
      "explanation": "[Analysis: (1) Summary of key facts from statement, (2) Evaluation of each inference with logical reasoning explaining why it is definitely true/false/unprovable, (3) Final conclusion about which inferences are valid]",
      "difficulty": "Medium",
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

def generate_statement_inference_questions():
    """
    Main function to generate statement & inference questions
    """
    
    print("=" * 80)
    print("STATEMENT & INFERENCE QUESTION GENERATOR")
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
    output_file = os.path.join(OUTPUT_BASE_DIR, f"statement_inference_questions_{timestamp}.json")
    error_log_file = os.path.join(OUTPUT_BASE_DIR, f"statement_inference_errors_{timestamp}.log")
    metadata_file = os.path.join(OUTPUT_BASE_DIR, f"statement_inference_metadata_{timestamp}.json")
    
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
                    expected_id = f"statement_inference_{start_id + idx:03d}"
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
    generate_statement_inference_questions()


