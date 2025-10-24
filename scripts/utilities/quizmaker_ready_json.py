import json
from pathlib import Path
import datetime

# --- ⚠️ CONFIGURATION: UPDATE THESE THREE VARIABLES ---

# 1. The path to the mock test file you want to convert.
SOURCE_JSON_PATH = "generated_tests/commercial_series/rbi_phase1_mock_02.json"

# 2. The name of the output file that will be created.
OUTPUT_JSON_PATH = "quiz_maker_import_mock_02.json"

# 3. The base URL path where your chart images are stored in WordPress.
#    (Find this from your WordPress Media Library - it MUST end with a '/')
CHART_IMAGE_BASE_URL = "https://argon-test.in/wp-content/uploads/2025/10/" 

# --- END OF CONFIGURATION ---


def process_question(question_obj, section_name, quiz_maker_questions, question_id_counter, chart_base_url):
    """Process a single question and add it to the quiz maker questions list."""
    
    # --- HANDLE DATA INTERPRETATION SETS ---
    if "data_source" in question_obj:
        di_set_id = question_obj.get('di_set_id', 'unknown_di_set')
        chart_image_url = f"{chart_base_url}{di_set_id}.png"
        
        # Create a separate question for each sub-question in the set
        for sub_question in question_obj.get('questions', []):
            answers = []
            for option_key, option_text in sub_question.get('options', {}).items():
                is_correct = "1" if option_key == sub_question.get('correct_answer') else "0"
                answers.append({
                    "answer": option_text,
                    "correct": is_correct,
                    "image": "" # You can add option-specific images here if needed
                })
            
            quiz_maker_question = {
                "id": str(question_id_counter[0]),
                "question": sub_question.get('question', ''),
                "question_image": chart_image_url,
                "type": "radio", # All your questions are multiple-choice
                "category": section_name,
                "explanation": sub_question.get('explanation', ''),
                "answers": answers,
                "published": "1",
                "weight": "1"
                # Add other static fields if needed
            }
            quiz_maker_questions.append(quiz_maker_question)
            question_id_counter[0] += 1

    # --- HANDLE REGULAR QUESTIONS ---
    else:
        answers = []
        for option_key, option_text in question_obj.get('options', {}).items():
            is_correct = "1" if option_key == question_obj.get('correct_answer') else "0"
            answers.append({
                "answer": option_text,
                "correct": is_correct,
                "image": ""
            })

        quiz_maker_question = {
            "id": str(question_id_counter[0]),
            "question": question_obj.get('question', ''),
            "question_image": None, # No image for regular questions
            "type": "radio",
            "category": section_name,
            "explanation": question_obj.get('explanation', ''),
            "answers": answers,
            "published": "1",
            "weight": "1"
        }
        quiz_maker_questions.append(quiz_maker_question)
        question_id_counter[0] += 1


def convert_argon_to_quiz_maker(source_file, output_file, chart_base_url):
    """
    Converts an Argon Test mock test JSON file to the Quiz Maker Pro import format.
    """
    print(f"🚀 Starting conversion of '{source_file}'...")
    
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            argon_test_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ FATAL ERROR: Source file not found at '{source_file}'. Please check the path.")
        return
    except json.JSONDecodeError:
        print(f"❌ FATAL ERROR: Source file '{source_file}' is not a valid JSON file.")
        return

    quiz_maker_questions = []
    question_id_counter = [1] # Use list to make it mutable

    # Loop through each section (GA, Reasoning, etc.)
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

    # Write the final converted data to the output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(quiz_maker_questions, f, indent=3)
        print(f"✅ Success! Converted {question_id_counter[0] - 1} questions.")
        print(f"Your import file is ready: '{output_file}'")
    except Exception as e:
        print(f"❌ FATAL ERROR: Could not write to output file. Error: {e}")


# --- This makes the script runnable from the command line ---
if __name__ == "__main__":
    convert_argon_to_quiz_maker(SOURCE_JSON_PATH, OUTPUT_JSON_PATH, CHART_IMAGE_BASE_URL)