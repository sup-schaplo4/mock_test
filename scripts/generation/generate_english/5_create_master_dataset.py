import json
from pathlib import Path
from datetime import datetime
from collections import Counter

# ============================================================================
# 📋 CONFIGURATION - EDIT THESE PATHS
# ============================================================================

# Input JSON files to merge (add your three file paths here)
INPUT_FILES = [
    "data/generated/english_questions/pilot_english/pilot_questions_20251002_152627.json",
    "data/generated/english_questions/rc_output/reading_comprehension_concatenated.json",
    "data/generated/english_questions/english_300_questions_20251010_022150.json"
]

# Output master JSON file path
OUTPUT_FILE = "data/generated/master_questions/english_master_question_bank.json"

# Add source file tracking to each question?
ADD_SOURCE_TRACKING = True

# ============================================================================
# ✅ VALIDATION FUNCTION
# ============================================================================

def validate_question(question, source_file):
    """
    Validate question structure and required fields
    
    Args:
        question: Question dict to validate
        source_file: Source file name for error reporting
    
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    # Check if question is a dictionary
    if not isinstance(question, dict):
        return False, [f"Question is not a dictionary: {type(question)}"]
    
    # Required fields
    required_fields = ['question', 'options', 'correct_answer']
    for field in required_fields:
        if field not in question:
            errors.append(f"Missing required field: '{field}'")
    
    # Validate question text
    if 'question' in question:
        if not isinstance(question['question'], str) or not question['question'].strip():
            errors.append("Question text is empty or invalid")
    
    # Validate options
    if 'options' in question:
        options = question['options']
        if not isinstance(options, dict):
            errors.append("Options must be a dictionary")
        else:
            # Check if options has at least A, B, C, D
            required_options = ['A', 'B', 'C', 'D']
            for opt in required_options:
                if opt not in options:
                    errors.append(f"Missing option: '{opt}'")
                elif not isinstance(options[opt], str) or not options[opt].strip():
                    errors.append(f"Option {opt} is empty or invalid")
    
    # Validate correct_answer
    if 'correct_answer' in question:
        correct = question['correct_answer']
        if not isinstance(correct, str) or correct not in ['A', 'B', 'C', 'D', 'E']:
            errors.append(f"Invalid correct_answer: '{correct}' (must be A, B, C, D, or E)")
    
    # Optional but recommended fields
    recommended_fields = ['explanation', 'difficulty', 'topic', 'subject']
    for field in recommended_fields:
        if field not in question:
            # Not an error, just a warning (we'll track these separately)
            pass
    
    is_valid = len(errors) == 0
    return is_valid, errors


# ============================================================================
# 🔄 MERGE FUNCTION
# ============================================================================

def merge_json_files(input_files, output_file, add_source=True):
    """
    Merge multiple JSON files into one master file with validation
    
    Args:
        input_files: List of input JSON file paths
        output_file: Output master JSON file path
        add_source: Whether to add source_file field to each question
    """
    
    print("\n" + "="*80)
    print("🔄 JSON MERGER WITH VALIDATION")
    print("="*80)
    
    # Track statistics
    total_questions = 0
    valid_questions = 0
    invalid_questions = 0
    questions_by_file = {}
    all_questions = []
    validation_errors = []
    
    # Process each input file
    for file_path in input_files:
        file_path = Path(file_path)
        
        print(f"\n📂 Processing: {file_path.name}")
        
        # Check if file exists
        if not file_path.exists():
            print(f"   ⚠️  File not found, skipping...")
            validation_errors.append({
                'file': str(file_path),
                'error': 'File not found'
            })
            continue
        
        try:
            # Load JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract questions from different JSON structures
            questions = []
            if isinstance(data, list):
                questions = data
            elif isinstance(data, dict):
                if 'questions' in data:
                    questions = data['questions']
                elif 'data' in data:
                    questions = data['data']
                elif 'items' in data:
                    questions = data['items']
                else:
                    # Assume the dict itself is a single question
                    questions = [data]
            
            print(f"   📊 Found {len(questions)} questions")
            
            # Validate and process each question
            file_valid = 0
            file_invalid = 0
            
            for i, question in enumerate(questions, 1):
                total_questions += 1
                
                # Validate question
                is_valid, errors = validate_question(question, file_path.name)
                
                if is_valid:
                    # Add source file tracking
                    if add_source and 'source_file' not in question:
                        question['source_file'] = file_path.name
                    
                    # Add merge date if not present
                    if 'merged_date' not in question:
                        question['merged_date'] = datetime.now().isoformat()
                    
                    all_questions.append(question)
                    file_valid += 1
                    valid_questions += 1
                else:
                    file_invalid += 1
                    invalid_questions += 1
                    validation_errors.append({
                        'file': file_path.name,
                        'question_index': i,
                        'question_id': question.get('question_id', f'Question_{i}'),
                        'errors': errors
                    })
            
            # File statistics
            questions_by_file[file_path.name] = {
                'total': len(questions),
                'valid': file_valid,
                'invalid': file_invalid,
                'file_size_kb': file_path.stat().st_size / 1024
            }
            
            print(f"   ✅ Valid: {file_valid}")
            if file_invalid > 0:
                print(f"   ❌ Invalid: {file_invalid}")
        
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON decode error: {e}")
            validation_errors.append({
                'file': str(file_path),
                'error': f'JSON decode error: {str(e)}'
            })
        except Exception as e:
            print(f"   ❌ Error: {e}")
            validation_errors.append({
                'file': str(file_path),
                'error': str(e)
            })
    
    # Generate statistics
    topics = Counter()
    difficulties = Counter()
    subjects = Counter()
    
    for q in all_questions:
        if 'topic' in q:
            topics[q['topic']] += 1
        if 'difficulty' in q:
            difficulties[q['difficulty']] += 1
        if 'subject' in q:
            subjects[q['subject']] += 1
    
    # Create master JSON structure
    master_data = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "total_questions": len(all_questions),
            "valid_questions": valid_questions,
            "invalid_questions": invalid_questions,
            "source_files_count": len(input_files),
            "source_files": list(questions_by_file.keys()),
            "statistics": {
                "by_file": questions_by_file,
                "by_topic": dict(topics),
                "by_difficulty": dict(difficulties),
                "by_subject": dict(subjects)
            },
            "validation_summary": {
                "total_validated": total_questions,
                "passed": valid_questions,
                "failed": invalid_questions,
                "error_count": len(validation_errors)
            }
        },
        "questions": all_questions
    }
    
    # Add validation errors if any
    if validation_errors:
        master_data["validation_errors"] = validation_errors
    
    # Save master JSON
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*80)
    print("✅ MERGE COMPLETE!")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   • Total questions processed: {total_questions}")
    print(f"   • Valid questions: {valid_questions} ✅")
    print(f"   • Invalid questions: {invalid_questions} ❌")
    print(f"   • Files merged: {len(questions_by_file)}")
    print(f"\n💾 Output: {output_file}")
    print(f"📦 File size: {output_path.stat().st_size / 1024:.2f} KB")
    
    # Show statistics
    if topics:
        print(f"\n📚 Questions by Topic:")
        for topic, count in topics.most_common():
            print(f"   • {topic}: {count}")
    
    if difficulties:
        print(f"\n⭐ Questions by Difficulty:")
        for diff, count in difficulties.most_common():
            print(f"   • {diff}: {count}")
    
    # Show validation errors if any
    if validation_errors:
        print(f"\n⚠️  Validation Errors Found: {len(validation_errors)}")
        print(f"\nFirst 5 errors:")
        for i, error in enumerate(validation_errors[:5], 1):
            print(f"\n{i}. File: {error.get('file')}")
            if 'question_index' in error:
                print(f"   Question: {error.get('question_id')} (index {error.get('question_index')})")
            if 'errors' in error:
                for err in error['errors']:
                    print(f"   • {err}")
            elif 'error' in error:
                print(f"   • {error['error']}")
        
        if len(validation_errors) > 5:
            print(f"\n   ... and {len(validation_errors) - 5} more errors")
            print(f"   (See 'validation_errors' in {output_file} for full list)")
    
    print("\n" + "="*80)
    
    return master_data


# ============================================================================
# 🔍 BONUS: VALIDATE MASTER FILE
# ============================================================================

def validate_master_file(master_file):
    """
    Validate the generated master JSON file
    
    Args:
        master_file: Path to master JSON file
    """
    
    print("\n" + "="*80)
    print("🔍 VALIDATING MASTER FILE")
    print("="*80)
    
    with open(master_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check structure
    print(f"\n✅ File loaded successfully")
    print(f"📊 Top-level keys: {list(data.keys())}")
    
    # Check metadata
    if 'metadata' in data:
        metadata = data['metadata']
        print(f"\n📋 Metadata:")
        print(f"   • Created: {metadata.get('created_at')}")
        print(f"   • Total questions: {metadata.get('total_questions')}")
        print(f"   • Valid: {metadata.get('valid_questions')}")
        print(f"   • Invalid: {metadata.get('invalid_questions')}")
        print(f"   • Source files: {metadata.get('source_files_count')}")
    
    # Check questions
    if 'questions' in data:
        questions = data['questions']
        print(f"\n📚 Questions: {len(questions)}")
        
        if questions:
            # Show sample question
            print(f"\n📋 Sample Question (first):")
            sample = questions[0]
            print(f"   • ID: {sample.get('question_id', 'N/A')}")
            print(f"   • Question: {sample.get('question', '')[:80]}...")
            print(f"   • Options: {list(sample.get('options', {}).keys())}")
            print(f"   • Correct: {sample.get('correct_answer')}")
            print(f"   • Topic: {sample.get('topic', 'N/A')}")
            print(f"   • Difficulty: {sample.get('difficulty', 'N/A')}")
            print(f"   • Source: {sample.get('source_file', 'N/A')}")
    
    # Check validation errors
    if 'validation_errors' in data:
        errors = data['validation_errors']
        print(f"\n⚠️  Validation errors found: {len(errors)}")
    else:
        print(f"\n✅ No validation errors")
    
    print("\n" + "="*80)


# ============================================================================
# 🚀 RUN THE SCRIPT
# ============================================================================

if __name__ == "__main__":
    # Merge files
    master_data = merge_json_files(
        input_files=INPUT_FILES,
        output_file=OUTPUT_FILE,
        add_source=ADD_SOURCE_TRACKING
    )
    
    # Validate the generated file
    validate_master_file(OUTPUT_FILE)
    
    print("\n✨ All done! Your master JSON file is ready.")
