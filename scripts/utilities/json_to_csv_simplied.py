# Extract just 25 questions for demo
import json
import pandas as pd

# Load your full JSON
with open('src/test_engine/generated_tests/commercial_series/rbi_phase1_mock_10.json', 'r') as f:
    data = json.load(f)

# Extract 25 questions from each section
all_questions = []
for section in data.get('sections', []):
    section_name = section.get('section_name', 'Unknown')
    section_questions = section.get('questions', [])
    
    # Take first 25 questions from this section
    section_sample = section_questions[:25]
    
    # Add section info to each question for reference
    for question in section_sample:
        question['section_name'] = section_name
    
    all_questions.extend(section_sample)
    print(f"✅ Extracted {len(section_sample)} questions from {section_name}")

print(f"\n📊 Total questions extracted: {len(all_questions)}")
demo_questions = all_questions

# Convert to CSV
df = pd.DataFrame([{
    'section': q.get('section_name', ''),
    'question': q.get('question', ''),
    'option_A': q.get('options', {}).get('A', ''),
    'option_B': q.get('options', {}).get('B', ''),
    'option_C': q.get('options', {}).get('C', ''),
    'option_D': q.get('options', {}).get('D', ''),
    'option_E': q.get('options', {}).get('E', ''),
    'correct_answer': q.get('correct_answer', ''),
    'explanation': q.get('explanation', ''),
} for q in demo_questions])

df.to_csv('demo_test_25_questions.csv', index=False)
print("✅ Demo CSV ready!")
