#!/usr/bin/env python3
"""
Script to concatenate passage and question fields from reading comprehension JSON
into a single question field in a new JSON file.
"""

import json
from pathlib import Path

def concat_passage_question(input_file, output_file):
    """
    Concatenate passage and question fields into a single question field.
    
    Args:
        input_file (str): Path to the input JSON file
        output_file (str): Path to the output JSON file
    """
    
    print(f"📖 Reading comprehension question concatenator")
    print("=" * 50)
    
    # Load the input JSON file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Loaded input file: {input_file}")
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found!")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON format in '{input_file}'!")
        return
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return
    
    # Extract metadata and questions
    metadata = data.get('metadata', {})
    questions = data.get('questions', [])
    
    print(f"📊 Found {len(questions)} reading comprehension questions")
    
    # Process each question
    processed_questions = []
    for i, question in enumerate(questions):
        # Create a copy of the question
        processed_q = question.copy()
        
        # Check if both passage and question fields exist
        if 'passage' in question and 'question' in question:
            # Concatenate passage and question with proper formatting
            passage = question['passage'].strip()
            question_text = question['question'].strip()
            
            # Create the combined question text
            combined_question = f"{passage}\n\n{question_text}"
            
            # Replace the question field with the combined text
            processed_q['question'] = combined_question
            
            # Remove the separate passage field since it's now part of question
            if 'passage' in processed_q:
                del processed_q['passage']
            
            processed_questions.append(processed_q)
            print(f"✅ Processed question {i+1}/{len(questions)}")
        else:
            print(f"⚠️ Skipping question {i+1}: Missing 'passage' or 'question' field")
            # Still add the question even if it doesn't have both fields
            processed_questions.append(processed_q)
    
    # Create the output data structure
    output_data = {
        "metadata": {
            **metadata,
            "total_questions": len(processed_questions),
            "processing_note": "Passage and question fields concatenated into single question field",
            "original_file": input_file
        },
        "questions": processed_questions
    }
    
    # Write the output JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Output file saved: {output_file}")
    except Exception as e:
        print(f"❌ Error saving output file: {e}")
        return
    
    # Display summary
    print("\n" + "=" * 50)
    print("PROCESSING SUMMARY")
    print("=" * 50)
    print(f"📖 Input file: {input_file}")
    print(f"📄 Output file: {output_file}")
    print(f"📊 Total questions processed: {len(processed_questions)}")
    print(f"🔗 Passage and question fields concatenated with '\\n\\n' separator")
    print(f"📝 Separate 'passage' field removed from output")
    print("=" * 50)
    
    return output_data

def main():
    """Main function to run the concatenation process"""
    
    # Define file paths
    input_file = "data/generated/english_questions/rc_output/reading_comprehension_20251002_165031.json"
    output_file = "data/generated/english_questions/rc_output/reading_comprehension_concatenated.json"
    
    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run the concatenation process
    result = concat_passage_question(input_file, output_file)
    
    if result:
        print(f"\n🎉 Successfully processed {len(result['questions'])} reading comprehension questions!")
        print(f"📁 Output saved to: {output_file}")
        
        # Show a sample of the processed data
        if result['questions']:
            print(f"\n📋 Sample processed question:")
            print("-" * 30)
            sample_q = result['questions'][0]
            print(f"Question ID: {sample_q.get('question_id', 'N/A')}")
            print(f"Difficulty: {sample_q.get('difficulty', 'N/A')}")
            print(f"Combined question length: {len(sample_q['question'])} characters")
            print(f"First 200 characters: {sample_q['question'][:200]}...")

if __name__ == "__main__":
    main()
