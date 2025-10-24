"""
Universal DI Generator Template
Easily adaptable for: Table, Bar Chart, Line Chart, Pie Chart, Mixed Charts, Caselet

Usage:
1. Set DI_TYPE, OUTPUT_FILE, and TOPICS
2. Run: python generators/generate_di_[type].py
"""

import os
import sys
import json
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.quant_utils import (
    generate_with_openai,
    validate_di_set,
    save_to_json,
    ensure_directory_exists,
    log_generation_progress,
    log_validation_results,
    generate_di_set_id,
    generate_metadata,
    retry_generation,
    Timer,
    format_time_elapsed
)

from prompts.di_prompts import (
    get_di_system_prompt,
    get_di_generation_prompt
)

# ============================================================================
# CONFIGURATION - CHANGE THESE FOR EACH DI TYPE
# ============================================================================

DI_TYPE = "Caselet"  # Change to: "Bar Chart", "Line Chart", "Pie Chart", "Mixed Charts", "Caselet"
OUTPUT_FILE = "di_caselet_questions_1.json"  # Change accordingly
TOPICS = [  # 5 topics for 5 sets
    "Sales & Revenue Analysis",
    "Banking & Finance",
    "Population & Demographics",
    "Production & Manufacturing",
    "Import & Export"
]

# Fixed configuration
TOTAL_SETS = 5
QUESTIONS_PER_SET = 5
OUTPUT_DIR = "data/generated/quant_questions"
DIFFICULTY_DISTRIBUTION = ["Easy", "Medium", "Medium", "Hard", "Hard"]

# ============================================================================
# GENERATION FUNCTIONS
# ============================================================================

def generate_single_set(set_num: int, difficulty: str, topic: str) -> dict:
    """Generate a single DI set"""
    
    print(f"\n{'='*70}")
    print(f"🎯 Set {set_num}/{TOTAL_SETS} | {difficulty} | {topic}")
    print(f"{'='*70}")
    
    # Generate set ID
    set_id = generate_di_set_id(DI_TYPE.replace(" ", "_").upper(), set_num)
    
    # Create prompt
    system_prompt = get_di_system_prompt()
    generation_prompt = get_di_generation_prompt(
        di_type=DI_TYPE,
        topic=topic,
        difficulty=difficulty,
        num_questions=QUESTIONS_PER_SET
    )
    
    full_prompt = f"{system_prompt}\n\n{generation_prompt}"
    
    # Call API
    print(f"📝 Calling API...")
    result = generate_with_openai(
        prompt=full_prompt,
        model="gpt-4o",
        max_tokens=4000,
        temperature=0.7,
        response_format="json_object"
    )
    
    if not result["success"]:
        print(f"❌ API failed: {result.get('error')}")
        return None
    
    print(f"✅ API success | ${result['cost']:.4f} | {result['tokens']['total']} tokens")
    
    # Parse response
    try:
        di_set = result["data"]
        di_set["di_set_id"] = set_id
        
        if "metadata" not in di_set:
            di_set["metadata"] = generate_metadata()
        
        di_set["metadata"]["api_cost"] = result["cost"]
        di_set["metadata"]["tokens_used"] = result["tokens"]["total"]
        
    except Exception as e:
        print(f"❌ Parse error: {e}")
        return None
    
    # Validate
    print(f"🔍 Validating...")
    validation = validate_di_set(di_set, expected_questions=QUESTIONS_PER_SET)
    log_validation_results(validation, f"Set {set_num}")
    
    return di_set


def generate_all_sets() -> bool:
    """Generate all DI sets"""
    
    print("\n" + "="*70)
    print(f"🚀 {DI_TYPE.upper()} DI GENERATION")
    print("="*70)
    print(f"📊 Target: {TOTAL_SETS} sets ({TOTAL_SETS * QUESTIONS_PER_SET} questions)")
    print(f"📈 Distribution: {DIFFICULTY_DISTRIBUTION}")
    print("="*70)
    
    ensure_directory_exists(OUTPUT_DIR)
    
    all_sets = []
    failed_sets = []
    total_cost = 0.0
    
    with Timer() as timer:
        for set_num in range(1, TOTAL_SETS + 1):
            difficulty = DIFFICULTY_DISTRIBUTION[set_num - 1]
            topic = TOPICS[set_num - 1]
            
            log_generation_progress(set_num, TOTAL_SETS, "Set", topic, f"Difficulty: {difficulty}")
            
            # Generate with retry
            di_set = retry_generation(
                generate_single_set,
                max_retries=3,
                delay=2,
                set_num=set_num,
                difficulty=difficulty,
                topic=topic
            )
            
            if di_set:
                all_sets.append(di_set)
                total_cost += di_set.get("metadata", {}).get("api_cost", 0.0)
                print(f"✅ Set {set_num} complete")
            else:
                failed_sets.append(f"Set {set_num} ({difficulty} - {topic})")
                print(f"❌ Set {set_num} failed")
            
            if set_num < TOTAL_SETS:
                time.sleep(1)
    
    # Summary
    total_questions = sum(len(s.get("questions", [])) for s in all_sets)
    
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"✅ Sets: {len(all_sets)}/{TOTAL_SETS}")
    print(f"✅ Questions: {total_questions}/{TOTAL_SETS * QUESTIONS_PER_SET}")
    print(f"💰 Cost: ${total_cost:.4f}")
    print(f"⏱️  Time: {format_time_elapsed(timer.elapsed)}")
    
    if failed_sets:
        print(f"\n❌ Failed: {len(failed_sets)}")
        for f in failed_sets:
            print(f"   - {f}")
    
    # Save
    if all_sets:
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        print(f"\n💾 Saving to: {output_path}")
        
        if save_to_json(all_sets, output_path, indent=2):
            file_size = os.path.getsize(output_path) / 1024
            print(f"✅ Saved | {file_size:.2f} KB")
            print(f"\n🎉 GENERATION COMPLETE")
            return True
        else:
            print(f"❌ Save failed")
            return False
    else:
        print("\n❌ No sets generated")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        return False
    
    print("✅ API Key found")
    return generate_all_sets()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
