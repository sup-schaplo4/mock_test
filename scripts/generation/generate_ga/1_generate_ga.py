import google.generativeai as genai
import json
import os
import time
from datetime import datetime
from pathlib import Path
from collections import Counter

# ==================== CONFIGURATION ====================

# API Key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("❌ Please set GEMINI_API_KEY environment variable")
genai.configure(api_key=GEMINI_API_KEY)

# Model Configuration
MODEL_NAME = "gemini-2.5-pro"

# File paths - ORGANIZED STRUCTURE
REPORTS_BASE_DIR = "data/reports"
OUTPUT_DIR = "data/generated/ga_questions"

# Question allocation per report category
QUESTIONS_PER_REPORT = {
    'economic_survey': 25,        # 2 files × 25 = 50 questions
    'rbi_annual_report': 20,      # 2 files × 20 = 40 questions
    'rbi_bulletin': 5,            # 12 files × 5 = 60 questions
    'monetary_policy_report': 15, # 3 files × 15 = 45 questions
    'financial_stability_report': 10, # 4 files × 10 = 40 questions
    'union_budget': 25            # 2 files × 25 = 50 questions
}
# Total: ~285 questions (expandable to 300)

# Difficulty distribution (percentage)
DIFFICULTY_DISTRIBUTION = {
    'Hard': 0.30,
    'Medium': 0.45,
    'Easy': 0.25
}

# Topic mapping by report type
TOPIC_MAPPING = {
    'economic_survey': ['Economic_Indicators', 'Government_Schemes', 'Sectoral_Performance'],
    'rbi_annual_report': ['RBI_Functions', 'Banking_Regulation', 'Monetary_Operations'],
    'rbi_bulletin': ['Current_Affairs', 'Economic_Updates', 'Policy_Changes'],
    'monetary_policy_report': ['Monetary_Policy', 'Inflation', 'Growth_Outlook'],
    'financial_stability_report': ['Financial_Stability', 'Banking_Sector', 'Risk_Assessment'],
    'union_budget': ['Budget_Allocations', 'Fiscal_Policy', 'Government_Schemes']
}

# ==================== PDF UPLOAD ====================

def upload_single_pdf(file_path):
    """Upload single PDF to Gemini"""
    
    display_name = os.path.basename(file_path)
    
    try:
        print(f"   📤 Uploading: {display_name}")
        
        uploaded_file = genai.upload_file(
            path=file_path,
            display_name=display_name
        )
        
        # Wait for processing
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)
        
        if uploaded_file.state.name == "FAILED":
            print(f"      ❌ Upload failed")
            return None
        
        print(f"      ✅ Ready")
        return uploaded_file
        
    except Exception as e:
        print(f"      ❌ Error: {e}")
        return None


# ==================== QUESTION GENERATION ====================

def generate_questions_for_pdf(model, pdf_file, pdf_name, report_category, num_questions):
    """Generate questions for a single PDF"""
    
    print(f"\n{'─'*70}")
    print(f"📄 Processing: {pdf_name}")
    print(f"   Category: {report_category}")
    print(f"   Target: {num_questions} questions")
    print(f"{'─'*70}")
    
    # Calculate difficulty split
    difficulty_split = {
        'Hard': max(1, int(num_questions * DIFFICULTY_DISTRIBUTION['Hard'])),
        'Medium': max(1, int(num_questions * DIFFICULTY_DISTRIBUTION['Medium'])),
        'Easy': max(1, int(num_questions * DIFFICULTY_DISTRIBUTION['Easy']))
    }
    
    # Adjust for rounding
    total = sum(difficulty_split.values())
    if total < num_questions:
        difficulty_split['Medium'] += (num_questions - total)
    elif total > num_questions:
        difficulty_split['Easy'] -= (total - num_questions)
    
    topics = TOPIC_MAPPING.get(report_category, ['General_Awareness'])
    
    # Create enhanced prompt (NO "As per..." prefix)
    prompt = f"""You are an expert question creator for RBI Grade B Phase 1 General Awareness examination.

**SOURCE DOCUMENT:** {pdf_name}
**CATEGORY:** {report_category.replace('_', ' ').title()}

**TASK:** Generate EXACTLY {num_questions} multiple-choice questions based on information from this document.

**DIFFICULTY DISTRIBUTION:**
- Hard: {difficulty_split['Hard']} questions (complex, analytical, requires inference)
- Medium: {difficulty_split['Medium']} questions (moderate difficulty, fact-based)
- Easy: {difficulty_split['Easy']} questions (straightforward, direct facts)

**PREFERRED TOPICS:** {', '.join(topics)}

**QUESTION STYLE GUIDELINES:**
✅ DO:
- Start questions directly without document references
- Use natural phrasing: "What was...", "Which of the following...", "In FY 2024-25..."
- Focus on key facts, figures, policies, and developments
- Make questions exam-realistic and professional
- Use exact data from the document

❌ DON'T:
- Start with "As per...", "According to...", "The document states..."
- Use document names in questions
- Create vague or ambiguous questions
- Fabricate information

**EXAMPLES OF GOOD QUESTIONS:**
✅ "What was India's GDP growth rate projected for FY 2024-25?"
✅ "The Gross NPA ratio of Scheduled Commercial Banks reached a 12-year low at the end of March 2024. What was this ratio?"
✅ "Which scheme was launched in Union Budget 2024-25 to support micro-enterprises?"

**JSON FORMAT:**
```json
[
  {{
    "question": "What was the repo rate maintained by RBI in Q2 of FY 2024-25?",
    "options": {{
      "A": "6.00%",
      "B": "6.25%",
      "C": "6.50%",
      "D": "6.75%",
      "E": "7.00%"
    }},
    "correct_answer": "C",
    "explanation": "The RBI maintained the repo rate at 6.50% during Q2 of FY 2024-25 to balance growth and inflation concerns.",
    "source_document": "{pdf_name}",
    "difficulty": "Easy",
    "topic": "{topics[0]}",
    "subject": "General_Awareness",
    "report_category": "{report_category}"
  }}
]
MANDATORY RULES:

Extract information ONLY from the uploaded document
Use topics from: {', '.join(topics)}
Difficulty must be: "Hard", "Medium", or "Easy"
Include page numbers in explanation when possible
Ensure all data is accurate and verifiable
NO document references in question text
Output ONLY valid JSON array
Generate EXACTLY {num_questions} questions."""

    try:
        print(f"   🤖 Generating with {MODEL_NAME}...")
        
        response = model.generate_content([prompt, pdf_file])
        response_text = response.text.strip()
        
        print(f"   ✅ Response received ({len(response_text)} characters)")
        
        questions = clean_json_response(response_text)
        
        if not questions or not isinstance(questions, list):
            print(f"   ❌ Failed to parse JSON")
            save_error_log(response_text, pdf_name, report_category)
            return []
        
        # Add metadata
        for q in questions:
            q['generated_date'] = datetime.now().isoformat()
            q['generation_model'] = MODEL_NAME
            q['generation_type'] = 'Per_PDF_RAG'
            q['subject'] = 'General_Awareness'
            q['report_category'] = report_category
            q['source_document'] = pdf_name
        
        print(f"   ✅ Generated {len(questions)} questions")
        
        # Show distribution
        diff_count = Counter([q.get('difficulty') for q in questions])
        print(f"   📊 Hard={diff_count.get('Hard', 0)}, "
            f"Medium={diff_count.get('Medium', 0)}, "
            f"Easy={diff_count.get('Easy', 0)}")
        
        return questions
        
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        save_error_log(str(e), pdf_name, report_category)
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

def save_error_log(content, pdf_name, report_category): 
    """Save error log"""

    os.makedirs('data/ga_errors', exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = f'data/ga_errors/error_{report_category}_{timestamp}.txt'

    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"PDF: {pdf_name}\n")
        f.write(f"Category: {report_category}\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write("="*70 + "\n")
        f.write(str(content))

    print(f"   💾 Error log: {error_file}")

# ==================== PROCESS ALL REPORTS ====================

def process_all_reports(): 
    """Process all PDFs organized by category"""

    print("\n" + "🎯"*35)
    print("RBI GRADE B - GENERAL AWARENESS QUESTION GENERATOR")
    print("Strategy: Per-PDF Generation with Natural Questions")
    print("🎯"*35)

    model = genai.GenerativeModel(model_name=MODEL_NAME)

    all_questions = []
    stats = {
        'total_pdfs': 0,
        'successful_pdfs': 0,
        'total_questions': 0,
        'by_category': {}
    }

    start_time = datetime.now()

    # Process each category
    for category, num_questions in QUESTIONS_PER_REPORT.items():
        category_dir = os.path.join(REPORTS_BASE_DIR, category)
        
        if not os.path.exists(category_dir):
            print(f"\n⚠️  Directory not found: {category_dir}")
            continue
        
        pdf_files = list(Path(category_dir).glob("*.pdf"))
        
        if not pdf_files:
            print(f"\n⚠️  No PDFs in: {category}")
            continue
        
        print(f"\n{'='*70}")
        print(f"📁 CATEGORY: {category.replace('_', ' ').upper()}")
        print(f"{'='*70}")
        print(f"   PDFs found: {len(pdf_files)}")
        print(f"   Questions per PDF: {num_questions}")
        print(f"   Total target: {len(pdf_files) * num_questions}")
        
        category_questions = []
        
        for pdf_path in pdf_files:
            stats['total_pdfs'] += 1
            
            # Upload PDF
            uploaded_file = upload_single_pdf(str(pdf_path))
            
            if not uploaded_file:
                continue
            
            # Generate questions
            questions = generate_questions_for_pdf(
                model,
                uploaded_file,
                pdf_path.name,
                category,
                num_questions
            )
            
            if questions:
                category_questions.extend(questions)
                stats['successful_pdfs'] += 1
                stats['total_questions'] += len(questions)
            
            # Rate limiting
            time.sleep(3)
        
        stats['by_category'][category] = len(category_questions)
        all_questions.extend(category_questions)
        
        # Save category questions
        save_category_questions(category, category_questions)

    # Save master file
    save_master_questions(all_questions, stats, start_time)

    print_final_summary(stats, start_time)

    return all_questions

def save_category_questions(category, questions): 
    """Save questions by category"""

    category_dir = os.path.join(OUTPUT_DIR, 'by_category')
    os.makedirs(category_dir, exist_ok=True)

    output_file = os.path.join(category_dir, f"{category}_questions.json")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'category': category,
            'total_questions': len(questions),
            'questions': questions
        }, f, indent=2, ensure_ascii=False)

    print(f"   💾 Saved: {output_file}")

def save_master_questions(all_questions, stats, start_time): 
    """Save master question bank"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    master_file = os.path.join(OUTPUT_DIR, f"ga_master_bank_{timestamp}.json")

    duration = (datetime.now() - start_time).total_seconds()

    master_data = {
        'metadata': {
            'title': 'RBI Grade B - General Awareness Master Question Bank',
            'generation_type': 'Per_PDF_RAG',
            'model': MODEL_NAME,
            'total_questions': len(all_questions),
            'total_pdfs_processed': stats['total_pdfs'],
            'successful_pdfs': stats['successful_pdfs'],
            'creation_date': datetime.now().isoformat(),
            'generation_duration_seconds': duration,
            'questions_by_category': stats['by_category']
        },
        'questions': all_questions
    }

    with open(master_file, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Master file: {master_file}")

def print_final_summary(stats, start_time):
    """Print final summary"""
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("✅ GENERATION COMPLETED!")
    print("="*70)
    
    print(f"\n⏱️  Duration: {duration/60:.1f} minutes")
    print(f"📄 PDFs processed: {stats['successful_pdfs']}/{stats['total_pdfs']}")
    print(f"📝 Total questions: {stats['total_questions']}")
    
    print(f"\n📊 Questions by Category:")
    for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"   • {category.replace('_', ' ').title():<35}: {count:>3} questions")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Review questions in: {OUTPUT_DIR}")
    print(f"   2. Check by_category folder for organized questions")
    print(f"   3. Validate question quality and accuracy")
    print(f"   4. Use for test generation with topic-based filtering")
    
    print("\n" + "="*70 + "\n")


# ==================== MAIN EXECUTION ====================

def main():
    """Main execution"""
    
    try:
        questions = process_all_reports()
        
        if questions:
            print(f"🎉 Successfully generated {len(questions)} questions!")
            
            # Quick statistics
            from collections import Counter
            
            diff_count = Counter([q.get('difficulty') for q in questions])
            topic_count = Counter([q.get('topic') for q in questions])
            category_count = Counter([q.get('report_category') for q in questions])
            
            print("\n📈 Overall Statistics:")
            print(f"\n   Difficulty Distribution:")
            print(f"      Hard: {diff_count.get('Hard', 0)} ({diff_count.get('Hard', 0)/len(questions)*100:.1f}%)")
            print(f"      Medium: {diff_count.get('Medium', 0)} ({diff_count.get('Medium', 0)/len(questions)*100:.1f}%)")
            print(f"      Easy: {diff_count.get('Easy', 0)} ({diff_count.get('Easy', 0)/len(questions)*100:.1f}%)")
            
            print(f"\n   Top 5 Topics:")
            for topic, count in topic_count.most_common(5):
                print(f"      • {topic}: {count}")
            
            print(f"\n   Category Distribution:")
            for category, count in sorted(category_count.items(), key=lambda x: x[1], reverse=True):
                print(f"      • {category}: {count}")
            
        else:
            print("\n❌ No questions generated")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🏁 Program completed\n")


if __name__ == "__main__":
    main()
