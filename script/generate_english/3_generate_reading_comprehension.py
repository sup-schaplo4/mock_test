import google.generativeai as genai
import json
import time
from datetime import datetime
from collections import Counter
import os
import re

# ==================== CONFIGURATION ====================

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("❌ Please set GEMINI_API_KEY environment variable")
MODEL_NAME = "gemini-2.0-flash-exp"
BATCH_SIZE = 10  # Smaller batches for complex RC questions
DELAY_BETWEEN_BATCHES = 5  # seconds
TARGET_QUESTIONS = 61  # Total RC questions needed

# Difficulty distribution (40% Hard, 40% Medium, 20% Easy)
DIFFICULTY_SPLIT = {
    'Hard': 25,
    'Medium': 24,
    'Easy': 12
}

# ==================== SETUP ====================

genai.configure(api_key=GEMINI_API_KEY)

generation_config = {
    "temperature": 0.8,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config=generation_config,
)

# ==================== CORE FUNCTIONS ====================

def clean_json_response(response_text):
    """Robust JSON cleaning specifically for RC passages"""
    
    print("  🧹 Cleaning JSON response...")
    
    # Remove markdown code blocks
    if '```json' in response_text:
        response_text = response_text.split('```json')[1].split('```')[0].strip()
    elif '```' in response_text:
        response_text = response_text.split('```')[1].split('```')[0].strip()
    
    # Try direct parsing first
    try:
        data = json.loads(response_text)
        print("  ✅ Direct JSON parse successful")
        return data
    except json.JSONDecodeError as e:
        print(f"  ⚠️  Direct parse failed: {str(e)[:100]}")
    
    # Method 1: Fix escape issues
    try:
        # Replace problematic characters
        cleaned = response_text.replace('\n', ' ')
        cleaned = cleaned.replace('\r', '')
        cleaned = cleaned.replace('\t', ' ')
        
        # Fix common escape issues
        cleaned = cleaned.replace('\\"', '"')
        cleaned = re.sub(r'\\+', '\\\\', cleaned)
        
        data = json.loads(cleaned)
        print("  ✅ Cleaned JSON parse successful (method 1)")
        return data
    except json.JSONDecodeError:
        pass
    
    # Method 2: Extract JSON array using regex
    try:
        json_match = re.search(r'$$\s*\{.*\}\s*$$', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            print("  ✅ Regex extraction successful (method 2)")
            return data
    except:
        pass
    
    # Method 3: Try to fix unterminated strings by finding complete objects
    try:
        # Find all complete question objects
        question_pattern = r'\{[^{}]*"question"[^{}]*"options"[^{}]*"correct_answer"[^{}]*"explanation"[^{}]*\}'
        matches = re.findall(question_pattern, response_text, re.DOTALL)
        
        if matches:
            json_str = '[' + ','.join(matches) + ']'
            data = json.loads(json_str)
            print(f"  ⚠️  Partial extraction successful: {len(data)} questions (method 3)")
            return data
    except:
        pass
    
    # Method 4: Manual parsing as last resort
    try:
        # Try to extract individual fields manually
        questions = []
        parts = response_text.split('"question"')
        
        for part in parts[1:]:  # Skip first empty part
            try:
                # Build a simple question object
                q = {}
                
                # Extract question text
                q_match = re.search(r':\s*"([^"]+)"', part)
                if q_match:
                    q['question'] = q_match.group(1)
                
                # This is very basic - return None if it gets here
                if len(q) > 0:
                    questions.append(q)
            except:
                continue
        
        if len(questions) > 0:
            print(f"  ⚠️  Manual extraction: {len(questions)} incomplete questions (method 4)")
            return None  # Don't use incomplete data
    except:
        pass
    
    print("  ❌ All cleaning methods failed")
    return None


def save_error_log(response_text, error, batch_num):
    """Save error details for debugging"""
    
    os.makedirs('data/rc_errors', exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = f'data/rc_errors/error_batch_{batch_num}_{timestamp}.txt'
    
    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"Batch: {batch_num}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Error: {str(error)}\n\n")
        f.write("="*70 + "\n")
        f.write("RAW RESPONSE:\n")
        f.write("="*70 + "\n")
        f.write(response_text)
    
    print(f"  💾 Error log saved: {error_file}")


def generate_rc_batch(batch_size, difficulty_target, batch_num):
    """Generate one batch of RC questions"""
    
    print(f"\n  📦 Batch {batch_num}")
    print(f"     Target: {batch_size} questions")
    print(f"     Difficulty: H:{difficulty_target['Hard']} M:{difficulty_target['Medium']} E:{difficulty_target['Easy']}")
    
    prompt = f"""You are an expert at creating Reading Comprehension questions for RBI Grade B Phase 1 examination.

**CRITICAL JSON FORMATTING RULES:**
1. Use ONLY double quotes (") for JSON keys and string values
2. Within passage text, AVOID using quotes - use alternate phrasing
3. Write "do not" instead of "don't", "cannot" instead of "can't"
4. Keep all text on single lines (no line breaks inside strings)
5. Escape any necessary quotes with backslash: \\"
6. Passages must be 150-250 words about banking/economics/financial topics

**DIFFICULTY LEVELS:**

**Hard (Generate {difficulty_target['Hard']} questions):**
- Complex 200-250 word passages on advanced topics (monetary policy, financial regulations, global economics)
- Inference and implication questions
- Requires deep comprehension and critical thinking
- Options are subtle and nuanced

**Medium (Generate {difficulty_target['Medium']} questions):**
- Moderate 175-200 word passages on standard banking topics
- Mix of direct and inference questions
- Requires good understanding of concepts
- Options are reasonably distinct

**Easy (Generate {difficulty_target['Easy']} questions):**
- Simple 150-175 word passages on basic topics (banking history, definitions, simple processes)
- Direct comprehension questions
- Information clearly stated in passage
- Options are clearly distinct

**TOPICS FOR PASSAGES:**
- Indian banking system and RBI functions
- Monetary policy and inflation
- Financial inclusion and digital banking
- Banking regulations and reforms
- Economic indicators and trends
- Government schemes and initiatives
- International banking and finance

**OUTPUT FORMAT (STRICT):**
```json
[
  {{
    "passage": "A passage of 150-250 words about banking or economics. Write naturally without using quotation marks within the text. Use simple punctuation only.",
    "question": "What is the primary inference that can be drawn from the passage?",
    "options": {{
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option",
      "E": "Fifth option"
    }},
    "correct_answer": "C",
    "explanation": "Clear explanation of why this answer is correct and others are wrong",
    "difficulty": "Hard",
    "topic": "Reading_Comprehension",
    "subject": "English"
  }}
]
CRITICAL RULES: ❌ NO line breaks inside passage text ❌ NO quotes or apostrophes inside passages (rephrase instead) ❌ NO casual language ✅ Use simple, clean sentences in passages ✅ Focus on banking/RBI/economics topics only ✅ Ensure valid JSON format ✅ Mark difficulty correctly: "Hard", "Medium", or "Easy"

Generate EXACTLY {batch_size} Reading Comprehension questions. Output ONLY valid JSON, nothing else. 
"""

    try:
        print("  🤖 Generating with Gemini...")
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        print(f"  📄 Response received ({len(response_text)} chars)")
        
        # Clean and parse JSON
        questions = clean_json_response(response_text)
        
        if questions is None:
            save_error_log(response_text, "JSON parsing failed", batch_num)
            return []
        
        if not isinstance(questions, list):
            print(f"  ❌ Expected list, got {type(questions)}")
            save_error_log(response_text, f"Invalid type: {type(questions)}", batch_num)
            return []
        
        # Add metadata
        for q in questions:
            q['generated_date'] = datetime.now().isoformat()
            q['source'] = 'AI_Generated_RC_Special'
            q['topic'] = 'Reading_Comprehension'
            q['subject'] = 'English'
            q['generation_model'] = MODEL_NAME
            q['batch_number'] = batch_num
        
        # Verify difficulty
        actual_diff = Counter([q.get('difficulty', 'Unknown') for q in questions])
        print(f"  ✅ Generated: {len(questions)} questions")
        print(f"     Difficulty: H:{actual_diff.get('Hard', 0)} M:{actual_diff.get('Medium', 0)} E:{actual_diff.get('Easy', 0)}")
        
        return questions
        
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {str(e)[:100]}")
        try:
            save_error_log(response.text if 'response' in locals() else "No response", str(e), batch_num)
        except:
            pass
        return []

def main(): 
    """Main generation pipeline for Reading Comprehension"""

    print("\n" + "="*70)
    print("📚 READING COMPREHENSION GENERATOR")
    print("="*70)
    print(f"🎯 Target: {TARGET_QUESTIONS} questions")
    print(f"📊 Distribution: Hard={DIFFICULTY_SPLIT['Hard']}, Medium={DIFFICULTY_SPLIT['Medium']}, Easy={DIFFICULTY_SPLIT['Easy']}")
    print(f"📦 Batch size: {BATCH_SIZE}")
    print("="*70)

    os.makedirs('data/rc_output', exist_ok=True)

    all_questions = []
    remaining_diff = DIFFICULTY_SPLIT.copy()

    num_batches = (TARGET_QUESTIONS + BATCH_SIZE - 1) // BATCH_SIZE

    start_time = datetime.now()

    for batch_num in range(1, num_batches + 1):
        remaining_total = TARGET_QUESTIONS - len(all_questions)
        batch_size = min(BATCH_SIZE, remaining_total)
        
        if remaining_total <= 0:
            break
        
        # Calculate proportional difficulty for this batch
        total_remaining = sum(remaining_diff.values())
        
        if total_remaining > 0:
            batch_diff = {}
            for level in ['Hard', 'Medium', 'Easy']:
                proportion = remaining_diff[level] / total_remaining
                batch_diff[level] = max(0, int(batch_size * proportion))
            
            # Adjust for rounding
            diff_sum = sum(batch_diff.values())
            if diff_sum < batch_size:
                max_level = max(remaining_diff.items(), key=lambda x: x[1])[0]
                batch_diff[max_level] += (batch_size - diff_sum)
        else:
            batch_diff = {'Hard': batch_size // 2, 'Medium': batch_size // 3, 'Easy': batch_size - (batch_size // 2) - (batch_size // 3)}
        
        print(f"\n{'='*70}")
        print(f"Batch {batch_num}/{num_batches}")
        print(f"{'='*70}")
        
        questions = generate_rc_batch(batch_size, batch_diff, batch_num)
        
        if questions:
            all_questions.extend(questions)
            
            # Update remaining
            for q in questions:
                diff = q.get('difficulty', 'Medium')
                if diff in remaining_diff and remaining_diff[diff] > 0:
                    remaining_diff[diff] -= 1
            
            print(f"\n  📊 Progress: {len(all_questions)}/{TARGET_QUESTIONS} questions")
            print(f"  📈 Remaining: H:{remaining_diff['Hard']} M:{remaining_diff['Medium']} E:{remaining_diff['Easy']}")
            
            # Save checkpoint
            checkpoint_file = f'data/rc_output/checkpoint_batch_{batch_num}.json'
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump({'questions': all_questions}, f, indent=2, ensure_ascii=False)
            print(f"  💾 Checkpoint saved")
        else:
            print(f"  ⚠️  Batch {batch_num} failed")
        
        # Rate limiting
        if batch_num < num_batches:
            print(f"\n  ⏳ Waiting {DELAY_BETWEEN_BATCHES}s...")
            time.sleep(DELAY_BETWEEN_BATCHES)

    # Final save
    duration = (datetime.now() - start_time).total_seconds()

    print("\n" + "="*70)
    print("✅ GENERATION COMPLETE")
    print("="*70)
    print(f"⏱️  Duration: {duration/60:.1f} minutes")
    print(f"📊 Generated: {len(all_questions)}/{TARGET_QUESTIONS} questions")

    # Calculate statistics
    diff_count = Counter([q.get('difficulty') for q in all_questions])
    print(f"\n📈 Final Difficulty Distribution:")
    print(f"   Hard:   {diff_count.get('Hard', 0)}/{DIFFICULTY_SPLIT['Hard']}")
    print(f"   Medium: {diff_count.get('Medium', 0)}/{DIFFICULTY_SPLIT['Medium']}")
    print(f"   Easy:   {diff_count.get('Easy', 0)}/{DIFFICULTY_SPLIT['Easy']}")

    # Save final output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_file = f'data/rc_output/reading_comprehension_{timestamp}.json'

    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'topic': 'Reading_Comprehension',
                'total_questions': len(all_questions),
                                'generation_date': datetime.now().isoformat(),
                'model': MODEL_NAME,
                'duration_seconds': duration,
                'target': TARGET_QUESTIONS,
                'difficulty_distribution': {
                    'target': DIFFICULTY_SPLIT,
                    'actual': {
                        'Hard': diff_count.get('Hard', 0),
                        'Medium': diff_count.get('Medium', 0),
                        'Easy': diff_count.get('Easy', 0)
                    }
                }
            },
            'questions': all_questions
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Final output saved: {final_file}")
    
    # Show sample
    if all_questions:
        print(f"\n📝 Sample Question:")
        print("="*70)
        sample = all_questions[0]
        passage_preview = sample.get('passage', '')[:150]
        print(f"Passage (preview): {passage_preview}...")
        print(f"\nQuestion: {sample.get('question', 'N/A')}")
        print(f"Difficulty: {sample.get('difficulty', 'N/A')}")
        print(f"Correct Answer: {sample.get('correct_answer', 'N/A')}")
        print("="*70)
    
    return all_questions, final_file

# ==================== VALIDATION ====================

def validate_rc_questions(questions):
    """Validate RC questions specifically"""
    
    print("\n" + "="*70)
    print("🔍 VALIDATING READING COMPREHENSION QUESTIONS")
    print("="*70)
    
    issues = []
    
    for i, q in enumerate(questions, 1):
        # Check required fields
        required = ['passage', 'question', 'options', 'correct_answer', 'explanation', 'difficulty']
        missing = [f for f in required if f not in q or not q[f]]
        
        if missing:
            issues.append(f"Q{i}: Missing fields: {missing}")
        
        # Check passage length
        if 'passage' in q:
            passage_len = len(q['passage'].split())
            if passage_len < 100:
                issues.append(f"Q{i}: Passage too short ({passage_len} words, need 150+)")
            elif passage_len > 300:
                issues.append(f"Q{i}: Passage too long ({passage_len} words, max 250)")
        
        # Check options
        if 'options' in q:
            if len(q['options']) != 5:
                issues.append(f"Q{i}: Should have 5 options, has {len(q['options'])}")
            
            if set(q['options'].keys()) != {'A', 'B', 'C', 'D', 'E'}:
                issues.append(f"Q{i}: Options should be A-E, got {set(q['options'].keys())}")
        
        # Check correct answer
        if 'correct_answer' in q:
            if q['correct_answer'] not in ['A', 'B', 'C', 'D', 'E']:
                issues.append(f"Q{i}: Invalid correct_answer: {q['correct_answer']}")
        
        # Check difficulty
        if 'difficulty' in q:
            if q['difficulty'] not in ['Hard', 'Medium', 'Easy']:
                issues.append(f"Q{i}: Invalid difficulty: {q['difficulty']}")
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} validation issues:\n")
        for issue in issues[:15]:
            print(f"   • {issue}")
        if len(issues) > 15:
            print(f"   ... and {len(issues) - 15} more issues")
        return False
    else:
        print(f"\n✅ All {len(questions)} questions passed validation!")
        return True

# ==================== EXECUTION ====================

if __name__ == "__main__":
    print("\n" + "📚"*35)
    print("RBI GRADE B - READING COMPREHENSION GENERATOR")
    print("📚"*35 + "\n")
    
    try:
        # Generate questions
        questions, output_file = main()
        
        if questions:
            # Validate
            is_valid = validate_rc_questions(questions)
            
            if is_valid:
                print("\n✅ All quality checks passed!")
            else:
                print("\n⚠️  Some validation issues found (see above)")
            
            print("\n" + "="*70)
            print("🎉 READY TO MERGE")
            print("="*70)
            print(f"\n📁 Output file: {output_file}")
            print(f"📊 Total questions: {len(questions)}")
            print("\n✅ You can now use the merge script to combine with main dataset")
        else:
            print("\n❌ No questions generated. Check error logs in data/rc_errors/")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("🏁 Program completed")
    print("="*70 + "\n")

