"""
Statement & Course of Action Question Generator
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
TOPIC_NAME = "Statement & Course of Action"
REASONING_TOPIC = "Statement & Course of Action"
MAIN_CATEGORY = "Analytical & Critical Reasoning"
SUBJECT = "Reasoning"
EXAM_NAME = "RBI Grade B Phase 1"

# ============================================================================
# PROMPT TEMPLATE (Under 80 lines)
# ============================================================================

PROMPT_TEMPLATE = """# TASK: STATEMENT & COURSE OF ACTION QUESTION GENERATOR

## CONTEXT
You are an expert in decision-making analysis and critical reasoning, tasked with creating high-quality Statement & Course of Action questions. These questions present a problem statement followed by proposed courses of action, testing the ability to evaluate whether actions logically address the problem, are practical, and follow naturally from the situation. This requires skills in assessing relevance, feasibility, effectiveness, and logical appropriateness of proposed solutions.

## YOUR TASK
Please generate {batch_size} Statement & Course of Action questions.

**Key Guidelines for Logical Validity:**
As an expert in decision analysis, your primary goal is to ensure every question accurately tests action evaluation. Please follow this internal verification process for each question you create:
1. First, craft a statement describing a clear problem, challenge, or situation requiring action.
2. Second, design courses of action that vary in their logical connection to the problem—some directly address the root cause, some address symptoms, some are tangential or ineffective.
3. Third, evaluate each course of action for: (a) Logical relevance—does it address the stated problem? (b) Practicality—is it feasible? (c) Effectiveness—will it likely improve the situation? (d) Appropriateness—does it follow logically from the problem context?
4. Fourth, distinguish actions that "follow" (are logical, relevant, and practical responses) from those that don't (irrelevant, impractical, premature, or addressing unstated problems).
5. Finally, verify your answer choice is defensible and that the explanation clearly articulates why each action follows or doesn't follow.
6. Please ensure actions are evaluated based on logical merit, not subjective preferences or requiring external knowledge.

## DIFFICULTY DISTRIBUTION
Please generate the following distribution:
- {easy_count} Easy question(s)
- {medium_count} Medium question(s)
- {hard_count} Hard question(s)

Total: {batch_size} questions

## DIFFICULTY PARAMETERS

### EASY
**Statement Structure:**
- Clear, single-issue problem (2-3 sentences) with obvious solution direction
- Context: local issues, straightforward problems, direct cause-effect scenarios
- 2 courses of action: typically one is clearly logical and one is clearly illogical/irrelevant
- Actions are distinctly different in relevance and practicality
- Answer: Usually one action follows (A or B) or both follow (E)
- Limited ambiguity in evaluating action appropriateness
- Examples: local safety issues, simple administrative problems, basic resource shortages

### MEDIUM
**Statement Structure:**
- Moderate complexity problem (3-4 sentences) with multiple dimensions or contributing factors
- Context: organizational issues, policy challenges, social problems, resource management
- 2-3 courses of action: mix of preventive/corrective, short-term/long-term, direct/supportive actions
- Requires careful evaluation to distinguish actions that directly address the problem from tangential actions
- Answer: May require evaluating complementary actions (both follow) or distinguishing between appropriate and premature actions
- Considerations: timing, scope, stakeholder impact, root cause vs. symptom treatment
- Examples: public health issues, educational challenges, business problems, environmental concerns

### HARD
**Statement Structure:**
- Complex, multi-faceted problem (4-5 sentences) with competing priorities, stakeholder conflicts, or systemic issues
- Context: policy dilemmas, strategic decisions, complex social issues, crisis situations
- 3-4 courses of action with subtle distinctions: some address root causes, some symptoms, some are partially relevant
- Requires sophisticated analysis: evaluating action sequence, recognizing prerequisite actions, assessing proportionality
- May include actions that seem logical but have hidden flaws (impractical scale, ignoring constraints, addressing wrong problem)
- Answer: Demands nuanced judgment about which combination of actions logically follows
- Examples: economic crises, systemic reforms, multi-stakeholder conflicts, large-scale policy issues

## WHAT MAKES A COURSE OF ACTION "FOLLOW"? (Core Criteria)
A course of action **follows** if it:
- **Relevance:** Directly addresses the problem stated (not a tangential or unrelated issue)
- **Logic:** Logically connected to solving or mitigating the problem
- **Practicality:** Feasible and realistic given the context (not requiring unstated resources or impossible conditions)
- **Appropriateness:** Suitable in scope, timing, and intensity for the stated problem
- **Effectiveness:** Has a reasonable likelihood of improving the situation

A course of action **does NOT follow** if it:
- Is irrelevant or addresses a different problem
- Is impractical, impossible, or requires unstated major assumptions
- Is premature (requires other actions first) or delayed (should have been done earlier)
- Is disproportionate (too extreme or too weak for the problem)
- Ignores key constraints or stakeholders mentioned in the statement
- Treats symptoms without addressing the stated root cause (when the root cause is clear)

## STANDARD ANSWER OPTIONS (Use these EXACT options)

**For 2 Courses of Action:**
- A: Only Course of Action I follows
- B: Only Course of Action II follows
- C: Either Course of Action I or II follows
- D: Neither Course of Action I nor II follows
- E: Both Courses of Action I and II follow

**For 3 Courses of Action (if used):**
- A: Only I follows
- B: Only II follows
- C: Only I and II follow
- D: Only II and III follow
- E: All follow

## STATEMENT DOMAINS (Use variety)
- **Public Policy:** Governance issues, regulatory challenges, public services
- **Social Issues:** Community problems, public safety, social welfare, demographic challenges
- **Economic:** Market issues, employment, inflation, resource allocation, business challenges
- **Health:** Public health crises, healthcare access, disease prevention, medical resource management
- **Education:** Learning outcomes, institutional challenges, access to education, quality concerns
- **Environment:** Pollution, conservation, resource depletion, climate-related issues
- **Infrastructure:** Transportation, utilities, urban planning, maintenance issues
- **Administration:** Bureaucratic inefficiencies, corruption, service delivery, organizational problems

## QUESTION ID FORMAT
Use this format for question IDs:
- statement_course_of_action_001
- statement_course_of_action_002
- And so on...

Start from ID: statement_course_of_action_{start_id:03d}

## OUTPUT FORMAT
Please return a valid JSON object with a "questions" array. Structure:

{{
  "questions": [
    {{
      "question_id": "statement_course_of_action_001",
      "question": "Statement: [Problem/situation description]\n\nCourses of Action:\nI. [First proposed action]\nII. [Second proposed action]\n[III. Third proposed action (if applicable)]",
      "options": {{
        "A": "[Option A text]",
        "B": "[Option B text]",
        "C": "[Option C text]",
        "D": "[Option D text]",
        "E": "[Option E text]"
      }},
      "correct_answer": "E",
      "explanation": "[Analysis: (1) Brief summary of the problem and its key aspects, (2) Evaluation of Course of Action I with reasoning on relevance/practicality/effectiveness, (3) Evaluation of Course of Action II similarly, (4) [Course of Action III if applicable], (5) Final conclusion about which actions logically follow]",
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

def generate_statement_course_of_action_questions():
    """
    Main function to generate statement & course of action questions
    """
    
    print("=" * 80)
    print("STATEMENT & COURSE OF ACTION QUESTION GENERATOR")
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
    output_file = os.path.join(OUTPUT_BASE_DIR, f"statement_course_of_action_questions_{timestamp}.json")
    error_log_file = os.path.join(OUTPUT_BASE_DIR, f"statement_course_of_action_errors_{timestamp}.log")
    metadata_file = os.path.join(OUTPUT_BASE_DIR, f"statement_course_of_action_metadata_{timestamp}.json")
    
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
                    expected_id = f"statement_course_of_action_{start_id + idx:03d}"
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
    generate_statement_course_of_action_questions()



