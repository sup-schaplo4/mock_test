import json
import csv
import pandas as pd

# ==================== CONVERT JSON TO CSV (ALL FIELDS) ====================

def json_to_csv_all_fields():
    """Convert reasoning_master_questions.json to CSV with ALL fields"""
    
    # Load JSON
    with open('data/generated/reasoning_questions/reasoning_master_questions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = data['questions']
    
    # Flatten the data with ALL fields
    flattened = []
    for q in questions:
        flat_q = {
            'question_id': q.get('question_id', ''),
            'question': q.get('question', ''),
            'option_A': q.get('options', {}).get('A', ''),
            'option_B': q.get('options', {}).get('B', ''),
            'option_C': q.get('options', {}).get('C', ''),
            'option_D': q.get('options', {}).get('D', ''),
            'option_E': q.get('options', {}).get('E', ''),  # In case some have 5 options
            'correct_answer': q.get('correct_answer', ''),
            'explanation': q.get('explanation', ''),
            'difficulty': q.get('difficulty', ''),
            'subject': q.get('subject', ''),
            'reasoning_topic': q.get('reasoning_topic', ''),
            'main_category': q.get('main_category', ''),
            'original_topic': q.get('original_topic', ''),
            'tags': ', '.join(q.get('tags', [])) if isinstance(q.get('tags'), list) else q.get('tags', ''),
            'year': q.get('year', ''),
            'exam_type': q.get('exam_type', ''),
            'source': q.get('source', ''),
            'metadata_extracted_from': q.get('metadata', {}).get('extracted_from', ''),
            'metadata_processed_date': q.get('metadata', {}).get('processed_date', ''),
            'metadata_assigned_by': q.get('metadata', {}).get('topic_assigned_by', '')
        }
        flattened.append(flat_q)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(flattened)
    output_file = 'data/generated/reasoning_questions/reasoning_questions_all_fields.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"✅ CSV created: {output_file}")
    print(f"📊 Total rows: {len(df)}")
    print(f"📋 Total columns: {len(df.columns)}")
    print(f"\n📋 Columns included:")
    for col in df.columns:
        print(f"   • {col}")


# ==================== CREATE CATEGORY MAPPING CSV ====================

def create_category_mapping_csv():
    """Create a CSV with category mappings: reasoning_topic, topic, main_category"""
    
    # Define the category structure
    category_mapping = [
        # Puzzles & Seating Arrangements
        {'reasoning_topic': 'Linear Seating Arrangement', 'topic': 'Linear Seating', 'main_category': 'Puzzles & Seating Arrangements'},
        {'reasoning_topic': 'Circular Seating Arrangement', 'topic': 'Circular Seating', 'main_category': 'Puzzles & Seating Arrangements'},
        {'reasoning_topic': 'Square/Rectangular/Triangular Seating', 'topic': 'Special Seating', 'main_category': 'Puzzles & Seating Arrangements'},
        {'reasoning_topic': 'Floor Based Puzzle', 'topic': 'Floor Puzzle', 'main_category': 'Puzzles & Seating Arrangements'},
        {'reasoning_topic': 'Box Based Puzzle', 'topic': 'Box Puzzle', 'main_category': 'Puzzles & Seating Arrangements'},
        {'reasoning_topic': 'Scheduling Puzzle', 'topic': 'Day/Month Puzzle', 'main_category': 'Puzzles & Seating Arrangements'},
        {'reasoning_topic': 'Multi-Variable Puzzle', 'topic': 'Complex Puzzle', 'main_category': 'Puzzles & Seating Arrangements'},
        
        # Verbal & Logical Reasoning
        {'reasoning_topic': 'Syllogisms', 'topic': 'Syllogisms', 'main_category': 'Verbal & Logical Reasoning'},
        {'reasoning_topic': 'Coding-Decoding', 'topic': 'Coding-Decoding', 'main_category': 'Verbal & Logical Reasoning'},
        {'reasoning_topic': 'Blood Relations', 'topic': 'Blood Relations', 'main_category': 'Verbal & Logical Reasoning'},
        {'reasoning_topic': 'Direction Sense', 'topic': 'Direction Sense', 'main_category': 'Verbal & Logical Reasoning'},
        {'reasoning_topic': 'Inequalities', 'topic': 'Inequalities', 'main_category': 'Verbal & Logical Reasoning'},
        
        # Analytical & Critical Reasoning
        {'reasoning_topic': 'Data Sufficiency', 'topic': 'Data Sufficiency', 'main_category': 'Analytical & Critical Reasoning'},
        {'reasoning_topic': 'Input-Output', 'topic': 'Input-Output', 'main_category': 'Analytical & Critical Reasoning'},
        {'reasoning_topic': 'Statement & Assumption', 'topic': 'Statement & Assumption', 'main_category': 'Analytical & Critical Reasoning'},
        {'reasoning_topic': 'Statement & Inference', 'topic': 'Statement & Inference', 'main_category': 'Analytical & Critical Reasoning'},
        {'reasoning_topic': 'Statement & Course of Action', 'topic': 'Statement & Course of Action', 'main_category': 'Analytical & Critical Reasoning'},
        {'reasoning_topic': 'Strengthening/Weakening Arguments', 'topic': 'Strengthen/Weaken', 'main_category': 'Analytical & Critical Reasoning'},
        {'reasoning_topic': 'Critical Reasoning', 'topic': 'Critical Reasoning', 'main_category': 'Analytical & Critical Reasoning'},
        
        # General
        {'reasoning_topic': 'General Reasoning', 'topic': 'General', 'main_category': 'General Reasoning'},
    ]
    
    # Create DataFrame
    df = pd.DataFrame(category_mapping)
    
    # Save to CSV
    output_file = 'data/generated/reasoning_questions/category_mapping.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n✅ Category mapping CSV created: {output_file}")
    print(f"📊 Total mappings: {len(df)}")
    print(f"\n📋 Category Breakdown:")
    print(df.groupby('main_category')['reasoning_topic'].count())


# ==================== CREATE EDITABLE QUESTIONS CSV ====================

def create_editable_questions_csv():
    """Create a simplified CSV for easy editing of categories"""
    
    # Load JSON
    with open('data/generated/reasoning_questions/reasoning_master_questions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = data['questions']
    
    # Create simplified version for editing
    simplified = []
    for q in questions:
        # Get first 100 chars of question for preview
        question_preview = q.get('question', '')[:100] + '...' if len(q.get('question', '')) > 100 else q.get('question', '')
        
        simple_q = {
            'question_id': q.get('question_id', ''),
            'question_preview': question_preview,
            'current_reasoning_topic': q.get('reasoning_topic', ''),
            'current_main_category': q.get('main_category', ''),
            'new_reasoning_topic': '',  # Empty for manual entry
            'new_main_category': '',    # Empty for manual entry
            'notes': ''                 # For any comments
        }
        simplified.append(simple_q)
    
    # Create DataFrame
    df = pd.DataFrame(simplified)
    output_file = 'data/generated/reasoning_questions/questions_for_editing.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n✅ Editable questions CSV created: {output_file}")
    print(f"📊 Total rows: {len(df)}")
    print(f"\n💡 Instructions:")
    print(f"   1. Open: {output_file}")
    print(f"   2. Review 'current_reasoning_topic' and 'current_main_category'")
    print(f"   3. If incorrect, fill 'new_reasoning_topic' and 'new_main_category'")
    print(f"   4. Add any notes in 'notes' column")
    print(f"   5. Save the file")


# ==================== UPDATE JSON FROM EDITED CSV ====================

def update_json_from_edited_csv():
    """Update the JSON file based on edited CSV"""
    
    # Load the edited CSV
    edited_csv = 'data/generated/reasoning_questions/questions_for_editing.csv'
    df = pd.read_csv(edited_csv, encoding='utf-8')
    
    # Load original JSON
    with open('data/generated/reasoning_questions/reasoning_master_questions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = data['questions']
    
    # Create a mapping of question_id to new topics
    updates = {}
    for _, row in df.iterrows():
        if pd.notna(row['new_reasoning_topic']) and row['new_reasoning_topic'].strip():
            updates[row['question_id']] = {
                'reasoning_topic': row['new_reasoning_topic'].strip(),
                'main_category': row['new_main_category'].strip() if pd.notna(row['new_main_category']) else ''
            }
    
    # Update questions
    updated_count = 0
    for q in questions:
        if q['question_id'] in updates:
            q['reasoning_topic'] = updates[q['question_id']]['reasoning_topic']
            if updates[q['question_id']]['main_category']:
                q['main_category'] = updates[q['question_id']]['main_category']
            updated_count += 1
    
    # Save updated JSON
    output_file = 'data/generated/reasoning_questions/reasoning_master_questions_updated.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Updated JSON created: {output_file}")
    print(f"📊 Total questions updated: {updated_count}")
    print(f"\n💡 Next steps:")
    print(f"   1. Review the updated file")
    print(f"   2. If satisfied, replace the original:")
    print(f"      reasoning_master_questions.json ← reasoning_master_questions_updated.json")


# ==================== MAIN EXECUTION ====================

def main():
    """Run all conversion functions"""
    
    print("\n" + "="*70)
    print("📄 REASONING QUESTIONS - CSV CONVERSION & EDITING TOOLS")
    print("="*70)
    
    # 1. Create full CSV with all fields
    print("\n1️⃣  Creating CSV with ALL fields...")
    json_to_csv_all_fields()
    
    # 2. Create category mapping CSV
    print("\n2️⃣  Creating category mapping CSV...")
    create_category_mapping_csv()
    
    # 3. Create editable questions CSV
    print("\n3️⃣  Creating editable questions CSV...")
    create_editable_questions_csv()
    
    print("\n" + "="*70)
    print("✅ ALL CSV FILES CREATED!")
    print("="*70)
    
    print("\n📁 Files created:")
    print("   1. reasoning_questions_all_fields.csv - Complete data with all fields")
    print("   2. category_mapping.csv - Topic to category mappings")
    print("   3. questions_for_editing.csv - Simplified for manual editing")
    
    print("\n" + "="*70)
    print("📝 WORKFLOW FOR MANUAL EDITING:")
    print("="*70)
    print("\n1. Open 'questions_for_editing.csv' in Excel/Google Sheets")
    print("2. Review columns:")
    print("   • question_preview - First 100 chars of question")
    print("   • current_reasoning_topic - Current classification")
    print("   • current_main_category - Current category")
    print("3. If incorrect, fill in:")
    print("   • new_reasoning_topic - Correct topic")
    print("   • new_main_category - Correct category")
    print("4. Save the file")
    print("5. Run: update_json_from_edited_csv() to apply changes")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
    
    # After editing the CSV, uncomment and run:
    # update_json_from_edited_csv()
