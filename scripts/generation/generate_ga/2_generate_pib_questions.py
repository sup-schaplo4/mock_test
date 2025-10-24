import google.generativeai as genai
import json
import os
import time
from datetime import datetime
from collections import Counter

# ==================== CONFIGURATION ====================

# API Key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("❌ Please set GEMINI_API_KEY environment variable")
genai.configure(api_key=GEMINI_API_KEY)

# Model Configuration
MODEL_NAME = "gemini-2.5-pro"

# ⚙️ ADJUSTABLE PARAMETERS
TOTAL_QUESTIONS = 110  # 🔧 CHANGE THIS to generate more/fewer questions

# Difficulty Distribution (must sum to 1.0)
DIFFICULTY_WEIGHTS = {
    'Hard': 0.30,    # 30%
    'Medium': 0.40,  # 40%
    'Easy': 0.30     # 30%
}

# File Configuration
PIB_FILE_PATH = "data/reports/pib_press_releases/pib_press_releases.txt"
OUTPUT_DIR = "data/generated/pib_questions"

# Topics for PIB Press Releases
PIB_TOPICS = [
    'Government_Finances',
    'Fiscal_Policy',
    'Government_Schemes',
    'Budget_Announcements',
    'Economic_Initiatives',
    'Banking_Developments',
    'Agriculture_Policies',
    'Corporate_Affairs',
    'Financial_Reforms',
    'Public_Sector',
    'Current_Developments'
]

# Batch Configuration (to avoid token limits)
QUESTIONS_PER_BATCH = 20  # Generate 20 questions per API call
MAX_RETRIES = 3

# ==================== FILE UPLOAD ====================

def upload_text_file(file_path):
    """Upload text file to Gemini"""
    
    print("\n" + "="*70)
    print("📤 UPLOADING PIB PRESS RELEASES")
    print("="*70)
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    # Get file stats
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        word_count = len(content.split())
        char_count = len(content)
    
    print(f"\n📊 File Statistics:")
    print(f"   Path: {file_path}")
    print(f"   Size: {os.path.getsize(file_path) / 1024:.1f} KB")
    print(f"   Words: {word_count:,}")
    print(f"   Characters: {char_count:,}")
    
    try:
        print(f"\n⏳ Uploading to Gemini...")
        
        uploaded_file = genai.upload_file(
            path=file_path,
            display_name="PIB_Press_Releases"
        )
        
        # Wait for processing
        while uploaded_file.state.name == "PROCESSING":
            print("   ⏳ Processing...", end="\r")
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)
        
        if uploaded_file.state.name == "FAILED":
            print("   ❌ Upload failed")
            return None
        
        print("   ✅ Upload successful!")
        print(f"   File URI: {uploaded_file.uri}")
        
        return uploaded_file
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


# ==================== QUESTION GENERATION ====================

def calculate_difficulty_split(total, weights):
    """Calculate number of questions per difficulty"""
    
    split = {
        'Hard': int(total * weights['Hard']),
        'Medium': int(total * weights['Medium']),
        'Easy': int(total * weights['Easy'])
    }
    
    # Adjust for rounding
    current_total = sum(split.values())
    if current_total < total:
        split['Medium'] += (total - current_total)
    elif current_total > total:
        split['Easy'] -= (current_total - total)
    
    return split


def generate_pib_questions_batch(model, uploaded_file, batch_num, num_questions, difficulty_split):
    """Generate a batch of questions from PIB press releases"""
    
    print(f"\n{'─'*70}")
    print(f"🤖 BATCH {batch_num}: Generating {num_questions} questions")
    print(f"{'─'*70}")
    print(f"   Hard: {difficulty_split['Hard']}")
    print(f"   Medium: {difficulty_split['Medium']}")
    print(f"   Easy: {difficulty_split['Easy']}")
    
    prompt = f"""You are an expert at creating General Awareness questions for RBI Grade B Phase 1 examination.

**SOURCE:** PIB Press Releases (Ministry of Finance, Agriculture, Corporate Affairs - July-September 2025)

**TASK:** Generate EXACTLY {num_questions} multiple-choice questions from the uploaded press releases.

**DIFFICULTY DISTRIBUTION:**
- Hard: {difficulty_split['Hard']} questions (analytical, requires deep understanding, multi-concept)
- Medium: {difficulty_split['Medium']} questions (moderate complexity, fact-based with reasoning)
- Easy: {difficulty_split['Easy']} questions (straightforward facts, figures, announcements)

**TOPIC CATEGORIES TO USE:**
{', '.join(PIB_TOPICS)}

**QUESTION STYLE GUIDELINES:**

✅ DO:
- Start questions naturally without document references
- Use specific dates, figures, schemes, and policy names from press releases
- Focus on: Government announcements, Budget data, Policy changes, Schemes, Financial figures
- Ask about: "What", "Which", "When", "How much", "Who", "By when"
- Make questions exam-realistic and time-bound (mention months/FY)
- Use exact data from the press releases

❌ DON'T:
- Start with "According to PIB...", "As per press release..."
- Use vague or ambiguous language
- Create hypothetical scenarios
- Fabricate any information

**EXAMPLES OF GOOD QUESTIONS:**

✅ "The Government of India received how much Tax Revenue (Net to Centre) upto August 2025?"
✅ "What was the Gross Market Borrowing planned by the Government for H2 of FY 2025-26?"
✅ "The Government of India and ADB signed a loan of \$125 million for which purpose in September 2025?"
✅ "What was the WMA limit fixed by RBI for H2 of FY 2025-26?"
✅ "Weekly borrowing through Treasury Bills in Q3 of FY 2025-26 was expected to be how much for 13 weeks?"

**MANDATORY JSON FORMAT:**
```json
[
  {{
    "question": "The Government of India received ₹12,82,709 crore upto August 2025, which was what percentage of the corresponding BE 2025-26?",
    "options": {{
      "A": "32.5%",
      "B": "36.7%",
      "C": "40.2%",
      "D": "35.8%",
      "E": "38.9%"
    }},
    "correct_answer": "B",
    "explanation": "According to the monthly accounts published in September 2025, the Government received ₹12,82,709 crore (36.7% of BE 2025-26) upto August 2025, comprising ₹8,10,407 crore Tax Revenue.",
    "source_document": "pib_press_releases.txt",
    "source_type": "PIB Press Releases",
    "release_date": "30 SEP 2025",
    "difficulty": "Medium",
    "topic": "Government_Finances",
    "category": "PIB_Press_Release",
    "subject": "General_Awareness"
  }}
]
CRITICAL RULES:

Extract information ONLY from the uploaded press releases
Use topics from the provided list
Include release_date when mentioned in the source
source_type should be: "PIB Press Release - Ministry of Finance/Agriculture/Corporate Affairs"
Ensure all figures, dates, and schemes are accurate
NO document references in question text
Output ONLY valid JSON array
Generate EXACTLY {num_questions} questions
Begin generation now."""

    try:
        print(f"   🤖 Calling Gemini API...")
        
        response = model.generate_content([prompt, uploaded_file])
        response_text = response.text.strip()
        
        print(f"   ✅ Response received ({len(response_text)} chars)")
        
        questions = clean_json_response(response_text)
        
        if not questions or not isinstance(questions, list):
            print(f"   ❌ JSON parsing failed")
            save_error_log(response_text, f"batch_{batch_num}")
            return []
        
        # Add metadata
        for q in questions:
            q['generated_date'] = datetime.now().isoformat()
            q['generation_model'] = MODEL_NAME
            q['generation_type'] = f'PIB_RAG_Batch_{batch_num}'
            q['subject'] = 'General_Awareness'
            q['category'] = 'PIB_Press_Release'
        
        print(f"   ✅ Generated {len(questions)} questions")
        
        # Show distribution
        diff_count = Counter([q.get('difficulty') for q in questions])
        topic_count = Counter([q.get('topic') for q in questions])
        
        print(f"   📊 Difficulty: H={diff_count.get('Hard', 0)} "
            f"M={diff_count.get('Medium', 0)} E={diff_count.get('Easy', 0)}")
        print(f"   📌 Top topics: {', '.join([f'{t}({c})' for t, c in topic_count.most_common(3)])}")
        
        return questions
        
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        save_error_log(str(e), f"batch_{batch_num}")
        return []

def clean_json_response(response_text): 
    """Clean and parse JSON from Gemini response"""
    import re

    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', response_text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()

    # Try direct parse
    try:
        questions = json.loads(text)
        return questions
    except json.JSONDecodeError:
        pass

    # Try finding JSON array
    try:
        match = re.search(r'$$.*$$', text, re.DOTALL)
        if match:
            questions = json.loads(match.group(0))
            return questions
    except json.JSONDecodeError:
        pass

    return None

def save_error_log(content, batch_info): 
    """Save error log"""
    os.makedirs('data/pib_errors', exist_ok=True)


    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = f'data/pib_errors/error_{batch_info}_{timestamp}.txt'

    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"Batch: {batch_info}\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write("="*70 + "\n")
        f.write(str(content))

    print(f"   💾 Error log: {error_file}")

# ==================== MAIN GENERATION ====================

def generate_all_pib_questions(uploaded_file, total_questions, difficulty_weights): 
    """Generate all PIB questions in batches"""
    print("\n" + "="*70)
    print(f"🚀 GENERATING {total_questions} PIB QUESTIONS")
    print("="*70)

    print(f"\n⚙️  Configuration:")
    print(f"   Model: {MODEL_NAME}")
    print(f"   Total target: {total_questions}")
    print(f"   Questions per batch: {QUESTIONS_PER_BATCH}")
    print(f"   Difficulty: Hard={DIFFICULTY_WEIGHTS['Hard']*100:.0f}% "
        f"Medium={DIFFICULTY_WEIGHTS['Medium']*100:.0f}% "
        f"Easy={DIFFICULTY_WEIGHTS['Easy']*100:.0f}%")

    model = genai.GenerativeModel(model_name=MODEL_NAME)

    # Calculate batches
    num_batches = (total_questions + QUESTIONS_PER_BATCH - 1) // QUESTIONS_PER_BATCH

    print(f"\n📦 Batch Plan:")
    print(f"   Total batches: {num_batches}")

    all_questions = []

    for batch_num in range(1, num_batches + 1):
        # Calculate questions for this batch
        remaining = total_questions - len(all_questions)
        batch_size = min(QUESTIONS_PER_BATCH, remaining)
        
        # Calculate difficulty split for this batch
        batch_difficulty = calculate_difficulty_split(batch_size, difficulty_weights)
        
        # Generate with retries
        batch_questions = None
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n{'='*70}")
            print(f"📦 BATCH {batch_num}/{num_batches} - Attempt {attempt}/{MAX_RETRIES}")
            print(f"{'='*70}")
            
            batch_questions = generate_pib_questions_batch(
                model,
                uploaded_file,
                batch_num,
                batch_size,
                batch_difficulty
            )
            
            if batch_questions:
                break
            
            if attempt < MAX_RETRIES:
                print(f"   ⏳ Retrying in 5 seconds...")
                time.sleep(5)
        
        if batch_questions:
            all_questions.extend(batch_questions)
            print(f"   ✅ Batch {batch_num} complete: {len(batch_questions)} questions")
        else:
            print(f"   ⚠️  Batch {batch_num} failed after {MAX_RETRIES} attempts")
        
        # Rate limiting
        if batch_num < num_batches:
            print(f"   ⏳ Waiting 5 seconds before next batch...")
            time.sleep(5)

    print(f"\n{'='*70}")
    print(f"✅ GENERATION COMPLETE: {len(all_questions)}/{total_questions} questions")
    print(f"{'='*70}")

    return all_questions

# ==================== SAVE & STATISTICS ====================
def save_pib_questions(questions):
    """Save PIB questions to file"""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"pib_questions_{timestamp}.json")
    
    # Calculate statistics
    diff_count = Counter([q.get('difficulty') for q in questions])
    topic_count = Counter([q.get('topic') for q in questions])
    
    output_data = {
        'metadata': {
            'title': 'RBI Grade B - PIB Press Releases Questions',
            'source': 'PIB Press Releases - Ministry of Finance, Agriculture, Corporate Affairs',
            'period': 'July - September 2025',
            'generation_type': 'PIB_RAG',
            'model': MODEL_NAME,
            'total_questions': len(questions),
            'creation_date': datetime.now().isoformat(),
            'difficulty_distribution': {
                'Hard': diff_count.get('Hard', 0),
                'Medium': diff_count.get('Medium', 0),
                'Easy': diff_count.get('Easy', 0)
            },
            'topic_distribution': dict(topic_count),
            'target_questions': TOTAL_QUESTIONS,
            'difficulty_weights': DIFFICULTY_WEIGHTS
        },
        'questions': questions
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Questions saved: {output_file}")
    
    return output_file


def print_final_statistics(questions, start_time):
    """Print comprehensive statistics"""
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("📊 FINAL STATISTICS")
    print("="*70)
    
    print(f"\n⏱️  Generation Time: {duration/60:.1f} minutes")
    print(f"📝 Total Questions: {len(questions)}")
    print(f"🎯 Target: {TOTAL_QUESTIONS}")
    print(f"✅ Success Rate: {len(questions)/TOTAL_QUESTIONS*100:.1f}%")
    
    # Difficulty distribution
    diff_count = Counter([q.get('difficulty') for q in questions])
    print(f"\n🎚️  Difficulty Distribution:")
    print(f"   Hard:   {diff_count.get('Hard', 0):>3} ({diff_count.get('Hard', 0)/len(questions)*100:>5.1f}%) "
          f"[Target: {DIFFICULTY_WEIGHTS['Hard']*100:.0f}%]")
    print(f"   Medium: {diff_count.get('Medium', 0):>3} ({diff_count.get('Medium', 0)/len(questions)*100:>5.1f}%) "
          f"[Target: {DIFFICULTY_WEIGHTS['Medium']*100:.0f}%]")
    print(f"   Easy:   {diff_count.get('Easy', 0):>3} ({diff_count.get('Easy', 0)/len(questions)*100:>5.1f}%) "
          f"[Target: {DIFFICULTY_WEIGHTS['Easy']*100:.0f}%]")
    
    # Topic distribution
    topic_count = Counter([q.get('topic') for q in questions])
    print(f"\n📌 Topic Distribution (Top 10):")
    for i, (topic, count) in enumerate(topic_count.most_common(10), 1):
        print(f"   {i:>2}. {topic:<30}: {count:>3} ({count/len(questions)*100:>5.1f}%)")
    
    # Source type distribution
    source_count = Counter([q.get('source_type', 'Unknown') for q in questions])
    print(f"\n📰 Source Ministry Distribution:")
    for source, count in sorted(source_count.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {source:<50}: {count:>3}")
    
    # Questions with dates
    dated_questions = [q for q in questions if q.get('release_date')]
    print(f"\n📅 Time-specific Questions: {len(dated_questions)} ({len(dated_questions)/len(questions)*100:.1f}%)")
    
    print("\n" + "="*70)


def validate_questions(questions):
    """Validate question quality"""
    
    print("\n" + "="*70)
    print("🔍 QUALITY VALIDATION")
    print("="*70)
    
    issues = []
    
    for i, q in enumerate(questions, 1):
        # Check required fields
        required_fields = ['question', 'options', 'correct_answer', 'explanation', 
                          'difficulty', 'topic', 'category']
        
        for field in required_fields:
            if field not in q or not q[field]:
                issues.append(f"Q{i}: Missing {field}")
        
        # Check options
        if 'options' in q:
            if len(q['options']) != 5:
                issues.append(f"Q{i}: Should have 5 options (A-E)")
            
            required_options = ['A', 'B', 'C', 'D', 'E']
            for opt in required_options:
                if opt not in q['options']:
                    issues.append(f"Q{i}: Missing option {opt}")
        
        # Check correct answer
        if 'correct_answer' in q:
            if q['correct_answer'] not in ['A', 'B', 'C', 'D', 'E']:
                issues.append(f"Q{i}: Invalid correct_answer: {q['correct_answer']}")
        
        # Check difficulty
        if 'difficulty' in q:
            if q['difficulty'] not in ['Hard', 'Medium', 'Easy']:
                issues.append(f"Q{i}: Invalid difficulty: {q['difficulty']}")
        
        # Check for document references in question
        question_text = q.get('question', '').lower()
        bad_phrases = ['according to', 'as per', 'the document', 'press release states']
        for phrase in bad_phrases:
            if phrase in question_text:
                issues.append(f"Q{i}: Contains '{phrase}' in question text")
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} issues:")
        for issue in issues[:20]:  # Show first 20
            print(f"   • {issue}")
        if len(issues) > 20:
            print(f"   ... and {len(issues)-20} more")
    else:
        print("\n✅ All questions passed validation!")
    
    print(f"\n📊 Validation Summary:")
    print(f"   Total questions: {len(questions)}")
    print(f"   Issues found: {len(issues)}")
    print(f"   Pass rate: {(len(questions)*len(required_fields)-len(issues))/(len(questions)*len(required_fields))*100:.1f}%")
    
    print("\n" + "="*70)
    
    return len(issues) == 0


# ==================== MAIN EXECUTION ====================

def main():
    """Main execution function"""
    
    print("\n" + "🎯"*35)
    print("RBI GRADE B - PIB PRESS RELEASES QUESTION GENERATOR")
    print("Source: Ministry of Finance, Agriculture, Corporate Affairs")
    print("Period: July - September 2025")
    print("🎯"*35)
    
    start_time = datetime.now()
    
    try:
        # Step 1: Upload file
        uploaded_file = upload_text_file(PIB_FILE_PATH)
        
        if not uploaded_file:
            print("\n❌ Failed to upload file. Exiting.")
            return
        
        # Step 2: Generate questions
        questions = generate_all_pib_questions(
            uploaded_file,
            TOTAL_QUESTIONS,
            DIFFICULTY_WEIGHTS
        )
        
        if not questions:
            print("\n❌ No questions generated. Exiting.")
            return
        
        # Step 3: Validate questions
        validate_questions(questions)
        
        # Step 4: Save questions
        output_file = save_pib_questions(questions)
        
        # Step 5: Print statistics
        print_final_statistics(questions, start_time)
        
        # Final summary
        print("\n" + "="*70)
        print("✅ SUCCESS!")
        print("="*70)
        print(f"\n📁 Output file: {output_file}")
        print(f"📊 Generated: {len(questions)}/{TOTAL_QUESTIONS} questions")
        print(f"⏱️  Time taken: {(datetime.now()-start_time).total_seconds()/60:.1f} minutes")
        
        print("\n💡 Next Steps:")
        print("   1. Review generated questions for accuracy")
        print("   2. Verify figures and dates against source")
        print("   3. Merge with existing question bank (570 questions)")
        print(f"   4. New total: 570 + {len(questions)} = {570 + len(questions)} questions")
        print("   5. Target remaining: 800 - {} = {} questions".format(
            570 + len(questions), 800 - 570 - len(questions)))
        
        print("\n🎉 PIB question generation complete!")
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🏁 Program terminated\n")


if __name__ == "__main__":
    # Display configuration before starting
    print("\n" + "⚙️ "*35)
    print("CONFIGURATION")
    print("⚙️ "*35)
    print(f"\n📊 Generation Settings:")
    print(f"   Total Questions: {TOTAL_QUESTIONS}")
    print(f"   Questions per Batch: {QUESTIONS_PER_BATCH}")
    print(f"   Model: {MODEL_NAME}")
    print(f"\n🎚️  Difficulty Weights:")
    print(f"   Hard:   {DIFFICULTY_WEIGHTS['Hard']*100:.0f}% ({int(TOTAL_QUESTIONS*DIFFICULTY_WEIGHTS['Hard'])} questions)")
    print(f"   Medium: {DIFFICULTY_WEIGHTS['Medium']*100:.0f}% ({int(TOTAL_QUESTIONS*DIFFICULTY_WEIGHTS['Medium'])} questions)")
    print(f"   Easy:   {DIFFICULTY_WEIGHTS['Easy']*100:.0f}% ({int(TOTAL_QUESTIONS*DIFFICULTY_WEIGHTS['Easy'])} questions)")
    print(f"\n📁 File Path: {PIB_FILE_PATH}")
    print(f"💾 Output Directory: {OUTPUT_DIR}")
    print("\n" + "="*70)
    
    input("\n▶️  Press ENTER to start generation...")
    
    main()
