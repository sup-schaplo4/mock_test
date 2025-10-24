import google.generativeai as genai
import json
import os

# TEMPORARY: Replace with your actual API key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("❌ Please set GEMINI_API_KEY environment variable")

genai.configure(api_key=GEMINI_API_KEY) 

#genai.configure(api_key=os.environ.get('AIzaSyAt-MPt1krvCo5tJhVTIcumf6FB-fPPdMY'))
model = genai.GenerativeModel('gemini-2.0-flash')  # Using Flash for speed

# Load your English dataset
with open('data/english_reference_set.json', 'r') as f:
    data = json.load(f)
    questions = data['questions']

# English question categories for RBI
CATEGORIES = {
    "Reading_Comprehension": "Questions based on a passage, asking about main idea, inference, tone, or specific details",
    "Error_Spotting": "Identify grammatical errors in sentence parts (A/B/C/D/No Error)",
    "Sentence_Correction": "Choose the correct/best way to phrase an underlined portion",
    "Sentence_Improvement": "Replace underlined part with better alternative",
    "Fill_in_the_Blanks": "Single/double blanks testing vocabulary or grammar",
    "Vocabulary": "Synonyms, antonyms, word meanings",
    "Para_Jumbles": "Rearrange sentences to form coherent paragraph",
    "Cloze_Test": "Fill multiple blanks in a passage",
    "Phrase_Replacement": "Replace highlighted phrase with correct alternative",
    "Idioms_Phrases": "Meaning of idioms or phrasal verbs"
}

def classify_question(question_text, options_text):
    """Use Gemini to classify a single question"""
    
    prompt = f"""Classify this RBI Grade B English question into ONE category.

**Question:** {question_text}

**Options:** {options_text}

**Categories:**
{json.dumps(CATEGORIES, indent=2)}

**Instructions:**
- Return ONLY the category name (e.g., "Reading_Comprehension")
- If passage is mentioned/attached, it's Reading_Comprehension
- If sentence parts labeled (A)/(B)/(C)/(D), likely Error_Spotting
- Base decision on question structure

**Output:** Just the category name, nothing else.
"""
    
    try:
        response = model.generate_content(prompt)
        category = response.text.strip()
        
        # Validate category
        if category in CATEGORIES:
            return category
        else:
            # Fallback: try to match partial
            for cat in CATEGORIES.keys():
                if cat.lower() in category.lower():
                    return cat
            return "Unknown"
    except Exception as e:
        print(f"Error classifying question: {e}")
        return "Unknown"

def batch_classify(questions, batch_size=10):
    """Classify questions in batches to show progress"""
    
    classified_questions = []
    total = len(questions)
    
    print(f"\nClassifying {total} English questions...")
    print("=" * 60)
    
    for i, q in enumerate(questions, 1):
        question_text = q.get('question', '')
        options_text = json.dumps(q.get('options', {}))
        
        # Classify
        category = classify_question(question_text, options_text)
        
        # Add topic to question
        q['topic'] = category
        classified_questions.append(q)
        
        # Progress indicator
        if i % 10 == 0:
            print(f"Progress: {i}/{total} questions classified...")
    
    print(f"\n✅ Classification complete!")
    
    # Summary
    from collections import Counter
    topic_dist = Counter([q['topic'] for q in classified_questions])
    
    print("\n" + "=" * 60)
    print("TOPIC DISTRIBUTION:")
    print("=" * 60)
    for topic, count in sorted(topic_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"  {topic:30s}: {count:3d} questions")
    
    return classified_questions

def main():
    print("Starting English question classification...")
    
    classified = batch_classify(questions)
    
    # Save updated dataset
    output = {
        "total_count": len(classified),
        "classification_date": "2025-10-01",
        "questions": classified
    }
    
    output_file = 'data/english_reference_set_classified.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved classified questions to: {output_file}")
    print("\n🎯 Next step: Run 1_generate_english.py to generate 300 questions")

if __name__ == "__main__":
    main()
