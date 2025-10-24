import json
import os
import random
from datetime import datetime
from collections import Counter

# ==================== CONFIGURATION ====================

# Paths to combine
PATHS_TO_COMBINE = [
    "data/generated/ga_questions/current_affairs_questions/",
    "data/generated/ga_questions/pib_questions/",
    "data/generated/ga_questions/pilot_ga/",
    "data/generated/ga_questions/reports_questions/"

]

# Output paths
OUTPUT_FILE = "data/generated/master_questions/general_awareness_master_question_bank.json"
PRACTICE_SETS_DIR = "data/generated/ga_questions/practice_sets/"

# Practice set configuration
PRACTICE_SET_CONFIG = {
    'num_sets': 5,  # Number of practice sets to create
    'questions_per_set': 30,  # Questions per set
    'difficulty_distribution': {
        'Hard': 0.30,    # 30%
        'Medium': 0.40,  # 40%
        'Easy': 0.30     # 30%
    }
}

# ==================== COMBINE FUNCTIONS ====================

def load_json_files(directory):
    """Load all JSON files from a directory"""
    
    questions = []
    metadata_list = []
    
    if not os.path.exists(directory):
        print(f"   ⚠️  Directory not found: {directory}")
        return questions, metadata_list
    
    json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
    
    if not json_files:
        print(f"   ⚠️  No JSON files in: {directory}")
        return questions, metadata_list
    
    print(f"\n📁 Processing: {directory}")
    print(f"   Found {len(json_files)} JSON file(s)")
    
    for filename in json_files:
        filepath = os.path.join(directory, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract questions
            if isinstance(data, dict):
                if 'questions' in data:
                    file_questions = data['questions']
                    questions.extend(file_questions)
                    print(f"   ✅ {filename}: {len(file_questions)} questions")
                    
                    # Store metadata
                    if 'metadata' in data:
                        metadata_list.append({
                            'filename': filename,
                            'metadata': data['metadata']
                        })
                elif 'question' in data:
                    # Single question format
                    questions.append(data)
                    print(f"   ✅ {filename}: 1 question")
            elif isinstance(data, list):
                # Direct list of questions
                questions.extend(data)
                print(f"   ✅ {filename}: {len(data)} questions")
        
        except Exception as e:
            print(f"   ❌ Error loading {filename}: {e}")
    
    return questions, metadata_list


def remove_duplicates(questions):
    """Remove duplicate questions based on question text"""
    
    print(f"\n🔍 Checking for duplicates...")
    print(f"   Initial count: {len(questions)}")
    
    seen_questions = set()
    unique_questions = []
    duplicates = 0
    
    for q in questions:
        question_text = q.get('question', '').strip().lower()
        
        if question_text and question_text not in seen_questions:
            seen_questions.add(question_text)
            unique_questions.append(q)
        else:
            duplicates += 1
    
    print(f"   Duplicates removed: {duplicates}")
    print(f"   Unique questions: {len(unique_questions)}")
    
    return unique_questions


def add_unique_ids(questions):
    """Add unique IDs to all questions"""
    
    print(f"\n🔢 Adding unique IDs...")
    
    for i, q in enumerate(questions, 1):
        q['question_id'] = f"GA_{i:05d}"
    
    print(f"   ✅ Added IDs: GA_00001 to GA_{len(questions):05d}")
    
    return questions


def calculate_statistics(questions):
    """Calculate comprehensive statistics"""
    
    stats = {
        'total_questions': len(questions),
        'difficulty_distribution': {},
        'topic_distribution': {},
        'category_distribution': {},
        'source_distribution': {},
        'subject_distribution': {}
    }
    
    # Difficulty
    diff_count = Counter([q.get('difficulty') for q in questions if q.get('difficulty') is not None])
    stats['difficulty_distribution'] = {
        'Hard': diff_count.get('Hard', 0),
        'Medium': diff_count.get('Medium', 0),
        'Easy': diff_count.get('Easy', 0)
    }
    
    # Topics
    topic_count = Counter([q.get('topic') for q in questions if q.get('topic') is not None])
    stats['topic_distribution'] = dict(topic_count.most_common())
    
    # Categories
    category_count = Counter([q.get('category') for q in questions if q.get('category') is not None])
    stats['category_distribution'] = dict(category_count)
    
    # Sources
    source_count = Counter([q.get('source_document', 'Unknown') for q in questions])
    stats['source_distribution'] = dict(source_count)
    
    # Subjects
    subject_count = Counter([q.get('subject', 'General_Awareness') for q in questions])
    stats['subject_distribution'] = dict(subject_count)
    
    return stats


def print_statistics(stats):
    """Print detailed statistics"""
    
    print("\n" + "="*70)
    print("📊 MASTER QUESTION BANK STATISTICS")
    print("="*70)
    
    print(f"\n📝 Total Questions: {stats['total_questions']}")
    
    # Difficulty
    print(f"\n🎚️  Difficulty Distribution:")
    diff = stats['difficulty_distribution']
    total = stats['total_questions']
    print(f"   Hard:   {diff.get('Hard', 0):>4} ({diff.get('Hard', 0)/total*100:>5.1f}%)")
    print(f"   Medium: {diff.get('Medium', 0):>4} ({diff.get('Medium', 0)/total*100:>5.1f}%)")
    print(f"   Easy:   {diff.get('Easy', 0):>4} ({diff.get('Easy', 0)/total*100:>5.1f}%)")
    
    # Categories
    print(f"\n📂 Category Distribution:")
    for category, count in stats['category_distribution'].items():
        print(f"   {category:<30}: {count:>4} ({count/total*100:>5.1f}%)")
    
    # Top 10 Topics
    print(f"\n📌 Top 10 Topics:")
    topic_items = list(stats['topic_distribution'].items())[:10]
    for i, (topic, count) in enumerate(topic_items, 1):
        print(f"   {i:>2}. {topic:<35}: {count:>4} ({count/total*100:>5.1f}%)")
    
    if len(stats['topic_distribution']) > 10:
        print(f"   ... and {len(stats['topic_distribution']) - 10} more topics")
    
    # Sources
    print(f"\n📄 Source Distribution:")
    for source, count in stats['source_distribution'].items():
        print(f"   {source:<40}: {count:>4} ({count/total*100:>5.1f}%)")
    
    print("\n" + "="*70)


def save_master_bank(questions, stats, source_metadata):
    """Save the master question bank"""
    
    print(f"\n💾 Saving master question bank...")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    master_data = {
        'metadata': {
            'title': 'RBI Grade B - General Awareness Master Question Bank',
            'description': 'Combined question bank from Current Affairs, PIB, and RAG-generated questions',
            'creation_date': datetime.now().isoformat(),
            'version': '1.0',
            'total_questions': stats['total_questions'],
            'difficulty_distribution': stats['difficulty_distribution'],
            'category_distribution': stats['category_distribution'],
            'topic_distribution': stats['topic_distribution'],
            'source_distribution': stats['source_distribution'],
            'subject_distribution': stats['subject_distribution'],
            'sources_combined': [
                'Current Affairs Questions',
                'PIB Questions',
                'RAG-Generated GA Questions'
            ],
            'source_files_metadata': source_metadata
        },
        'questions': questions
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, indent=2, ensure_ascii=False)
    
    file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)  # MB
    
    print(f"   ✅ Saved: {OUTPUT_FILE}")
    print(f"   📦 File size: {file_size:.2f} MB")
    print(f"   📝 Total questions: {len(questions)}")


def validate_master_bank(questions):
    """Validate the master question bank"""
    
    print(f"\n🔍 Validating master question bank...")
    
    issues = []
    
    # Check for required fields
    required_fields = ['question', 'options', 'correct_answer', 'explanation', 'difficulty']
    
    for i, q in enumerate(questions, 1):
        for field in required_fields:
            if field not in q or not q[field]:
                issues.append(f"Q{i} ({q.get('question_id', 'NO_ID')}): Missing {field}")
        
        # Check options
        if 'options' in q:
            if not isinstance(q['options'], dict):
                issues.append(f"Q{i}: Options should be a dictionary")
            elif len(q['options']) != 5:
                issues.append(f"Q{i}: Should have 5 options")
        
        # Check correct answer
        if 'correct_answer' in q:
            if q['correct_answer'] not in ['A', 'B', 'C', 'D', 'E']:
                issues.append(f"Q{i}: Invalid correct_answer")
        
        # Check difficulty
        if 'difficulty' in q:
            if q['difficulty'] not in ['Hard', 'Medium', 'Easy']:
                issues.append(f"Q{i}: Invalid difficulty")
    
    if issues:
        print(f"   ⚠️  Found {len(issues)} validation issues")
        for issue in issues[:10]:
            print(f"      • {issue}")
        if len(issues) > 10:
            print(f"      ... and {len(issues) - 10} more")
    else:
        print(f"   ✅ All questions passed validation!")
    
    return len(issues) == 0


# ==================== PRACTICE SET GENERATION ====================

def create_practice_sets(questions):
    """Create practice sets from master question bank"""
    
    print("\n" + "="*70)
    print("📚 CREATING PRACTICE SETS")
    print("="*70)
    
    os.makedirs(PRACTICE_SETS_DIR, exist_ok=True)
    
    num_sets = PRACTICE_SET_CONFIG['num_sets']
    questions_per_set = PRACTICE_SET_CONFIG['questions_per_set']
    difficulty_dist = PRACTICE_SET_CONFIG['difficulty_distribution']
    
    print(f"\n⚙️  Configuration:")
    print(f"   Number of sets: {num_sets}")
    print(f"   Questions per set: {questions_per_set}")
    print(f"   Difficulty: Hard={difficulty_dist['Hard']*100:.0f}% "
          f"Medium={difficulty_dist['Medium']*100:.0f}% "
          f"Easy={difficulty_dist['Easy']*100:.0f}%")
    
    # Group questions by difficulty
    questions_by_difficulty = {
        'Hard': [q for q in questions if q.get('difficulty') == 'Hard'],
        'Medium': [q for q in questions if q.get('difficulty') == 'Medium'],
        'Easy': [q for q in questions if q.get('difficulty') == 'Easy']
    }
    
    print(f"\n📊 Available questions:")
    print(f"   Hard: {len(questions_by_difficulty['Hard'])}")
    print(f"   Medium: {len(questions_by_difficulty['Medium'])}")
    print(f"   Easy: {len(questions_by_difficulty['Easy'])}")
    
    # Calculate questions needed per difficulty
    needed = {
        'Hard': int(questions_per_set * difficulty_dist['Hard']),
        'Medium': int(questions_per_set * difficulty_dist['Medium']),
        'Easy': int(questions_per_set * difficulty_dist['Easy'])
    }
    
    # Adjust for rounding
    total_needed = sum(needed.values())
    if total_needed < questions_per_set:
        needed['Medium'] += (questions_per_set - total_needed)
    
    print(f"\n📋 Questions per set:")
    print(f"   Hard: {needed['Hard']}")
    print(f"   Medium: {needed['Medium']}")
    print(f"   Easy: {needed['Easy']}")
    
    # Check if we have enough questions
    for diff in ['Hard', 'Medium', 'Easy']:
        required = needed[diff] * num_sets
        available = len(questions_by_difficulty[diff])
        if available < required:
            print(f"\n⚠️  Warning: Not enough {diff} questions!")
            print(f"   Required: {required}, Available: {available}")
            print(f"   Some questions will be reused across sets.")
    
    # Create practice sets
    practice_sets = []
    used_questions = set()
    
    for set_num in range(1, num_sets + 1):
        print(f"\n📝 Creating Practice Set {set_num}...")
        
        set_questions = []
        
        # Select questions for each difficulty
        for difficulty in ['Hard', 'Medium', 'Easy']:
            available = [q for q in questions_by_difficulty[difficulty] 
                        if q.get('question_id') not in used_questions]
            
            # If not enough unused questions, use all questions
            if len(available) < needed[difficulty]:
                available = questions_by_difficulty[difficulty].copy()
                random.shuffle(available)
            
            # Select required number
            selected = random.sample(available, min(needed[difficulty], len(available)))
            set_questions.extend(selected)
            
            # Mark as used
            for q in selected:
                used_questions.add(q.get('question_id'))
        
        # Shuffle the set
        random.shuffle(set_questions)
        
        # Renumber questions within the set
        for i, q in enumerate(set_questions, 1):
            q['set_question_number'] = i
        
        # Calculate set statistics
        set_stats = calculate_statistics(set_questions)
        
        # Create practice set data
        practice_set = {
            'metadata': {
                'title': f'RBI Grade B - General Awareness Practice Set {set_num}',
                'set_number': set_num,
                'total_questions': len(set_questions),
                'creation_date': datetime.now().isoformat(),
                'difficulty_distribution': set_stats['difficulty_distribution'],
                'topic_distribution': set_stats['topic_distribution'],
                'category_distribution': set_stats['category_distribution'],
                'time_limit_minutes': 20,  # Suggested time limit
                'passing_score': 15,  # 50% passing
                'instructions': [
                    'This practice set contains 30 General Awareness questions',
                    'Each question has 5 options (A, B, C, D, E)',
                    'Only one option is correct',
                    'Recommended time: 20 minutes',
                    'No negative marking in practice mode'
                ]
            },
            'questions': set_questions
        }
        
        practice_sets.append(practice_set)
        
        # Save individual practice set
        set_filename = os.path.join(PRACTICE_SETS_DIR, f'practice_set_{set_num}.json')
        with open(set_filename, 'w', encoding='utf-8') as f:
            json.dump(practice_set, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Saved: {set_filename}")
        print(f"   📝 Questions: {len(set_questions)}")
        print(f"   🎚️  Difficulty: H={set_stats['difficulty_distribution'].get('Hard', 0)} "
              f"M={set_stats['difficulty_distribution'].get('Medium', 0)} "
              f"E={set_stats['difficulty_distribution'].get('Easy', 0)}")
    
    # Create consolidated practice sets file
    consolidated_file = os.path.join(PRACTICE_SETS_DIR, 'all_practice_sets.json')
    consolidated_data = {
        'metadata': {
            'title': 'RBI Grade B - All General Awareness Practice Sets',
            'total_sets': len(practice_sets),
            'questions_per_set': questions_per_set,
            'creation_date': datetime.now().isoformat(),
            'description': 'Comprehensive collection of practice sets for General Awareness'
        },
        'practice_sets': practice_sets
    }
    
    with open(consolidated_file, 'w', encoding='utf-8') as f:
        json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ All practice sets created successfully!")
    print(f"   📁 Directory: {PRACTICE_SETS_DIR}")
    print(f"   📚 Total sets: {len(practice_sets)}")
    print(f"   📝 Questions per set: {questions_per_set}")
    print(f"   📄 Consolidated file: {consolidated_file}")
    
    return practice_sets


def create_answer_keys(practice_sets):
    """Create answer keys for all practice sets"""
    
    print("\n" + "="*70)
    print("🔑 CREATING ANSWER KEYS")
    print("="*70)
    
    answer_keys_dir = os.path.join(PRACTICE_SETS_DIR, 'answer_keys')
    os.makedirs(answer_keys_dir, exist_ok=True)
    
    for practice_set in practice_sets:
        set_num = practice_set['metadata']['set_number']
        
        answer_key = {
            'metadata': {
                'title': f'Answer Key - Practice Set {set_num}',
                'set_number': set_num,
                'total_questions': practice_set['metadata']['total_questions'],
                'creation_date': datetime.now().isoformat()
            },
            'answers': []
        }
        
        for q in practice_set['questions']:
            answer_entry = {
                'question_number': q.get('set_question_number'),
                'question_id': q.get('question_id'),
                'correct_answer': q.get('correct_answer'),
                'difficulty': q.get('difficulty'),
                'topic': q.get('topic'),
                'explanation': q.get('explanation')
            }
            answer_key['answers'].append(answer_entry)
        
        # Save answer key
        answer_key_file = os.path.join(answer_keys_dir, f'answer_key_set_{set_num}.json')
        with open(answer_key_file, 'w', encoding='utf-8') as f:
            json.dump(answer_key, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Created answer key for Set {set_num}: {answer_key_file}")
    
    print(f"\n✅ All answer keys created!")
    print(f"   📁 Directory: {answer_keys_dir}")


def create_practice_set_summary():
    """Create a summary document for practice sets"""
    
    print("\n" + "="*70)
    print("📄 CREATING PRACTICE SET SUMMARY")
    print("="*70)
    
    summary_file = os.path.join(PRACTICE_SETS_DIR, 'PRACTICE_SETS_README.md')
    
    summary_content = f"""# RBI Grade B - General Awareness Practice Sets

## 📚 Overview

This folder contains **{PRACTICE_SET_CONFIG['num_sets']} practice sets** for General Awareness preparation.

---

## 📋 Practice Set Details

- **Questions per set:** {PRACTICE_SET_CONFIG['questions_per_set']}
- **Time limit:** 20 minutes (suggested)
- **Difficulty distribution:**
  - Hard: {PRACTICE_SET_CONFIG['difficulty_distribution']['Hard']*100:.0f}%
  - Medium: {PRACTICE_SET_CONFIG['difficulty_distribution']['Medium']*100:.0f}%
  - Easy: {PRACTICE_SET_CONFIG['difficulty_distribution']['Easy']*100:.0f}%

---

## 📁 File Structure

practice_sets/ │
 ├── practice_set_1.json # Practice Set 1 
 ├── practice_set_2.json # Practice Set 2 
 ├── practice_set_3.json # Practice Set 3 
 ├── practice_set_4.json # Practice Set 4 
 ├── practice_set_5.json # Practice Set 5 
 ├── all_practice_sets.json # All sets in one file 
 ├── answer_keys/ │
    ├── answer_key_set_1.json # Answer key for Set 1 │
    ├── answer_key_set_2.json # Answer key for Set 2 │ 
    ├── answer_key_set_3.json # Answer key for Set 3 │ 
    ├── answer_key_set_4.json # Answer key for Set 4 │ 
    └── answer_key_set_5.json # Answer key for Set 5 │ 
└── PRACTICE_SETS_README.md # This file

---

## 🎯 How to Use

### 1. **Take a Practice Test**
   - Open any `practice_set_X.json` file
   - Answer all {PRACTICE_SET_CONFIG['questions_per_set']} questions
   - Try to complete within 20 minutes

### 2. **Check Your Answers**
   - Open the corresponding `answer_key_set_X.json` from `answer_keys/` folder
   - Compare your answers
   - Read explanations for incorrect answers

### 3. **Track Your Progress**
   - Set 1: ___/30
   - Set 2: ___/30
   - Set 3: ___/30
   - Set 4: ___/30
   - Set 5: ___/30

---

## 📊 Scoring Guide

| Score | Performance |
|-------|-------------|
| 25-30 | Excellent ⭐⭐⭐ |
| 20-24 | Good ⭐⭐ |
| 15-19 | Average ⭐ |
| 10-14 | Needs Improvement 📚 |
| 0-9   | More Practice Required 💪 |

---

## 💡 Tips

1. **Time Management:** Spend 40 seconds per question on average
2. **Skip & Return:** If stuck, move to the next question
3. **Eliminate Options:** Rule out obviously wrong answers first
4. **Review Mistakes:** Understand why you got questions wrong
5. **Regular Practice:** Take one set every 2-3 days

---

## 📅 Created

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📞 Support

For questions or issues, refer to the main documentation.

---

**Good Luck! 🎯**
"""
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print(f"   ✅ Summary created: {summary_file}")


# ==================== MAIN EXECUTION ====================
# ==================== MAIN EXECUTION ====================

def main():
    """Main execution function"""
    
    start_time = datetime.now()
    
    print("\n" + "="*70)
    print("🎯 GENERAL AWARENESS MASTER QUESTION BANK CREATOR")
    print("="*70)
    print(f"📅 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_questions = []
    all_metadata = []
    
    # Step 1: Load all JSON files
    print("\n" + "="*70)
    print("📥 LOADING QUESTIONS FROM ALL SOURCES")
    print("="*70)
    
    for path in PATHS_TO_COMBINE:
        questions, metadata = load_json_files(path)
        all_questions.extend(questions)
        all_metadata.extend(metadata)
    
    if not all_questions:
        print("\n❌ ERROR: No questions found!")
        return
    
    print(f"\n📊 Total questions loaded: {len(all_questions)}")
    
    # Step 2: Remove duplicates
    unique_questions = remove_duplicates(all_questions)
    
    # Step 3: Add unique IDs
    unique_questions = add_unique_ids(unique_questions)
    
    # Step 4: Calculate statistics
    print("\n" + "="*70)
    print("📊 CALCULATING STATISTICS")
    print("="*70)
    
    stats = calculate_statistics(unique_questions)
    print_statistics(stats)
    
    # Step 5: Validate
    print("\n" + "="*70)
    print("✅ VALIDATION")
    print("="*70)
    
    is_valid = validate_master_bank(unique_questions)
    
    # Step 6: Save master bank
    print("\n" + "="*70)
    print("💾 SAVING MASTER QUESTION BANK")
    print("="*70)
    
    save_master_bank(unique_questions, stats, all_metadata)
    
    # Step 7: Create practice sets
    practice_sets = create_practice_sets(unique_questions)
    
    # Step 8: Create answer keys
    create_answer_keys(practice_sets)
    
    # Step 9: Create summary document
    create_practice_set_summary()
    
    # Final summary
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("✅ MASTER BANK & PRACTICE SETS CREATION COMPLETE")
    print("="*70)
    print(f"⏱️  Time taken: {duration:.2f} seconds")
    print(f"\n📊 Summary:")
    print(f"   📝 Total unique questions: {len(unique_questions)}")
    print(f"   📁 Master bank: {OUTPUT_FILE}")
    print(f"   📚 Practice sets created: {PRACTICE_SET_CONFIG['num_sets']}")
    print(f"   📋 Questions per set: {PRACTICE_SET_CONFIG['questions_per_set']}")
    print(f"   📁 Practice sets directory: {PRACTICE_SETS_DIR}")
    print(f"   ✅ Validation: {'PASSED' if is_valid else 'FAILED'}")
    
    print("\n" + "="*70)
    print("📂 OUTPUT FILES CREATED:")
    print("="*70)
    print(f"\n1. Master Question Bank:")
    print(f"   {OUTPUT_FILE}")
    
    print(f"\n2. Practice Sets:")
    for i in range(1, PRACTICE_SET_CONFIG['num_sets'] + 1):
        print(f"   {PRACTICE_SETS_DIR}practice_set_{i}.json")
    
    print(f"\n3. Consolidated Practice Sets:")
    print(f"   {PRACTICE_SETS_DIR}all_practice_sets.json")
    
    print(f"\n4. Answer Keys:")
    for i in range(1, PRACTICE_SET_CONFIG['num_sets'] + 1):
        print(f"   {PRACTICE_SETS_DIR}answer_keys/answer_key_set_{i}.json")
    
    print(f"\n5. Documentation:")
    print(f"   {PRACTICE_SETS_DIR}PRACTICE_SETS_README.md")
    
    print("\n" + "="*70)
    print("🎉 ALL DONE! Your question bank is ready for use!")
    print("="*70)
    print("\n💡 Next Steps:")
    print("   1. Review the master question bank")
    print("   2. Try a practice set to test the format")
    print("   3. Check answer keys for accuracy")
    print("   4. Share practice sets with students/users")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
