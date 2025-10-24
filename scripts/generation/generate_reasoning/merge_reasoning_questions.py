"""
Merge all reasoning question JSON files into a single master file
"""

import os
import json
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_DIR = "data/generated/reasoning_questions"
OUTPUT_FILE = "data/generated/reasoning_master_questions.json"

# ============================================================================
# MAIN MERGE FUNCTION
# ============================================================================

def merge_reasoning_questions():
    """
    Merge all JSON files containing '_questions' into a single master file
    """
    
    print("=" * 80)
    print("REASONING QUESTIONS MERGER")
    print("=" * 80)
    print(f"Input Directory: {INPUT_DIR}")
    print(f"Output File: {OUTPUT_FILE}")
    print("=" * 80)
    print()
    
    # Check if input directory exists
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Error: Directory '{INPUT_DIR}' does not exist!")
        return
    
    # Get all JSON files containing '_questions'
    json_files = [
        f for f in os.listdir(INPUT_DIR)
        if f.endswith('.json') and '_questions' in f
    ]
    
    if not json_files:
        print(f"❌ No JSON files containing '_questions' found in '{INPUT_DIR}'")
        return
    
    print(f"📂 Found {len(json_files)} question files to merge:")
    for idx, file in enumerate(json_files, 1):
        print(f"   {idx}. {file}")
    print()
    
    # Merge all questions
    all_questions = []
    file_stats = []
    total_files_processed = 0
    total_files_failed = 0
    
    for file in sorted(json_files):
        file_path = os.path.join(INPUT_DIR, file)
        
        try:
            print(f"📄 Processing: {file}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract questions (handle different JSON structures)
            questions = []
            if isinstance(data, dict):
                if 'questions' in data:
                    questions = data['questions']
                elif 'data' in data and isinstance(data['data'], list):
                    questions = data['data']
                else:
                    # Try to find any list in the dict
                    for value in data.values():
                        if isinstance(value, list):
                            questions = value
                            break
            elif isinstance(data, list):
                questions = data
            
            if not questions:
                print(f"   ⚠️  Warning: No questions found in {file}")
                total_files_failed += 1
                continue
            
            # Add source file information to each question
            for question in questions:
                if isinstance(question, dict):
                    question['source_file'] = file
            
            all_questions.extend(questions)
            total_files_processed += 1
            
            file_stats.append({
                "file": file,
                "questions_count": len(questions)
            })
            
            print(f"   ✅ Loaded {len(questions)} questions")
            
        except json.JSONDecodeError as e:
            print(f"   ❌ Error: Invalid JSON in {file} - {str(e)}")
            total_files_failed += 1
        except Exception as e:
            print(f"   ❌ Error processing {file}: {str(e)}")
            total_files_failed += 1
    
    print()
    print("=" * 80)
    print("MERGE SUMMARY")
    print("=" * 80)
    print(f"Total files found: {len(json_files)}")
    print(f"Files processed successfully: {total_files_processed}")
    print(f"Files failed: {total_files_failed}")
    print(f"Total questions merged: {len(all_questions)}")
    print()
    
    if not all_questions:
        print("❌ No questions to save!")
        return
    
    # Create master file structure
    master_data = {
        "metadata": {
            "title": "Reasoning Master Questions",
            "description": "Merged collection of all reasoning question types",
            "total_questions": len(all_questions),
            "merge_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_files": file_stats,
            "categories": {}
        },
        "questions": all_questions
    }
    
    # Calculate category distribution
    categories = {}
    topics = {}
    difficulties = {"Easy": 0, "Medium": 0, "Hard": 0}
    
    for question in all_questions:
        if isinstance(question, dict):
            # Count by main category
            category = question.get("main_category", "Unknown")
            categories[category] = categories.get(category, 0) + 1
            
            # Count by topic
            topic = question.get("topic", "Unknown")
            topics[topic] = topics.get(topic, 0) + 1
            
            # Count by difficulty
            difficulty = question.get("difficulty", "Unknown")
            if difficulty in difficulties:
                difficulties[difficulty] += 1
    
    master_data["metadata"]["categories"] = categories
    master_data["metadata"]["topics"] = topics
    master_data["metadata"]["difficulty_distribution"] = difficulties
    
    # Save master file
    try:
        # Create output directory if needed
        output_dir = os.path.dirname(OUTPUT_FILE)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully saved master file: {OUTPUT_FILE}")
        print()
        
        # Display statistics
        print("📊 QUESTION STATISTICS")
        print("=" * 80)
        
        print("\n📋 By Category:")
        for category, count in sorted(categories.items()):
            percentage = (count / len(all_questions)) * 100
            print(f"   {category}: {count} ({percentage:.1f}%)")
        
        print("\n📚 By Topic:")
        for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(all_questions)) * 100
            print(f"   {topic}: {count} ({percentage:.1f}%)")
        
        print("\n📊 By Difficulty:")
        for difficulty, count in sorted(difficulties.items()):
            percentage = (count / len(all_questions)) * 100 if len(all_questions) > 0 else 0
            print(f"   {difficulty}: {count} ({percentage:.1f}%)")
        
        print()
        print("=" * 80)
        
        # Calculate file size
        file_size = os.path.getsize(OUTPUT_FILE)
        file_size_mb = file_size / (1024 * 1024)
        print(f"💾 File size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        
        print("=" * 80)
        print("✅ MERGE COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error saving master file: {str(e)}")


# ============================================================================
# RUN THE MERGE
# ============================================================================

if __name__ == "__main__":
    merge_reasoning_questions()
