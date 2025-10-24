"""
Strengthening/Weakening Arguments Question Generator
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
TOPIC_NAME = "Strengthening/Weakening Arguments"
REASONING_TOPIC = "Strengthen/Weaken"
MAIN_CATEGORY = "Analytical & Critical Reasoning"
SUBJECT = "Reasoning"
EXAM_NAME = "RBI Grade B Phase 1"

# ============================================================================
# PROMPT TEMPLATE (Under 80 lines)
# ============================================================================

PROMPT_TEMPLATE = """# TASK: STRENGTHENING/WEAKENING ARGUMENTS QUESTION GENERATOR

## CONTEXT
You are an expert in critical reasoning and argument analysis, tasked with creating high-quality Strengthen/Weaken questions. These questions present an argument with a conclusion based on premises, followed by options that either strengthen or weaken the argument. This tests the ability to identify logical connections, evaluate evidence relevance, recognize assumptions, and assess how new information impacts argument validity.

## YOUR TASK
Please generate {batch_size} Strengthen/Weaken Argument questions.

**Key Guidelines for Logical Validity:**
As an expert in argument analysis, your primary goal is to ensure every question accurately tests argument evaluation. Please follow this internal verification process for each question you create:
1. First, construct an argument with a clear conclusion and supporting premises, ensuring there's a logical gap or assumption that can be strengthened or weakened.
2. Second, identify the core assumption or logical link between premises and conclusion—this is what answer options should target.
3. Third, for STRENGTHEN questions: create options where the correct answer provides evidence supporting the assumption, filling the logical gap, or providing data that makes the conclusion more likely.
4. Fourth, for WEAKEN questions: create options where the correct answer provides counterevidence, exposes the assumption as questionable, introduces alternative explanations, or shows the conclusion doesn't follow.
5. Fifth, design distractor options that are: relevant but neutral (doesn't affect argument strength), address the wrong assumption, provide weak/indirect support, or are out of scope.
6. Finally, verify the correct answer has the MOST DIRECT and SIGNIFICANT impact on the argument's strength, and your explanation clearly articulates the logical mechanism.
7. Please ensure arguments have identifiable logical structures and that strengthen/weaken effects are clear and defensible.

## DIFFICULTY DISTRIBUTION
Please generate the following distribution:
- {easy_count} Easy question(s)
- {medium_count} Medium question(s)
- {hard_count} Hard question(s)

Total: {batch_size} questions

## DIFFICULTY PARAMETERS

### EASY
**Argument Structure:**
- Simple causal or correlational argument (3-4 sentences)
- Clear, single assumption linking premise to conclusion
- Direct evidence/counterevidence relationship
- Context: everyday scenarios, straightforward cause-effect, simple policy proposals
- Options: One clearly strengthens/weakens, others are obviously irrelevant or weakly related
- Limited ambiguity in determining impact on argument
- Question type: "Which of the following, if true, most strengthens/weakens the argument?"

### MEDIUM
**Argument Structure:**
- Moderate complexity argument (4-5 sentences) with multiple supporting premises or conditional logic
- One or two key assumptions, requiring identification of which is central
- Context: business decisions, scientific findings, policy analyses, trend projections
- Options: Mix of direct/indirect strengtheners/weakeners, some address alternative assumptions
- Requires distinguishing between strong and weak impacts on argument validity
- May include options that strengthen/weaken a premise but not the main conclusion
- Question type: May ask for MOST strengthens/weakens or EXCEPT questions

### HARD
**Argument Structure:**
- Complex argument (5-6 sentences) with layered reasoning, multiple causal links, or statistical claims
- Multiple interrelated assumptions or subtle logical gaps
- Context: research studies with methodology, complex policy reasoning, multi-variable analyses
- Options: Subtle distinctions between strengtheners/weakeners of varying degrees
- Requires sophisticated analysis: distinguishing necessary vs. sufficient conditions, recognizing scope limitations, identifying confounding factors
- May include options that strengthen one part while weakening another
- Question type: Comparative strengthening/weakening, EXCEPT questions, or most/least impact scenarios

## WHAT STRENGTHENS AN ARGUMENT?
An option **strengthens** an argument if it:
- Provides evidence supporting a key assumption
- Fills a logical gap between premise and conclusion
- Provides data/examples making the conclusion more probable
- Rules out alternative explanations or confounding factors
- Shows the causal mechanism is plausible/valid
- Confirms correlation implies causation (when argued)

## WHAT WEAKENS AN ARGUMENT?
An option **weakens** an argument if it:
- Provides counterevidence against a key assumption
- Introduces alternative explanations for the observed phenomenon
- Shows the conclusion doesn't necessarily follow from premises
- Reveals confounding factors or selection bias
- Demonstrates correlation does NOT imply causation
- Exposes methodology flaws or data limitations

## COMMON STRENGTHEN/WEAKEN PATTERNS
- **Causal arguments:** Strengthen by confirming causal link; Weaken by showing alternative causes
- **Analogy arguments:** Strengthen by showing similarity; Weaken by showing dissimilarity
- **Statistical arguments:** Strengthen by confirming representativeness; Weaken by showing sample bias
- **Prediction arguments:** Strengthen by showing relevant factors constant; Weaken by showing changed conditions
- **Plan/Policy arguments:** Strengthen by showing feasibility; Weaken by showing unintended consequences

## QUESTION FORMATS (Vary usage)
1. "Which of the following, if true, most **strengthens** the argument?"
2. "Which of the following, if true, most **weakens** the argument?"
3. "Which of the following, if true, would cast the most doubt on the conclusion?"
4. "All of the following weaken the argument EXCEPT:"
5. "Which of the following assumptions would most strengthen the argument?"

## ARGUMENT DOMAINS (Use variety)
- **Business/Economics:** Market predictions, corporate strategies, consumer behavior, economic policies
- **Science/Research:** Study conclusions, experimental results, causal claims, research methodologies
- **Social/Policy:** Public policy proposals, social trends, regulatory impacts, program effectiveness
- **Health/Medicine:** Treatment effectiveness, health interventions, epidemiological findings, medical recommendations
- **Education:** Learning strategies, educational reforms, academic performance factors
- **Environment:** Conservation policies, environmental impact, sustainability measures
- **Technology:** Tech adoption, innovation impacts, digital transformation

## QUESTION ID FORMAT
Use this format for question IDs:
- strengthen_weaken_001
- strengthen_weaken_002
- And so on...

Start from ID: strengthen_weaken_{start_id:03d}

## OUTPUT FORMAT
Please return a valid JSON object with a "questions" array. Structure:

{{
  "questions": [
    {{
      "question_id": "strengthen_weaken_001",
      "question": "[Argument passage]\n\nWhich of the following, if true, most strengthens/weakens the argument?",
      "options": {{
        "A": "[Option A text]",
        "B": "[Option B text]",
        "C": "[Option C text]",
        "D": "[Option D text]",
        "E": "[Option E text]"
      }},
      "correct_answer": "B",
      "explanation": "[Analysis: (1) Identify the argument's conclusion and key premises, (2) Identify the central assumption or logical gap, (3) Explain how the correct answer strengthens/weakens by addressing this assumption, (4) Briefly explain why other options don't have the same impact]",
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

def generate_strengthen_weaken_questions():
    """
    Main function to generate strengthen/weaken argument questions
    """
    
    print("=" * 80)
    print("STRENGTHENING/WEAKENING ARGUMENTS QUESTION GENERATOR")
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
    output_file = os.path.join(OUTPUT_BASE_DIR, f"strengthen_weaken_questions_{timestamp}.json")
    error_log_file = os.path.join(OUTPUT_BASE_DIR, f"strengthen_weaken_errors_{timestamp}.log")
    metadata_file = os.path.join(OUTPUT_BASE_DIR, f"strengthen_weaken_metadata_{timestamp}.json")
    
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
                    expected_id = f"strengthen_weaken_{start_id + idx:03d}"
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
    generate_strengthen_weaken_questions()




