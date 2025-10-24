import json
import csv
import os
from datetime import datetime
from collections import Counter

# ==================== CONFIGURATION ====================

MANUAL_CHANGES_CSV = "data/generated/reasoning_questions/reasoning_manual_category_change.csv"
MASTER_JSON = "data/generated/reasoning_questions/reasoning_master_questions.json"
OUTPUT_DIR = "data/generated/reasoning_questions/"
BY_TOPIC_DIR = os.path.join(OUTPUT_DIR, "by_topic/")

# ==================== LOAD MANUAL CHANGES ====================

def load_manual_changes():
    """Load manual category changes from CSV"""
    
    print("\n" + "="*70)
    print("📋 LOADING MANUAL CATEGORY CHANGES")
    print("="*70)
    
    changes = {}
    
    try:
        with open(MANUAL_CHANGES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                question_id = row['question_id'].strip()
                changes[question_id] = {
                    'reasoning_topic': row['reasoning_topic'].strip(),
                    'topic': row['topic'].strip(),
                    'main_category': row['main_category'].strip()
                }
        
        print(f"✅ Loaded {len(changes)} manual changes from CSV")
        return changes
    
    except FileNotFoundError:
        print(f"❌ ERROR: File not found: {MANUAL_CHANGES_CSV}")
        return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None


# ==================== UPDATE MASTER JSON ====================

def update_master_json(changes):
    """Update the master JSON file with manual changes"""
    
    print("\n" + "="*70)
    print("🔄 UPDATING MASTER JSON FILE")
    print("="*70)
    
    # Load master JSON
    try:
        with open(MASTER_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: Master JSON not found: {MASTER_JSON}")
        return None
    
    questions = data['questions']
    updated_count = 0
    not_found = []
    
    # Apply changes
    for question in questions:
        question_id = question.get('question_id', '')
        
        if question_id in changes:
            # Update the fields
            question['reasoning_topic'] = changes[question_id]['reasoning_topic']
            question['topic'] = changes[question_id]['topic']
            question['main_category'] = changes[question_id]['main_category']
            
            # Update metadata
            if 'metadata' not in question:
                question['metadata'] = {}
            question['metadata']['manually_updated'] = True
            question['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            updated_count += 1
            print(f"   ✅ Updated: {question_id} → {changes[question_id]['reasoning_topic']}")
    
    # Check for IDs not found
    for question_id in changes.keys():
        if not any(q.get('question_id') == question_id for q in questions):
            not_found.append(question_id)
    
    if not_found:
        print(f"\n⚠️  WARNING: {len(not_found)} question IDs not found in master JSON:")
        for qid in not_found:
            print(f"   • {qid}")
    
    # Save updated master JSON
    data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['metadata']['manual_updates_applied'] = updated_count
    
    with open(MASTER_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Master JSON updated successfully")
    print(f"   📊 Total questions updated: {updated_count}")
    
    return questions


# ==================== CALCULATE STATISTICS ====================

def calculate_statistics(questions):
    """Calculate comprehensive statistics"""
    
    print("\n" + "="*70)
    print("📊 CALCULATING STATISTICS")
    print("="*70)
    
    stats = {
        'total_questions': len(questions),
        'by_reasoning_topic': Counter(),
        'by_main_category': Counter(),
        'by_difficulty': Counter(),
        'manually_updated_count': 0
    }
    
    for q in questions:
        stats['by_reasoning_topic'][q.get('reasoning_topic', 'Unknown')] += 1
        stats['by_main_category'][q.get('main_category', 'Unknown')] += 1
        stats['by_difficulty'][q.get('difficulty', 'Unknown')] += 1
        
        if q.get('metadata', {}).get('manually_updated', False):
            stats['manually_updated_count'] += 1
    
    # Convert Counter to dict for JSON serialization
    stats['by_reasoning_topic'] = dict(stats['by_reasoning_topic'])
    stats['by_main_category'] = dict(stats['by_main_category'])
    stats['by_difficulty'] = dict(stats['by_difficulty'])
    
    return stats


# ==================== PRINT STATISTICS ====================

def print_statistics(stats):
    """Print statistics to console"""
    
    print(f"\n📊 Total Questions: {stats['total_questions']}")
    print(f"📝 Manually Updated: {stats['manually_updated_count']}")
    
    print(f"\n📂 By Main Category:")
    for category, count in sorted(stats['by_main_category'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats['total_questions']) * 100
        print(f"   {category:<45}: {count:>3} ({percentage:>5.1f}%)")
    
    print(f"\n🏷️  By Reasoning Topic:")
    for topic, count in sorted(stats['by_reasoning_topic'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats['total_questions']) * 100
        print(f"   {topic:<45}: {count:>3} ({percentage:>5.1f}%)")


# ==================== SAVE STATISTICS JSON ====================

def save_statistics_json(stats):
    """Save statistics to JSON file"""
    
    stats_file = os.path.join(OUTPUT_DIR, "reasoning_statistics.json")
    
    stats_data = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'statistics': stats
    }
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Statistics saved: {stats_file}")


# ==================== SAVE BY CATEGORY ====================

def save_by_category(questions):
    """Save questions grouped by main category"""
    
    print("\n" + "="*70)
    print("📁 SAVING CATEGORY-WISE JSON FILES")
    print("="*70)
    
    # Group by main category
    categories = {}
    for q in questions:
        category = q.get('main_category', 'Unknown')
        if category not in categories:
            categories[category] = []
        categories[category].append(q)
    
    # Save each category
    for category, cat_questions in categories.items():
        # Create safe filename
        safe_name = category.lower().replace(' ', '_').replace('&', 'and').replace('/', '_')
        filename = os.path.join(OUTPUT_DIR, f"{safe_name}.json")
        
        category_data = {
            'category': category,
            'total_questions': len(cat_questions),
            'questions': cat_questions,
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'RBI_Master_Dataset'
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(category_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ {category}: {len(cat_questions)} questions → {safe_name}.json")


# ==================== SAVE BY TOPIC ====================

def save_by_topic(questions):
    """Save questions grouped by reasoning topic"""
    
    print("\n" + "="*70)
    print("📁 SAVING TOPIC-WISE JSON FILES")
    print("="*70)
    
    # Create by_topic directory if it doesn't exist
    os.makedirs(BY_TOPIC_DIR, exist_ok=True)
    
    # Group by reasoning topic
    topics = {}
    for q in questions:
        topic = q.get('reasoning_topic', 'Unknown')
        if topic not in topics:
            topics[topic] = []
        topics[topic].append(q)
    
    # Save each topic
    for topic, topic_questions in sorted(topics.items()):
        # Create safe filename
        safe_name = topic.lower().replace(' ', '_').replace('&', 'and').replace('/', '_')
        filename = os.path.join(BY_TOPIC_DIR, f"{safe_name}.json")
        
        topic_data = {
            'topic': topic,
            'total_questions': len(topic_questions),
            'questions': topic_questions,
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'RBI_Master_Dataset'
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(topic_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ {topic}: {len(topic_questions)} questions → {safe_name}.json")


# ==================== MAIN EXECUTION ====================

def main():
    """Main execution function"""
    
    start_time = datetime.now()
    
    print("\n" + "="*70)
    print("🔄 REASONING QUESTIONS - MANUAL UPDATE & REGENERATION")
    print("="*70)
    print(f"📅 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Load manual changes from CSV
    changes = load_manual_changes()
    if changes is None or len(changes) == 0:
        print("\n❌ No changes to apply. Exiting.")
        return
    
    # Step 2: Update master JSON
    questions = update_master_json(changes)
    if questions is None:
        print("\n❌ Failed to update master JSON. Exiting.")
        return
    
    # Step 3: Calculate statistics
    stats = calculate_statistics(questions)
    print_statistics(stats)
    
    # Step 4: Save statistics JSON
    save_statistics_json(stats)
    
    # Step 5: Save by category
    save_by_category(questions)
    
    # Step 6: Save by topic
    save_by_topic(questions)
    
    # Final summary
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("✅ UPDATE & REGENERATION COMPLETE")
    print("="*70)
    print(f"⏱️  Time taken: {duration:.2f} seconds")
    print(f"\n📊 Summary:")
    print(f"   📝 Total questions: {len(questions)}")
    print(f"   🔄 Manually updated: {stats['manually_updated_count']}")
    print(f"   🏷️  Topics: {len(stats['by_reasoning_topic'])}")
    print(f"   📂 Categories: {len(stats['by_main_category'])}")
    
    print("\n📁 Files Updated:")
    print(f"   ✅ reasoning_master_questions.json")
    print(f"   ✅ reasoning_statistics.json")
    print(f"   ✅ {len(stats['by_main_category'])} category files")
    print(f"   ✅ {len(stats['by_reasoning_topic'])} topic files in by_topic/")
    
    print("\n" + "="*70)
    print("🎉 ALL DONE! Your reasoning questions are updated!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
