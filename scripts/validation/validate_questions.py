#!/usr/bin/env python3
"""
Script to validate the number of questions in each mock test file.
This will help identify any discrepancies in question counting.
"""

import json
import os
from pathlib import Path

def count_questions_in_file(file_path):
    """Count questions in a single mock test file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Count questions in main sections
        main_questions = 0
        subsection_questions = 0
        total_question_ids = 0
        
        print(f"\n📁 File: {file_path}")
        print("=" * 60)
        
        # Count questions in each section
        for section in data.get('sections', []):
            section_name = section.get('section_name', 'Unknown')
            section_questions = len(section.get('questions', []))
            main_questions += section_questions
            
            print(f"  📊 {section_name}: {section_questions} questions")
            
            # Count questions in subsections
            for subsection in section.get('subsections', []):
                subsection_name = subsection.get('subsection_name', 'Unknown')
                subsection_q_count = len(subsection.get('questions', []))
                subsection_questions += subsection_q_count
                
                print(f"    📋 {subsection_name}: {subsection_q_count} questions")
        
        # Count all question_id occurrences in the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            total_question_ids = content.count('"question_id"')
        
        # Get expected total from the test metadata
        expected_total = data.get('total_questions', 0)
        
        print(f"\n📈 Summary:")
        print(f"  Main sections questions: {main_questions}")
        print(f"  Subsection questions: {subsection_questions}")
        print(f"  Total question_id occurrences: {total_question_ids}")
        print(f"  Expected total: {expected_total}")
        print(f"  Actual total (main + subsections): {main_questions + subsection_questions}")
        
        # Check for discrepancies
        if total_question_ids != (main_questions + subsection_questions):
            print(f"  ⚠️  WARNING: question_id count ({total_question_ids}) doesn't match calculated total ({main_questions + subsection_questions})")
            print(f"      This suggests there are duplicate questions!")
        
        if (main_questions + subsection_questions) != expected_total:
            print(f"  ❌ ERROR: Total questions ({main_questions + subsection_questions}) doesn't match expected ({expected_total})")
        else:
            print(f"  ✅ SUCCESS: Question count matches expected total!")
        
        return {
            'file': file_path,
            'main_questions': main_questions,
            'subsection_questions': subsection_questions,
            'total_question_ids': total_question_ids,
            'expected_total': expected_total,
            'actual_total': main_questions + subsection_questions
        }
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return None

def main():
    """Main function to validate all mock test files."""
    print("🔍 MOCK TEST QUESTION VALIDATION")
    print("=" * 60)
    
    # Find all mock test files
    mock_test_dir = Path("generated_tests/commercial_series")
    mock_files = list(mock_test_dir.glob("rbi_phase1_mock_*.json"))
    
    if not mock_files:
        print("❌ No mock test files found in generated_tests/commercial_series/")
        return
    
    print(f"Found {len(mock_files)} mock test files")
    
    results = []
    for mock_file in sorted(mock_files):
        result = count_questions_in_file(mock_file)
        if result:
            results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 OVERALL SUMMARY")
    print("=" * 60)
    
    total_files = len(results)
    correct_files = sum(1 for r in results if r['actual_total'] == r['expected_total'])
    duplicate_files = sum(1 for r in results if r['total_question_ids'] != r['actual_total'])
    
    print(f"Total files processed: {total_files}")
    print(f"Files with correct question count: {correct_files}")
    print(f"Files with duplicate questions: {duplicate_files}")
    
    if duplicate_files > 0:
        print(f"\n⚠️  Files with duplicate questions:")
        for r in results:
            if r['total_question_ids'] != r['actual_total']:
                print(f"  - {r['file'].name}: {r['total_question_ids']} question_ids vs {r['actual_total']} actual")
    
    print(f"\n📋 Individual file results:")
    for r in results:
        status = "✅" if r['actual_total'] == r['expected_total'] else "❌"
        print(f"  {status} {r['file'].name}: {r['actual_total']}/{r['expected_total']} questions")

if __name__ == "__main__":
    main()
