#!/usr/bin/env python3
"""
Script to convert quizmaker format JSON to commercial series format
"""

import json
import sys
import os
import glob
from datetime import datetime
from collections import defaultdict

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

def categorize_questions(questions):
    """Categorize questions by subject/category"""
    categories = defaultdict(list)
    
    for question in questions:
        category = question.get('category', 'General Awareness')
        categories[category].append(question)
    
    return categories

def convert_question_format(quizmaker_question, question_counter):
    """Convert a single question from quizmaker format to commercial format"""
    
    # Extract answers and convert to options format
    options = {}
    correct_answer = ""
    
    if 'answers' in quizmaker_question:
        for i, answer in enumerate(quizmaker_question['answers']):
            option_key = chr(65 + i)  # A, B, C, D, E
            options[option_key] = answer.get('answer', '')
            if answer.get('correct') == '1':
                correct_answer = option_key
    
    # Generate question ID based on category and counter
    category = quizmaker_question.get('category', 'General Awareness')
    category_prefix = {
        'General Awareness': 'GA',
        'English Language': 'EN',
        'Quantitative Aptitude': 'QA',
        'Reasoning': 'RE'
    }.get(category, 'GA')
    
    question_id = f"{category_prefix}_{question_counter:05d}"
    
    # Convert to commercial format
    commercial_question = {
        "question": quizmaker_question.get('question', ''),
        "options": options,
        "correct_answer": correct_answer,
        "explanation": quizmaker_question.get('explanation', ''),
        "source_document": "Converted_from_QuizMaker",
        "difficulty": "Medium",  # Default difficulty since not available in quizmaker format
        "topic": "General",  # Default topic
        "subject": category.replace(' ', '_'),
        "report_category": "converted_quiz",
        "generated_date": datetime.now().isoformat(),
        "generation_model": "conversion_script",
        "generation_type": "QuizMaker_Conversion",
        "question_id": question_id
    }
    
    return commercial_question

def create_section(category_name, questions, section_id, marks_per_question=1, negative_marks=0.25):
    """Create a section in commercial format"""
    
    # Count difficulty distribution (defaulting to Medium since not available)
    difficulty_dist = {"Easy": 0, "Medium": len(questions), "Hard": 0}
    
    # Count topic distribution (defaulting to General)
    topic_dist = {"General": len(questions)}
    
    section = {
        "section_id": section_id,
        "section_name": category_name,
        "total_questions": len(questions),
        "marks_per_question": marks_per_question,
        "negative_marks": negative_marks,
        "questions": questions,
        "questions_generated": len(questions),
        "questions_expected": len(questions),
        "difficulty_distribution": difficulty_dist,
        "topic_distribution": topic_dist
    }
    
    return section

def discover_json_files(directory):
    """Discover all JSON files in the specified directory"""
    pattern = os.path.join(directory, "*.json")
    json_files = glob.glob(pattern)
    
    # Filter out non-quiz files (like quiz_maker_json_format.json)
    quiz_files = []
    for file_path in json_files:
        filename = os.path.basename(file_path)
        if filename.startswith("quiz_maker_import_rbi_phase1_mock_"):
            quiz_files.append(file_path)
    
    return sorted(quiz_files)

def extract_test_info_from_filename(file_path):
    """Extract test ID and name from filename"""
    filename = os.path.basename(file_path)
    
    # Extract mock number from filename like "quiz_maker_import_rbi_phase1_mock_01.json"
    if "mock_" in filename:
        mock_num = filename.split("mock_")[1].split(".")[0]
        test_id = f"RBI_PHASE1_MOCK_{mock_num}"
        test_name = f"RBI Grade B Phase 1 - Mock Test #{mock_num}"
    else:
        test_id = "RBI_PHASE1_MOCK_UNKNOWN"
        test_name = "RBI Grade B Phase 1 - Mock Test"
    
    return test_id, test_name

def convert_quizmaker_to_commercial(quizmaker_data, test_id="RBI_PHASE1_MOCK_01", test_name="RBI Grade B Phase 1 - Mock Test #1"):
    """Convert quizmaker format to commercial format"""
    
    if not isinstance(quizmaker_data, list):
        print("Error: Expected quizmaker data to be a list of questions")
        return None
    
    # Categorize questions
    categorized_questions = categorize_questions(quizmaker_data)
    
    # Convert questions to commercial format
    converted_sections = []
    total_questions = 0
    question_counter = 1
    
    # Define section mapping
    section_mapping = {
        'General Awareness': ('SECTION_A', 1, 0.25),
        'English Language': ('SECTION_B', 1, 0.25),
        'Quantitative Aptitude': ('SECTION_C', 1, 0.25),
        'Reasoning': ('SECTION_D', 1, 0.25)
    }
    
    for category, questions in categorized_questions.items():
        if not questions:
            continue
            
        # Convert questions to commercial format
        converted_questions = []
        for question in questions:
            converted_question = convert_question_format(question, question_counter)
            converted_questions.append(converted_question)
            question_counter += 1
        
        # Get section configuration
        section_id, marks_per_question, negative_marks = section_mapping.get(
            category, ('SECTION_UNKNOWN', 1, 0.25)
        )
        
        # Create section
        section = create_section(
            category, 
            converted_questions, 
            section_id, 
            marks_per_question, 
            negative_marks
        )
        
        converted_sections.append(section)
        total_questions += len(questions)
    
    # Calculate difficulty distribution
    total_easy = sum(section['difficulty_distribution']['Easy'] for section in converted_sections)
    total_medium = sum(section['difficulty_distribution']['Medium'] for section in converted_sections)
    total_hard = sum(section['difficulty_distribution']['Hard'] for section in converted_sections)
    
    # Create the commercial format structure
    commercial_data = {
        "test_id": test_id,
        "test_name": test_name,
        "test_number": 1,
        "test_series": "RBI Grade B 2025 - Premium Series",
        "total_questions": total_questions,
        "total_marks": total_questions,  # Assuming 1 mark per question
        "duration_minutes": 120,
        "negative_marking": 0.25,
        "passing_marks": 0,
        "difficulty_distribution": {
            "Easy": total_easy,
            "Medium": total_medium,
            "Hard": total_hard
        },
        "overlap_percentage": 20,
        "sections": converted_sections,
        "metadata": {
            "conversion_date": datetime.now().isoformat(),
            "original_format": "quizmaker",
            "conversion_script": "convert_quizmaker_to_commercial.py",
            "total_original_questions": len(quizmaker_data)
        },
        "pricing": {
            "individual_price": 99,
            "bundle_price": 499,
            "bundle_size": 10,
            "currency": "INR"
        }
    }
    
    return commercial_data

def process_single_file(input_file, output_dir):
    """Process a single quizmaker file and convert it to commercial format"""
    print(f"\nProcessing: {os.path.basename(input_file)}")
    print("-" * 50)
    
    # Load quizmaker data
    quizmaker_data = load_json_file(input_file)
    
    if quizmaker_data is None:
        print(f"❌ Failed to load {input_file}")
        return False
    
    print(f"✅ Found {len(quizmaker_data)} questions in quizmaker format")
    
    # Extract test info from filename
    test_id, test_name = extract_test_info_from_filename(input_file)
    
    # Convert to commercial format
    print("🔄 Converting to commercial format...")
    commercial_data = convert_quizmaker_to_commercial(quizmaker_data, test_id, test_name)
    
    if commercial_data is None:
        print(f"❌ Conversion failed for {input_file}")
        return False
    
    # Generate output filename
    input_filename = os.path.basename(input_file)
    output_filename = input_filename.replace("quiz_maker_import_", "").replace(".json", "_converted.json")
    output_file = os.path.join(output_dir, output_filename)
    
    # Save converted file
    print("💾 Saving converted file...")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(commercial_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully converted {len(quizmaker_data)} questions")
        print(f"📁 Output saved to: {output_file}")
        
        # Print summary
        print(f"\n📊 CONVERSION SUMMARY for {test_id}")
        print(f"Total questions converted: {commercial_data['total_questions']}")
        print(f"Total sections created: {len(commercial_data['sections'])}")
        
        for section in commercial_data['sections']:
            print(f"  - {section['section_name']}: {section['total_questions']} questions")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

def main():
    # Define directories
    input_dir = "/Users/shubham/Documents/mock_test/generated_tests/quizmaker_ready"
    output_dir = "/Users/shubham/Documents/mock_test/generated_tests/commercial_series"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print("🔍 Discovering JSON files in quizmaker_ready folder...")
    json_files = discover_json_files(input_dir)
    
    if not json_files:
        print("❌ No quizmaker JSON files found!")
        return
    
    print(f"📋 Found {len(json_files)} quizmaker files to process:")
    for file_path in json_files:
        print(f"  - {os.path.basename(file_path)}")
    
    # Process all files
    successful_conversions = 0
    failed_conversions = 0
    
    print(f"\n🚀 Starting batch conversion of {len(json_files)} files...")
    print("=" * 80)
    
    for i, input_file in enumerate(json_files, 1):
        print(f"\n[{i}/{len(json_files)}] Processing file...")
        
        if process_single_file(input_file, output_dir):
            successful_conversions += 1
        else:
            failed_conversions += 1
    
    # Final summary
    print("\n" + "=" * 80)
    print("🎯 BATCH CONVERSION COMPLETE")
    print("=" * 80)
    print(f"✅ Successful conversions: {successful_conversions}")
    print(f"❌ Failed conversions: {failed_conversions}")
    print(f"📁 Output directory: {output_dir}")
    
    if successful_conversions > 0:
        print(f"\n🎉 Successfully converted {successful_conversions} quizmaker files to commercial format!")
    
    if failed_conversions > 0:
        print(f"\n⚠️  {failed_conversions} files failed to convert. Check the error messages above.")

if __name__ == "__main__":
    main()
