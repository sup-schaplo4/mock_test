"""
Universal Arithmetic Generator Template
Generates 15 questions in 3 batches of 5 questions each

Usage:
1. Set TOPIC and OUTPUT_FILE
2. Run: python generators/generate_arithmetic_[topic].py
"""

import os
import sys
import json
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.quant_utils import (
    generate_with_openai,
    validate_arithmetic_question,
    save_to_json,
    ensure_directory_exists,
    log_generation_progress,
    generate_metadata,
    retry_generation,
    Timer,
    format_time_elapsed
)

from prompts.arithmetic_prompts import (
    get_arithmetic_system_prompt,
    get_arithmetic_generation_prompt
)

# ============================================================================
# CONFIGURATION - CHANGE THESE FOR EACH TOPIC
# ============================================================================

TOPIC = "Percentage"  # Change to any arithmetic topic
OUTPUT_FILE = "arithmetic_percentage_questions.json"  # Change accordingly

# Fixed configuration
TOTAL_QUESTIONS = 15
QUESTIONS_PER_BATCH = 5
NUM_BATCHES = 3
OUTPUT_DIR = "data/generated/quant_questions"

# Difficulty distribution per batch
BATCH_DIFFICULTY = [
    {"Easy": 1, "Medium": 2, "Hard": 2},    # Batch 1: 3E + 2M
    {"Easy": 1, "Medium": 2, "Hard": 2},    # Batch 2: 4M + 1H
    {"Easy": 1, "Medium": 2, "Hard": 2}     # Batch 3: 5H
]

# ============================================================================
# GENERATION FUNCTIONS
# ============================================================================

def generate_single_batch(batch_num: int, difficulty_dist: dict) -> list:
    """Generate a single batch of 5 questions"""
    
    print(f"\n{'='*70}")
    print(f"🎯 Batch {batch_num}/{NUM_BATCHES} | {TOPIC}")
    print(f"📊 Distribution: {difficulty_dist}")
    print(f"{'='*70}")
    
    # Create prompt
    system_prompt = get_arithmetic_system_prompt()
    generation_prompt = get_arithmetic_generation_prompt(
        topic=TOPIC,
        num_questions=QUESTIONS_PER_BATCH,
        difficulty_distribution=difficulty_dist
    )
    
    full_prompt = f"{system_prompt}\n\n{generation_prompt}"
    
    # Call API
    print(f"📝 Calling API...")
    result = generate_with_openai(
        prompt=full_prompt,
        model="gpt-4o",
        max_tokens=3000,
        temperature=0.7,
        response_format="json_object"
    )
    
    if not result["success"]:
        print(f"❌ API failed: {result.get('error')}")
        return None
    
    print(f"✅ API success | ${result['cost']:.4f} | {result['tokens']['total']} tokens")
    
    # Parse response
    try:
        response_data = result["data"]
        
        # Handle different response formats
        if "questions" in response_data:
            questions = response_data["questions"]
        elif isinstance(response_data, list):
            questions = response_data
        else:
            print(f"❌ Unexpected response format")
            return None
        
        # Add metadata to each question
        for i, q in enumerate(questions):
            if "metadata" not in q:
                q["metadata"] = generate_metadata()
            q["metadata"]["batch_number"] = batch_num
            q["metadata"]["api_cost"] = result["cost"] / len(questions)
            q["metadata"]["question_number"] = (batch_num - 1) * QUESTIONS_PER_BATCH + i + 1
        
        print(f"✅ Parsed {len(questions)} questions")
        
    except Exception as e:
        print(f"❌ Parse error: {e}")
        return None
    
    # Validate each question
    print(f"🔍 Validating questions...")
    valid_count = 0
    for q in questions:
        validation = validate_arithmetic_question(q)
        if validation.get("valid", False):
            valid_count += 1
    
    print(f"✅ Valid questions: {valid_count}/{len(questions)}")
    
    return questions


def generate_all_questions() -> bool:
    """Generate all arithmetic questions in 3 batches"""
    
    print("\n" + "="*70)
    print(f"🚀 {TOPIC.upper()} GENERATION")
    print("="*70)
    print(f"📊 Target: {TOTAL_QUESTIONS} questions in {NUM_BATCHES} batches")
    print(f"📈 Distribution: 3 Easy + 6 Medium + 6 Hard")
    print("="*70)
    
    ensure_directory_exists(OUTPUT_DIR)
    
    all_questions = []
    failed_batches = []
    total_cost = 0.0
    
    with Timer() as timer:
        for batch_num in range(1, NUM_BATCHES + 1):
            difficulty_dist = BATCH_DIFFICULTY[batch_num - 1]
            
            log_generation_progress(
                batch_num, 
                NUM_BATCHES, 
                "Batch", 
                TOPIC, 
                f"Distribution: {difficulty_dist}"
            )
            
            # Generate with retry
            questions = retry_generation(
                generate_single_batch,
                max_retries=3,
                delay=2,
                batch_num=batch_num,
                difficulty_dist=difficulty_dist
            )
            
            if questions:
                all_questions.extend(questions)
                batch_cost = sum(q.get("metadata", {}).get("api_cost", 0.0) for q in questions)
                total_cost += batch_cost
                print(f"✅ Batch {batch_num} complete ({len(questions)} questions)")
            else:
                failed_batches.append(f"Batch {batch_num}")
                print(f"❌ Batch {batch_num} failed")
            
            # Small delay between batches
            if batch_num < NUM_BATCHES:
                time.sleep(1)
    
    # Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"✅ Questions: {len(all_questions)}/{TOTAL_QUESTIONS}")
    print(f"✅ Batches: {NUM_BATCHES - len(failed_batches)}/{NUM_BATCHES}")
    print(f"💰 Cost: ${total_cost:.4f}")
    print(f"⏱️  Time: {format_time_elapsed(timer.elapsed)}")
    
    if failed_batches:
        print(f"\n❌ Failed Batches: {len(failed_batches)}")
        for f in failed_batches:
            print(f"   - {f}")
    
    # Count by difficulty
    if all_questions:
        difficulty_count = {"Easy": 0, "Medium": 0, "Hard": 0}
        for q in all_questions:
            diff = q.get("difficulty", "Unknown")
            if diff in difficulty_count:
                difficulty_count[diff] += 1
        print(f"\n📈 Difficulty Breakdown: {difficulty_count}")
    
    # Save
    if all_questions:
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        print(f"\n💾 Saving to: {output_path}")
        
        if save_to_json(all_questions, output_path, indent=2):
            file_size = os.path.getsize(output_path) / 1024
            print(f"✅ Saved | {file_size:.2f} KB")
            print(f"\n🎉 GENERATION COMPLETE")
            return True
        else:
            print(f"❌ Save failed")
            return False
    else:
        print("\n❌ No questions generated")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        return False
    
    print("✅ API Key found")
    return generate_all_questions()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
