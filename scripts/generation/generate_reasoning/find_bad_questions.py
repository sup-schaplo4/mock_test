import google.generativeai as genai
import json
import os
import time

# --- CONFIGURATION ---
# 1. Add your API Key here
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("❌ Please set GEMINI_API_KEY environment variable")

# 2. Set the path to the JSON file you want to test
# Example: 'path/to/your/Linear_Seating_Arrangement.json'
FILE_TO_TEST = "data/reference_questions/reasoning/by_topic/linear_seating_arrangement.json" 

# --- SCRIPT ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-pro') # Using 1.5 Pro as it's sensitive

def load_questions_from_file(file_path):
    """Loads all questions from the specified JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # This part handles your exact structure
        if isinstance(data, dict) and "questions" in data:
            return data["questions"]
        
        # This part handles a simple list of questions
        elif isinstance(data, list):
            return data
            
        else:
            print(f"❌ Error: Unexpected JSON structure in {file_path}")
            return []
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return []

def main():
    print(f"🔬 Starting scan on file: {FILE_TO_TEST}...")
    all_questions = load_questions_from_file(FILE_TO_TEST)
    
    if not all_questions:
        print("No questions found to test. Exiting.")
        return

    flagged_questions = []
    
    for i, question_data in enumerate(all_questions):
        # Use a more reliable way to get question ID if 'id' might be missing
        question_id = question_data.get('id', f"Unknown_ID_at_index_{i}")
        question_text = question_data.get('questions', '')

        if not question_text:
            print(f"⚠️ Warning: No 'question' text found for ID {question_id}. Skipping.")
            continue

        try:
            # We send a very simple prompt. Its only job is to see if the API
            # will process the text without a safety block.
            prompt = f"Please review the following text and confirm it is safe. Text: {question_text}"
            response = model.generate_content(prompt)
            
            # This line is crucial. We try to access the text. If it's blocked, it will raise an error.
            _ = response.text 
            print(f"✅ CLEAN: Question '{question_id}' passed.")

        except Exception as e:
            # The specific error for a safety block often includes this message.
            if "finish_reason: SAFETY" in str(e) or "response.text" in str(e):
                print(f"❌ FLAGGED: Question '{question_id}' triggered a safety filter!")
                flagged_questions.append(question_id)
            else:
                print(f"❓UNKNOWN ERROR on Question '{question_id}': {e}")
        
        # Add a small delay to respect API rate limits
        time.sleep(1)

    print("\n--- SCAN COMPLETE ---")
    if flagged_questions:
        print("🚨 The following question IDs triggered the safety filter and should be removed or edited:")
        for q_id in flagged_questions:
            print(f"- {q_id}")
    else:
        print("🎉 All questions in this file are clean!")

if __name__ == "__main__":
    main()