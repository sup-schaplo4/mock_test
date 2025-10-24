import google.generativeai as genai
import json
import os
import time
from datetime import datetime
from pathlib import Path
import re

# ==================== CONFIGURATION ====================

# API Key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("❌ Please set GEMINI_API_KEY environment variable")
genai.configure(api_key=GEMINI_API_KEY)

# Model Configuration
MODEL_NAME = "gemini-2.5-pro"  # Using 1.5 Pro for pilot


# File paths
REPORTS_DIR = "data/reports"  # Your PDFs folder
OUTPUT_DIR = "data/generated/pilot_ga"

# Pilot Configuration
PILOT_QUESTIONS = 5
DIFFICULTY_SPLIT = {
    'Hard': 2,
    'Medium': 2,
    'Easy': 1
}

# ==================== FILE UPLOAD ====================

def upload_pdf_to_gemini(file_path, display_name=None):
    """Upload PDF to Gemini and return file reference"""
    
    if display_name is None:
        display_name = os.path.basename(file_path)
    
    print(f"   📤 Uploading: {display_name}")
    
    try:
        uploaded_file = genai.upload_file(
            path=file_path,
            display_name=display_name
        )
        
        print(f"      ✅ Uploaded - URI: {uploaded_file.name}")
        
        # Wait for file to be processed
        while uploaded_file.state.name == "PROCESSING":
            print(f"      ⏳ Processing...")
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)
        
        if uploaded_file.state.name == "FAILED":
            print(f"      ❌ Upload failed")
            return None
        
        print(f"      ✅ Ready - State: {uploaded_file.state.name}")
        return uploaded_file
        
    except Exception as e:
        print(f"      ❌ Error uploading: {e}")
        return None


def upload_all_reports(reports_dir):
    """Upload all PDF reports to Gemini"""
    
    print("\n" + "="*70)
    print("📚 UPLOADING REPORTS TO GEMINI")
    print("="*70)
    
    pdf_files = list(Path(reports_dir).glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n❌ No PDF files found in {reports_dir}")
        return []
    
    print(f"\n📂 Found {len(pdf_files)} PDF files")
    
    uploaded_files = []
    
    for pdf_file in pdf_files:
        uploaded = upload_pdf_to_gemini(str(pdf_file))
        if uploaded:
            uploaded_files.append({
                'file': uploaded,
                'name': pdf_file.name,
                'path': str(pdf_file)
            })
        time.sleep(1)  # Rate limiting
    
    print(f"\n✅ Successfully uploaded {len(uploaded_files)}/{len(pdf_files)} files")
    
    return uploaded_files


# ==================== QUESTION GENERATION ====================

def generate_ga_questions_with_rag(uploaded_files, num_questions, difficulty_split):
    """Generate GA questions using RAG approach"""
    
    print("\n" + "="*70)
    print(f"🤖 GENERATING {num_questions} GA QUESTIONS WITH RAG")
    print("="*70)
    
    # Create model
    model = genai.GenerativeModel(model_name=MODEL_NAME)
    
    # Prepare file references for prompt
    file_refs = [f['file'] for f in uploaded_files]
    file_names = [f['name'] for f in uploaded_files]
    
    print(f"\n📚 Using {len(file_refs)} documents:")
    for name in file_names:
        print(f"   • {name}")
    
    # Create prompt
    prompt = f"""You are an expert at creating General Awareness questions for RBI Grade B Phase 1 examination.

**IMPORTANT: Use the uploaded PDF documents as your PRIMARY source. Extract facts, figures, policies, and data from these documents.**

**DOCUMENTS AVAILABLE:**
{chr(10).join([f"- {name}" for name in file_names])}

**TASK:** Generate EXACTLY {num_questions} multiple-choice questions based on information from these documents.

**DIFFICULTY DISTRIBUTION:**
- Hard: {difficulty_split['Hard']} questions (requires deep understanding, inference, cross-document connections)
- Medium: {difficulty_split['Medium']} questions (requires good comprehension, single document)
- Easy: {difficulty_split['Easy']} questions (direct facts, clearly stated information)

**TOPIC AREAS TO COVER:**
1. RBI Functions & Policies (from RBI Annual Reports, Bulletins)
2. Monetary Policy & Inflation (from Monetary Policy Reports)
3. Banking Sector & Regulations (from RBI Reports, FSR)
4. Economic Indicators & Trends (from Economic Survey)
5. Union Budget 2024-25 (from Budget documents)
6. Financial Stability (from Financial Stability Reports)
7. Government Schemes & Initiatives (from Economic Survey, Budget)
8. Recent Banking Developments (from RBI Bulletins)

**QUESTION TYPES:**
- Factual: What is X? When did Y happen? Who is Z?
- Conceptual: Why does X happen? How does Y work?
- Data-based: What was the GDP growth rate in FY 2024?
- Comparative: What's the difference between X and Y?

**CRITICAL JSON FORMAT:**
```json
[
  {{
    "question": "What was the GDP growth rate projected for FY 2024-25 in the Economic Survey?",
    "options": {{
      "A": "6.5%",
      "B": "7.0%",
      "C": "7.5%",
      "D": "8.0%",
      "E": "8.5%"
    }},
    "correct_answer": "B",
    "explanation": "According to Economic Survey 2024-25, the GDP growth rate was projected at 7.0% for FY 2024-25.",
    "source_document": "Economic Survey 2024-25",
    "difficulty": "Easy",
    "topic": "Economic_Indicators",
    "subject": "General_Awareness"
  }}
]
MANDATORY RULES:

✅ Extract information ONLY from uploaded documents
✅ Include source_document name for each question
✅ Use actual figures, dates, and facts from documents
✅ Ensure options are plausible but clearly distinguishable
✅ Write clear explanations with document reference
✅ Mark difficulty correctly: "Hard", "Medium", or "Easy"
✅ Use topic from: Economic_Indicators, Banking_Sector, RBI_Policies, Monetary_Policy, Budget_Schemes, Financial_Stability, Government_Initiatives, Current_Affairs
❌ NO fabricated data or information
❌ NO line breaks in JSON strings
❌ NO quotes within question/option text (rephrase instead)
Generate EXACTLY {num_questions} questions. Output ONLY valid JSON array, nothing else.
"""

    try:
        print(f"\n🤖 Generating questions with {MODEL_NAME}...")
        print(f"   ⏳ This may take 30-60 seconds...\n")
        
        # Generate with file context
        response = model.generate_content([prompt] + file_refs)
        
        response_text = response.text.strip()
        
        print(f"   ✅ Response received ({len(response_text)} characters)")
        
        # Clean and parse JSON
        questions = clean_json_response(response_text)
        
        if questions is None:
            print(f"   ❌ Failed to parse JSON")
            save_error_log(response_text, "JSON parsing failed", "pilot")
            return []
        
        if not isinstance(questions, list):
            print(f"   ❌ Expected list, got {type(questions)}")
            return []
        
        # Add metadata
        for q in questions:
            q['generated_date'] = datetime.now().isoformat()
            q['generation_model'] = MODEL_NAME
            q['generation_type'] = 'RAG_Pilot'
            q['subject'] = 'General_Awareness'
        
        print(f"\n✅ Successfully generated {len(questions)} questions")
        
        # Show distribution
        from collections import Counter
        diff_count = Counter([q.get('difficulty') for q in questions])
        topic_count = Counter([q.get('topic') for q in questions])
        
        print(f"\n📊 Difficulty: Hard={diff_count.get('Hard', 0)}, "
            f"Medium={diff_count.get('Medium', 0)}, "
            f"Easy={diff_count.get('Easy', 0)}")
        
        print(f"\n📚 Topics covered:")
        for topic, count in topic_count.most_common():
            print(f"   • {topic}: {count}")
        
        return questions
        
    except Exception as e:
        print(f"\n❌ Error during generation: {type(e).__name__}: {e}")
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
    except json.JSONDecodeError as e:
        print(f"      ⚠️  Direct JSON parse failed: {str(e)[:50]}")
    
    # Try finding JSON array
    try:
        match = re.search(r'$$.*$$', text, re.DOTALL)
        if match:
            json_text = match.group(0)
            questions = json.loads(json_text)
            print(f"      ✅ Extracted JSON array from response")
            return questions
    except json.JSONDecodeError as e:
        print(f"      ⚠️  Array extraction failed: {str(e)[:50]}")
    
    # Try finding JSON object (in case it returns single object)
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_text = match.group(0)
            obj = json.loads(json_text)
            # If it's a single object, wrap in array
            if isinstance(obj, dict):
                print(f"      ✅ Found single object, wrapping in array")
                return [obj]
            return obj
    except json.JSONDecodeError as e:
        print(f"      ⚠️  Object extraction failed: {str(e)[:50]}")
    
    print(f"      ❌ All JSON parsing attempts failed")
    return None



def save_error_log(response_text, error, batch_name): 
    """Save error log for debugging"""

    os.makedirs('data/ga_errors', exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = f'data/ga_errors/error_{batch_name}_{timestamp}.txt'

    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"Batch: {batch_name}\n")
        f.write(f"Error: {str(error)}\n\n")
        f.write("="*70 + "\n")
        f.write("RAW RESPONSE:\n")
        f.write("="*70 + "\n")
        f.write(response_text)

    print(f"   💾 Error log: {error_file}")

#==================== VALIDATION ====================

def validate_ga_questions(questions): 
    """Validate generated questions"""

    print("\n" + "="*70)
    print("🔍 VALIDATING QUESTIONS")
    print("="*70)

    issues = []

    for i, q in enumerate(questions, 1):
        # Required fields
        required = ['question', 'options', 'correct_answer', 'explanation', 'difficulty', 'topic', 'source_document']
        missing = [f for f in required if f not in q or not q[f]]
        
        if missing:
            issues.append(f"Q{i}: Missing fields: {missing}")
        
        # Check options
        if 'options' in q:
            if len(q['options']) != 5:
                issues.append(f"Q{i}: Should have 5 options, has {len(q['options'])}")
            
            if set(q['options'].keys()) != {'A', 'B', 'C', 'D', 'E'}:
                issues.append(f"Q{i}: Invalid option keys: {set(q['options'].keys())}")
        
        # Check correct answer
        if 'correct_answer' in q and q['correct_answer'] not in ['A', 'B', 'C', 'D', 'E']:
            issues.append(f"Q{i}: Invalid correct_answer: {q['correct_answer']}")
        
        # Check difficulty
        if 'difficulty' in q and q['difficulty'] not in ['Hard', 'Medium', 'Easy']:
            issues.append(f"Q{i}: Invalid difficulty: {q['difficulty']}")

    if issues:
        print(f"\n⚠️  Found {len(issues)} validation issues:")
        for issue in issues[:10]:
            print(f"   • {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more")
        return False
    else:
        print(f"\n✅ All {len(questions)} questions are valid!")
        return True

# ==================== MAIN EXECUTION ====================

def main():
    """Main pilot run execution"""
    
    print("\n" + "🎯"*35)
    print("RBI GRADE B - GENERAL AWARENESS PILOT RUN (RAG)")
    print("🎯"*35)
    
    print(f"\n📋 Configuration:")
    print(f"   Model: {MODEL_NAME}")
    print(f"   Target: {PILOT_QUESTIONS} questions")
    print(f"   Difficulty: Hard={DIFFICULTY_SPLIT['Hard']}, "
          f"Medium={DIFFICULTY_SPLIT['Medium']}, Easy={DIFFICULTY_SPLIT['Easy']}")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    start_time = datetime.now()
    
    # Step 1: Upload reports
    uploaded_files = upload_all_reports(REPORTS_DIR)
    
    if not uploaded_files:
        print("\n❌ No files uploaded. Cannot proceed.")
        return
    
    # Step 2: Generate questions
    questions = generate_ga_questions_with_rag(
        uploaded_files,
        PILOT_QUESTIONS,
        DIFFICULTY_SPLIT
    )
    
    if not questions:
        print("\n❌ Failed to generate questions")
        return
    
    # Step 3: Validate questions
    is_valid = validate_ga_questions(questions)
    
    # Step 4: Save questions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"ga_pilot_{PILOT_QUESTIONS}_questions_{timestamp}.json")
    
    print(f"\n💾 Saving questions...")
    
    output_data = {
        'metadata': {
            'title': 'RBI Grade B - General Awareness Pilot Run',
            'generation_type': 'RAG',
            'model': MODEL_NAME,
            'total_questions': len(questions),
            'target_questions': PILOT_QUESTIONS,
            'creation_date': datetime.now().isoformat(),
            'difficulty_distribution': DIFFICULTY_SPLIT,
            'source_documents': [f['name'] for f in uploaded_files],
            'validation_status': 'Passed' if is_valid else 'Issues Found'
        },
        'questions': questions
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Saved to: {output_file}")
    
    # Step 5: Create summary report
    summary_file = output_file.replace('.json', '_summary.txt')
    
    from collections import Counter
    
    diff_count = Counter([q.get('difficulty') for q in questions])
    topic_count = Counter([q.get('topic') for q in questions])
    source_count = Counter([q.get('source_document') for q in questions])
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("RBI GRADE B - GENERAL AWARENESS PILOT RUN SUMMARY\n")
        f.write("="*70 + "\n\n")
        f.write(f"Generation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Model Used: {MODEL_NAME}\n")
        f.write(f"Generation Type: RAG (Retrieval-Augmented Generation)\n")
        f.write(f"Total Questions: {len(questions)}\n")
        f.write(f"Target Questions: {PILOT_QUESTIONS}\n")
        f.write(f"Validation Status: {'✅ Passed' if is_valid else '⚠️ Issues Found'}\n\n")
        
        f.write("="*70 + "\n")
        f.write("SOURCE DOCUMENTS\n")
        f.write("="*70 + "\n")
        for i, uf in enumerate(uploaded_files, 1):
            f.write(f"{i}. {uf['name']}\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("DIFFICULTY DISTRIBUTION\n")
        f.write("="*70 + "\n")
        for diff in ['Hard', 'Medium', 'Easy']:
            count = diff_count.get(diff, 0)
            target = DIFFICULTY_SPLIT.get(diff, 0)
            status = "✅" if count == target else "⚠️"
            f.write(f"{status} {diff:<8}: {count}/{target}\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("TOPIC DISTRIBUTION\n")
        f.write("="*70 + "\n")
        for topic, count in sorted(topic_count.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{topic:<30}: {count}\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("SOURCE DOCUMENT USAGE\n")
        f.write("="*70 + "\n")
        for source, count in sorted(source_count.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{source:<50}: {count}\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("SAMPLE QUESTIONS\n")
        f.write("="*70 + "\n\n")
        
        for i, q in enumerate(questions[:3], 1):
            f.write(f"Q{i}. {q.get('question', 'N/A')}\n")
            f.write(f"    Difficulty: {q.get('difficulty', 'N/A')}\n")
            f.write(f"    Topic: {q.get('topic', 'N/A')}\n")
            f.write(f"    Source: {q.get('source_document', 'N/A')}\n")
            f.write(f"    Correct Answer: {q.get('correct_answer', 'N/A')}\n\n")
    
    print(f"   ✅ Summary saved to: {summary_file}")
    
    # Step 6: Display sample questions
    print("\n" + "="*70)
    print("📝 SAMPLE QUESTIONS")
    print("="*70)
    
    for i, q in enumerate(questions[:3], 1):
        print(f"\nQ{i}. {q.get('question', 'N/A')}")
        print(f"    Difficulty: {q.get('difficulty', 'N/A')}")
        print(f"    Topic: {q.get('topic', 'N/A')}")
        print(f"    Source: {q.get('source_document', 'N/A')}")
        for key, value in q.get('options', {}).items():
            marker = "✓" if key == q.get('correct_answer') else " "
            print(f"    {marker} {key}. {value}")
        print(f"    Explanation: {q.get('explanation', 'N/A')[:100]}...")
    
    # Final summary
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("✅ PILOT RUN COMPLETED!")
    print("="*70)
    
    print(f"\n⏱️  Total time: {duration:.1f} seconds")
    print(f"📊 Questions generated: {len(questions)}/{PILOT_QUESTIONS}")
    print(f"✅ Validation: {'Passed' if is_valid else 'Issues Found'}")
    print(f"📁 Output file: {output_file}")
    print(f"📄 Summary file: {summary_file}")
    
    print(f"\n📊 Quick Stats:")
    print(f"   Hard: {diff_count.get('Hard', 0)}/{DIFFICULTY_SPLIT['Hard']}")
    print(f"   Medium: {diff_count.get('Medium', 0)}/{DIFFICULTY_SPLIT['Medium']}")
    print(f"   Easy: {diff_count.get('Easy', 0)}/{DIFFICULTY_SPLIT['Easy']}")
    
    print(f"\n📚 Documents used: {len(uploaded_files)}")
    for uf in uploaded_files:
        print(f"   • {uf['name']}")
    
    print("\n💡 Next Steps:")
    print("   1. Review the generated questions in the output file")
    print("   2. Check the summary report for quality assessment")
    print("   3. If satisfied, proceed with full batch generation (300 questions)")
    print("   4. Use the same MODEL_NAME for consistency")
    
    print("\n🎉 Pilot run successful! Ready for full generation.")
    
    print("\n" + "="*70 + "\n")
    
    return questions, output_file


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🏁 Program completed\n")

#
