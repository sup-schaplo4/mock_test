"""
Merge Quant Questions by Category
- Arithmetic: Merges all arithmetic_*.json files
- Data Interpretation: Merges all di_*.json files
- Number Series: Single file
- Quadratic Equations: Single file
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

# Category configurations
CATEGORIES = {
    "arithmetic": {
        "prefix": "arithmetic_",
        "output_file": "arithmetic_master_question_bank.json",
        "category_name": "Arithmetic",
        "expected_files": 8,  # 8 topics
        "expected_questions": 120  # 8 topics × 15 questions
    },
    "data_interpretation": {
        "prefix": "di_",
        "output_file": "di_master_question_bank.json",
        "category_name": "Data Interpretation",
        "expected_files": 10,  # 5 types
        "expected_questions": 250  # 5 types × 5 sets × 5 questions
    }
}

# ============================================================================
# HELPER FUNCTIONS
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
                        # Add set_id to each question
                        for q in set_data["questions"]:
                            q["set_id"] = set_data.get("set_id", "Unknown")
                            q["di_type"] = set_data.get("type", "Unknown")
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


def get_files_by_prefix(directory: str, prefix: str) -> list:
    """Get all files starting with prefix"""
    try:
        all_files = os.listdir(directory)
        matching_files = [f for f in all_files if f.startswith(prefix) and f.endswith('.json')]
        return sorted(matching_files)
    except Exception as e:
        print(f"❌ Error listing directory: {e}")
        return []


def calculate_stats(questions: list) -> dict:
    """Calculate statistics for questions"""
    stats = {
        "total_questions": len(questions),
        "by_topic": defaultdict(int),
        "by_subtopic": defaultdict(int),
        "by_difficulty": defaultdict(int),
        "by_file": defaultdict(int),
        "total_cost": 0.0
    }
    
    for q in questions:
        # Topic
        topic = q.get("topic", "Unknown")
        stats["by_topic"][topic] += 1
        
        # Subtopic
        subtopic = q.get("subtopic", "Unknown")
        if subtopic != "Unknown":
            stats["by_subtopic"][subtopic] += 1
        
        # Difficulty
        difficulty = q.get("difficulty", "Unknown")
        stats["by_difficulty"][difficulty] += 1
        
        # Source file
        source = q.get("source_file", "Unknown")
        stats["by_file"][source] += 1
        
        # Cost
        metadata = q.get("metadata", {})
        api_cost = metadata.get("api_cost", 0.0)
        if isinstance(api_cost, (int, float)):
            stats["total_cost"] += api_cost
    
    return stats


def print_category_stats(category_name: str, stats: dict, expected_questions: int):
    """Print detailed statistics for a category"""
    print("\n" + "="*70)
    print(f"📊 {category_name.upper()} STATISTICS")
    print("="*70)
    
    actual = stats["total_questions"]
    difference = actual - expected_questions
    status = "✅" if difference == 0 else "⚠️"
    
    print(f"\n{status} Total Questions: {actual} (Expected: {expected_questions}, Diff: {difference:+d})")
    print(f"💰 Total Cost: ${stats['total_cost']:.4f}")
    print(f"📁 Files Processed: {len(stats['by_file'])}")
    
    # Difficulty breakdown
    print(f"\n📈 By Difficulty:")
    for difficulty in ["Easy", "Medium", "Hard"]:
        count = stats['by_difficulty'].get(difficulty, 0)
        percentage = (count / actual * 100) if actual > 0 else 0
        print(f"   {difficulty:10s}: {count:3d} ({percentage:5.1f}%)")
    
    # Topic breakdown
    print(f"\n📚 By Topic:")
    for topic, count in sorted(stats['by_topic'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / actual * 100) if actual > 0 else 0
        print(f"   {topic:30s}: {count:3d} ({percentage:5.1f}%)")
    
    # File breakdown
    print(f"\n📄 By Source File:")
    for filename, count in sorted(stats['by_file'].items()):
        print(f"   {filename:40s}: {count:3d}")
    
    # Top subtopics
    if stats['by_subtopic']:
        print(f"\n📖 Top 10 Subtopics:")
        sorted_subtopics = sorted(stats['by_subtopic'].items(), key=lambda x: x[1], reverse=True)[:10]
        for subtopic, count in sorted_subtopics:
            print(f"   {subtopic:35s}: {count:3d}")


# ============================================================================
# MERGE FUNCTION
# ============================================================================

def merge_category(category_key: str, config: dict) -> bool:
    """Merge all files for a specific category"""
    
    prefix = config["prefix"]
    output_file = config["output_file"]
    category_name = config["category_name"]
    expected_files = config["expected_files"]
    expected_questions = config["expected_questions"]
    
    print("\n" + "="*70)
    print(f"🚀 MERGING {category_name.upper()}")
    print("="*70)
    print(f"📂 Input: {INPUT_DIR}")
    print(f"📂 Output: {OUTPUT_DIR}/{output_file}")
    print(f"🔍 Prefix: {prefix}*.json")
    print(f"🎯 Expected: {expected_files} files, {expected_questions} questions")
    print("="*70)
    
    # Get all matching files
    matching_files = get_files_by_prefix(INPUT_DIR, prefix)
    
    print(f"\n✅ Found {len(matching_files)} files:")
    for f in matching_files:
        print(f"   - {f}")
    
    if len(matching_files) != expected_files:
        print(f"\n⚠️  Warning: Expected {expected_files} files, found {len(matching_files)}")
    
    # Load all files
    all_questions = []
    files_loaded = 0
    files_failed = 0
    
    print(f"\n📥 Loading files...")
    for filename in matching_files:
        filepath = os.path.join(INPUT_DIR, filename)
        print(f"\n   📄 {filename}")
        
        questions = load_json_file(filepath)
        
        if questions:
            # Tag questions with source file
            for q in questions:
                q["source_file"] = filename
                q["category"] = category_name
            
            all_questions.extend(questions)
            files_loaded += 1
            print(f"      ✅ Loaded {len(questions)} questions")
        else:
            files_failed += 1
            print(f"      ❌ Failed to load")
    
    print(f"\n{'='*70}")
    print(f"📊 LOAD SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Files loaded: {files_loaded}/{len(matching_files)}")
    print(f"❌ Files failed: {files_failed}/{len(matching_files)}")
    print(f"📝 Total questions: {len(all_questions)}")
    
    if not all_questions:
        print(f"\n❌ No questions loaded for {category_name}!")
        return False
    
    # Renumber questions
    print(f"\n🔢 Renumbering questions...")
    category_prefix = category_key.upper()[:4]
    
    for i, q in enumerate(all_questions, 1):
        # Preserve original ID
        if "question_id" in q and "original_question_id" not in q:
            q["original_question_id"] = q["question_id"]
        
        # Create new category-specific ID
        q["question_id"] = f"{category_prefix}_{i:04d}"
        q["category_question_number"] = i
    
    print(f"   ✅ Renumbered {len(all_questions)} questions")
    
    # Calculate statistics
    stats = calculate_stats(all_questions)
    
    # Print statistics
    print_category_stats(category_name, stats, expected_questions)
    
    # Create master object
    master_data = {
        "category": category_name,
        "total_questions": len(all_questions),
        "generation_date": datetime.now().isoformat(),
        "statistics": {
            "total_questions": stats["total_questions"],
            "expected_questions": expected_questions,
            "difference": stats["total_questions"] - expected_questions,
            "by_difficulty": dict(stats["by_difficulty"]),
            "by_topic": dict(stats["by_topic"]),
            "by_subtopic": dict(stats["by_subtopic"]),
            "total_cost": round(stats["total_cost"], 4),
            "files_merged": files_loaded
        },
        "source_files": matching_files,
        "questions": all_questions
    }
    
    # Save
    ensure_directory_exists(OUTPUT_DIR)
    output_path = os.path.join(OUTPUT_DIR, output_file)
    
    print(f"\n💾 Saving to: {output_path}")
    
    if save_to_json(master_data, output_path, indent=2):
        file_size = os.path.getsize(output_path) / 1024
        print(f"✅ Saved successfully")
        print(f"📦 File size: {file_size:.2f} KB")
        print(f"\n🎉 {category_name.upper()} MERGE COMPLETE!")
        return True
    else:
        print(f"❌ Failed to save {category_name}")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Merge all categories"""
    
    print("\n" + "="*70)
    print("🚀 QUANT CATEGORY MERGER")
    print("="*70)
    print(f"Categories to merge: {len(CATEGORIES)}")
    for cat_key, cat_config in CATEGORIES.items():
        print(f"   - {cat_config['category_name']}")
    print("="*70)
    
    results = {}
    
    # Merge each category
    for category_key, config in CATEGORIES.items():
        success = merge_category(category_key, config)
        results[config['category_name']] = success
    
    # Final summary
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)
    
    for category_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {category_name}")
    
    all_success = all(results.values())
    
    if all_success:
        print(f"\n🎉 ALL CATEGORIES MERGED SUCCESSFULLY!")
        
        # Show output files
        print(f"\n📁 Output files created:")
        for config in CATEGORIES.values():
            output_path = os.path.join(OUTPUT_DIR, config['output_file'])
            if os.path.exists(output_path):
                size = os.path.getsize(output_path) / 1024
                print(f"   ✅ {config['output_file']} ({size:.2f} KB)")
    else:
        print(f"\n⚠️  Some categories failed to merge")
    
    return all_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
