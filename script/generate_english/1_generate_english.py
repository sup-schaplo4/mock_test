import google.generativeai as genai
import json
import os
import random
from datetime import datetime
from collections import Counter
import time

# ==================== CONFIGURATION ====================

MODEL_NAME = 'gemini-2.0-flash-exp'  # Using Flash as it worked perfectly in pilot

print("="*70)
print("🚀 FULL PRODUCTION RUN - English Question Generation")
print("="*70)
print(f"🤖 Model: {MODEL_NAME}")
print(f"📊 Target: 300 questions total")
print(f"📈 Difficulty: 40% Hard, 40% Medium, 20% Easy")
print("="*70)

# Configure API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("❌ Please set GEMINI_API_KEY environment variable")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# Rate limiting
REQUESTS_PER_MINUTE = 15
BATCH_SIZE = 20  # Generate 20 questions per API call
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE + 1  # ~5 seconds safety margin

# ==================== LOAD REFERENCE DATA ====================

with open('data/reference_questions/english/english_reference_set_classified.json', 'r') as f:
    reference_data = json.load(f)
    REFERENCE_QUESTIONS = [q for q in reference_data['questions'] if q.get('topic') != 'Unknown']

print(f"\n✅ Loaded {len(REFERENCE_QUESTIONS)} reference questions")

topic_counts = Counter([q['topic'] for q in REFERENCE_QUESTIONS])
print("\n📊 Reference topic distribution:")
for topic, count in topic_counts.most_common():
    print(f"  {topic:30s}: {count:3d} questions")

# ==================== TARGET DISTRIBUTION ====================

# Full production distribution (300 questions total)
FULL_DISTRIBUTION = {
    "Fill_in_the_Blanks": 50,
    "Vocabulary": 60,
    "Error_Spotting": 40,
    "Sentence_Correction": 40,
    "Para_Jumbles": 40,
    "Cloze_Test": 10
}

# Difficulty distribution: 40% Hard, 40% Medium, 20% Easy
DIFFICULTY_DISTRIBUTION = {
    "Hard": 0.40,
    "Medium": 0.40,
    "Easy": 0.20
}

print(f"\n🎯 Target generation distribution:")
for topic, count in FULL_DISTRIBUTION.items():
    ref_count = topic_counts.get(topic, 0)
    hard_count = int(count * DIFFICULTY_DISTRIBUTION["Hard"])
    medium_count = int(count * DIFFICULTY_DISTRIBUTION["Medium"])
    easy_count = int(count * DIFFICULTY_DISTRIBUTION["Easy"])
    print(f"  {topic:30s}: {count:3d} questions (H:{hard_count} M:{medium_count} E:{easy_count}) [ref:{ref_count}]")

total_target = sum(FULL_DISTRIBUTION.values())
print(f"\n📊 Total target: {total_target} questions")
print(f"   Hard: {int(total_target * 0.40)} | Medium: {int(total_target * 0.40)} | Easy: {int(total_target * 0.20)}")

# ==================== HELPER FUNCTIONS ====================

def get_topic_examples(topic, count=10):
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
    
    for i, ex in enumerate(examples[:8], 1):
        question_text = ex.get('question', '')
        
        if len(question_text) > 600:
            question_text = question_text[:600] + "... [truncated]"
        
        formatted.append(f"""
EXAMPLE {i}:
Question: {question_text}
Options: {json.dumps(ex.get('options', {}), ensure_ascii=False)}
Correct Answer: {ex.get('correct_answer', '')}
Explanation: {ex.get('explanation', 'Not provided')[:250]}
Difficulty: {ex.get('difficulty', 'Hard')}
---""")
    
    return "\n".join(formatted)

def calculate_difficulty_split(total_count):
    """Calculate how many questions of each difficulty level"""
    hard_count = int(total_count * 0.40)
    medium_count = int(total_count * 0.40)
    easy_count = total_count - hard_count - medium_count  # Remaining goes to Easy
    
    return {
        "Hard": hard_count,
        "Medium": medium_count,
        "Easy": easy_count
    }

def save_checkpoint(questions, checkpoint_name):
    """Save intermediate results"""
    os.makedirs('data/generated/checkpoints', exist_ok=True)
    
    checkpoint_file = f'data/generated/checkpoints/{checkpoint_name}_{len(questions)}q_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
    
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_generated': len(questions),
            'timestamp': datetime.now().isoformat(),
            'model': MODEL_NAME,
            'questions': questions
        }, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Checkpoint saved: {checkpoint_file}")
    return checkpoint_file

# ==================== TOPIC INSTRUCTIONS ====================

TOPIC_INSTRUCTIONS = {
    "Reading_Comprehension": """
**STRUCTURE:**
Generate questions based on passages.

**Passage Requirements:**
- Length: 350-450 words
- Topics: Banking regulations, RBI policies, economic analysis, fintech, financial markets, monetary policy, financial inclusion
- Tone: Professional, analytical (The Economist/RBI bulletin style)
- Complexity varies by difficulty:
  * HARD: Complex economic theories, nuanced policy analysis, requires deep inference
  * MEDIUM: Standard banking concepts, moderate inference needed
  * EASY: Direct factual questions, explicit information

**Question Distribution:**
- Main idea/Central theme: 20%
- Factual/Detail questions: 35%
- Inference/Implication: 30%
- Vocabulary in context: 10%
- Author's tone/purpose: 5%

**Difficulty Guidelines:**
- HARD (40%): Multi-step inference, nuanced interpretation, complex vocabulary
- MEDIUM (40%): Moderate inference, standard banking terms, clear but not obvious
- EASY (20%): Direct facts from passage, straightforward comprehension

**CRITICAL:** 
- Include full passage text with EACH question
- Questions should match the specified difficulty level
- Use varied banking/economics topics across passages
""",
    
    "Error_Spotting": """
**FORMAT:**
Sentence divided into 4 parts:
"(A) First part / (B) Second part / (C) Third part / (D) Fourth part"

Options: A, B, C, D, E (where E = "No error")

**Grammar Concepts:**
- Subject-verb agreement: 25%
- Tense errors: 25%
- Preposition usage: 20%
- Article errors: 10%
- Pronoun agreement: 10%
- Parallelism/Modifiers: 10%

**Difficulty Guidelines:**
- HARD (40%): Subtle grammatical errors, complex sentence structures, advanced usage
- MEDIUM (40%): Standard grammar rules, moderately complex sentences
- EASY (20%): Common errors, simpler sentences, clear mistakes

**Context:** Banking sector, RBI policies, financial operations, economic news

**CRITICAL:**
- Include 20% "No error" sentences distributed across difficulties
- Use professional, formal language
- Banking/economics context mandatory
- Error subtlety should match difficulty level
""",
    
    "Fill_in_the_Blanks": """
**TYPES:**
- Single blank (60%): Test vocabulary OR grammar
- Double blank (40%): Test logical word pairs

**Vocabulary by Difficulty:**
- HARD (40%): obfuscate, sanguine, pervasive, taciturn, ameliorate, exacerbate, pragmatic
- MEDIUM (40%): mitigate, consolidate, volatile, stringent, expedite, bolster, curtail
- EASY (20%): increase, reduce, improve, manage, support, develop, maintain

**Grammar Focus:**
- Prepositions with verbs (comply with, adhere to, pursuant to)
- Conjunctions (although, whereas, despite, nevertheless)
- Modal verbs in banking context

**Context:** Banking operations, monetary policy, financial markets, RBI regulations

**Difficulty Guidelines:**
- HARD: Advanced vocabulary, subtle contextual differences, complex grammar
- MEDIUM: Standard banking terms, moderate vocabulary, clear grammar rules
- EASY: Common words, straightforward context, basic grammar

**CRITICAL:**
- All distractors must be grammatically/contextually plausible
- Test precise word choice appropriate to difficulty level
- Banking/economics context mandatory
""",
    
    "Vocabulary": """
**DISTRIBUTION:**
- Synonyms: 50%
- Antonyms: 40%
- Contextual meaning: 10%

**Word Complexity by Difficulty:**
- HARD (40%): obfuscate, sanguine, taciturn, pervasive, quixotic, juxtapose, inundate, propitiate
- MEDIUM (40%): ameliorate, capitulate, pragmatic, ephemeral, tangible, stringent, mitigate, consolidate
- EASY (20%): volatile, lucrative, prudent, transparent, efficient, substantial, adequate, feasible

**Format:**
- Provide target word
- For HARD words: Include context sentence
- For MEDIUM/EASY: Word alone is sufficient
- 5 options with semantically close distractors

**CRITICAL:**
- Use words relevant to banking/economics
- Distractors should be semantically close (not random)
- Test nuanced differences matching difficulty level
- Provide context sentences for harder words
""",
    
    "Sentence_Correction": """
**FORMAT:**
Sentence with underlined portion. 5 options:
- Options A-D: Different corrections
- Option E: "No correction required"

**Focus Areas:**
- Verb forms and tenses (30%)
- Parallelism in lists (25%)
- Idiomatic expressions (20%)
- Sentence structure (15%)
- Modifier placement (10%)

**Difficulty Guidelines:**
- HARD (40%): Subtle errors, complex idioms, nuanced grammar rules, advanced structures
- MEDIUM (40%): Standard grammar issues, common idioms, moderate complexity
- EASY (20%): Clear errors, basic grammar, simple sentence structures

**Context:** Banking policies, economic reports, business communications, RBI circulars

**CRITICAL:**
- Make the "correct" option clearly better, not just acceptable
- Include genuine "No correction required" cases (15% distributed across difficulties)
- Test banking-specific idioms (comply with, in accordance with, pursuant to)
- Error subtlety matches difficulty level
""",
    
    "Para_Jumbles": """
**FORMAT:**
5-6 sentences (labeled A, B, C, D, E, F) in jumbled order.
Fix ONE sentence as first OR last (state which one).
Ask for correct sequence of remaining sentences.

**Topics:** 
Banking sector updates, policy changes, economic analysis, fintech developments, RBI initiatives, financial regulations

**Logical Flow Patterns:**
- Cause and effect (40%)
- Chronological (30%)
- Problem-solution (20%)
- General to specific (10%)

**Difficulty Guidelines:**
- HARD (40%): Complex reasoning, subtle transitions, multiple plausible sequences (but only one correct)
- MEDIUM (40%): Clear transitions, moderate logical flow, standard patterns
- EASY (20%): Obvious sequence, strong transition words, straightforward logic

**CRITICAL:**
- Ensure ONLY ONE logically correct sequence
- Use transition words appropriate to difficulty (however, moreover, therefore, consequently)
- Include pronouns/demonstratives for coherence (this, these, such, it)
- Topics should be current and relevant to banking
- Complexity of reasoning matches difficulty level
""",
    
    "Cloze_Test": """
**FORMAT:**
250-300 word passage with 5 numbered blanks.
Each blank = 1 question with 5 options (A-E)

**Structure:**
Generate passages with exactly 5 blanks each.

**Blank Types:**
- Vocabulary (contextual fit): 60%
- Grammar (prepositions, conjunctions, articles): 40%

**Topics:** 
Banking sector analysis, RBI monetary policy, digital banking, financial inclusion, regulatory frameworks, fintech, NBFCs

**Difficulty Guidelines:**
- HARD (40%): Subtle word choices, advanced vocabulary, nuanced grammar, context requires careful reading
- MEDIUM (40%): Standard banking terms, clear context, moderate vocabulary
- EASY (20%): Common words, obvious context clues, basic grammar

**CRITICAL:**
- Passage should flow naturally
- Each blank should have only ONE truly correct answer
- Test both meaning and grammar
- Use banking/economics terminology
- Blank difficulty matches specified level
- Distribute difficulty across the 5 blanks within each passage proportionally
"""
}

# ==================== GENERATION FUNCTION ====================

def generate_questions_batch(topic, batch_size, difficulty_target, examples):
    """Generate a batch of questions for a specific topic with difficulty distribution"""
    
    examples_text = format_examples_for_prompt(examples)
    instructions = TOPIC_INSTRUCTIONS.get(topic, "Generate questions matching reference style.")
    
    # Create difficulty requirement string
    difficulty_req = f"""
**DIFFICULTY DISTRIBUTION FOR THIS BATCH:**
Generate exactly:
- {difficulty_target['Hard']} HARD questions (40%)
- {difficulty_target['Medium']} MEDIUM questions (40%)
- {difficulty_target['Easy']} EASY questions (20%)

**DIFFICULTY DEFINITIONS:**

HARD:
- Requires deep analysis, multi-step reasoning, or nuanced understanding
- Advanced vocabulary and complex sentence structures
- Not immediately obvious; requires careful thought
- Examples: Subtle grammar errors, complex inferences, advanced vocabulary

MEDIUM:
- Requires moderate analysis and standard knowledge
- Common banking/economics terminology
- Clear but not immediately obvious
- Examples: Standard grammar rules, moderate inference, common vocabulary

EASY:
- Straightforward and direct
- Basic vocabulary and simple concepts
- Obvious with careful reading
- Examples: Direct factual questions, common words, clear grammar errors
"""
    
    prompt = f"""You are an expert at creating RBI Grade B Phase 1 English questions.

**TOPIC:** {topic}

**REFERENCE EXAMPLES FROM ACTUAL RBI EXAMS (2017-2023):**
{examples_text}

{difficulty_req}

**YOUR TASK:**
Generate {batch_size} NEW questions that PRECISELY match the reference examples in:
- Question structure and format
- Banking/economics context
- Explanation quality
- But with the SPECIFIC difficulty distribution above

**SPECIFIC INSTRUCTIONS FOR {topic}:**
{instructions}

**MANDATORY REQUIREMENTS:**
✅ MUST follow difficulty distribution: {difficulty_target['Hard']} Hard, {difficulty_target['Medium']} Medium, {difficulty_target['Easy']} Easy
✅ Use banking/economics/finance contexts exclusively
✅ Follow EXACT format of reference examples
✅ Create plausible distractors (wrong options should be tempting)
✅ Provide detailed explanations with clear reasoning
✅ Use professional, formal language
✅ Ensure grammatical perfection
✅ Vary topics within banking/economics domain

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
CRITICAL RULES: ❌ Do NOT deviate from the difficulty distribution ❌ Do NOT use casual or informal language ❌ Do NOT create trivial questions for any difficulty level ✅ DO ensure difficulty matches the definitions above ✅ DO use current banking/RBI terminology ✅ DO provide comprehensive explanations ✅ DO mark difficulty field correctly: "Hard", "Medium", or "Easy"

Generate EXACTLY {batch_size} questions with the specified difficulty distribution. Output ONLY valid JSON, no other text. 
"""

    try:
        response = model.generate_content(prompt)
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
            q['source'] = 'AI_Generated_Production'
            q['reference_count'] = len(examples)
            q['topic'] = topic
            q['subject'] = 'English'
            q['generation_model'] = MODEL_NAME
        
        # Verify difficulty distribution
        actual_diff = Counter([q.get('difficulty', 'Unknown') for q in questions])
        print(f"  📊 Difficulty breakdown: H:{actual_diff.get('Hard', 0)} M:{actual_diff.get('Medium', 0)} E:{actual_diff.get('Easy', 0)}")
        
        return questions
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"📄 Response preview: {response_text[:300]}...")
        
        # Save error
        os.makedirs('data/generated/errors', exist_ok=True)
        error_file = f'data/generated/errors/error_{topic}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"Topic: {topic}\n")
            f.write(f"Batch size: {batch_size}\n")
            f.write(f"Difficulty target: {difficulty_target}\n")
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

# ================= TOPIC GENERATION WITH BATCHING ====================

def generate_questions_for_topic(topic, target_count): 
    """Generate questions for a topic with batching and rate limiting"""

    print(f"\n{'='*70}")
    print(f"🎯 Generating {target_count} questions for: {topic}")
    print(f"{'='*70}")

    # Calculate difficulty split for this topic
    difficulty_split = calculate_difficulty_split(target_count)
    print(f"📊 Target difficulty: Hard={difficulty_split['Hard']}, Medium={difficulty_split['Medium']}, Easy={difficulty_split['Easy']}")

    # Get reference examples
    examples = get_topic_examples(topic, count=10)

    if not examples:
        print(f"❌ No reference examples for {topic}")
        return []

    print(f"📚 Using {len(examples)} reference examples")

    # Calculate batches
    num_batches = (target_count + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"📦 Splitting into {num_batches} batches of up to {BATCH_SIZE} questions each")

    all_questions = []
    remaining_diff = difficulty_split.copy()

    for batch_num in range(num_batches):
        remaining = target_count - len(all_questions)
        batch_size = min(BATCH_SIZE, remaining)
        
        # Calculate difficulty for this batch (proportional)
        batch_diff = {}
        total_remaining = sum(remaining_diff.values())
        
        if total_remaining > 0:
            for diff_level in ['Hard', 'Medium', 'Easy']:
                proportion = remaining_diff[diff_level] / total_remaining
                batch_diff[diff_level] = max(0, int(batch_size * proportion))
            
            # Adjust for rounding
            diff_sum = sum(batch_diff.values())
            if diff_sum < batch_size:
                # Add remaining to the level with most remaining
                max_remaining = max(remaining_diff.items(), key=lambda x: x[1])[0]
                batch_diff[max_remaining] += (batch_size - diff_sum)
        else:
            # Fallback if something goes wrong
            batch_diff = calculate_difficulty_split(batch_size)
        
        print(f"\n  Batch {batch_num + 1}/{num_batches}:")
        print(f"  📝 Generating {batch_size} questions (H:{batch_diff['Hard']} M:{batch_diff['Medium']} E:{batch_diff['Easy']})")
        
        batch_questions = generate_questions_batch(topic, batch_size, batch_diff, examples)
        
        if batch_questions:
            all_questions.extend(batch_questions)
            
            # Update remaining difficulty counts
            for q in batch_questions:
                diff = q.get('difficulty', 'Medium')
                if diff in remaining_diff:
                    remaining_diff[diff] = max(0, remaining_diff[diff] - 1)
            
            print(f"  ✅ Batch complete: {len(batch_questions)} questions generated")
            print(f"  📊 Topic progress: {len(all_questions)}/{target_count}")
            print(f"  📉 Remaining difficulty: H:{remaining_diff['Hard']} M:{remaining_diff['Medium']} E:{remaining_diff['Easy']}")
        else:
            print(f"  ⚠️  Batch failed, continuing...")
        
        # Rate limiting between batches
        if batch_num < num_batches - 1:
            print(f"  ⏳ Waiting {DELAY_BETWEEN_REQUESTS:.1f}s (rate limiting)...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Final difficulty verification
    final_diff = Counter([q.get('difficulty', 'Unknown') for q in all_questions])
    print(f"\n✅ Topic complete: Generated {len(all_questions)}/{target_count} questions")
    print(f"📊 Final difficulty: Hard={final_diff.get('Hard', 0)}, Medium={final_diff.get('Medium', 0)}, Easy={final_diff.get('Easy', 0)}")

    # Show sample
    if all_questions:
        print(f"\n📝 Sample question preview:")
        sample = random.choice(all_questions)
        q_preview = sample['question'][:120]
        print(f"   Q: {q_preview}...")
        print(f"   Difficulty: {sample.get('difficulty', 'N/A')}")
        print(f"   Answer: {sample.get('correct_answer', 'N/A')}")

    return all_questions

# ==================== MAIN EXECUTION ====================

def main(): 
    all_generated_questions = []

    print("\n" + "="*70)
    print("🚀 STARTING FULL PRODUCTION GENERATION")
    print("="*70)
    print(f"🎯 Target: 300 total questions")
    print(f"📊 Difficulty: 120 Hard (40%), 120 Medium (40%), 60 Easy (20%)")
    print(f"🤖 Model: {MODEL_NAME}")
    print(f"⏱️  Estimated time: ~{len(FULL_DISTRIBUTION) * 5} minutes (with rate limiting)")
    print("="*70)

    os.makedirs('data/generated', exist_ok=True)

    start_time = datetime.now()

    # Generate questions topic by topic
    for i, (topic, count) in enumerate(FULL_DISTRIBUTION.items(), 1):
        print(f"\n{'#'*70}")
        print(f"[{i}/{len(FULL_DISTRIBUTION)}] PROCESSING TOPIC: {topic}")
        print(f"{'#'*70}")
        
        topic_start = datetime.now()
        
        questions = generate_questions_for_topic(topic, count)
        
        if questions:
            all_generated_questions.extend(questions)
            
            topic_duration = (datetime.now() - topic_start).total_seconds()
            print(f"\n✅ Topic '{topic}' completed in {topic_duration:.1f}s")
            print(f"📊 Running total: {len(all_generated_questions)}/{sum(FULL_DISTRIBUTION.values())} questions")
            
            # Save checkpoint after each topic
            save_checkpoint(all_generated_questions, f"checkpoint_{topic}")
        else:
            print(f"\n⚠️  Warning: No questions generated for {topic}")
        
        # Rate limiting between topics
        if i < len(FULL_DISTRIBUTION):
            print(f"\n⏳ Waiting {DELAY_BETWEEN_REQUESTS:.1f}s before next topic...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    total_duration = (datetime.now() - start_time).total_seconds()

    # ==================== FINAL ANALYSIS & SAVE ====================

    print("\n" + "="*70)
    print("💾 SAVING FINAL RESULTS")
    print("="*70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Calculate statistics
    topic_breakdown = {}
    difficulty_breakdown = Counter()

    for topic in FULL_DISTRIBUTION.keys():
        topic_questions = [q for q in all_generated_questions if q.get('topic') == topic]
        topic_breakdown[topic] = {
            'total': len(topic_questions),
            'Hard': len([q for q in topic_questions if q.get('difficulty') == 'Hard']),
            'Medium': len([q for q in topic_questions if q.get('difficulty') == 'Medium']),
            'Easy': len([q for q in topic_questions if q.get('difficulty') == 'Easy'])
        }
        
        for q in topic_questions:
            difficulty_breakdown[q.get('difficulty', 'Unknown')] += 1

    # Save complete dataset
    final_file = f'data/generated/english_300_questions_{timestamp}.json'
    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_questions': len(all_generated_questions),
                'generation_date': datetime.now().isoformat(),
                'model': MODEL_NAME,
                'generation_duration_seconds': total_duration,
                'target_distribution': FULL_DISTRIBUTION,
                'difficulty_distribution': {
                    'target': {'Hard': '40%', 'Medium': '40%', 'Easy': '20%'},
                    'actual': {
                        'Hard': difficulty_breakdown.get('Hard', 0),
                        'Medium': difficulty_breakdown.get('Medium', 0),
                        'Easy': difficulty_breakdown.get('Easy', 0)
                    }
                },
                'topic_breakdown': topic_breakdown
            },
            'questions': all_generated_questions
        }, f, indent=2, ensure_ascii=False)

    print(f"✅ Final dataset saved to: {final_file}")

    # Generate comprehensive summary report
    summary_file = f'data/generated/generation_summary_{timestamp}.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("ENGLISH QUESTION GENERATION - FINAL REPORT\n")
        f.write("="*70 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Model: {MODEL_NAME}\n")
        f.write(f"Duration: {total_duration/60:.1f} minutes\n")
        f.write(f"Total Questions: {len(all_generated_questions)}/300\n\n")
        
        f.write("="*70 + "\n")
        f.write("DIFFICULTY DISTRIBUTION\n")
        f.write("="*70 + "\n")
        f.write(f"Target:  Hard=120 (40%), Medium=120 (40%), Easy=60 (20%)\n")
        f.write(f"Actual:  Hard={difficulty_breakdown.get('Hard', 0)}, ")
        f.write(f"Medium={difficulty_breakdown.get('Medium', 0)}, ")
        f.write(f"Easy={difficulty_breakdown.get('Easy', 0)}\n")
        
        total_gen = len(all_generated_questions)
        if total_gen > 0:
            f.write(f"Percent: Hard={difficulty_breakdown.get('Hard', 0)/total_gen*100:.1f}%, ")
            f.write(f"Medium={difficulty_breakdown.get('Medium', 0)/total_gen*100:.1f}%, ")
            f.write(f"Easy={difficulty_breakdown.get('Easy', 0)/total_gen*100:.1f}%\n\n")
        
        f.write("="*70 + "\n")
        f.write("TOPIC BREAKDOWN\n")
        f.write("="*70 + "\n")
        f.write(f"{'Topic':<30} {'Total':<8} {'Hard':<8} {'Medium':<8} {'Easy':<8}\n")
        f.write("-" * 70 + "\n")
        
        for topic, stats in topic_breakdown.items():
            target = FULL_DISTRIBUTION[topic]
            f.write(f"{topic:<30} {stats['total']}/{target:<6} ")
            f.write(f"{stats['Hard']:<8} {stats['Medium']:<8} {stats['Easy']:<8}\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("SAMPLE QUESTIONS (One per Topic)\n")
        f.write("="*70 + "\n\n")
        
        for topic in FULL_DISTRIBUTION.keys():
            topic_questions = [q for q in all_generated_questions if q.get('topic') == topic]
            if topic_questions:
                sample = random.choice(topic_questions)
                f.write(f"\n{'='*70}\n")
                f.write(f"TOPIC: {topic}\n")
                f.write(f"{'='*70}\n\n")
                f.write(f"Difficulty: {sample.get('difficulty', 'N/A')}\n\n")
                f.write(f"Question:\n{sample['question']}\n\n")
                f.write(f"Options:\n")
                for key, value in sample.get('options', {}).items():
                    f.write(f"  {key}: {value}\n")
                f.write(f"\nCorrect Answer: {sample.get('correct_answer', 'N/A')}\n")
                f.write(f"\nExplanation:\n{sample.get('explanation', 'N/A')}\n")
    
    print(f"✅ Summary report saved to: {summary_file}")
    
    # Print final console summary
    print("\n" + "="*70)
    print("📊 GENERATION COMPLETE - FINAL SUMMARY")
    print("="*70)
    print(f"⏱️  Total time: {total_duration/60:.1f} minutes")
    print(f"📝 Questions generated: {len(all_generated_questions)}/300")
    print(f"\n📈 Difficulty Distribution:")
    print(f"   Hard:   {difficulty_breakdown.get('Hard', 0):3d} ({difficulty_breakdown.get('Hard', 0)/total_gen*100:5.1f}%) [Target: 40%]")
    print(f"   Medium: {difficulty_breakdown.get('Medium', 0):3d} ({difficulty_breakdown.get('Medium', 0)/total_gen*100:5.1f}%) [Target: 40%]")
    print(f"   Easy:   {difficulty_breakdown.get('Easy', 0):3d} ({difficulty_breakdown.get('Easy', 0)/total_gen*100:5.1f}%) [Target: 20%]")
    
    print(f"\n📋 Topic Distribution:")
    for topic, stats in topic_breakdown.items():
        target = FULL_DISTRIBUTION[topic]
        completion = (stats['total']/target*100) if target > 0 else 0
        print(f"   {topic:<30}: {stats['total']:3d}/{target:3d} ({completion:5.1f}%)")
    
    print(f"\n💾 Files saved:")
    print(f"   • Main dataset: {final_file}")
    print(f"   • Summary report: {summary_file}")
    
    # Check if generation was successful
    success_rate = (len(all_generated_questions) / 300) * 100
    
    if success_rate >= 95:
        print(f"\n✅ SUCCESS: {success_rate:.1f}% of target achieved!")
    elif success_rate >= 80:
        print(f"\n⚠️  PARTIAL SUCCESS: {success_rate:.1f}% of target achieved")
    else:
        print(f"\n❌ LOW SUCCESS RATE: {success_rate:.1f}% of target achieved")
        print("   Consider re-running failed topics or adjusting batch size")
    
    print("\n" + "="*70)
    print("🎉 GENERATION PIPELINE COMPLETED")
    print("="*70 + "\n")
    
    return all_generated_questions

# ==================== VALIDATION FUNCTIONS ====================

def validate_question_quality(questions):
    """Validate generated questions for quality and completeness"""
    
    print("\n" + "="*70)
    print("🔍 VALIDATING QUESTION QUALITY")
    print("="*70)
    
    issues = []
    
    for i, q in enumerate(questions, 1):
        # Check required fields
        required_fields = ['question', 'options', 'correct_answer', 'explanation', 'difficulty', 'topic']
        missing_fields = [field for field in required_fields if field not in q or not q[field]]
        
        if missing_fields:
            issues.append(f"Question {i}: Missing fields: {missing_fields}")
        
        # Check options
        if 'options' in q:
            if len(q['options']) != 5:
                issues.append(f"Question {i}: Should have exactly 5 options, has {len(q['options'])}")
            
            expected_keys = {'A', 'B', 'C', 'D', 'E'}
            if set(q['options'].keys()) != expected_keys:
                issues.append(f"Question {i}: Options should be A-E, got {set(q['options'].keys())}")
        
        # Check correct answer
        if 'correct_answer' in q:
            if q['correct_answer'] not in ['A', 'B', 'C', 'D', 'E']:
                issues.append(f"Question {i}: Invalid correct_answer: {q['correct_answer']}")
        
        # Check difficulty
        if 'difficulty' in q:
            if q['difficulty'] not in ['Hard', 'Medium', 'Easy']:
                issues.append(f"Question {i}: Invalid difficulty: {q['difficulty']}")
        
        # Check minimum lengths
        if 'question' in q and len(q['question']) < 20:
            issues.append(f"Question {i}: Question text too short ({len(q['question'])} chars)")
        
        if 'explanation' in q and len(q['explanation']) < 30:
            issues.append(f"Question {i}: Explanation too short ({len(q['explanation'])} chars)")
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} validation issues:\n")
        for issue in issues[:20]:  # Show first 20 issues
            print(f"   • {issue}")
        if len(issues) > 20:
            print(f"   ... and {len(issues) - 20} more issues")
    else:
        print(f"\n✅ All {len(questions)} questions passed validation!")
    
    return len(issues) == 0

# ==================== UTILITY FUNCTIONS ====================

def create_practice_sets(questions, num_sets=10, questions_per_set=30):
    """Create practice test sets from generated questions"""
    
    print(f"\n📚 Creating {num_sets} practice sets ({questions_per_set} questions each)...")
    
    os.makedirs('data/generated/practice_sets', exist_ok=True)
    
    # Shuffle questions
    shuffled = questions.copy()
    random.shuffle(shuffled)
    
    for set_num in range(1, num_sets + 1):
        start_idx = (set_num - 1) * questions_per_set
        end_idx = start_idx + questions_per_set
        
        if start_idx >= len(shuffled):
            print(f"⚠️  Not enough questions for set {set_num}")
            break
        
        set_questions = shuffled[start_idx:end_idx]
        
        # Calculate set statistics
        difficulty_count = Counter([q.get('difficulty') for q in set_questions])
        topic_count = Counter([q.get('topic') for q in set_questions])
        
        set_file = f'data/generated/practice_sets/practice_set_{set_num}.json'
        with open(set_file, 'w', encoding='utf-8') as f:
            json.dump({
                'set_number': set_num,
                'total_questions': len(set_questions),
                'difficulty_distribution': dict(difficulty_count),
                'topic_distribution': dict(topic_count),
                'time_limit_minutes': 30,
                'questions': set_questions
            }, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Practice Set {set_num} created ({len(set_questions)} questions)")
    
    print(f"\n💾 Practice sets saved to: data/generated/practice_sets/")

def export_to_csv(questions, filename='english_questions.csv'):
    """Export questions to CSV format"""
    
    import csv
    
    csv_file = f'data/generated/{filename}'
    
    print(f"\n📄 Exporting to CSV: {csv_file}")
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['topic', 'difficulty', 'question', 'option_A', 'option_B', 
                      'option_C', 'option_D', 'option_E', 'correct_answer', 'explanation']
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for q in questions:
            row = {
                'topic': q.get('topic', ''),
                'difficulty': q.get('difficulty', ''),
                'question': q.get('question', ''),
                'option_A': q.get('options', {}).get('A', ''),
                'option_B': q.get('options', {}).get('B', ''),
                'option_C': q.get('options', {}).get('C', ''),
                'option_D': q.get('options', {}).get('D', ''),
                'option_E': q.get('options', {}).get('E', ''),
                'correct_answer': q.get('correct_answer', ''),
                'explanation': q.get('explanation', '')
            }
            writer.writerow(row)
    
    print(f"✅ CSV export complete: {len(questions)} questions")

# ==================== EXECUTION ====================

if __name__ == "__main__":
    print("\n" + "🎓"*35)
    print("RBI GRADE B PHASE 1 - ENGLISH QUESTION GENERATOR")
    print("Full Production Mode: 300 Questions")
    print("🎓"*35 + "\n")
    
    try:
        # Run main generation
        generated_questions = main()
        
        # Validate quality
        if generated_questions:
            is_valid = validate_question_quality(generated_questions)
            
            if is_valid:
                print("\n✅ Quality validation passed!")
            else:
                print("\n⚠️  Some quality issues found. Review the validation output above.")
            
            # Create practice sets
            if len(generated_questions) >= 30:
                num_sets = min(10, len(generated_questions) // 30)
                create_practice_sets(generated_questions, num_sets=num_sets, questions_per_set=30)
            
            # Export to CSV
            export_to_csv(generated_questions)
            
            print("\n" + "="*70)
            print("🎉 ALL TASKS COMPLETED SUCCESSFULLY!")
            print("="*70)
            print("\n📦 Generated files:")
            print("   • Main JSON dataset (with metadata)")
            print("   • Summary report (TXT)")
            print("   • Practice sets (JSON)")
            print("   • CSV export")
            print("   • Checkpoints (saved after each topic)")
            print("\n✅ You can now use these questions for RBI Grade B preparation!")
            
        else:
            print("\n❌ No questions were generated. Check error logs in data/generated/errors/")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        print("💾 Checkpoint files have been saved. You can resume from the last checkpoint.")
    
    except Exception as e:
        print(f"\n❌ Fatal error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("\n💾 Check error logs in data/generated/errors/ for details")
    
    finally:
        print("\n" + "="*70)
        print("🏁 Program execution completed")
        print("="*70 + "\n")
