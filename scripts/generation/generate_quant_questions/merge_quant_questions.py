"""
Merge All Quant (Math) Questions into Master File
Combines all arithmetic, DI, number series, and quadratic questions
"""

import os
import sys
import json
from datetime import datetime
from collections import defaultdict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.quant_utils import save_to_json, ensure_directory_exists

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_DIR = "data/generated/quant_questions"
OUTPUT_DIR = "data/generated/master_questions"
OUTPUT_FILE = "quant_master_question_bank.json"

# All quant question files
QUANT_FILES = [
    # Arithmetic (8 topics × 15 questions = 120)
    "arithmetic_percentage_questions.json",
    "arithmetic_profit_loss_questions.json",
    "arithmetic_interest_questions.json",
    "arithmetic_ratio_questions.json",
    "arithmetic_time_speed_questions.json",
    "arithmetic_time_work_questions.json",
    "arithmetic_averages_questions.json",
    "arithmetic_mixtures_questions.json",
    
    # Data Interpretation (5 types × 5 sets × 5 questions = 125)
    "di_tabular_questions.json",
    "di_bar_questions.json",
    "di_line_questions.json",
    "di_pie_questions.json",
    "di_caselet_questions.json",
    
    # Number Series (30 questions)
    "number_series_questions.json",
    
    # Quadratic Equations (30 questions)
    "quadratic_questions.json"
]

# ============================================================================
# MERGE FUNCTIONS
# ============================================================================

def load_json_file(filepath: str) -> list:
    """Load questions from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle different formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "questions" in data:
                return data["questions"]
            elif isinstance(data, dict) and "sets" in data:
                # DI format - flatten sets into questions
                questions = []
                for set_data in data["sets"]:
                    if "questions" in set_data:
                        questions.extend(set_data["questions"])
                return questions
            else:
                print(f"⚠️  Unknown format in {filepath}")
                return []
    except FileNotFoundError:
        print(f"⚠️  File not found: {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ JSON error in {filepath}: {e}")
        return []
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return []


def get_question_stats(questions: list) -> dict:
    """Calculate detailed statistics for questions"""
    stats = {
        "total_questions": len(questions),
        "by_topic": defaultdict(int),
        "by_difficulty": defaultdict(int),
        "by_subtopic": defaultdict(int),
        "total_cost": 0.0,
        "files_processed": 0
    }
    
    for q in questions:
        # Topic count
        topic = q.get("topic", "Unknown")
        stats["by_topic"][topic] += 1
        
        # Difficulty count
        difficulty = q.get("difficulty", "Unknown")
        stats["by_difficulty"][difficulty] += 1
        
        # Subtopic count
        subtopic = q.get("subtopic", "Unknown")
        if subtopic != "Unknown":
            stats["by_subtopic"][subtopic] += 1
        
        # Cost
        metadata = q.get("metadata", {})
        api_cost = metadata.get("api_cost", 0.0)
        if isinstance(api_cost, (int, float)):
            stats["total_cost"] += api_cost
    
    return stats


def print_stats(stats: dict, title: str = "Statistics"):
    """Pretty print statistics"""
    print("\n" + "="*70)
    print(f"📊 {title}")
    print("="*70)
    
    print(f"\n✅ Total Questions: {stats['total_questions']}")
    print(f"💰 Total Cost: ${stats['total_cost']:.4f}")
    print(f"📁 Files Processed: {stats['files_processed']}")
    
    print(f"\n📈 By Difficulty:")
    for difficulty in ["Easy", "Medium", "Hard"]:
        count = stats['by_difficulty'].get(difficulty, 0)
        percentage = (count / stats['total_questions'] * 100) if stats['total_questions'] > 0 else 0
        print(f"   {difficulty:10s}: {count:3d} ({percentage:5.1f}%)")
    
    print(f"\n📚 By Topic:")
    for topic, count in sorted(stats['by_topic'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats['total_questions'] * 100) if stats['total_questions'] > 0 else 0
        print(f"   {topic:30s}: {count:3d} ({percentage:5.1f}%)")
    
    if stats['by_subtopic']:
        print(f"\n📖 Top 10 Subtopics:")
        sorted_subtopics = sorted(stats['by_subtopic'].items(), key=lambda x: x[1], reverse=True)[:10]
        for subtopic, count in sorted_subtopics:
            print(f"   {subtopic:30s}: {count:3d}")


def merge_quant_questions() -> bool:
    """Main function to merge all quant questions"""
    
    print("\n" + "="*70)
    print("🚀 MERGING QUANT QUESTIONS")
    print("="*70)
    
    ensure_directory_exists(OUTPUT_DIR)
    
    all_questions = []
    files_found = 0
    files_missing = 0
    
    print(f"\n📂 Loading from: {INPUT_DIR}")
    print(f"📂 Output to: {OUTPUT_DIR}/{OUTPUT_FILE}")
    
    # Load all files
    for filename in QUANT_FILES:
        filepath = os.path.join(INPUT_DIR, filename)
        print(f"\n📄 Loading: {filename}")
        
        questions = load_json_file(filepath)
        
        if questions:
            all_questions.extend(questions)
            files_found += 1
            print(f"   ✅ Loaded {len(questions)} questions")
        else:
            files_missing += 1
            print(f"   ⚠️  No questions loaded")
    
    print(f"\n{'='*70}")
    print(f"📊 LOAD SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Files found: {files_found}/{len(QUANT_FILES)}")
    print(f"⚠️  Files missing: {files_missing}/{len(QUANT_FILES)}")
    print(f"📝 Total questions loaded: {len(all_questions)}")
    
    if not all_questions:
        print("\n❌ No questions to merge!")
        return False
    
    # Renumber questions
    print(f"\n🔢 Renumbering questions...")
    for i, q in enumerate(all_questions, 1):
        # Preserve original question_id as backup
        if "question_id" in q and "original_question_id" not in q:
            q["original_question_id"] = q["question_id"]
        
        # Create new master ID
        topic_prefix = q.get("topic", "QUANT")[:3].upper()
        q["question_id"] = f"QUANT_{i:04d}"
        q["master_question_number"] = i
    
    # Calculate statistics
    stats = get_question_stats(all_questions)
    stats["files_processed"] = files_found
    
    # Print statistics
    print_stats(stats, "QUANT MASTER BANK STATISTICS")
    
    # Create master object
    master_data = {
        "section": "Quantitative Aptitude",
        "total_questions": len(all_questions),
        "generation_date": datetime.now().isoformat(),
        "statistics": {
            "total_questions": stats["total_questions"],
            "by_difficulty": dict(stats["by_difficulty"]),
            "by_topic": dict(stats["by_topic"]),
            "total_cost": round(stats["total_cost"], 4),
            "files_merged": files_found
        },
        "topics_included": [
            "Arithmetic (8 topics)",
            "Data Interpretation (5 types)",
            "Number Series",
            "Quadratic Equations"
        ],
        "questions": all_questions
    }
    
    # Save master file
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    print(f"\n💾 Saving master file...")
    
    if save_to_json(master_data, output_path, indent=2):
        file_size = os.path.getsize(output_path) / 1024
        print(f"✅ Saved to: {output_path}")
        print(f"📦 File size: {file_size:.2f} KB")
        print(f"\n🎉 MERGE COMPLETE!")
        return True
    else:
        print(f"❌ Failed to save master file")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    return merge_quant_questions()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
