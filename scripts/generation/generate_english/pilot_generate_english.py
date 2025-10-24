import google.generativeai as genai
import json
import os
import random
from datetime import datetime
from collections import Counter
import time

# ==================== CONFIGURATION ====================

MODEL_NAME = 'gemini-2.5-flash'  # Fast and available model
PILOT_QUESTIONS_PER_TOPIC = 5  # Small test batch

print("="*70)
print("🧪 PILOT RUN - English Question Generation")
print("="*70)
print(f"🤖 Model: {MODEL_NAME}")
print(f"📊 Target: {PILOT_QUESTIONS_PER_TOPIC} questions per topic")
print("="*70)

# Configure API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("❌ Please set GEMINI_API_KEY environment variable")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# ==================== LOAD REFERENCE DATA ====================

with open('data/english_reference_set_classified.json', 'r') as f:
    reference_data = json.load(f)
    REFERENCE_QUESTIONS = [q for q in reference_data['questions'] if q.get('topic') != 'Unknown']

print(f"\n✅ Loaded {len(REFERENCE_QUESTIONS)} reference questions")

topic_counts = Counter([q['topic'] for q in REFERENCE_QUESTIONS])
print("\n📊 Reference topic distribution:")
for topic, count in topic_counts.most_common():
    print(f"  {topic:30s}: {count:3d} questions")

# ==================== PILOT TEST TOPICS ====================

# Test with just 3 diverse topics first
PILOT_TOPICS = {
    "Vocabulary": PILOT_QUESTIONS_PER_TOPIC,           # Easy to validate
    "Error_Spotting": PILOT_QUESTIONS_PER_TOPIC,       # Grammar-based
    "Fill_in_the_Blanks": PILOT_QUESTIONS_PER_TOPIC    # Context-based
}

print(f"\n🎯 Pilot topics (total {sum(PILOT_TOPICS.values())} questions):")
for topic, count in PILOT_TOPICS.items():
    ref_count = topic_counts.get(topic, 0)
    print(f"  {topic:30s}: {count:3d} questions (using {ref_count} references)")

# ==================== HELPER FUNCTIONS ====================

def get_topic_examples(topic, count=8):
    """Get reference examples for a specific topic"""
    topic_questions = [q for q in REFERENCE_QUESTIONS if q.get('topic') == topic]
    
    if not topic_questions:
        print(f"⚠️  No reference questions found for {topic}")
        return []
    
    sample_size = min(count, len(topic_questions))
    return random.sample(topic_questions, sample_size)

def format_examples_for_prompt(examples):
    """Format reference questions for few-shot prompt"""
    formatted = []
    
    for i, ex in enumerate(examples[:6], 1):  # Limit to 6 for pilot
        question_text = ex.get('question', '')
        
        if len(question_text) > 400:
            question_text = question_text[:400] + "..."
        
        formatted.append(f"""
                            EXAMPLE {i}:
                            Question: {question_text}
                            Options: {json.dumps(ex.get('options', {}), ensure_ascii=False)}
                            Correct Answer: {ex.get('correct_answer', '')}
                            Explanation: {ex.get('explanation', 'Not provided')[:200]}
                            Difficulty: {ex.get('difficulty', 'Hard')}
                            ---""")
    
    return "\n".join(formatted)

# ==================== TOPIC INSTRUCTIONS ====================

TOPIC_INSTRUCTIONS = {
    "Vocabulary": """
**DISTRIBUTION:**
- Synonyms: 3 questions
- Antonyms: 2 questions

**Word Complexity:**
Use advanced words relevant to banking/economics:
- Medium level: ameliorate, pragmatic, tangible, stringent, volatile
- Hard level: obfuscate, sanguine, pervasive, taciturn

**FORMAT:**
Choose the word CLOSEST/OPPOSITE in meaning to the given word.
Provide context sentence for harder words.

**CRITICAL:**
- Distractors should be semantically close
- Use banking/finance context
- Clear explanations with nuances
""",
    
    "Error_Spotting": """
**FORMAT:**
Sentence divided into 4 parts:
"(A) First part / (B) Second part / (C) Third part / (D) Fourth part"

Options: A, B, C, D, E (where E = "No error")

**Grammar Focus for 5 questions:**
- Subject-verb agreement: 1 question
- Tense error: 1 question
- Preposition usage: 1 question
- Pronoun/article error: 1 question
- No error: 1 question

**Context:** Banking sector, RBI policies, financial operations

**CRITICAL:**
- Errors must be SUBTLE (not obvious)
- Use professional, formal language
- Banking terminology required
""",
    
    "Fill_in_the_Blanks": """
**TYPES:**
- Single blank: 3 questions (test vocabulary OR grammar)
- Double blank: 2 questions (test logical word pairs)

**Vocabulary:**
Use advanced banking terms: mitigate, consolidate, volatile, ameliorate, stringent, expedite, bolster, curtail, prudent

**Grammar:**
Prepositions with verbs (comply with, adhere to, pursuant to)
Conjunctions (although, whereas, despite, nevertheless)

**Context:** Banking operations, monetary policy, financial markets, RBI regulations

**CRITICAL:**
- All distractors must be grammatically/contextually plausible
- Test precise word choice
- Banking/economics context mandatory
"""
}

# ==================== GENERATION FUNCTION ====================

def generate_questions_for_topic(topic, target_count):
    """Generate questions for a specific topic"""
    
    print(f"\n{'='*70}")
    print(f"🎯 Generating {target_count} questions for: {topic}")
    print(f"{'='*70}")
    
    # Get reference examples
    examples = get_topic_examples(topic, count=8)
    
    if not examples:
        print(f"❌ No reference examples for {topic}")
        return []
    
    print(f"📚 Using {len(examples)} reference examples")
    
    examples_text = format_examples_for_prompt(examples)
    instructions = TOPIC_INSTRUCTIONS.get(topic, "Generate questions matching reference style.")
    
    prompt = f"""You are an expert at creating RBI Grade B Phase 1 English questions.

**TOPIC:** {topic}

**REFERENCE EXAMPLES FROM ACTUAL RBI EXAMS (2017-2023):**
{examples_text}

**YOUR TASK:**
Generate {target_count} NEW questions that PRECISELY match the reference examples in:
- Difficulty level (85% Hard)
- Question structure and format
- Banking/economics context
- Explanation quality

**SPECIFIC INSTRUCTIONS FOR {topic}:**
{instructions}

**MANDATORY REQUIREMENTS:**
✅ Match reference difficulty (mostly Hard, genuinely challenging)
✅ Use banking/economics/finance contexts exclusively
✅ Follow EXACT format of reference examples
✅ Create plausible distractors (wrong options should be tempting)
✅ Provide detailed explanations with clear reasoning
✅ Use professional, formal language
✅ Ensure grammatical perfection

**OUTPUT FORMAT (Valid JSON Array):**
```json
[
  {{
    "question": "Full question text here",
    "options": {{
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text",
      "E": "Option E text"
    }},
    "correct_answer": "C",
    "explanation": "Detailed explanation with clear reasoning",
    "difficulty": "Hard",
    "topic": "{topic}",
    "subject": "English"
  }}
]
CRITICAL RULES: ❌ Do NOT make questions easier than references ❌ Do NOT use casual or informal language ❌ Do NOT create obvious or trivial questions ✅ DO ensure all questions are challenging but fair ✅ DO use current banking/RBI terminology ✅ DO provide comprehensive explanations

Generate EXACTLY {target_count} questions now. Output ONLY valid JSON, no other text. 
"""

    try:
        print("⏳ Sending request to Gemini...")
        response = model.generate_content(
            prompt,
            request_options={"timeout": 120}
        )
        
        response_text = response.text.strip()
        
        # Clean JSON
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        questions = json.loads(response_text)
        
        # Add metadata
        for q in questions:
            q['generated_date'] = datetime.now().isoformat()
            q['source'] = 'AI_Generated_Pilot'
            q['reference_count'] = len(examples)
            q['topic'] = topic
            q['subject'] = 'English'
            q['generation_model'] = MODEL_NAME
        
        print(f"✅ Successfully generated {len(questions)}/{target_count} questions")
        
        # Show samples
        if questions:
            print(f"\n📝 Sample question preview:")
            sample = questions[0]
            q_preview = sample['question'][:150]
            print(f"   Q: {q_preview}...")
            print(f"   Options: {list(sample['options'].keys())}")
            print(f"   Answer: {sample.get('correct_answer', 'N/A')}")
            print(f"   Difficulty: {sample.get('difficulty', 'N/A')}")
        
        return questions
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"\n📄 Response preview:\n{response_text[:500]}")
        
        # Save error
        os.makedirs('data/pilot/errors', exist_ok=True)
        error_file = f'data/pilot/errors/error_{topic}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"Topic: {topic}\n")
            f.write(f"Target count: {target_count}\n")
            f.write(f"Error: {str(e)}\n\n")
            f.write("="*70 + "\n")
            f.write("RAW RESPONSE:\n")
            f.write("="*70 + "\n")
            f.write(response_text)
        
        print(f"💾 Error details saved to: {error_file}")
        return []

    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return []

# ==================== MAIN PILOT EXECUTION ====================
def main(): 
    all_pilot_questions = []
    print("\n" + "="*70)
    print("🚀 STARTING PILOT GENERATION")
    print("="*70)

    os.makedirs('data/pilot', exist_ok=True)

    # Generate questions topic by topic
    for i, (topic, count) in enumerate(PILOT_TOPICS.items(), 1):
        print(f"\n[{i}/{len(PILOT_TOPICS)}] Processing: {topic}")
        
        questions = generate_questions_for_topic(topic, count)
        
        if questions:
            all_pilot_questions.extend(questions)
            print(f"📊 Running total: {len(all_pilot_questions)}/{sum(PILOT_TOPICS.values())} questions")
        else:
            print(f"⚠️  Failed to generate questions for {topic}")
        
        # Small delay between topics (rate limiting)
        if i < len(PILOT_TOPICS):
            print("⏳ Waiting 5 seconds before next topic...")
            time.sleep(5)

# ==================== SAVE RESULTS ====================

    print("\n" + "="*70)
    print("💾 SAVING PILOT RESULTS")
    print("="*70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save complete pilot set
    pilot_file = f'data/pilot/pilot_questions_{timestamp}.json'
    with open(pilot_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_questions': len(all_pilot_questions),
                'generation_date': datetime.now().isoformat(),
                'model': MODEL_NAME,
                'type': 'pilot_run',
                'topics_tested': list(PILOT_TOPICS.keys())
            },
            'questions': all_pilot_questions
        }, f, indent=2, ensure_ascii=False)

    print(f"✅ Pilot questions saved to: {pilot_file}")

    # Save topic-wise breakdown
    topic_breakdown = {}
    for topic in PILOT_TOPICS.keys():
        topic_questions = [q for q in all_pilot_questions if q.get('topic') == topic]
        topic_breakdown[topic] = len(topic_questions)

    # Generate summary report
    summary_file = f'data/pilot/pilot_summary_{timestamp}.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("PILOT RUN SUMMARY\n")
        f.write("="*70 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Model: {MODEL_NAME}\n")
        f.write(f"Total Questions: {len(all_pilot_questions)}/{sum(PILOT_TOPICS.values())}\n\n")
        
        f.write("Topic Breakdown:\n")
        f.write("-" * 70 + "\n")
        for topic, count in topic_breakdown.items():
            target = PILOT_TOPICS[topic]
            f.write(f"{topic:30s}: {count}/{target} questions\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("SAMPLE QUESTIONS\n")
        f.write("="*70 + "\n\n")
        
        for topic in PILOT_TOPICS.keys():
            topic_questions = [q for q in all_pilot_questions if q.get('topic') == topic]
            if topic_questions:
                f.write(f"\n--- {topic} ---\n\n")
                sample = topic_questions[0]
                f.write(f"Q: {sample['question'][:200]}...\n\n")
                f.write(f"Options:\n")
                for key, val in sample['options'].items():
                    f.write(f"  {key}) {val[:100]}...\n")
                f.write(f"\nAnswer: {sample['correct_answer']}\n")
                f.write(f"Difficulty: {sample.get('difficulty', 'N/A')}\n")
                f.write(f"Explanation: {sample['explanation'][:150]}...\n")
                f.write("\n" + "-"*70 + "\n")

    print(f"✅ Summary report saved to: {summary_file}")

    # ====================

if __name__ == "__main__":
    main()
