#!/usr/bin/env python3
"""
Batch Quiz Maker Converter with Validation
Converts all mock tests in generated_tests/commercial_series/ to Quiz Maker format
and saves them to generated_tests/quizmaker_ready/ with full validation.
"""

import json
import os
from pathlib import Path
import datetime
from collections import Counter

# --- ⚠️ CONFIGURATION ---
SOURCE_DIR = "generated_tests/commercial_series/"
OUTPUT_DIR = "generated_tests/quizmaker_ready/"
CHART_IMAGE_BASE_URL = "https://argon-test.in/wp-content/uploads/2025/10/"

def process_question(question_obj, section_name, quiz_maker_questions, question_id_counter, chart_base_url):
    """Process a single question and add it to the quiz maker questions list."""
    
    # --- HANDLE DATA INTERPRETATION SETS (from main sections) ---
    if "data_source" in question_obj:
        di_set_id = question_obj.get('di_set_id', 'unknown_di_set')
        chart_image_url = f"{chart_base_url}{di_set_id}-scaled.png"
        
        # Create a separate question for each sub-question in the set
        for sub_question in question_obj.get('questions', []):
            answers = []
            for option_key, option_text in sub_question.get('options', {}).items():
                is_correct = "1" if option_key == sub_question.get('correct_answer') else "0"
                weight = 1 if is_correct == "1" else -0.25
                answers.append({
                    "answer": option_text,
                    "correct": is_correct,
                    "weight": weight,
                    "image": ""
                })
            
            quiz_maker_question = {
                "id": str(question_id_counter[0]),
                "question": sub_question.get('question', ''),
                "question_image": chart_image_url,
                "type": "radio",
                "category": section_name,
                "explanation": sub_question.get('explanation', ''),
                "answers": answers,
                "published": "1",
                "weight": 1
            }
            quiz_maker_questions.append(quiz_maker_question)
            question_id_counter[0] += 1

    # --- HANDLE INDIVIDUAL DI QUESTIONS (from subsections) ---
    elif question_obj.get('question_id', '').startswith('DI_'):
        # Extract DI set ID from question_id (e.g., DI_PIE_CHART_006_Q1 -> DI_PIE_CHART_006)
        question_id = question_obj.get('question_id', '')
        di_set_id = '_'.join(question_id.split('_')[:-1])  # Remove the _Q1, _Q2, etc.
        chart_image_url = f"{chart_base_url}{di_set_id}-scaled.png"
        
        answers = []
        for option_key, option_text in question_obj.get('options', {}).items():
            is_correct = "1" if option_key == question_obj.get('correct_answer') else "0"
            weight = 1 if is_correct == "1" else -0.25
            answers.append({
                "answer": option_text,
                "correct": is_correct,
                "weight": weight,
                "image": ""
            })

        quiz_maker_question = {
            "id": str(question_id_counter[0]),
            "question": question_obj.get('question', ''),
            "question_image": chart_image_url,
            "type": "radio",
            "category": section_name,
            "explanation": question_obj.get('explanation', ''),
            "answers": answers,
            "published": "1",
            "weight": 1
        }
        quiz_maker_questions.append(quiz_maker_question)
        question_id_counter[0] += 1

    # --- HANDLE REGULAR QUESTIONS ---
    else:
        answers = []
        for option_key, option_text in question_obj.get('options', {}).items():
            is_correct = "1" if option_key == question_obj.get('correct_answer') else "0"
            weight = 1 if is_correct == "1" else -0.25
            answers.append({
                "answer": option_text,
                "correct": is_correct,
                "weight": weight,
                "image": ""
            })

        quiz_maker_question = {
            "id": str(question_id_counter[0]),
            "question": question_obj.get('question', ''),
            "question_image": None,
            "type": "radio",
            "category": section_name,
            "explanation": question_obj.get('explanation', ''),
            "answers": answers,
            "published": "1",
            "weight": 1
        }
        quiz_maker_questions.append(quiz_maker_question)
        question_id_counter[0] += 1

def validate_questions(quiz_maker_questions, expected_count=200):
    """Validate the converted questions for count and duplicates."""
    validation_results = {
        'total_questions': len(quiz_maker_questions),
        'expected_count': expected_count,
        'count_match': len(quiz_maker_questions) == expected_count,
        'duplicates': [],
        'duplicate_count': 0,
        'sections': {},
        'di_questions_with_images': 0,
        'di_questions_without_images': 0,
        'non_di_questions_with_images': 0,
        'errors': []
    }
    
    # Check for duplicate questions
    question_texts = [q.get('question', '') for q in quiz_maker_questions]
    question_text_counts = Counter(question_texts)
    
    for question_text, count in question_text_counts.items():
        if count > 1:
            validation_results['duplicates'].append({
                'question': question_text[:100] + '...' if len(question_text) > 100 else question_text,
                'count': count
            })
            validation_results['duplicate_count'] += count - 1
    
    # Count questions by section and validate image fields
    for i, question in enumerate(quiz_maker_questions):
        section = question.get('category', 'Unknown')
        validation_results['sections'][section] = validation_results['sections'].get(section, 0) + 1
        
        # Validate question_image field based on question type
        has_image = question.get('question_image') is not None and question.get('question_image') != ""
        is_di_question = section == "Data Interpretation"
        
        if is_di_question:
            if has_image:
                validation_results['di_questions_with_images'] += 1
            else:
                validation_results['di_questions_without_images'] += 1
                validation_results['errors'].append(f"Question {i+1}: DI question missing image")
        else:
            if has_image:
                validation_results['non_di_questions_with_images'] += 1
                validation_results['errors'].append(f"Question {i+1}: Non-DI question has image (should be None)")
    
    # Check for missing required fields
    for i, question in enumerate(quiz_maker_questions):
        if not question.get('question'):
            validation_results['errors'].append(f"Question {i+1}: Missing question text")
        if not question.get('answers'):
            validation_results['errors'].append(f"Question {i+1}: Missing answers")
        if not question.get('category'):
            validation_results['errors'].append(f"Question {i+1}: Missing category")
    
    return validation_results

def convert_single_mock(source_file, output_file, chart_base_url):
    """Convert a single mock test file to Quiz Maker format."""
    print(f"🔄 Processing: {source_file}")
    
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            argon_test_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: Source file not found: {source_file}")
        return None
    except json.JSONDecodeError:
        print(f"❌ ERROR: Invalid JSON file: {source_file}")
        return None

    quiz_maker_questions = []
    question_id_counter = [1]

    # Process all sections and subsections
    for section in argon_test_data.get('sections', []):
        section_name = section.get('section_name', 'Uncategorized')
        
        # Process questions from main section
        for question_obj in section.get('questions', []):
            process_question(question_obj, section_name, quiz_maker_questions, question_id_counter, chart_base_url)
        
        # Process questions from subsections
        for subsection in section.get('subsections', []):
            subsection_name = subsection.get('subsection_name', 'Uncategorized')
            for question_obj in subsection.get('questions', []):
                process_question(question_obj, subsection_name, quiz_maker_questions, question_id_counter, chart_base_url)

    # Validate the converted questions
    validation = validate_questions(quiz_maker_questions)
    
    # Write the converted file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(quiz_maker_questions, f, indent=3)
        
        return {
            'source_file': source_file,
            'output_file': output_file,
            'questions_converted': len(quiz_maker_questions),
            'validation': validation,
            'success': True
        }
    except Exception as e:
        print(f"❌ ERROR: Could not write to {output_file}: {e}")
        return {
            'source_file': source_file,
            'output_file': output_file,
            'error': str(e),
            'success': False
        }

def main():
    """Main function to process all mock tests."""
    print("🚀 BATCH QUIZ MAKER CONVERTER WITH VALIDATION")
    print("=" * 60)
    
    # Create output directory if it doesn't exist
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Find all mock test files
    source_path = Path(SOURCE_DIR)
    if not source_path.exists():
        print(f"❌ ERROR: Source directory not found: {SOURCE_DIR}")
        return
    
    mock_files = list(source_path.glob("rbi_phase1_mock_*.json"))
    if not mock_files:
        print(f"❌ ERROR: No mock test files found in {SOURCE_DIR}")
        return
    
    print(f"📁 Found {len(mock_files)} mock test files")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print()
    
    results = []
    successful_conversions = 0
    total_questions = 0
    
    # Process each mock test file
    for mock_file in sorted(mock_files):
        output_file = Path(OUTPUT_DIR) / f"quiz_maker_import_{mock_file.stem}.json"
        
        result = convert_single_mock(mock_file, output_file, CHART_IMAGE_BASE_URL)
        results.append(result)
        
        if result['success']:
            successful_conversions += 1
            total_questions += result['questions_converted']
            
            # Print validation results
            validation = result['validation']
            status = "✅" if validation['count_match'] and validation['duplicate_count'] == 0 and not validation['errors'] else "⚠️"
            
            print(f"  {status} {mock_file.name} → {output_file.name}")
            print(f"     Questions: {validation['total_questions']}/{validation['expected_count']}")
            print(f"     DI questions with images: {validation['di_questions_with_images']}")
            print(f"     Non-DI questions with images: {validation['non_di_questions_with_images']}")
            
            if validation['duplicate_count'] > 0:
                print(f"     ⚠️  Duplicates: {validation['duplicate_count']}")
            
            if validation['errors']:
                print(f"     ❌ Errors: {len(validation['errors'])}")
                for error in validation['errors'][:3]:  # Show first 3 errors
                    print(f"        - {error}")
                if len(validation['errors']) > 3:
                    print(f"        ... and {len(validation['errors']) - 3} more errors")
            
            print()
        else:
            print(f"  ❌ {mock_file.name} → FAILED")
            print(f"     Error: {result.get('error', 'Unknown error')}")
            print()
    
    # Summary
    print("=" * 60)
    print("📊 CONVERSION SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {len(mock_files)}")
    print(f"Successful conversions: {successful_conversions}")
    print(f"Failed conversions: {len(mock_files) - successful_conversions}")
    print(f"Total questions converted: {total_questions}")
    print()
    
    # Detailed validation summary
    print("📋 VALIDATION SUMMARY")
    print("-" * 40)
    
    # Calculate overall category summary
    total_category_counts = {}
    for result in results:
        if result['success']:
            for category, count in result['validation']['sections'].items():
                total_category_counts[category] = total_category_counts.get(category, 0) + count
    
    print("📊 QUESTIONS PER CATEGORY SUMMARY:")
    for category, count in sorted(total_category_counts.items()):
        print(f"   {category}: {count} questions")
    print()
    
    perfect_files = 0
    files_with_issues = 0
    
    for result in results:
        if result['success']:
            validation = result['validation']
            if validation['count_match'] and validation['duplicate_count'] == 0 and not validation['errors']:
                perfect_files += 1
            else:
                files_with_issues += 1
                print(f"⚠️  {Path(result['source_file']).name}:")
                if not validation['count_match']:
                    print(f"   - Question count mismatch: {validation['total_questions']}/{validation['expected_count']}")
                if validation['duplicate_count'] > 0:
                    print(f"   - Duplicates found: {validation['duplicate_count']}")
                if validation['di_questions_without_images'] > 0:
                    print(f"   - DI questions missing images: {validation['di_questions_without_images']}")
                if validation['non_di_questions_with_images'] > 0:
                    print(f"   - Non-DI questions with images: {validation['non_di_questions_with_images']}")
                if validation['errors']:
                    print(f"   - Errors: {len(validation['errors'])}")
    
    print(f"\n✅ Perfect files: {perfect_files}")
    print(f"⚠️  Files with issues: {files_with_issues}")
    
    if perfect_files == len(mock_files):
        print("\n🎉 ALL CONVERSIONS PERFECT! No issues found.")
    else:
        print(f"\n⚠️  {files_with_issues} files have issues that need attention.")
    
    print(f"\n📁 All converted files saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
