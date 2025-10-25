#!/usr/bin/env python3
"""
Script to convert JSON test files to CSV format
Supports both original commercial format and converted format
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

def load_json_file(file_path):
    """Load and parse JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{file_path}' - {e}")
        return None
    except Exception as e:
        print(f"Error loading '{file_path}': {e}")
        return None

def extract_questions_from_commercial_format(data):
    """Extract questions from commercial series format"""
    questions = []
    
    if isinstance(data, dict) and 'sections' in data:
        for section in data.get('sections', []):
            section_name = section.get('section_name', 'Unknown')
            for question in section.get('questions', []):
                questions.append({
                    'question_id': question.get('question_id', ''),
                    'section': section_name,
                    'question': question.get('question', ''),
                    'option_a': question.get('options', {}).get('A', ''),
                    'option_b': question.get('options', {}).get('B', ''),
                    'option_c': question.get('options', {}).get('C', ''),
                    'option_d': question.get('options', {}).get('D', ''),
                    'option_e': question.get('options', {}).get('E', ''),
                    'correct_answer': question.get('correct_answer', ''),
                    'explanation': question.get('explanation', ''),
                    'difficulty': question.get('difficulty', ''),
                    'topic': question.get('topic', ''),
                    'subject': question.get('subject', ''),
                    'source_document': question.get('source_document', ''),
                    'report_category': question.get('report_category', ''),
                    'generated_date': question.get('generated_date', ''),
                    'generation_model': question.get('generation_model', ''),
                    'generation_type': question.get('generation_type', ''),
                    'test_id': data.get('test_id', ''),
                    'test_name': data.get('test_name', ''),
                    'test_series': data.get('test_series', ''),
                    'total_questions': data.get('total_questions', ''),
                    'duration_minutes': data.get('duration_minutes', ''),
                    'negative_marking': data.get('negative_marking', '')
                })
    
    return questions

def extract_questions_from_quizmaker_format(data):
    """Extract questions from quizmaker format"""
    questions = []
    
    if isinstance(data, list):
        for question in data:
            # Convert answers array to individual options
            options = {}
            correct_answer = ""
            
            if 'answers' in question:
                for i, answer in enumerate(question['answers']):
                    option_key = chr(65 + i)  # A, B, C, D, E
                    options[option_key] = answer.get('answer', '')
                    if answer.get('correct') == '1':
                        correct_answer = option_key
            
            questions.append({
                'question_id': question.get('id', ''),
                'section': question.get('category', ''),
                'question': question.get('question', ''),
                'option_a': options.get('A', ''),
                'option_b': options.get('B', ''),
                'option_c': options.get('C', ''),
                'option_d': options.get('D', ''),
                'option_e': options.get('E', ''),
                'correct_answer': correct_answer,
                'explanation': question.get('explanation', ''),
                'difficulty': '',  # Not available in quizmaker format
                'topic': '',  # Not available in quizmaker format
                'subject': question.get('category', ''),
                'source_document': 'QuizMaker_Format',
                'report_category': 'quizmaker',
                'generated_date': '',
                'generation_model': 'quizmaker',
                'generation_type': 'quizmaker_import',
                'test_id': 'QuizMaker_Import',
                'test_name': 'QuizMaker Import',
                'test_series': 'QuizMaker Series',
                'total_questions': len(data),
                'duration_minutes': '',
                'negative_marking': ''
            })
    
    return questions

def write_questions_to_csv(questions, output_file, file_type="commercial"):
    """Write questions to CSV file"""
    
    if not questions:
        print(f"No questions found to write to {output_file}")
        return False
    
    # Define CSV headers
    headers = [
        'question_id', 'section', 'question', 'option_a', 'option_b', 'option_c', 
        'option_d', 'option_e', 'correct_answer', 'explanation', 'difficulty', 
        'topic', 'subject', 'source_document', 'report_category', 'generated_date',
        'generation_model', 'generation_type', 'test_id', 'test_name', 'test_series',
        'total_questions', 'duration_minutes', 'negative_marking'
    ]
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for question in questions:
                # Clean up the data for CSV
                cleaned_question = {}
                for key in headers:
                    value = question.get(key, '')
                    # Replace newlines and quotes in text fields
                    if isinstance(value, str):
                        value = value.replace('\n', ' ').replace('\r', ' ').replace('"', '""')
                    cleaned_question[key] = value
                
                writer.writerow(cleaned_question)
        
        print(f"✅ Successfully wrote {len(questions)} questions to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error writing to {output_file}: {e}")
        return False

def convert_json_to_csv(input_file, output_file, file_type="commercial"):
    """Convert JSON file to CSV format"""
    
    print(f"Converting {input_file} to CSV...")
    
    # Load JSON data
    data = load_json_file(input_file)
    if data is None:
        return False
    
    # Extract questions based on file type
    if file_type == "commercial":
        questions = extract_questions_from_commercial_format(data)
    elif file_type == "quizmaker":
        questions = extract_questions_from_quizmaker_format(data)
    else:
        print(f"Unknown file type: {file_type}")
        return False
    
    if not questions:
        print(f"No questions found in {input_file}")
        return False
    
    # Write to CSV
    success = write_questions_to_csv(questions, output_file, file_type)
    
    if success:
        print(f"📊 Summary for {input_file}:")
        print(f"   - Total questions: {len(questions)}")
        
        # Count by section
        section_counts = {}
        for q in questions:
            section = q.get('section', 'Unknown')
            section_counts[section] = section_counts.get(section, 0) + 1
        
        print(f"   - Sections:")
        for section, count in section_counts.items():
            print(f"     * {section}: {count} questions")
    
    return success

def main():
    """Main function to convert both JSON files to CSV"""
    
    print("="*80)
    print("JSON TO CSV CONVERTER")
    print("="*80)
    
    # Define file paths
    files_to_convert = [
        {
            "input": "/Users/shubham/Documents/mock_test/generated_tests/commercial_series/rbi_phase1_mock_06.json",
            "output": "/Users/shubham/Documents/mock_test/rbi_phase1_mock_06_original.csv",
            "type": "commercial",
            "description": "Original Commercial Format"
        },
        {
            "input": "/Users/shubham/Documents/mock_test/generated_tests/commercial_series/rbi_phase1_mock_06_converted.json",
            "output": "/Users/shubham/Documents/mock_test/rbi_phase1_mock_06_converted.csv",
            "type": "commercial",
            "description": "Converted from QuizMaker Format"
        },

    ]
    
    successful_conversions = 0
    total_files = len(files_to_convert)
    
    for file_info in files_to_convert:
        print(f"\n📁 Processing: {file_info['description']}")
        print(f"   Input:  {file_info['input']}")
        print(f"   Output: {file_info['output']}")
        
        if convert_json_to_csv(
            file_info['input'], 
            file_info['output'], 
            file_info['type']
        ):
            successful_conversions += 1
        else:
            print(f"❌ Failed to convert {file_info['input']}")
    
    print("\n" + "="*80)
    print("CONVERSION SUMMARY")
    print("="*80)
    print(f"Successfully converted: {successful_conversions}/{total_files} files")
    
    if successful_conversions == total_files:
        print("🎉 All files converted successfully!")
    else:
        print("⚠️  Some conversions failed. Check the error messages above.")
    
    print("\n📋 Generated CSV files:")
    for file_info in files_to_convert:
        if Path(file_info['output']).exists():
            file_size = Path(file_info['output']).stat().st_size
            print(f"   ✅ {file_info['output']} ({file_size:,} bytes)")
        else:
            print(f"   ❌ {file_info['output']} (not created)")
    
    print("="*80)

if __name__ == "__main__":
    main()
