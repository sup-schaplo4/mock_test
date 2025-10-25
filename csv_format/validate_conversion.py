#!/usr/bin/env python3
"""
Script to validate the conversion from quizmaker to commercial format
"""

import json

def validate_conversion():
    """Validate the converted file structure and content"""
    
    # Load both files
    with open('/Users/shubham/Documents/mock_test/generated_tests/quizmaker_ready/quiz_maker_import_rbi_phase1_mock_02.json', 'r') as f:
        original = json.load(f)
    
    with open('/Users/shubham/Documents/mock_test/generated_tests/commercial_series/rbi_phase1_mock_02_converted.json', 'r') as f:
        converted = json.load(f)
    
    print("VALIDATION REPORT")
    print("="*50)
    
    # Check total questions
    original_count = len(original)
    converted_count = converted['total_questions']
    
    print(f"Original questions: {original_count}")
    print(f"Converted questions: {converted_count}")
    print(f"Match: {'✓' if original_count == converted_count else '✗'}")
    
    # Check sections
    sections = converted['sections']
    print(f"\nSections created: {len(sections)}")
    
    total_section_questions = sum(section['total_questions'] for section in sections)
    print(f"Total questions in sections: {total_section_questions}")
    print(f"Match with total: {'✓' if total_section_questions == converted_count else '✗'}")
    
    # Check each section
    print("\nSection breakdown:")
    for section in sections:
        print(f"- {section['section_name']}: {section['total_questions']} questions")
    
    # Sample question validation
    print("\nSample question validation:")
    if sections and sections[0]['questions']:
        sample_question = sections[0]['questions'][0]
        print(f"Question ID: {sample_question['question_id']}")
        print(f"Question text length: {len(sample_question['question'])}")
        print(f"Options count: {len(sample_question['options'])}")
        print(f"Has explanation: {'✓' if sample_question['explanation'] else '✗'}")
        print(f"Correct answer: {sample_question['correct_answer']}")
    
    print("\nValidation complete!")

if __name__ == "__main__":
    validate_conversion()
