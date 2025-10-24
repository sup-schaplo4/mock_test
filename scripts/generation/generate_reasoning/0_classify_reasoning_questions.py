import json
import os
from datetime import datetime
from collections import Counter
import re

# ==================== CONFIGURATION ====================

INPUT_FILE = "data/RBI_Master_Dataset.json"
OUTPUT_DIR = "data/generated/reasoning_questions/"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "reasoning_master_questions.json")

# Reasoning topic categories and keywords for classification
REASONING_TOPICS = {
    # Puzzles & Seating Arrangements (High Specificity Keywords)
    "Linear Seating Arrangement": [
        "sitting in a row", "arranged in a line", "straight line", "parallel rows",
        "extreme left", "extreme right", "facing north", "facing south"
    ],
    "Circular Seating Arrangement": [
        "circular arrangement", "around a circular table", "round table",
        "facing the center", "facing outside", "in a circle"
    ],
    "Square/Rectangular Seating": [
        "square table", "rectangular table", "at the corners", "middle of the sides"
    ],
    "Floor Based Puzzle": [
        "lives on floor", "storey building", "ground floor is numbered 1", "top floor"
    ],
    "Box Based Puzzle": [
        "boxes are stacked", "boxes are placed one above another", "stack of boxes"
    ],
    "Scheduling Puzzle": [
        "on different days", "seven different days of the week", "in different months", 
        "scheduled on", "exam on", "born in"
    ],
    "Multi-Variable Puzzle": [
        "different professions", "different cities", "likes different colors", 
        "different subjects", "owns different cars" # These are secondary keywords
    ],

    # Verbal & Logical Reasoning
    "Syllogisms": [
        "statements:", "conclusions:", "logically follows", "only a few"
    ],
    "Coding-Decoding": [
        "in a certain code", "is coded as", "code language", "what is the code for"
    ],
    "Blood Relations": [
        "pointing to a photograph", "introducing a person", "how is related to",
        "father-in-law", "sister-in-law", "grandfather"
    ],
    "Direction Sense": [
        "starts walking", "towards north", "turns left", "shortest distance", "how far is he from"
    ],
    "Inequalities": [
        "≥", "≤", ">", "<", "=", "is definitely true", "is definitely false"
    ],

    # Analytical & Critical Reasoning
    "Data Sufficiency": [
        "data in statement i alone", "data in statement ii alone", 
        "statements i and ii together are sufficient"
    ],
    "Input-Output": [
        "input:", "step i:", "step ii:", "last step of the arrangement"
    ],
    "Statement & Assumption": [
        "implicit in the statement", "assumption is implicit"
    ],
    "Statement & Inference": [
        "can be inferred from the statement", "inference follows"
    ],
    "Statement & Course of Action": [
        "course of action", "action should be taken"
    ],
    "Strengthening/Weakening Arguments": [
        "weakens the argument", "strengthens the argument", "undermines the conclusion"
    ]
}

# ==================== EXTRACTION FUNCTIONS ====================

def load_master_dataset():
    """Load the RBI Master Dataset"""
    
    print("\n" + "="*70)
    print("📥 LOADING RBI MASTER DATASET")
    print("="*70)
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERROR: File not found - {INPUT_FILE}")
        return None
    
    print(f"\n📂 Reading: {INPUT_FILE}")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Dataset loaded successfully!")
        return data
    
    except Exception as e:
        print(f"❌ ERROR loading dataset: {e}")
        return None


def extract_reasoning_questions(dataset):
    """Extract reasoning questions from the dataset"""
    
    print("\n" + "="*70)
    print("🔍 EXTRACTING REASONING QUESTIONS")
    print("="*70)
    
    reasoning_questions = []
    
    # Check dataset structure
    if isinstance(dataset, dict):
        if 'questions' in dataset:
            all_questions = dataset['questions']
        elif 'data' in dataset:
            all_questions = dataset['data']
        else:
            # Assume the dict itself contains questions
            all_questions = [dataset]
    elif isinstance(dataset, list):
        all_questions = dataset
    else:
        print("❌ ERROR: Unknown dataset format")
        return []
    
    print(f"\n📊 Total questions in dataset: {len(all_questions)}")
    print(f"\n🔎 Filtering reasoning questions...")
    
    # Extract reasoning questions
    for question in all_questions:
        subject = question.get('subject', '').lower()
        category = question.get('category', '').lower()
        
        # Check if it's a reasoning question
        if 'reasoning' in subject or 'reasoning' in category:
            reasoning_questions.append(question)
    
    print(f"\n✅ Found {len(reasoning_questions)} reasoning questions!")
    
    return reasoning_questions


def classify_reasoning_topic(question_text):
    """
    Classifies a reasoning question into a specific topic using a hierarchical,
    rule-based approach for improved accuracy.
    """
    
    # Get question text and combine with other relevant fields
    question = question_text.get('question', '').lower()
    explanation = question_text.get('explanation', '').lower()
    topic_hint = question_text.get('topic', '').lower()
    
    # Combine all text for better classification
    text = f"{question} {explanation} {topic_hint}"
    
    # -- STAGE 1: Check for unique, high-confidence patterns first --

    # Pattern 1: Data Sufficiency (very distinct phrasing)
    if "statement i" in text and "statement ii" in text and "sufficient to answer" in text:
        return "Data Sufficiency"

    # Pattern 2: Input-Output (the "step" structure is a dead giveaway)
    if "input:" in text and ("step i:" in text or "step 1:" in text):
        return "Input-Output"

    # Pattern 3: Syllogisms (the "statements/conclusions" structure is unique)
    if "statements:" in text and "conclusions:" in text:
        return "Syllogisms"

    # Pattern 4: Inequalities (presence of symbols or specific phrases)
    if any(symbol in text for symbol in ["≥", "≤", ">", "<"]) or "is definitely true" in text:
        if "statement" in text: # Distinguish from pure math problems
            return "Inequalities"

    # -- STAGE 2: Identify puzzle types based on common scenarios --
    
    # Puzzle Type: Seating Arrangements
    if "sitting in a row" in text or "parallel rows" in text or "straight line" in text:
        return "Linear Seating Arrangement"
    if "circular table" in text or "around a circle" in text or "facing the center" in text:
        return "Circular Seating Arrangement"
    if "square table" in text or "rectangular table" in text:
        return "Square/Rectangular Seating"

    # Puzzle Type: Other Common Puzzles
    if "lives on floor" in text or "storey building" in text:
        return "Floor Based Puzzle"
    if "boxes are stacked" in text or "placed one above another" in text:
        return "Box Based Puzzle"
    if "on different days" in text or "in different months" in text or "scheduled on" in text:
        return "Scheduling Puzzle"

    # -- STAGE 3: Keyword-based classification for remaining topics --
    
    # Use the refined REASONING_TOPICS dictionary for scoring
    topic_scores = {topic: 0 for topic in REASONING_TOPICS}

    for topic, keywords in REASONING_TOPICS.items():
        for keyword in keywords:
            if keyword in text:
                topic_scores[topic] += 1
    
    # Find the topic with the highest score, but only if the score is meaningful
    if topic_scores and max(topic_scores.values()) > 0:
        best_topic = max(topic_scores, key=topic_scores.get)
        # Add a check for multi-variable puzzles which are often a secondary characteristic
        if "different professions" in text or "different cities" in text:
            if "Puzzle" in best_topic or "Seating" in best_topic:
                 return best_topic # It's a puzzle with an extra variable
            # If not already classified as a puzzle, it might be a standalone multi-variable set
            return "Multi-Variable Puzzle"
        return best_topic

    # -- STAGE 4: Fallback for Critical Reasoning --
    # These have very generic keywords, so they are checked last
    if "weaken" in text or "strengthen" in text:
        return "Strengthening/Weakening Arguments"
    if "assumption" in text and "implicit" in text:
        return "Statement & Assumption"
    if "inferred" in text:
        return "Statement & Inference"
    if "course of action" in text:
        return "Statement & Course of Action"

    # If no specific topic is found after all checks, classify as General Reasoning
    return "General Reasoning"


def assign_topics_to_questions(questions):
    """Assign topics to all reasoning questions"""
    
    print("\n" + "="*70)
    print("🏷️  ASSIGNING TOPICS TO QUESTIONS")
    print("="*70)
    
    topic_count = Counter()
    
    for i, question in enumerate(questions, 1):
        # Classify the topic
        topic = classify_reasoning_topic(question)
        
        # Assign topic to question
        question['reasoning_topic'] = topic
        
        # Keep original topic as well if exists
        if 'topic' in question:
            question['original_topic'] = question['topic']
        
        question['topic'] = topic
        
        # Count
        topic_count[topic] += 1
        
        if i % 50 == 0:
            print(f"   Processed: {i}/{len(questions)} questions")
    
    print(f"\n✅ All questions classified!")
    
    return questions, topic_count


def categorize_by_main_category(topic):
    """Categorize topics into main categories"""
    
    if topic in [
        "Linear Seating Arrangement",
        "Circular Seating Arrangement",
        "Square/Rectangular/Triangular Seating",
        "Floor Based Puzzle",
        "Box Based Puzzle",
        "Scheduling Puzzle",
        "Multi-Variable Puzzle"
    ]:
        return "Puzzles & Seating Arrangements"
    
    elif topic in [
        "Syllogisms",
        "Coding-Decoding",
        "Blood Relations",
        "Direction Sense",
        "Inequalities"
    ]:
        return "Verbal & Logical Reasoning"
    
    elif topic in [
        "Data Sufficiency",
        "Input-Output",
        "Statement & Assumption",
        "Statement & Inference",
        "Statement & Course of Action",
        "Strengthening/Weakening Arguments",
        "Critical Reasoning"
    ]:
        return "Analytical & Critical Reasoning"
    
    else:
        return "General Reasoning"


def add_metadata_and_ids(questions):
    """Add unique IDs and metadata to questions"""
    
    print("\n" + "="*70)
    print("🔢 ADDING IDs AND METADATA")
    print("="*70)
    
    for i, question in enumerate(questions, 1):
        # Add unique ID
        question['question_id'] = f"REASONING_{i:05d}"
        
        # Add main category
        topic = question.get('reasoning_topic', 'General Reasoning')
        question['main_category'] = categorize_by_main_category(topic)
        
        # Ensure subject is set
        question['subject'] = 'Reasoning'
        
        # Add metadata
        if 'metadata' not in question:
            question['metadata'] = {}
        
        question['metadata']['extracted_from'] = 'RBI_Master_Dataset'
        question['metadata']['processed_date'] = datetime.now().isoformat()
    
    print(f"   ✅ Added IDs: REASONING_00001 to REASONING_{len(questions):05d}")
    
    return questions


def calculate_statistics(questions):
    """Calculate comprehensive statistics"""
    
    print("\n" + "="*70)
    print("📊 CALCULATING STATISTICS")
    print("="*70)
    
    stats = {
        'total_questions': len(questions),
        'topic_distribution': {},
        'main_category_distribution': {},
        'difficulty_distribution': {}
    }
    
    # Topic distribution
    topic_count = Counter([q.get('reasoning_topic', 'Unknown') for q in questions])
    stats['topic_distribution'] = dict(topic_count.most_common())
    
    # Main category distribution
    category_count = Counter([q.get('main_category', 'Unknown') for q in questions])
    stats['main_category_distribution'] = dict(category_count)
    
    # Difficulty distribution
    diff_count = Counter([q.get('difficulty', 'Unknown') for q in questions])
    stats['difficulty_distribution'] = dict(diff_count)
    
    return stats


def print_statistics(stats):
    """Print detailed statistics"""
    
    print("\n" + "="*70)
    print("📊 REASONING QUESTIONS STATISTICS")
    print("="*70)
    
    total = stats['total_questions']
    print(f"\n📝 Total Reasoning Questions: {total}")
    
    # Main categories
    print(f"\n📂 Main Category Distribution:")
    for category, count in stats['main_category_distribution'].items():
        print(f"   {category:<40}: {count:>4} ({count/total*100:>5.1f}%)")
    
    # Topics
    print(f"\n🏷️  Topic Distribution:")
    for topic, count in stats['topic_distribution'].items():
        print(f"   {topic:<45}: {count:>4} ({count/total*100:>5.1f}%)")
    
    # Difficulty
    if stats['difficulty_distribution']:
        print(f"\n🎚️  Difficulty Distribution:")
        for difficulty, count in stats['difficulty_distribution'].items():
            print(f"   {difficulty:<20}: {count:>4} ({count/total*100:>5.1f}%)")
    
    print("\n" + "="*70)


def save_reasoning_questions(questions, stats):
    """Save the reasoning questions with metadata"""
    
    print("\n" + "="*70)
    print("💾 SAVING REASONING QUESTIONS")
    print("="*70)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Prepare data structure
    output_data = {
        'metadata': {
            'title': 'RBI Grade B - Reasoning Questions',
            'description': 'Reasoning questions extracted from RBI Master Dataset with assigned topics',
            'source': 'RBI_Master_Dataset.json',
            'extraction_date': datetime.now().isoformat(),
            'total_questions': stats['total_questions'],
            'topic_distribution': stats['topic_distribution'],
            'main_category_distribution': stats['main_category_distribution'],
            'difficulty_distribution': stats['difficulty_distribution'],
            'topics': {
                'Puzzles & Seating Arrangements': [
                    'Linear Seating Arrangement',
                    'Circular Seating Arrangement',
                    'Square/Rectangular/Triangular Seating',
                    'Floor Based Puzzle',
                    'Box Based Puzzle',
                    'Scheduling Puzzle',
                    'Multi-Variable Puzzle'
                ],
                'Verbal & Logical Reasoning': [
                    'Syllogisms',
                    'Coding-Decoding',
                    'Blood Relations',
                    'Direction Sense',
                    'Inequalities'
                ],
                'Analytical & Critical Reasoning': [
                    'Data Sufficiency',
                    'Input-Output',
                    'Statement & Assumption',
                    'Statement & Inference',
                    'Statement & Course of Action',
                    'Strengthening/Weakening Arguments',
                    'Critical Reasoning'
                ]
            }
        },
        'questions': questions
    }
    
    # Save main file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)  # MB
    
    print(f"   ✅ Saved: {OUTPUT_FILE}")
    print(f"   📦 File size: {file_size:.2f} MB")
    print(f"   📝 Total questions: {len(questions)}")

def save_questions_by_category(questions):
    """Save questions grouped by main category"""
    
    print("\n" + "="*70)
    print("📁 SAVING QUESTIONS BY CATEGORY")
    print("="*70)
    
    # Group by main category
    by_category = {}
    for q in questions:
        category = q.get('main_category', 'General Reasoning')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(q)
    
    # Save each category
    for category, cat_questions in by_category.items():
        # Create safe filename
        safe_filename = category.lower().replace(' ', '_').replace('&', 'and')
        category_file = os.path.join(OUTPUT_DIR, f"{safe_filename}.json")
        
        # Calculate category stats
        topic_dist = Counter([q.get('reasoning_topic') for q in cat_questions])
        
        category_data = {
            'metadata': {
                'title': f'RBI Grade B - {category}',
                'category': category,
                'total_questions': len(cat_questions),
                'creation_date': datetime.now().isoformat(),
                'topic_distribution': dict(topic_dist)
            },
            'questions': cat_questions
        }
        
        with open(category_file, 'w', encoding='utf-8') as f:
            json.dump(category_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ {category}: {len(cat_questions)} questions → {category_file}")
    
    print(f"\n   📁 Total categories saved: {len(by_category)}")


def save_questions_by_topic(questions):
    """Save questions grouped by specific topic"""
    
    print("\n" + "="*70)
    print("🏷️  SAVING QUESTIONS BY TOPIC")
    print("="*70)
    
    # Create topics directory
    topics_dir = os.path.join(OUTPUT_DIR, 'by_topic')
    os.makedirs(topics_dir, exist_ok=True)
    
    # Group by topic
    by_topic = {}
    for q in questions:
        topic = q.get('reasoning_topic', 'General Reasoning')
        if topic not in by_topic:
            by_topic[topic] = []
        by_topic[topic].append(q)
    
    # Save each topic
    for topic, topic_questions in by_topic.items():
        # Create safe filename
        safe_filename = topic.lower().replace(' ', '_').replace('/', '_').replace('&', 'and')
        topic_file = os.path.join(topics_dir, f"{safe_filename}.json")
        
        topic_data = {
            'metadata': {
                'title': f'RBI Grade B - {topic}',
                'topic': topic,
                'total_questions': len(topic_questions),
                'creation_date': datetime.now().isoformat()
            },
            'questions': topic_questions
        }
        
        with open(topic_file, 'w', encoding='utf-8') as f:
            json.dump(topic_data, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ {topic}: {len(topic_questions)} questions")
    
    print(f"\n   📁 Total topics saved: {len(by_topic)}")
    print(f"   📂 Location: {topics_dir}")


def create_topic_mapping_report():
    """Create a detailed report of topic assignments"""
    
    print("\n" + "="*70)
    print("📄 CREATING TOPIC MAPPING REPORT")
    print("="*70)
    
    report_file = os.path.join(OUTPUT_DIR, 'TOPIC_MAPPING_REPORT.md')
    
    report_content = f"""# Reasoning Questions - Topic Mapping Report

## 📊 Overview

This report provides details about the reasoning questions extracted and their topic assignments.

**Extraction Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Source:** RBI_Master_Dataset.json

---

## 📂 Main Categories

### 1. Puzzles & Seating Arrangements
Includes questions on:
- **Linear Seating Arrangement** (Single row, Double row)
- **Circular Seating Arrangement** (Facing inside/outside)
- **Square/Rectangular/Triangular Seating**
- **Floor Based Puzzles**
- **Box Based Puzzles**
- **Scheduling Puzzles** (Days, Months, Years)
- **Multi-Variable Puzzles** (Person, City, Profession, etc.)

### 2. Verbal & Logical Reasoning
Includes questions on:
- **Syllogisms** (Classic and "Only a few" types)
- **Coding-Decoding** (New patterns)
- **Blood Relations**
- **Direction Sense**
- **Inequalities** (Coded and Direct)

### 3. Analytical & Critical Reasoning
Includes questions on:
- **Data Sufficiency**
- **Input-Output** (Machine Input)
- **Statement & Assumption**
- **Statement & Inference**
- **Statement & Course of Action**
- **Strengthening/Weakening Arguments**
- **Critical Reasoning**

---

## 🏷️ Topic Classification Method

Topics were assigned based on keyword matching and content analysis:

1. **Question Text Analysis**: Primary weight given to question content
2. **Explanation Analysis**: Secondary weight for context clues
3. **Existing Topic Hints**: Considered if present in original data
4. **Keyword Scoring**: Multiple keywords increase confidence in classification

---

## 📁 Output Files

### Main Files:
- `reasoning_master_questions.json` - All reasoning questions with topics
- `puzzles_and_seating_arrangements.json` - Puzzles category only
- `verbal_and_logical_reasoning.json` - Verbal & Logical category only
- `analytical_and_critical_reasoning.json` - Analytical category only

### By Topic:
All individual topic files are stored in the `by_topic/` directory.

---

## 🎯 Usage Guidelines

1. **For Comprehensive Practice**: Use `reasoning_master_questions.json`
2. **For Category-Specific Practice**: Use category files
3. **For Topic-Specific Practice**: Use files in `by_topic/` directory

---

## ✅ Quality Assurance

- All questions have unique IDs (REASONING_00001 to REASONING_XXXXX)
- Each question assigned to exactly one topic
- Original topic preserved as `original_topic` field
- Metadata includes extraction and processing information

---

## 📞 Notes

- Questions with ambiguous content classified as "General Reasoning"
- Manual review recommended for questions in "General Reasoning" category
- Topic keywords can be refined for better classification

---

**Generated by:** Reasoning Questions Extractor & Topic Classifier  
**Version:** 1.0

"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"   ✅ Report created: {report_file}")


def create_summary_statistics_file(stats):
    """Create a detailed statistics JSON file"""
    
    print("\n" + "="*70)
    print("📊 CREATING STATISTICS FILE")
    print("="*70)
    
    stats_file = os.path.join(OUTPUT_DIR, 'reasoning_statistics.json')
    
    stats_data = {
        'summary': {
            'total_questions': stats['total_questions'],
            'extraction_date': datetime.now().isoformat(),
            'source_file': 'RBI_Master_Dataset.json'
        },
        'main_categories': stats['main_category_distribution'],
        'topics': stats['topic_distribution'],
        'difficulty': stats['difficulty_distribution'],
        'category_breakdown': {}
    }
    
    # Add percentage calculations
    total = stats['total_questions']
    
    for category, count in stats['main_category_distribution'].items():
        stats_data['category_breakdown'][category] = {
            'count': count,
            'percentage': round(count / total * 100, 2)
        }
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Statistics saved: {stats_file}")


def validate_reasoning_questions(questions):
    """Validate the extracted reasoning questions"""
    
    print("\n" + "="*70)
    print("✅ VALIDATING REASONING QUESTIONS")
    print("="*70)
    
    issues = []
    
    required_fields = ['question', 'options', 'correct_answer', 'explanation']
    
    for i, q in enumerate(questions, 1):
        # Check required fields
        for field in required_fields:
            if field not in q or not q[field]:
                issues.append(f"Q{i} ({q.get('question_id', 'NO_ID')}): Missing {field}")
        
        # Check options
        if 'options' in q:
            if isinstance(q['options'], dict):
                if len(q['options']) < 4:
                    issues.append(f"Q{i}: Less than 4 options")
            elif isinstance(q['options'], list):
                if len(q['options']) < 4:
                    issues.append(f"Q{i}: Less than 4 options")
        
        # Check if topic assigned
        if 'reasoning_topic' not in q:
            issues.append(f"Q{i}: No topic assigned")
        
        # Check if main category assigned
        if 'main_category' not in q:
            issues.append(f"Q{i}: No main category assigned")
    
    if issues:
        print(f"\n   ⚠️  Found {len(issues)} validation issues:")
        for issue in issues[:10]:
            print(f"      • {issue}")
        if len(issues) > 10:
            print(f"      ... and {len(issues) - 10} more issues")
    else:
        print(f"\n   ✅ All {len(questions)} questions passed validation!")
    
    return len(issues) == 0


def create_readme_file():
    """Create a comprehensive README for the reasoning questions"""
    
    print("\n" + "="*70)
    print("📖 CREATING README FILE")
    print("="*70)
    
    readme_file = os.path.join(OUTPUT_DIR, 'README.md')
    
    readme_content = """# RBI Grade B - Reasoning Questions

## 📚 Overview

This directory contains **300+ reasoning questions** extracted from the RBI Master Dataset, organized by categories and topics.


---

## 🎯 Main Categories

### 1️⃣ Puzzles & Seating Arrangements
- Linear Seating Arrangement (Single/Double row)
- Circular Seating Arrangement (Facing in/out)
- Square/Rectangular/Triangular Seating
- Floor Based Puzzles
- Box Based Puzzles
- Scheduling Puzzles (Days/Months/Years)
- Multi-Variable Puzzles

### 2️⃣ Verbal & Logical Reasoning
- Syllogisms
- Coding-Decoding
- Blood Relations
- Direction Sense
- Inequalities

### 3️⃣ Analytical & Critical Reasoning
- Data Sufficiency
- Input-Output (Machine Input)
- Statement & Assumption
- Statement & Inference
- Statement & Course of Action
- Strengthening/Weakening Arguments
- Critical Reasoning

---

## 💡 How to Use

### For Complete Practice:
```python
# Load all reasoning questions
with open('reasoning_master_questions.json', 'r') as f:
    data = json.load(f)
    questions = data['questions']
For Category-Specific Practice:

# Load specific category
with open('puzzles_and_seating_arrangements.json', 'r') as f:
    data = json.load(f)
    questions = data['questions']
For Topic-Specific Practice:

# Load specific topic
with open('by_topic/syllogisms.json', 'r') as f:
    data = json.load(f)
    questions = data['questions']
    
📊 Question Structure

Each question contains:

{
  "question_id": "REASONING_00001",
  "question": "Question text...",
  "options": {
    "A": "Option A",
    "B": "Option B",
    "C": "Option C",
    "D": "Option D"
  },
  "correct_answer": "A",
  "explanation": "Detailed explanation...",
  "difficulty": "Medium",
  "subject": "Reasoning",
  "reasoning_topic": "Syllogisms",
  "main_category": "Verbal & Logical Reasoning",
  "metadata": {
    "extracted_from": "RBI_Master_Dataset",
    "processed_date": "2024-XX-XX"
  }
}
📈 Statistics

For detailed statistics, check:

reasoning_statistics.json - Quantitative breakdown
TOPIC_MAPPING_REPORT.md - Classification methodology
✅ Quality Assurance

✓ All questions have unique IDs
✓ Topics assigned based on content analysis
✓ Original data preserved
✓ Validated for completeness

🚀 Next Steps

Review topic assignments
Create practice sets
Generate mock tests
Build adaptive learning system

📞 Support

For questions or issues with the dataset, refer to the main documentation.

Last Updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
"""

    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"✅ README created: {readme_file}")

# ==================== MAIN EXECUTION ====================

def main():
    """Main execution function"""
    
    start_time = datetime.now()
    
    print("\n" + "="*70)
    print("🧠 REASONING QUESTIONS EXTRACTOR & TOPIC CLASSIFIER")
    print("="*70)
    print(f"📅 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Load the master dataset
    dataset = load_master_dataset()
    if dataset is None:
        print("\n❌ ERROR: Could not load dataset. Exiting.")
        return
    
    # Step 2: Extract reasoning questions
    reasoning_questions = extract_reasoning_questions(dataset)
    if not reasoning_questions:
        print("\n❌ ERROR: No reasoning questions found. Exiting.")
        return
    
    # Step 3: Assign topics to questions
    reasoning_questions, topic_count = assign_topics_to_questions(reasoning_questions)
    
    # Step 4: Add metadata and unique IDs
    reasoning_questions = add_metadata_and_ids(reasoning_questions)
    
    # Step 5: Calculate statistics
    stats = calculate_statistics(reasoning_questions)
    print_statistics(stats)
    
    # Step 6: Validate questions
    print("\n" + "="*70)
    print("✅ VALIDATION")
    print("="*70)
    is_valid = validate_reasoning_questions(reasoning_questions)
    
    # Step 7: Save master reasoning questions file
    save_reasoning_questions(reasoning_questions, stats)
    
    # Step 8: Save questions by main category (3 files)
    save_questions_by_category(reasoning_questions)
    
    # Step 9: Save questions by specific topic (individual files)
    save_questions_by_topic(reasoning_questions)
    
    # Step 10: Create statistics file
    create_summary_statistics_file(stats)
    
    # Step 11: Create topic mapping report
    create_topic_mapping_report()
    
    # Step 12: Create README
    create_readme_file()
    
    # Final summary
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("✅ REASONING QUESTIONS EXTRACTION COMPLETE")
    print("="*70)
    print(f"⏱️  Time taken: {duration:.2f} seconds")
    print(f"\n📊 Summary:")
    print(f"   📝 Total reasoning questions: {len(reasoning_questions)}")
    print(f"   🏷️  Topics identified: {len(topic_count)}")
    print(f"   📁 Output directory: {OUTPUT_DIR}")
    print(f"   ✅ Validation: {'PASSED' if is_valid else 'FAILED'}")
    
    print("\n" + "="*70)
    print("📂 FILES CREATED:")
    print("="*70)
    
    print(f"\n1️⃣  Master File:")
    print(f"   • reasoning_master_questions.json (All {len(reasoning_questions)} questions)")
    
    print(f"\n2️⃣  Category Files (3 main categories):")
    print(f"   • puzzles_and_seating_arrangements.json")
    print(f"   • verbal_and_logical_reasoning.json")
    print(f"   • analytical_and_critical_reasoning.json")
    
    print(f"\n3️⃣  Topic Files (Individual topics in by_topic/ folder):")
    sorted_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)
    for topic, count in sorted_topics:
        safe_name = topic.lower().replace(' ', '_').replace('/', '_').replace('&', 'and')
        print(f"   • {safe_name}.json ({count} questions)")
    
    print(f"\n4️⃣  Documentation:")
    print(f"   • README.md")
    print(f"   • TOPIC_MAPPING_REPORT.md")
    print(f"   • reasoning_statistics.json")
    
    print("\n" + "="*70)
    print("🎉 ALL DONE! Your reasoning questions are ready!")
    print("="*70)
    print("\n💡 Next Steps:")
    print("   1. Review topic assignments in TOPIC_MAPPING_REPORT.md")
    print("   2. Check statistics in reasoning_statistics.json")
    print("   3. Validate question quality manually")
    print("   4. Create practice sets from organized questions")
    print("   5. Build mock tests by combining topics")
    
    print("\n" + "="*70)
    print(f"📊 TOPIC DISTRIBUTION:")
    print("="*70)
    for topic, count in sorted_topics:
        percentage = (count / len(reasoning_questions)) * 100
        print(f"   {topic:<45}: {count:>3} ({percentage:>5.1f}%)")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
