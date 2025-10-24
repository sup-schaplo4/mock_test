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
TOTAL_QUESTIONS = 120  # 🔧 CHANGE THIS to generate more/fewer questions

# Difficulty Distribution (must sum to 1.0)
DIFFICULTY_WEIGHTS = {
    'Hard': 0.30,    # 30%
    'Medium': 0.40,  # 40%
    'Easy': 0.30     # 30%
}

# File Configuration
CURRENT_AFFAIRS_FILE = "data/reports/current_affairs/current_affairs.txt"
OUTPUT_DIR = "data/generated/current_affairs_questions"

# Topics for Current Affairs
# Topics for Current Affairs
CURRENT_AFFAIRS_TOPICS = [
    'National_Events',
    'International_Relations',
    'Economic_Developments',
    'Banking_News',
    'Government_Initiatives',
    'Policy_Updates',
    'Awards_Honours',
    'Appointments',
    'Summits_Conferences',
    'Technology_Innovation',
    'Financial_Markets',
    'Regulatory_Changes',
    'Budget_Fiscal',
    'Trade_Commerce',
    'Infrastructure_Projects',
    'Mining_Minerals',
    'Steel_Industry',
    'Cement_Industry',
    'MSME_Sector',
    'Textiles_Apparel'
]

# Time Period (for metadata)
TIME_PERIOD = "October 2024 - September 2025"

# Batch Configuration
QUESTIONS_PER_BATCH = 20  # Generate 20 questions per API call
MAX_RETRIES = 3

# ==================== FILE HANDLING ====================

def load_current_affairs_content(file_path):
    """Load current affairs content from file or use provided text"""
    
    print("\n" + "="*70)
    print("📰 LOADING CURRENT AFFAIRS CONTENT")
    print("="*70)
    
    if os.path.exists(file_path):
        print(f"\n📁 Reading from file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        word_count = len(content.split())
        char_count = len(content)
        
        print(f"\n📊 Content Statistics:")
        print(f"   File size: {os.path.getsize(file_path) / 1024:.1f} KB")
        print(f"   Words: {word_count:,}")
        print(f"   Characters: {char_count:,}")
        print(f"   Estimated questions possible: {word_count // 250}-{word_count // 200}")
        
        return content, 'file'
    
    else:
        print(f"\n⚠️  File not found: {file_path}")
        print(f"💡 Using inline content mode")
        
        # Get inline content
        content = get_inline_current_affairs_content()
        word_count = len(content.split())
        char_count = len(content)
        
        print(f"\n📊 Inline Content Statistics:")
        print(f"   Words: {word_count:,}")
        print(f"   Characters: {char_count:,}")
        print(f"   Estimated questions possible: {word_count // 250}-{word_count // 200}")
        
        return content, 'inline'


def upload_to_gemini(content, content_type='file'):
    """Upload content to Gemini API"""
    
    print("\n" + "="*70)
    print("📤 UPLOADING TO GEMINI")
    print("="*70)
    
    try:
        if content_type == 'file' and os.path.exists(CURRENT_AFFAIRS_FILE):
            print(f"\n⏳ Uploading file to Gemini...")
            
            uploaded_file = genai.upload_file(
                path=CURRENT_AFFAIRS_FILE,
                display_name="Current_Affairs_Content"
            )
            
            # Wait for processing
            while uploaded_file.state.name == "PROCESSING":
                print("   ⏳ Processing...", end="\r")
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                print("   ❌ Upload failed")
                return None, 'inline'
            
            print("   ✅ File upload successful!")
            print(f"   File URI: {uploaded_file.uri}")
            
            return uploaded_file, 'file'
        
        else:
            print(f"\n💡 Using inline content mode (no file upload)")
            return content, 'inline'
            
    except Exception as e:
        print(f"   ⚠️  Upload error: {e}")
        print(f"   💡 Falling back to inline content mode")
        return content, 'inline'


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


def generate_current_affairs_batch(model, content, content_type, batch_num, num_questions, difficulty_split):
    """Generate a batch of current affairs questions"""
    
    print(f"\n{'─'*70}")
    print(f"🤖 BATCH {batch_num}: Generating {num_questions} questions")
    print(f"{'─'*70}")
    print(f"   Hard: {difficulty_split['Hard']}")
    print(f"   Medium: {difficulty_split['Medium']}")
    print(f"   Easy: {difficulty_split['Easy']}")
    
    prompt = f"""You are an expert at creating Current Affairs questions for RBI Grade B Phase 1 examination.

**SOURCE:** Current Affairs compilation ({TIME_PERIOD})

**TASK:** Generate EXACTLY {num_questions} multiple-choice questions from the provided current affairs content.

**DIFFICULTY DISTRIBUTION:**
- Hard: {difficulty_split['Hard']} questions (analytical, requires connecting multiple events, understanding implications)
- Medium: {difficulty_split['Medium']} questions (moderate complexity, fact-based with context)
- Easy: {difficulty_split['Easy']} questions (straightforward facts, dates, names, figures)

**TOPIC CATEGORIES TO USE:**
{', '.join(CURRENT_AFFAIRS_TOPICS)}

**QUESTION STYLE GUIDELINES:**

✅ DO:
- Start questions naturally without source references
- Use specific dates, names, figures, and event details
- Focus on: Economic events, Banking developments, Government policies, International relations, Appointments, Awards
- Ask about: "What", "Which", "When", "Who", "Where", "How much"
- Make questions time-specific (mention exact months/dates/years)
- Use exact data from the current affairs content
- Cover diverse topics (banking, economy, international, national, awards, etc.)

❌ DON'T:
- Start with "According to...", "As per current affairs..."
- Use vague or ambiguous language
- Create hypothetical scenarios
- Fabricate any information
- Repeat similar questions

**EXAMPLES OF GOOD QUESTIONS:**

✅ "Who was appointed as the new Governor of Reserve Bank of India in December 2024?"
✅ "India's GDP growth rate for Q2 FY 2024-25 was projected at what percentage?"
✅ "Which country hosted the G20 Summit in September 2025?"
✅ "The RBI increased the repo rate by how many basis points in August 2025?"
✅ "Who won the Nobel Prize in Economics in 2024?"
✅ "India signed a Free Trade Agreement with which country in July 2025?"
✅ "What was the theme of World Economic Forum 2025?"
✅ "The Government launched which scheme for MSME financing in June 2025?"

**MANDATORY JSON FORMAT:**
```json
[
  {{
    "question": "Who was appointed as the Executive Director of the International Monetary Fund (IMF) representing India in August 2025?",
    "options": {{
      "A": "Krishnamurthy Subramanian",
      "B": "Raghuram Rajan",
      "C": "Viral Acharya",
      "D": "Urjit Patel",
      "E": "Shaktikanta Das"
    }},
    "correct_answer": "A",
    "explanation": "Krishnamurthy Subramanian was appointed as India's Executive Director at the IMF in August 2025, succeeding the previous representative.",
    "source_document": "current_affairs.txt",
    "event_date": "August 2025",
    "difficulty": "Medium",
    "topic": "Appointments",
    "category": "Current_Affairs",
    "subject": "General_Awareness",
    "time_period": "{TIME_PERIOD}"
  }},
  {{
    "question": "India's foreign exchange reserves crossed which milestone in September 2025?",
    "options": {{
      "A": "$600 billion",
      "B": "$650 billion",
      "C": "$700 billion",
      "D": "$750 billion",
      "E": "$800 billion"
    }},
    "correct_answer": "C",
    "explanation": "India's forex reserves surpassed the $700 billion mark in September 2025, reaching an all-time high driven by strong FDI inflows and current account surplus.",
    "source_document": "current_affairs.txt",
    "event_date": "September 2025",
    "difficulty": "Easy",
    "topic": "Economic_Developments",
    "category": "Current_Affairs",
    "subject": "General_Awareness",
    "time_period": "{TIME_PERIOD}"
  }}
]
CRITICAL RULES:

Extract information ONLY from the provided current affairs content
Use topics from the provided list
Include event_date (month/year) when mentioned
Ensure diversity across topics (don't focus only on one area)
NO source references in question text
Output ONLY valid JSON array
Generate EXACTLY {num_questions} questions
Make questions exam-realistic and time-bound
Begin generation now."""

    try:
        print(f"   🤖 Calling Gemini API...")
        
        # Build request based on content type
        if content_type == 'file':
            response = model.generate_content([prompt, content])
        else:
            # For inline mode, include content in prompt
            full_prompt = f"{prompt}\n\n**CURRENT AFFAIRS CONTENT:**\n\n{content[:50000]}"  # Limit to 50k chars
            response = model.generate_content(full_prompt)
        
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
            q['generation_type'] = f'Current_Affairs_Batch_{batch_num}'
            q['subject'] = 'General_Awareness'
            q['category'] = 'Current_Affairs'
            q['time_period'] = TIME_PERIOD
        
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
    os.makedirs('data/ca_errors', exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = f'data/ca_errors/error_{batch_info}_{timestamp}.txt'

    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"Batch: {batch_info}\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write("="*70 + "\n")
        f.write(str(content))

    print(f"   💾 Error log: {error_file}")

# ==================== MAIN GENERATION ====================
def generate_all_current_affairs_questions(content, content_type, total_questions, difficulty_weights):
    """Generate all current affairs questions in batches"""
    
    print("\n" + "="*70)
    print(f"🚀 GENERATING {total_questions} CURRENT AFFAIRS QUESTIONS")
    print("="*70)
    
    print(f"\n⚙️  Configuration:")
    print(f"   Model: {MODEL_NAME}")
    print(f"   Total target: {total_questions}")
    print(f"   Questions per batch: {QUESTIONS_PER_BATCH}")
    print(f"   Content mode: {content_type}")
    print(f"   Time period: {TIME_PERIOD}")
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
            
            batch_questions = generate_current_affairs_batch(
                model,
                content,
                content_type,
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
            print(f"   📊 Total so far: {len(all_questions)}/{total_questions}")
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

def save_current_affairs_questions(questions):
    """Save current affairs questions to file"""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"current_affairs_questions_{timestamp}.json")
    
    # Calculate statistics
    diff_count = Counter([q.get('difficulty') for q in questions])
    topic_count = Counter([q.get('topic') for q in questions])
    
    output_data = {
        'metadata': {
            'title': 'RBI Grade B - Current Affairs Questions',
            'source': 'Current Affairs Compilation',
            'period': TIME_PERIOD,
            'generation_type': 'Current_Affairs_RAG',
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
    print(f"\n📌 Topic Distribution:")
    for i, (topic, count) in enumerate(topic_count.most_common(), 1):
        print(f"   {i:>2}. {topic:<30}: {count:>3} ({count/len(questions)*100:>5.1f}%)")
    
    # Questions with dates
    dated_questions = [q for q in questions if q.get('event_date')]
    print(f"\n📅 Time-specific Questions: {len(dated_questions)} ({len(dated_questions)/len(questions)*100:.1f}%)")
    
    # Month-wise distribution (if event_date present)
    if dated_questions:
        month_count = Counter()
        for q in dated_questions:
            event_date = q.get('event_date', '')
            # Extract month
            for month in ['January', 'February', 'March', 'April', 'May', 'June', 
                         'July', 'August', 'September', 'October', 'November', 'December']:
                if month in event_date:
                    month_count[month] += 1
                    break
        
        if month_count:
            print(f"\n📆 Month-wise Distribution:")
            for month, count in month_count.most_common():
                print(f"   • {month:<12}: {count:>3}")
    
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
        
        # Check for source references in question
        question_text = q.get('question', '').lower()
        bad_phrases = ['according to', 'as per', 'the document', 'current affairs states', 'in the news']
        for phrase in bad_phrases:
            if phrase in question_text:
                issues.append(f"Q{i}: Contains '{phrase}' in question text")
        
        # Check topic validity
        if 'topic' in q:
            if q['topic'] not in CURRENT_AFFAIRS_TOPICS:
                issues.append(f"Q{i}: Invalid topic: {q['topic']}")
    
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
    print(f"   Pass rate: {(1 - len(issues)/(len(questions)*len(required_fields)))*100:.1f}%")
    
    print("\n" + "="*70)
    
    return len(issues) == 0


# ==================== INLINE CONTENT MODE ====================
def get_inline_current_affairs_content():
    """
    Provide current affairs content directly in code
    Use this if you don't have a file
    """
    
    content = """
# CURRENT AFFAIRS - OCTOBER 2024 TO SEPTEMBER 2025
# RBI Grade B Phase 1 Preparation

## BANKING & FINANCIAL SECTOR

### October 2024
- RBI maintained repo rate at 6.50% in October 2024 monetary policy review
- India's forex reserves reached $675 billion in October 2024
- HDFC Bank merged with HDFC Ltd, creating India's largest private bank
- RBI introduced new guidelines for digital lending platforms
- SEBI launched new framework for Social Stock Exchange
- India's banking sector credit growth stood at 15.2% YoY

### November 2024
- India's GDP growth for Q2 FY 2024-25 estimated at 7.2%
- Government launched PM Vishwakarma scheme for traditional artisans with ₹13,000 crore allocation
- RBI imposed penalty of ₹10.5 crore on Paytm Payments Bank for regulatory violations
- India signed currency swap agreement with Sri Lanka worth $400 million
- NPCI reported UPI transactions crossed 12 billion in October 2024
- India's fiscal deficit at 45% of full-year target in H1 FY25

### December 2024
- Sanjay Malhotra appointed as new RBI Governor replacing Shaktikanta Das
- India's CPI inflation stood at 5.4% in November 2024
- Government announced ₹1 lakh crore credit guarantee scheme for MSMEs
- SEBI introduced new regulations for ESG disclosures by listed companies
- RBI announced withdrawal of ₹2000 currency notes from circulation
- India's Index of Industrial Production grew 5.8% in October 2024

### January 2025
- Union Budget 2025-26 presented by Finance Minister Nirmala Sitharaman
- Capital expenditure allocation increased to ₹11.11 lakh crore (11% of GDP)
- New income tax slabs announced with exemption limit raised to ₹7 lakh
- India's fiscal deficit target set at 4.9% of GDP for FY 2025-26
- Agriculture sector allocation increased to ₹1.52 lakh crore
- Infrastructure spending focused on PM Gati Shakti National Master Plan

### February 2025
- RBI increased repo rate by 25 basis points to 6.75% to combat inflation
- India's merchandise exports crossed $500 billion mark in FY 2024-25
- Government launched National Logistics Policy 2025 to reduce logistics cost to 8% of GDP
- IRDAI increased FDI limit in insurance sector to 74% from 49%
- India's manufacturing sector added 1.2 million jobs in Q3 FY25
- RBI introduced stricter norms for unsecured personal loans

### March 2025
- India's forex reserves touched $700 billion milestone in March 2025
- RBI launched retail pilot of Central Bank Digital Currency (e₹-R) across 13 cities
- Government announced Production Linked Incentive (PLI) scheme for semiconductors worth ₹76,000 crore
- India signed Comprehensive Free Trade Agreement with European Union
- India's current account deficit narrowed to 1.5% of GDP in Q3 FY25
- SEBI mandated quarterly ESG disclosures for top 1000 listed companies

### April 2025
- New financial year 2025-26 began with revised GST rates on 213 items
- RBI launched UPI for feature phones initiative called UPI123Pay
- India's unemployment rate declined to 6.8% in March 2025
- Government increased deposit insurance coverage to ₹10 lakh per depositor
- NPCI launched UPI Lite for small-value transactions up to ₹500
- India's bank credit growth moderated to 14.5% YoY

### May 2025
- India became world's 3rd largest economy with GDP of $4.5 trillion, surpassing Japan
- RBI introduced comprehensive framework for regulation of fintech companies
- Government launched Atmanirbhar Bharat 3.0 package worth ₹2.5 lakh crore
- India's manufacturing PMI reached 58.5, highest in 15 months
- SEBI reduced timeline for listing of IPOs from T+6 to T+3 days
- India's services exports crossed $350 billion in FY 2024-25

### June 2025
- RBI maintained status quo on repo rate at 6.75% in June monetary policy
- India's GST collection crossed ₹1.8 lakh crore in May 2025, highest ever monthly collection
- Government announced National Green Hydrogen Mission with ₹19,744 crore outlay
- NABARD launched ₹50,000 crore Rural Infrastructure Development Fund (RIDF-30)
- India's WPI inflation eased to 3.2% in May 2025
- RBI introduced new guidelines for digital payment aggregators

### July 2025
- India's monsoon forecast predicted normal rainfall at 96% of Long Period Average
- RBI made Account Aggregator framework mandatory for all scheduled commercial banks
- Government increased MSP for Kharif crops by 7-10% across all crops
- India's Index of Industrial Production (IIP) grew by 5.2% in May 2025
- SEBI introduced T+0 settlement cycle for top 500 stocks
- India's forex reserves composition: $620 billion in foreign currency assets

### August 2025
- India's current account deficit narrowed to 1.2% of GDP in Q1 FY26
- RBI launched pilot project for offline CBDC transactions in remote areas
- Government announced ₹2 lakh crore package for agricultural infrastructure development
- India's services PMI stood at 60.5 in July 2025, indicating strong expansion
- IRDAI launched 'Bima Sugam' - unified insurance marketplace
- India's direct tax collections grew 22% YoY to ₹6.8 lakh crore

### September 2025
- India's forex reserves reached all-time high of $720 billion in September 2025
- RBI kept repo rate unchanged at 6.75% in September bi-monthly policy review
- Government launched National Quantum Mission with ₹6,000 crore allocation over 5 years
- India's WPI inflation moderated to 2.8% in August 2025
- SEBI introduced framework for Social Impact Bonds
- India's bank deposits grew 11.2% YoY to ₹205 lakh crore

## INTERNATIONAL DEVELOPMENTS

### October 2024
- IMF projected global growth at 3.2% for 2024 and 3.5% for 2025
- World Bank approved $1.5 billion loan to India for green energy projects
- G20 Finance Ministers meeting held in Washington DC discussed global debt concerns
- BRICS nations discussed common currency proposal at summit in Kazan, Russia
- India's ranking in Global Innovation Index improved to 39th position
- WTO projected global trade growth at 3.3% for 2024

### November 2024
- COP29 climate summit held in Baku, Azerbaijan with 198 countries participating
- India committed to net-zero emissions by 2070 and 50% renewable energy by 2030
- Asian Development Bank approved $500 million loan for India's metro rail projects
- FATF retained India in regular follow-up category, removed from grey list
- India-Australia trade reached $30 billion under ECTA agreement
- Global crude oil prices averaged $85 per barrel in November 2024

### December 2024
- WTO 13th Ministerial Conference held in Abu Dhabi, UAE
- India opposed developed nations' farm subsidy proposals at WTO
- New Development Bank (NDB) approved $1 billion loan for India's infrastructure
- India-UAE bilateral trade reached $85 billion in 2024
- India signed MoU with Japan for semiconductor collaboration
- Global FDI flows declined 12% to $1.3 trillion in 2024

### January 2025
- World Economic Forum held in Davos with theme "Rebuilding Trust"
- India's Prime Minister addressed WEF highlighting India's growth story
- IMF upgraded India's growth forecast to 6.7% for 2025
- India-UK Free Trade Agreement negotiations entered final stage
- OECD projected India to contribute 18% to global growth in 2025
- Global inflation expected to moderate to 4.5% in 2025

### February 2025
- G20 Finance Ministers meeting held in São Paulo, Brazil
- India advocated for reform of multilateral development banks
- World Bank approved $2 billion loan for India's urban infrastructure
- India-Middle East-Europe Economic Corridor (IMEC) project initiated
- Asian Infrastructure Investment Bank approved $750 million for Indian projects
- Global supply chain disruptions eased with container freight rates declining 40%

### March 2025
- India signed Bilateral Investment Treaty (BIT) with 15 countries
- BRICS expanded membership to include Saudi Arabia, UAE, Egypt, Ethiopia, Iran
- India's trade deficit with China narrowed to $85 billion in FY25
- WTO ruled in favor of India in sugar subsidy dispute with Australia
- India-ASEAN trade crossed $130 billion mark
- Global semiconductor shortage eased with capacity additions

### April 2025
- IMF Spring Meetings held in Washington DC discussed debt sustainability
- India contributed $2.5 billion to IMF's Poverty Reduction and Growth Trust
- India-Japan bilateral trade reached $22 billion in FY 2024-25
- FATF plenary meeting recognized India's efforts in combating money laundering
- India signed Open Skies Agreement with 25 countries
- Global crude oil prices stabilized at $78-82 per barrel range

### May 2025
- G7 Summit held in Italy discussed global economic challenges
- India invited as guest country to G7 Summit
- World Bank projected India's GDP growth at 6.9% for FY 2025-26
- India-Canada trade negotiations resumed after diplomatic tensions
- Asian Development Bank increased India's lending limit to $5 billion annually
- Global inflation moderated to 4.2% in April 2025

### June 2025
- Shanghai Cooperation Organisation (SCO) Summit held in Astana, Kazakhstan
- India hosted SCO Defence Ministers meeting in New Delhi
- OECD admitted India as 39th member country
- India-Russia trade reached $65 billion despite global sanctions
- IMF approved $1.2 billion loan for India's climate resilience projects
- Global trade growth projected at 3.8% for 2025

### July 2025
- BRICS Summit held in Johannesburg, South Africa
- India proposed BRICS payment system as alternative to SWIFT
- World Bank approved $1.8 billion for India's education sector reforms
- India-Germany trade crossed $30 billion with focus on green technology
- G20 Sherpa meetings began for India's upcoming presidency in 2026
- Global FDI inflows increased 8% YoY to $1.5 trillion

### August 2025
- ASEAN Regional Forum held in Jakarta, Indonesia
- India signed Regional Comprehensive Economic Partnership (RCEP) after modifications
- IMF released Article IV consultation report praising India's economic management
- India-France strategic partnership expanded with €10 billion investment commitments
- World Economic Forum released Global Competitiveness Report ranking India 40th
- Global supply chains diversified with 'China Plus One' strategy

### September 2025
- UN General Assembly 80th session held in New York
- India's External Affairs Minister addressed UNGA on multilateral reforms
- World Bank projected India to become $5 trillion economy by 2027
- India-US trade reached $190 billion, highest ever bilateral trade
- IMF approved India's quota increase reflecting economic weight
- Global economic outlook improved with synchronized growth across regions

## GOVERNMENT SCHEMES & INITIATIVES

### October 2024
- PM Gati Shakti National Master Plan Phase 2 launched for logistics efficiency
- Ayushman Bharat expanded to cover 55 crore beneficiaries
- Digital India 2.0 launched with focus on AI and emerging technologies
- Skill India Mission 2.0 targets training 30 crore youth by 2030

### November 2024
- PM Vishwakarma Yojana launched with ₹13,000 crore for traditional artisans
- National Education Policy implementation accelerated in all states
- Jal Jeevan Mission achieved 70% household tap water connections
- Swachh Bharat Mission 2.0 expanded to include waste-to-wealth initiatives

### December 2024
- PM Kisan Samman Nidhi 16th installment released to 11 crore farmers
- Pradhan Mantri Awas Yojana Urban 2.0 launched with target of 1 crore houses
- National Hydrogen Mission allocated ₹19,744 crore for green hydrogen production
- Digital Agriculture Mission launched for precision farming

### January 2025
- Budget 2025-26 announced major infrastructure push under PM Gati Shakti
- Amrit Kaal Vision 2047 roadmap released for developed India
- National Logistics Policy aims to reduce logistics cost from 14% to 8% of GDP
- PM Internship Scheme launched to provide internships to 1 crore youth

### February 2025
- Vibrant Villages Programme launched for border area development with ₹4,800 crore
- National Data Governance Framework Policy released
- PM PRANAM scheme launched to reduce chemical fertilizer use
- Millet Mission expanded to promote nutritional security

### March 2025
- Production Linked Incentive (PLI) Scheme expanded to 27 sectors worth ₹3 lakh crore
- National Green Hydrogen Mission targets 5 MMT production by 2030
- Digital Public Infrastructure expanded to include health and education
- PM Matsya Sampada Yojana allocated ₹20,050 crore for fisheries sector

### April 2025
- Atal Innovation Mission 2.0 launched to establish 10,000 Atal Tinkering Labs
- National Quantum Mission allocated ₹6,000 crore over 5 years
- PM Poshan Shakti Nirman scheme expanded to 12 crore students
- National Apprenticeship Promotion Scheme targets 50 lakh apprentices

### May 2025
- Atmanirbhar Bharat 3.0 package worth ₹2.5 lakh crore announced
- National Infrastructure Pipeline expanded to ₹150 lakh crore investment
- PM Street Vendor's AtmaNirbhar Nidhi scheme benefited 50 lakh vendors
- National Mission on Natural Farming launched for chemical-free agriculture

### June 2025
- PM Ujjwala Yojana 3.0 launched targeting 3 crore additional beneficiaries
- National Rail Plan 2030 aims to create future-ready railway system
- Sagarmala Project Phase 2 launched for port-led development
- National Clean Air Programme targets 40% reduction in PM2.5 by 2026

### July 2025
- Kharif Marketing Season 2025 MSP increased by 7-10% across all crops
- PM Fasal Bima Yojana coverage expanded to 40 crore farmers
- National Bamboo Mission allocated ₹1,290 crore for bamboo sector development
- Digital India Land Records Modernization Programme achieved 95% digitization

### August 2025
- National Food Security Mission targets 330 MMT food grain production
- PM Kusum Scheme targets 30 GW solar capacity in agriculture sector
- National Beekeeping & Honey Mission launched with ₹500 crore allocation
- Smart Cities Mission Phase 2 launched for 100 additional cities

### September 2025
- National Quantum Mission established 4 Thematic Hubs across India
- PM Gati Shakti Cargo Terminal Development Scheme launched
- National Single Window System integrated 32 Central and State departments
- Digital India BHASHINI platform launched for language translation in 22 languages

## AWARDS & HONOURS

### October 2024
- Nobel Prize in Economics 2024 awarded to Claudia Goldin for gender gap research
- Booker Prize 2024 won by Paul Lynch for novel "Prophet Song"
- India won 107 medals at Asian Games 2023 (final tally)
- Bharat Ratna posthumously awarded to Karpoori Thakur and LK Advani

### November 2024
- Miss Universe 2024 crown won by Sheynnis Palacios from Nicaragua
- India ranked 111th in Global Hunger Index 2024
- Ramon Magsaysay Award 2024 announced for 4 individuals including 1 Indian
- India improved to 40th rank in Global Innovation Index 2024

```python
### December 2024
- TIME Person of the Year 2024: Taylor Swift
- Padma Awards 2024 announced: 5 Padma Vibhushan, 17 Padma Bhushan, 110 Padma Shri
- India ranked 63rd in Global Talent Competitiveness Index 2024
- Satyajit Ray Lifetime Achievement Award at IFFI Goa to Michael Douglas
- India won ICC Men's ODI Team of the Year award

### January 2025
- Padma Vibhushan 2025 awarded to Vyjayanthimala Bali, Koneru Ramakrishna Rao, Dilip Sanghvi
- National Film Awards 2023 announced: Best Film - Kantara (Kannada)
- India ranked 80th in Corruption Perception Index 2024 by Transparency International
- Dadasaheb Phalke Award 2024 conferred on Waheeda Rehman
- Infosys Prize 2024 announced in 6 categories

### February 2025
- Grammy Awards 2025: Album of the Year won by Taylor Swift for "Midnights"
- BAFTA Awards 2025: Best Film - "Oppenheimer"
- India ranked 127th in Gender Gap Index 2024 by World Economic Forum
- Sahitya Akademi Awards 2024 announced for 20 authors
- National Sports Awards 2024: Major Dhyan Chand Khel Ratna to Neeraj Chopra

### March 2025
- Academy Awards (Oscars) 2025: Best Picture - "Oppenheimer" (7 Oscars total)
- Abel Prize 2025 in Mathematics awarded to Michel Talagrand (France)
- India ranked 105th in World Happiness Report 2025
- Pritzker Architecture Prize 2025 awarded to Riken Yamamoto (Japan)
- Jnanpith Award 2024 conferred on Gujarati writer Dalpatram

### April 2025
- Pulitzer Prize 2025 for Fiction won by Jayne Anne Phillips for "Night Watch"
- Time 100 Most Influential People 2025 list included 3 Indians
- India ranked 54th in World Press Freedom Index 2025
- Man Booker International Prize 2025 shortlist announced
- National Film Awards 2024 announced: Best Actor - Rishab Shetty (Kantara)

### May 2025
- Cannes Film Festival 2025: Palme d'Or won by "Anora" directed by Sean Baker
- India ranked 38th in IMD World Competitiveness Index 2025
- Templeton Prize 2025 awarded to Marcelo Gleiser (Brazil)
- Abel Prize ceremony held in Oslo for Michel Talagrand
- India won Thomas Cup Badminton Championship (Men's team)

### June 2025
- FIFA Best Men's Player 2025 awarded to Lionel Messi (8th time)
- India ranked 116th in Sustainable Development Goals Index 2025
- Princess of Asturias Awards 2025 announced for 8 categories
- Laureus World Sports Awards 2025: Sportsman - Novak Djokovic
- India's rank improved to 48th in Global Cybersecurity Index 2025

### July 2025
- Wimbledon 2025: Men's Singles won by Carlos Alcaraz (Spain)
- India ranked 67th in Global Peace Index 2025
- Fields Medal 2025 (Mathematics) awarded at International Congress
- ESPY Awards 2025: Best Athlete - Simone Biles
- India won 5 medals at World Athletics Championships

### August 2025
- India ranked 72nd in Human Development Index 2024 (released in 2025)
- MTV Video Music Awards 2025: Video of the Year - Taylor Swift
- India improved to 55th rank in Ease of Doing Business Index 2025
- National Teacher Awards 2025 conferred on 75 teachers
- India won Asian Champions Trophy Hockey tournament

### September 2025
- Emmy Awards 2025: Outstanding Drama Series - "Succession"
- India ranked 90th in Environmental Performance Index 2025
- Right Livelihood Award 2025 (Alternative Nobel) announced
- Ig Nobel Prizes 2025 awarded for humorous scientific achievements
- India won 28 medals at World Wrestling Championships

## APPOINTMENTS & RESIGNATIONS

### October 2024
- Sanjay Malhotra appointed as 26th Governor of Reserve Bank of India
- Ajay Seth appointed as Finance Secretary of India
- Rajesh Khullar appointed as Executive Director of World Bank
- Tuhin Kanta Pandey appointed as Secretary, Department of Investment and Public Asset Management
- Vivek Joshi appointed as Cabinet Secretary of India

### November 2024
- Swaminathan Janakiraman appointed as MD & CEO of RBL Bank
- Dinesh Kumar Khara reappointed as Chairman of State Bank of India
- Rabi Sankar reappointed as Deputy Governor of RBI
- Ashwini Kumar appointed as Chairman of NABARD
- Pradeep Kumar Sinha appointed as Non-Executive Chairman of Axis Bank

### December 2024
- Atul Kumar Goel appointed as MD & CEO of Punjab National Bank
- Rakesh Sharma appointed as MD & CEO of IDBI Bank
- Swaminathan J appointed as Deputy Governor of RBI
- Ajay Kumar Bhalla appointed as Governor of Manipur
- Manoj Ahuja appointed as Secretary, Department of Agriculture

### January 2025
- Sanjay Malhotra assumed charge as RBI Governor on January 11, 2025
- Debashish Panda appointed as Secretary, Department of Financial Services
- Ashok Lavasa appointed as Vice President of Asian Development Bank
- Soma Roy Burman appointed as Chairperson of Central Board of Direct Taxes
- Nitin Gadkari reappointed as Minister of Road Transport and Highways

### February 2025
- Rajkiran Rai G appointed as MD & CEO of Union Bank of India
- Atul Bheda appointed as Chairman of SEBI
- Michael Patra reappointed as Deputy Governor of RBI (monetary policy)
- Shaktikanta Das appointed as Chairman of Financial Stability Institute, BIS
- Ajay Bhushan Pandey appointed as India's Executive Director at IMF

### March 2025
- Ashima Goyal reappointed as member of RBI Monetary Policy Committee
- Jayanth Rama Varma reappointed as member of RBI Monetary Policy Committee
- Shashanka Bhide reappointed as member of RBI Monetary Policy Committee
- Rajiv Kumar appointed as Chief Election Commissioner of India
- Manoj Soni reappointed as Chairman of UPSC

### April 2025
- Krishnamurthy Subramanian appointed as Executive Director of IMF (India constituency)
- Ajay Seth appointed as India's representative at G20 Finance Track
- Tuhin Kanta Pandey appointed as Secretary, DIPAM
- Rajesh Verma appointed as Secretary, Ministry of Electronics and IT
- Arun Goel appointed as Election Commissioner of India

### May 2025
- Madhabi Puri Buch reappointed as Chairperson of SEBI for second term
- Anand Mahindra reappointed as Chairman of Mahindra Group
- N Chandrasekaran reappointed as Chairman of Tata Sons
- Uday Kotak stepped down as MD of Kotak Mahindra Bank
- Sandeep Bakhshi reappointed as MD & CEO of ICICI Bank

### June 2025
- Amitabh Kant appointed as India's G20 Sherpa for 2026 presidency
- Pankaj Jain appointed as Secretary, Department of Commerce
- Tarun Bajaj appointed as Secretary, Department of Economic Affairs
- Ajay Prakash Sawhney appointed as Secretary, Ministry of Electronics and IT
- Rajiv Gauba reappointed as Cabinet Secretary

### July 2025
- Atanu Chakraborty appointed as Chairman of HDFC Bank
- Chanda Kochhar resigned from ICICI Bank board (retrospective)
- Sanjiv Chadha reappointed as MD & CEO of Bank of Baroda
- Ashok Vaswani appointed as MD & CEO of Kotak Mahindra Bank
- Ravneet Gill appointed as MD & CEO of Deutsche Bank India

### August 2025
- Shyamala Gopinath appointed as Chairperson of IRDA
- Debasish Panda appointed as Chairman of IRDAI
- Injeti Srinivas appointed as Chairman of International Financial Services Centre Authority
- Ajay Tyagi retired as Chairman of SEBI
- Pramod Agrawal appointed as Chairman of Coal India Limited

### September 2025
- Dinesh Kumar Khara retired as Chairman of State Bank of India
- CS Setty appointed as new Chairman of State Bank of India
- Michael Patra continued as Deputy Governor of RBI (monetary policy)
- T Rabi Sankar continued as Deputy Governor of RBI (payment systems)
- M Rajeshwar Rao appointed as Deputy Governor of RBI

## SUMMITS & CONFERENCES

### October 2024
- G20 Finance Ministers Meeting held in Washington DC, USA
- IMF-World Bank Annual Meetings 2024 held in Marrakech, Morocco
- India Mobile Congress 2024 held in New Delhi
- Global Fintech Fest 2024 held in Mumbai
- BRICS Summit 2024 held in Kazan, Russia

### November 2024
- COP29 Climate Summit held in Baku, Azerbaijan
- G20 Summit 2024 held in Rio de Janeiro, Brazil
- ASEAN-India Summit held in Vientiane, Laos
- India Energy Week 2024 held in Goa
- World Economic Forum India Economic Summit held in New Delhi

### December 2024
- WTO 13th Ministerial Conference held in Abu Dhabi, UAE
- India-Africa Forum Summit held in New Delhi
- Global Partnership on Artificial Intelligence Summit held in Tokyo
- Vibrant Gujarat Summit 2024 held in Gandhinagar
- Pravasi Bharatiya Divas 2025 held in Indore

### January 2025
- World Economic Forum Annual Meeting 2025 held in Davos, Switzerland
- Raisina Dialogue 2025 held in New Delhi
- India Economic Conclave 2025 held in Mumbai
- DefExpo 2025 held in Gandhinagar
- Republic Day celebrations with France as Chief Guest

### February 2025
- G20 Finance Ministers Meeting held in São Paulo, Brazil
- Munich Security Conference 2025 held in Germany
- Mobile World Congress 2025 held in Barcelona, Spain
- Aero India 2025 held in Bengaluru
- India-Middle East Economic Corridor Summit held in Abu Dhabi

### March 2025
- India-EU Summit 2025 held in Brussels, Belgium
- BRICS Foreign Ministers Meeting held in Cape Town, South Africa
- India-Japan Annual Summit held in Tokyo
- World Water Forum 2025 held in Bali, Indonesia
- Global Education Summit 2025 held in London

### April 2025
- IMF-World Bank Spring Meetings 2025 held in Washington DC
- Boao Forum for Asia 2025 held in Hainan, China
- India-ASEAN Business Summit held in Jakarta
- Global Technology Summit 2025 held in Bengaluru
- World Health Assembly 2025 held in Geneva

### May 2025
- G7 Summit 2025 held in Puglia, Italy (India as guest country)
- India-Africa Defence Ministers Conclave held in Gandhinagar
- World Economic Forum Special Meeting held in Riyadh, Saudi Arabia
- India-UK Business Summit held in London
- BIMSTEC Summit 2025 held in Bangkok, Thailand

### June 2025
- Shanghai Cooperation Organisation (SCO) Summit held in Astana, Kazakhstan
- India-US Strategic Dialogue held in Washington DC
- World Ocean Summit 2025 held in Singapore
- India Smart Cities Summit held in Surat
- Global Investors Summit 2025 held in Lucknow

### July 2025
- BRICS Summit 2025 held in Johannesburg, South Africa
- India-Russia Annual Summit held in Moscow
- ASEAN Regional Forum held in Jakarta, Indonesia
- World Youth Skills Day Summit held in New York
- India-Germany Intergovernmental Consultations held in Berlin

### August 2025
- SAARC Summit 2025 held in Colombo, Sri Lanka (after long gap)
- India-Central Asia Dialogue held in New Delhi
- World Water Week 2025 held in Stockholm, Sweden
- India International Trade Fair 2025 preparations began
- Global Entrepreneurship Summit 2025 held in Hyderabad

### September 2025
- UN General Assembly 80th Session held in New York
- G20 Leaders Summit preparations for 2026 India presidency
- India-France Strategic Dialogue held in Paris
- World Economic Forum Sustainable Development Impact Summit held in New York
- India Energy Storage Week 2025 held in New Delhi

## TECHNOLOGY & INNOVATION

### October 2024
- India launched 5G services in 200 cities across the country
- ISRO successfully tested Gaganyaan crew module
- India's semiconductor mission allocated ₹76,000 crore
- Digital India achieved 1 billion digital transactions per day
- India launched AI-powered railway reservation system

### November 2024
- India's space startup ecosystem crossed 150 companies
- ISRO announced Chandrayaan-4 mission for 2026
- India launched National Quantum Mission with ₹6,000 crore
- Digital rupee (e₹) pilot expanded to 13 cities
- India's UPI transactions crossed 12 billion per month

### December 2024
- India launched Aditya-L1 solar mission successfully
- 5G subscriber base in India crossed 100 million
- India's AI market projected to reach $17 billion by 2027
- ISRO announced plans for Venus Orbiter Mission (Shukrayaan)
- India launched National Data Governance Framework

### January 2025
- India's internet users crossed 900 million milestone
- ISRO successfully launched PSLV-C58 with 10 satellites
- India announced National Artificial Intelligence Mission
- Digital India achieved 99% Aadhaar saturation
- India's smartphone market crossed 750 million users

### February 2025
- India launched 6G technology testbed in IIT Madras
- ISRO announced Gaganyaan mission scheduled for December 2025
- India's fintech sector attracted $10 billion FDI in FY25
- Digital payments crossed ₹200 lakh crore in January 2025
- India launched National Blockchain Framework

### March 2025
- India successfully tested indigenous 5G technology
- ISRO launched GSLV-F14 with communication satellite
- India's EV market crossed 2 million vehicles milestone
- Digital India launched AI-powered governance platform
- India announced National Semiconductor Mission Phase 2

### April 2025
- India's space economy projected to reach $13 billion by 2025
- ISRO signed MoU with NASA for joint space missions
- India launched National Cyber Security Strategy 2025
- Digital rupee transactions crossed 1 million per day
- India's drone industry achieved $1 billion valuation

### May 2025
- India became 3rd largest startup ecosystem globally with 100+ unicorns
- ISRO successfully tested reusable launch vehicle
- India launched National Mission on Quantum Technologies
- 5G coverage expanded to 500 cities across India
- India's AI adoption rate reached 45% among enterprises

### June 2025
- India launched NISAR satellite jointly with NASA
- Digital India achieved 100% digital literacy in urban areas
- India's semiconductor fabrication units attracted $20 billion investment
- ISRO announced plans for Indian Space Station by 2035
- India's renewable energy capacity crossed 200 GW

### July 2025
- India successfully tested indigenous GPS system NavIC for civilian use
- ISRO launched Chandrayaan-4 sample return mission
- India's electric vehicle sales crossed 15% market share
- Digital payments ecosystem processed 15 billion transactions
- India launched National AI Portal for public services

### August 2025
- India's space sector opened for 100% FDI
- ISRO successfully tested semi-cryogenic engine
- India's 5G subscriber base crossed 300 million
- Digital India launched blockchain-based land registry
- India's drone policy enabled beyond visual line of sight operations

### September 2025
- India launched XPoSat (X-ray Polarimeter Satellite) successfully
- ISRO announced lunar base establishment plans by 2040
- India's AI market size reached $7.8 billion
- Digital India achieved 1.5 billion Aadhaar-linked mobile numbers
- India's quantum computing research centers established in 4 IITs

## SPORTS

### October 2024
- India won Asian Games 2023 with 107 medals (28 Gold, 38 Silver, 41 Bronze)
- Neeraj Chopra won Diamond League Finals with 87.66m throw
- India qualified for Paris Olympics 2024 in 16 disciplines
- Indian women's cricket team reached Asia Cup finals
- Chess Olympiad 2024: India won gold in both open and women's categories

### November 2024
- India hosted FIFA U-17 World Cup qualifiers
- PV Sindhu won Syed Modi International badminton tournament
- India won Kabaddi World Cup 2024 defeating Pakistan in final
- Virat Kohli scored 50th ODI century against New Zealand
- India ranked 4th in ICC Men's ODI Team Rankings

### December 2024
- India won ICC Men's ODI Team of the Year award
- Rohit Sharma appointed permanent captain across formats
- India hosted Khelo India Youth Games in Madhya Pradesh
- Mirabai Chanu won gold at Commonwealth Weightlifting Championships
- India qualified for Paris Olympics 2024 with 120+ athlete quota

### January 2025
- Australian Open 2025: Novak Djokovic won 11th Melbourne title
- India won U-19 Cricket World Cup defeating Australia in final
- Neeraj Chopra started season with 86.50m throw in South Africa
- Indian Super League Season 2024-25 reached 150 million viewership
- India announced hosting of FIFA U-17 Women's World Cup 2025

### February 2025
- India won 3rd Test against England to clinch series 4-1
- PV Sindhu won Indonesia Masters Super 500 badminton tournament
- India qualified for Paris Olympics in hockey after 41 years (both men and women)
- Virat Kohli became highest run-scorer in IPL history crossing 7,500 runs
- India won SAFF Championship 2025 defeating Kuwait in final

### March 2025
- IPL 2025 season began with record ₹48,000 crore media rights value
- India won Test series against Australia 3-1 to retain Border-Gavaskar Trophy
- Neeraj Chopra threw 88.77m at World Athletics Continental Tour
- Indian women's hockey team ranked 6th in FIH World Rankings
- India hosted Badminton Asia Championships in New Delhi

### April 2025
- India won Thomas Cup Badminton Championship for 2nd consecutive time
- Rohit Sharma scored 40th ODI century against New Zealand
- India qualified for FIH Hockey World Cup 2026 as hosts
- Koneru Humpy won Women's Grand Swiss Chess Tournament
- India won 5 medals at Asian Wrestling Championships

### May 2025
- IPL 2025 Final: Chennai Super Kings won 6th title
- Neeraj Chopra won Doha Diamond League with 89.34m throw
- India won Sudirman Cup Badminton Mixed Team Championship
- Indian football team qualified for AFC Asian Cup 2027
- India ranked 3rd in ICC World Test Championship standings

### June 2025
- India won ICC World Test Championship Final 2023-25 defeating Australia
- Wimbledon 2025: Carlos Alcaraz won Men's Singles title
- India hosted FIFA U-17 Women's World Cup in 3 cities
- PV Sindhu won Indonesia Open Super 1000 title
- India won Asian Champions Trophy Hockey tournament

### July 2025
- Paris Olympics 2024 (held in July 2024): India won 7 medals including 1 Gold
- Neeraj Chopra defended Olympic gold with 87.58m throw
- India won bronze in men's hockey at Paris Olympics
- Tour de France 2025 won by Jonas Vingegaard (Denmark)
- India hosted FIBA Basketball World Cup qualifiers

### August 2025
- India won 28 medals at World Wrestling Championships in Belgrade
- Rohit Sharma became 2nd Indian to score 10,000 runs in T20 cricket
- India ranked 100th in FIFA World Rankings, highest in 20 years
- Asian Champions Trophy Hockey: India defeated Malaysia 4-3 in final
- India qualified for BWF World Tour Finals with 8 shuttlers

### September 2025
- India announced bid for hosting 2036 Summer Olympics
- Neeraj Chopra won Diamond League Finals with 88.94m throw
- India won SAFF Women's Championship defeating Nepal 3-1
- Asian Games 2026 preparations began with venue inspections
- India won Durand Cup football tournament for 18th time

## OBITUARIES

### October 2024
- Kunwar Natwar Singh (93) - Former External Affairs Minister, diplomat, author
- Kader Khan (86) - Bollywood actor, comedian, screenwriter (passed away earlier, tribute events)
- Matthew Perry (54) - American actor famous for 'Friends' TV series
- Bobby Charlton (86) - English football legend, Manchester United icon

### November 2024
- Mangal Dhillon (72) - Punjabi and Hindi film actor
- Shane MacGowan (65) - Irish musician, lead singer of The Pogues
- Rosalynn Carter (96) - Former First Lady of USA, humanitarian
- Henry Kissinger (100) - Former US Secretary of State, Nobel laureate

### December 2024
- Zakir Hussain (76) - Tabla maestro, Padma Vibhushan awardee
- Norman Lear (101) - American television producer, writer
- Ryan O'Neal (82) - American actor known for 'Love Story'
- Andre Braugher (61) - American actor, Emmy award winner

### January 2025
- Glynis Johns (100) - British actress known for 'Mary Poppins'
- David Soul (80) - American-British actor, singer
- Franz Beckenbauer (78) - German football legend, World Cup winner
- Melanie Safka (76) - American singer-songwriter

### February 2025
- Carl Weathers (76) - American actor famous for 'Rocky' series
- Alexei Navalny (47) - Russian opposition leader, anti-corruption activist
- Andreas Brehme (63) - German footballer, 1990 World Cup winner
- Richard Lewis (76) - American comedian, actor

### March 2025
- Akira Toriyama (68) - Japanese manga artist, creator of 'Dragon Ball'
- M Karunanidhi (100th birth anniversary commemorated) - Former Tamil Nadu CM
- Iris Apfel (102) - American fashion icon, interior designer
- Eric Carmen (74) - American singer-songwriter

### April 2025
- O J Simpson (76) - American football player, controversial figure
- Bob Graham (87) - Former US Senator, Florida Governor
- Paul Auster (77) - American author, novelist
- Joe Flaherty (82) - Canadian-American comedian, actor

### May 2025
- Bernard Hill (79) - British actor known for 'Titanic', 'Lord of the Rings'
- Roger Corman (98) - American film director, producer
- Morgan Spurlock (53) - American documentary filmmaker
- Alice Munro (92) - Canadian Nobel Prize-winning author

### June 2025
- Françoise Hardy (80) - French singer-songwriter, actress
- Donald Sutherland (88) - Canadian actor, Hunger Games series
- Willie Mays (93) - American baseball legend, Hall of Famer
- Kinky Friedman (79) - American singer, novelist, politician

### July 2025
- Shannen Doherty (53) - American actress known for 'Beverly Hills 90210'
- Dr Ruth Westheimer (96) - German-American sex therapist, TV personality
- Richard Simmons (76) - American fitness instructor, TV personality
- Bob Newhart (94) - American comedian, actor

### August 2025
- Gena Rowlands (94) - American actress, independent film icon
- Alain Delon (88) - French actor, cinema legend
- Sven-Göran Eriksson (76) - Swedish football manager, former England coach
- Phil Donahue (88) - American talk show host, media personality

### September 2025
- James Earl Jones (93) - American actor, voice of Darth Vader
- Tito Jackson (70) - American musician, member of Jackson 5
- Maggie Smith (89) - British actress, Harry Potter series, Downton Abbey
- Kris Kristofferson (88) - American singer-songwriter, actor

## BOOKS & AUTHORS

### October 2024
- "The Covenant of Water" by Abraham Verghese won Goodreads Choice Award
- "Victory City" by Salman Rushdie - historical fiction about Vijayanagara Empire
- "The Heaven & Earth Grocery Store" by James McBride released
- Booker Prize 2024 won by Paul Lynch for "Prophet Song"

### November 2024
- "The Woman in Me" - Autobiography by Britney Spears became bestseller
- "Holly" by Stephen King - new thriller novel released
- "The Republic of False Truths" by Alaa Al Aswany won International Prize for Arabic Fiction
- JCB Prize for Literature 2024 announced

### December 2024
- "2024: The Election That Surprised India" by Rajdeep Sardesai
- "The Fraud" by Zadie Smith - historical novel released
- Jnanpith Award 2024 announced for outstanding literary contribution
- "India's Ancient Past" by R.S. Sharma commemorative edition released

### January 2025
- Economic Survey 2024-25 released before Union Budget
- "Nehru: The Debates that Defined India" edited by Tripurdaman Singh and Adeel Hussain
- "The Age of AI" by Henry Kissinger posthumously published
- National Book Awards 2024 winners announced in USA

### February 2025
- "India at 100: Envisioning Tomorrow's Economic Powerhouse" - Economic Affairs compilation
- "The Exchange" by John Grisham - legal thriller released
- Sahitya Akademi Awards 2024 announced for 20 authors in different languages
- "RBI @ 90: The Journey" - commemorative book on RBI history

### March 2025
- "Fourth Wing" by Rebecca Yarros continued as bestseller
- "Tom Lake" by Ann Patchett won major literary awards
- "India's Economy: From Independence to 2047" by Arvind Panagariya
- World Book Day 2025 celebrated globally

### April 2025
- Pulitzer Prize 2025 for Fiction awarded to Jayne Anne Phillips
- "Lessons in Chemistry" by Bonnie Garmus remained bestseller
- "The Financial History of RBI" by economic historians released
- Man Booker International Prize 2025 shortlist announced

### May 2025
- "India 2047: The Path to a Developed Nation" by Government Think Tank
- "The Wager" by David Grann won critical acclaim
- "Banking Reforms in India: The Digital Revolution" published
- International Booker Prize 2025 winner announced

### June 2025
- "Tomorrow, and Tomorrow, and Tomorrow" by Gabrielle Zevin continued success
- "The Great Banking Transition" by financial experts released
- "India's Quantum Leap" by technology writers published
- World Environment Day special publications released

### July 2025
- "Fourth Wing sequel: Iron Flame" by Rebecca Yarros released
- "The Financial Revolution: CBDCs and the Future" by RBI economists
- "India@100: The Economic Roadmap" by policy experts
- National Reading Month celebrated across India

### August 2025
- "Holly" by Stephen King topped thriller bestseller lists
- "The Three-Body Problem" trilogy gained renewed interest after Netflix series
- "Banking on India: The Next Decade" by financial analysts released
- Independence Day special editions of historical books released

### September 2025
- "The Woman in the Library" by Sulari Gentill won mystery awards
- "India's Green Transition: The Hydrogen Economy" published
- "The AI Revolution in Banking" by fintech experts released
- Banned Books Week celebrated highlighting freedom of expression

## MISCELLANEOUS

### October 2024
- India's population reached 144.5 crore, overtaking China as most populous nation
- Diwali celebrated on November 1, 2024 across India
- India launched world's longest sea bridge - Mumbai Trans Harbour Link (22 km)
- Kashmir witnessed highest tourist arrivals in 15 years (1.88 crore)

### November 2024
- India hosted G20 Culture Ministers Meeting in Varanasi
- New Parliament building completed with Sengol installation
- India's life expectancy increased to 70.19 years
- Indian Railways announced Vande Bharat sleeper trains for 2025

### December 2024
- New Year preparations began with record tourism bookings
- India's tiger population increased to 3,682 (2023 census)
- Mumbai Metro network expanded to 350 km
- India launched National Mission for Clean Ganga Phase-3

### January 2025
- Republic Day 2025 celebrated with France as Chief Guest
- India's defense budget increased to ₹6.21 lakh crore
- Ayodhya Ram Temple received 5 crore visitors since inauguration
- India's airline passenger traffic crossed 400 million annually

### February 2025
- Valentine's Day celebrated with ₹10,000 crore retail sales
- India's road network reached 67 lakh km, 2nd largest globally
- Indian Railways achieved 100% electrification of broad gauge network
- India launched National Clean Air Programme Phase-2

### March 2025
- Holi celebrated on March 14, 2025 across India
- India's installed renewable energy capacity crossed 200 GW
- Mumbai-Ahmedabad bullet train construction 60% complete
- India's domestic air traffic exceeded pre-COVID levels by 25%

### April 2025
- Indian New Year celebrated across various states
- India's coal production declined 15% as renewable energy increased
- Delhi Metro Phase-4 construction 40% complete
- India launched National River Rejuvenation Programme

### May 2025
- Summer heat wave affected north India with temperatures above 45°C
- India's solar energy capacity crossed 100 GW milestone
- Indian Railways launched 'One Station One Product' scheme
- India's EV charging infrastructure reached 50,000 stations

### June 2025
- Southwest monsoon arrived on time covering Kerala on June 1
- India's wind energy capacity crossed 45 GW
- Indian Railways announced hydrogen-powered train trials
- India's urban population reached 50 crore (35% of total)

### July 2025
- Independence Day preparations began across nation
- India's forest cover increased to 25.17% of total geographical area
- Mumbai Coastal Road project Phase-1 inaugurated (29.2 km)
- India launched National Mission for Sustainable Agriculture

### August 2025
- Independence Day celebrated across India on August 15, 2025
- Raksha Bandhan and Janmashtami celebrated across India
- India's literacy rate increased to 81.4%
- Indian Railways launched 'Amrit Bharat' stations modernization scheme

### September 2025
- Ganesh Chaturthi celebrated with eco-friendly practices
- India's waste-to-energy capacity reached 1,000 MW
- Delhi-Mumbai Expressway Phase-2 opened for traffic
- India launched National Mission for Biodiversity Conservation

---

# Additional Important Topics for Current Affairs Questions

## MONETARY POLICY & INFLATION
- Repo Rate: 6.75% (as of September 2025)
- Reverse Repo Rate: 3.35%
- Cash Reserve Ratio (CRR): 4.50%
- Statutory Liquidity Ratio (SLR): 18.00%
- Marginal Standing Facility (MSF): 7.00%
- Bank Rate: 7.00%
- CPI Inflation Target: 4% (+/- 2%)
- India's CPI Inflation: 5.4% (November 2024), moderated to 4.8% (August 2025)
- WPI Inflation: 2.8% (August 2025)

## KEY ECONOMIC INDICATORS
- GDP Growth Rate: 7.2% (FY 2024-25), projected 6.9% (FY 2025-26)
- Forex Reserves: $720 billion (September 2025)
- Fiscal Deficit: 4.9% of GDP (FY 2025-26 target)
- Current Account Deficit: 1.2% of GDP (Q1 FY26)
- India's GDP Size: $4.5 trillion (became 3rd largest economy in May 2025)
- Per Capita Income: $2,850 (FY 2024-25)
- Unemployment Rate: 6.8% (March 2025)
- Agricultural Growth: 4.7% (FY 2024-25)
- Industrial Growth: 6.5% (FY 2024-25)
- Services Growth: 7.8% (FY 2024-25)

## BANKING SECTOR
- Bank Credit Growth: 14.5% YoY (April 2025)
- Bank Deposit Growth: 11.2% YoY (September 2025)
- Total Bank Deposits: ₹205 lakh crore (September 2025)
- Gross NPA Ratio: 3.2% (lowest in 10 years)
- Net NPA Ratio: 0.8%
- Capital Adequacy Ratio: 16.8% (well above Basel III norms of 11.5%)
- Priority Sector Lending: 40% of ANBC for domestic banks
- MCLR (1-year): 8.35% to 8.75% (varies by bank)
- Base Rate: 8.15% to 8.95% (legacy rate for old loans)
- Deposit Insurance Coverage: ₹10 lakh per depositor (increased in April 2025)

## TRADE & COMMERCE
- Merchandise Exports: $500 billion (FY 2024-25)
- Merchandise Imports: $720 billion (FY 2024-25)
- Trade Deficit: $220 billion (FY 2024-25)
- Services Exports: $350 billion (FY 2024-25)
- Services Imports: $180 billion (FY 2024-25)
- Services Surplus: $170 billion
- Current Account Balance: -$54 billion (1.2% of GDP)
- India-US Trade: $190 billion (highest bilateral trade)
- India-China Trade: $118 billion (deficit of $85 billion)
- India-UAE Trade: $85 billion

## FOREIGN DIRECT INVESTMENT (FDI)
- Total FDI Inflows: $71 billion (FY 2024-25)
- FDI in Services: $14.2 billion
- FDI in Computer Software & Hardware: $11.8 billion
- FDI in Telecommunications: $6.5 billion
- FDI in Trading: $5.8 billion
- FDI in Automobile: $5.2 billion
- Top FDI Source: Singapore ($16.2 billion)
- 2nd: Mauritius ($8.7 billion)
- 3rd: USA ($7.9 billion)
- FDI Equity Inflows: $52 billion (73% of total FDI)

## GOVERNMENT FINANCES
- Total Revenue Receipts: ₹30.80 lakh crore (Budget 2025-26)
- Total Expenditure: ₹48.21 lakh crore (Budget 2025-26)
- Capital Expenditure: ₹11.11 lakh crore (11% of GDP)
- Revenue Expenditure: ₹37.10 lakh crore
- Tax Revenue: ₹26.02 lakh crore
- Non-Tax Revenue: ₹4.78 lakh crore
- Disinvestment Target: ₹50,000 crore (FY 2025-26)
- Direct Tax Collection: ₹19.58 lakh crore (Budget estimate)
- Indirect Tax Collection: ₹15.93 lakh crore (Budget estimate)
- GST Collection: ₹1.8 lakh crore per month (May 2025 - highest ever)

## CAPITAL MARKETS
- BSE Sensex: 65,000-75,000 range (2025)
- NSE Nifty: 19,500-22,500 range (2025)
- Market Capitalization: ₹350 lakh crore (September 2025)
- Total Listed Companies: 5,500+ on BSE
- IPO Fundraising: ₹1.2 lakh crore (FY 2024-25)
- Mutual Fund AUM: ₹50 lakh crore (September 2025)
- FPI Inflows: $28 billion (FY 2024-25)
- Demat Accounts: 15 crore+ (September 2025)
- Daily Trading Volume: ₹1.2 lakh crore (NSE average)
- SEBI Registered Intermediaries: 95,000+

## DIGITAL PAYMENTS
- UPI Transactions: 15 billion per month (August 2025)
- UPI Transaction Value: ₹20 lakh crore per month
- Total Digital Transactions: 1 billion per day
- Digital Payment Value: ₹200 lakh crore (January 2025)
- Aadhaar Enabled Payment System (AEPS): 350 million transactions/month
- IMPS Transactions: 450 million per month
- NEFT Transactions: 380 million per month
- RTGS Transactions: 18 million per month
- Credit Card Transactions: ₹1.5 lakh crore per month
- Debit Card Transactions: ₹80,000 crore per month

## INSURANCE SECTOR
- Total Insurance Premium: ₹8.5 lakh crore (FY 2024-25)
- Life Insurance Premium: ₹6.8 lakh crore
- Non-Life Insurance Premium: ₹1.7 lakh crore
- Insurance Penetration: 4.2% of GDP
- Insurance Density: $92 per capita
- Life Insurance Policies: 40 crore+
- Health Insurance Policies: 55 crore+ (including Ayushman Bharat)
- FDI Limit in Insurance: 74% (increased from 49%)
- Total Insurance Companies: 66 (24 life, 34 non-life, 8 standalone health)
- Ayushman Bharat Coverage: 55 crore beneficiaries

## INFRASTRUCTURE
- National Infrastructure Pipeline: ₹150 lakh crore investment (2020-2030)
- Road Network: 67 lakh km (2nd largest globally)
- National Highways: 1.46 lakh km
- Railway Network: 68,000 km
- Electrified Railway: 100% broad gauge electrification achieved
- Airports: 148 operational airports
- Major Ports: 12 major ports
- Non-Major Ports: 200+ ports
- Metro Rail Networks: 21 cities with operational metro
- Total Metro Length: 950 km operational

## ENERGY SECTOR
- Total Installed Power Capacity: 440 GW (September 2025)
- Renewable Energy Capacity: 200 GW (45% of total)
- Solar Energy Capacity: 100 GW
- Wind Energy Capacity: 45 GW
- Hydropower Capacity: 47 GW
- Nuclear Power Capacity: 7.5 GW
- Coal-based Power: 210 GW
- Gas-based Power: 25 GW
- Renewable Energy Target: 500 GW by 2030
- Green Hydrogen Production Target: 5 MMT by 2030

## AGRICULTURE
- Agricultural GDP: ₹55 lakh crore (FY 2024-25)
- Food Grain Production: 330 MMT (2024-25 target)
- Rice Production: 135 MMT
- Wheat Production: 112 MMT
- Pulses Production: 27 MMT
- Oilseeds Production: 39 MMT
- Sugarcane Production: 490 MMT
- Cotton Production: 34 million bales
- Agricultural Exports: $50 billion (FY 2024-25)
- Agricultural Credit Target: ₹20 lakh crore (FY 2025-26)

## EMPLOYMENT & WAGES
- Labour Force Participation Rate: 57.9%
- Unemployment Rate: 6.8% (March 2025)
- Urban Unemployment: 8.2%
- Rural Unemployment: 6.1%
- Youth Unemployment (15-29 years): 17.3%
- Minimum Wage (National Floor): ₹178 per day
- MGNREGA Wage: ₹220-310 per day (varies by state)
- Organized Sector Employment: 6.5 crore
- Unorganized Sector Employment: 40 crore+
- EPFO Subscribers: 7.2 crore

## POVERTY & SOCIAL INDICATORS
- Poverty Rate: 10.2% (Multidimensional Poverty Index 2024)
- Below Poverty Line Population: 14 crore (estimated)
- Literacy Rate: 81.4% (2025)
- Male Literacy: 87.7%
- Female Literacy: 74.4%
- Infant Mortality Rate: 28 per 1,000 live births
- Maternal Mortality Ratio: 97 per 100,000 live births
- Life Expectancy: 70.19 years
- Sex Ratio: 943 females per 1,000 males
- Total Fertility Rate: 2.0

## TAXATION
- Corporate Tax Rate: 22% (for domestic companies not availing exemptions)
- Corporate Tax with Exemptions: 25.17% (including surcharge and cess)
- New Manufacturing Companies: 15% (plus surcharge and cess)
- Personal Income Tax Slabs (New Regime FY 2025-26):
  - Up to ₹3 lakh: Nil
  - ₹3-7 lakh: 5%
  - ₹7-10 lakh: 10%
  - ₹10-12 lakh: 15%
  - ₹12-15 lakh: 20%
  - Above ₹15 lakh: 30%
- Standard Deduction: ₹50,000 (new regime)
- GST Revenue: ₹1.8 lakh crore per month (May 2025)
- Direct Tax Collection: ₹6.8 lakh crore (22% YoY growth)

## GLOBAL RANKINGS
- GDP Ranking: 3rd largest economy (May 2025)
- Ease of Doing Business: 55th (2025)
- Global Innovation Index: 40th (2024)
- Human Development Index: 72nd (2024)
- Corruption Perception Index: 80th (2024)
- Global Hunger Index: 111th (2024)
- Gender Gap Index: 127th (2024)
- World Happiness Report: 105th (2025)
- Environmental Performance Index: 90th (2025)
- Global Competitiveness Index: 40th (2025)
- Press Freedom Index: 54th (2025)
- Sustainable Development Goals Index: 116th (2025)

## POPULATION STATISTICS
- Total Population: 144.5 crore (2024)
- Urban Population: 50 crore (35%)
- Rural Population: 94.5 crore (65%)
- Population Growth Rate: 0.97% per annum
- Population Density: 464 per sq km
- Most Populous State: Uttar Pradesh (24 crore)
- Least Populous State: Sikkim (7 lakh)
- Most Populous City: Mumbai (2.1 crore metro area)
- Working Age Population (15-64): 68% of total
- Dependency Ratio: 47.2%

## DEFENSE & SECURITY
- Defense Budget: ₹6.21 lakh crore (FY 2025-26)
- Capital Outlay: ₹1.72 lakh crore
- Revenue Expenditure: ₹2.82 lakh crore
- Pensions: ₹1.67 lakh crore
- Defense as % of GDP: 2.1%
- Defense Exports: $2.5 billion (FY 2024-25)
- Indigenization Target: 75% by 2030
- Active Military Personnel: 14.5 lakh
- Reserve Forces: 11.5 lakh
- Paramilitary Forces: 10 lakh

## EDUCATION
- Education Budget: ₹1.25 lakh crore (FY 2025-26)
- Gross Enrollment Ratio (Higher Education): 28.4%
- Total Universities: 1,100+
- IITs: 23
- IIMs: 20
- AIIMS: 23
- Central Universities: 54
- State Universities: 450+
- Private Universities: 400+
- Total Students in Higher Education: 4.3 crore

## HEALTHCARE
- Health Budget: ₹89,155 crore (FY 2025-26)
- Ayushman Bharat Allocation: ₹7,200 crore
- Total Hospitals: 70,000+
- Government Hospitals: 25,000+
- Private Hospitals: 45,000+
- Hospital Beds: 19 lakh (1.3 per 1,000 population)
- Doctors: 13 lakh (1 per 1,445 population)
- Nurses: 31 lakh
- Doctor-Population Ratio: 1:1,445 (WHO norm: 1:1,000)
- Health Insurance Coverage: 55 crore under Ayushman Bharat

## URBANIZATION
- Urban Population: 50 crore (35% of total)
- Number of Cities: 7,900+
- Metropolitan Cities (1 million+): 53
- Mega Cities (10 million+): 5 (Delhi, Mumbai, Kolkata, Bangalore, Chennai)
- Smart Cities Mission: 100 cities selected
- AMRUT Cities: 500 cities covered
- Swachh Bharat Urban: 100% ODF cities achieved
- Urban Local Bodies: 4,700+
- Municipal Corporations: 200+
- Municipalities: 2,500+

## RURAL DEVELOPMENT
- Rural Population: 94.5 crore (65% of total)
- Total Villages: 6.4 lakh
- Gram Panchayats: 2.6 lakh
- MGNREGA Budget: ₹86,000 crore (FY 2025-26)
- PM Awas Yojana Rural: 3 crore houses completed
- Jal Jeevan Mission: 70% households with tap water
- PM Gram Sadak Yojana: 7.5 lakh km roads constructed
- Rural Electrification: 100% villages electrified
- BharatNet: 2.5 lakh gram panchayats connected
- Rural Broadband Penetration: 35%

## ENVIRONMENT & CLIMATE
- Forest Cover: 25.17% of geographical area (8.09 lakh sq km)
- Tree Cover: 2.91% (95,000 sq km)
- Total Green Cover: 28.08%
- Mangrove Cover: 4,992 sq km
- Tiger Population: 3,682 (2023 census)
- Protected Areas: 990 (5% of geographical area)
- National Parks: 106
- Wildlife Sanctuaries: 567
- Renewable Energy Capacity: 200 GW (45% of total)
- Carbon Emission: 2.88 billion tonnes CO2 (2024)
- Per Capita Emission: 2.0 tonnes CO2 (global average: 4.8 tonnes)
- Net Zero Target: 2070

## STARTUPS & INNOVATION
- Total Startups: 1,17,000+ (DPIIT recognized)
- Unicorns: 100+ (valuation $1 billion+)
- Startup Valuation: $340 billion (total)
- Startup Funding: $25 billion (2024)
- Incubators: 700+
- Accelerators: 200+
- Angel Investors: 15,000+
- Venture Capital Firms: 1,000+
- Startup Ecosystem Ranking: 3rd globally (after USA and China)
- Women-led Startups: 15% of total
- Tier-2 & Tier-3 City Startups: 45% of total
- Fintech Startups: 2,100+ (largest segment)
- Edtech Startups: 4,500+
- Healthtech Startups: 3,200+
- Agritech Startups: 1,500+
- Patent Applications: 85,000 per year
- Patent Grants: 35,000 per year
- R&D Expenditure: 0.7% of GDP
- Scientific Publications: 1.5 lakh per year (3rd globally)
- AI Startups: 5,000+

## TELECOMMUNICATIONS
- Total Telecom Subscribers: 118 crore
- Mobile Subscribers: 115 crore
- Wireless Teledensity: 84.51%
- Urban Teledensity: 135.87%
- Rural Teledensity: 58.69%
- Broadband Subscribers: 88 crore
- Internet Subscribers: 90 crore
- Internet Penetration: 62%
- 4G Subscribers: 75 crore
- 5G Subscribers: 100 million (crossed in May 2025)
- 5G Towers: 4.5 lakh (September 2025)
- Average Mobile Data Usage: 24 GB per user per month (highest globally)
- Average Data Price: $0.17 per GB (cheapest globally)
- Telecom Revenue: ₹3.2 lakh crore (FY 2024-25)
- Spectrum Auction 2024: ₹96,000 crore
- AGR Dues Outstanding: ₹1.1 lakh crore
- Total Telecom Towers: 10 lakh+
- Fiber Optic Network: 22 lakh route km
- BharatNet Implementation: 2.5 lakh gram panchayats connected
- Telecom Exports: $4.2 billion (FY 2024-25)

## AVIATION
- Total Airports: 148 operational
- International Airports: 34
- Domestic Airports: 114
- Air Passengers: 400 million (FY 2024-25)
- Domestic Passengers: 330 million
- International Passengers: 70 million
- Total Aircraft Fleet: 750+
- Scheduled Airlines: 13
- Regional Connectivity Scheme (UDAN): 460 routes operational
- UDAN Airports: 72
- Cargo Handled: 3.8 million tonnes
- Air Cargo Growth: 8.5% YoY
- Private Airlines Market Share: 93%
- Largest Airline: IndiGo (58% market share)
- Airport Authority of India Airports: 137
- Private Airports: 11
- Greenfield Airports Under Development: 15
- Aviation Turbine Fuel (ATF) Price: ₹95,000 per kiloliter (Delhi, September 2025)
- India's Aviation Ranking: 3rd largest domestic aviation market globally
- MRO (Maintenance, Repair, Overhaul) Market: $2 billion

## RAILWAYS
- Total Route Length: 68,000 km
- Electrified Route: 68,000 km (100% broad gauge)
- Broad Gauge: 63,000 km
- Meter Gauge: 3,600 km
- Narrow Gauge: 1,400 km
- Total Railway Stations: 7,349
- Daily Passengers: 2.3 crore
- Annual Passengers: 840 crore (FY 2024-25)
- Freight Traffic: 1,580 MMT (FY 2024-25)
- Freight Revenue: ₹1.6 lakh crore
- Passenger Revenue: ₹72,000 crore
- Total Revenue: ₹2.4 lakh crore
- Railway Budget Allocation: ₹2.6 lakh crore (FY 2025-26)
- Vande Bharat Trains: 75 operational (September 2025)
- Bullet Train Project: Mumbai-Ahmedabad (60% complete)
- Dedicated Freight Corridors: 3,300 km (Eastern & Western)
- Railway Employees: 12 lakh
- Capital Expenditure: ₹2.4 lakh crore (FY 2025-26)
- Safety Budget: ₹1 lakh crore (5-year Rashtriya Rail Sanraksha Kosh)
- Average Train Speed: 50 km/h (aim to increase to 75 km/h)
- Metro Rail Length: 950 km operational in 21 cities

## REAL ESTATE
- Real Estate Market Size: $265 billion (2024)
- Housing Sales: 4.2 lakh units (2024)
- Housing Launches: 4.8 lakh units (2024)
- Commercial Office Space Absorption: 65 million sq ft (2024)
- Retail Space Absorption: 8.5 million sq ft (2024)
- Warehousing Space Absorption: 42 million sq ft (2024)
- Real Estate Investment Trusts (REITs): 3 listed
- Infrastructure Investment Trusts (InvITs): 15 listed
- PM Awas Yojana Urban: 1.2 crore houses sanctioned
- PM Awas Yojana Rural: 3 crore houses completed
- Affordable Housing Target: 2 crore houses by 2026
- RERA Registered Projects: 95,000+
- Real Estate Agents Registered: 75,000+
- FDI in Real Estate: $6.5 billion (FY 2024-25)
- Top Real Estate Market: Mumbai ($55 billion)
- NCR Real Estate Market: $38 billion
- Bangalore Real Estate Market: $28 billion
- Average Property Price Appreciation: 5-7% per annum
- Commercial Real Estate Value: $80 billion
- Residential Real Estate Value: $185 billion

## TOURISM
- Foreign Tourist Arrivals: 1.2 crore (2024)
- Domestic Tourist Visits: 240 crore (2024)
- Tourism Revenue: ₹16.5 lakh crore (2024)
- Tourism GDP Contribution: 6.8%
- Tourism Employment: 4.2 crore jobs
- e-Visa Countries: 166
- UNESCO World Heritage Sites: 42 (40 as of 2024)
- Wildlife Sanctuaries: 567
- National Parks: 106
- Tiger Reserves: 54
- Ramsar Sites (Wetlands): 82
- Top Tourist State: Tamil Nadu (37 crore domestic tourists)
- 2nd: Uttar Pradesh (34 crore)
- 3rd: Karnataka (21 crore)
- Top Foreign Tourist Destination: Delhi
- 2nd: Mumbai
- 3rd: Agra
- Hotel Rooms: 2.5 lakh classified rooms
- Travel & Tourism Competitiveness: 39th globally (2024)
- Medical Tourism: $9 billion (2024)
- Medical Tourists: 2 million annually

## AUTOMOTIVE INDUSTRY
- Total Vehicle Production: 2.6 crore vehicles (FY 2024-25)
- Total Vehicle Sales: 2.5 crore vehicles
- Two-Wheeler Sales: 1.8 crore units
- Passenger Vehicle Sales: 42 lakh units
- Commercial Vehicle Sales: 10 lakh units
- Electric Vehicle Sales: 15 lakh units (15% market share)
- EV Two-Wheelers: 8 lakh units
- EV Passenger Vehicles: 6 lakh units
- Automotive Industry Size: $118 billion
- Automotive Exports: $30 billion
- Auto Component Industry: $60 billion
- Auto Component Exports: $18 billion
- Manufacturing Units: 45,000+
- Direct Employment: 5 million
- Indirect Employment: 3.5 crore
- R&D Investment: ₹35,000 crore
- Top Manufacturer: Maruti Suzuki (40% passenger car market)
- 2nd: Hyundai (15%)
- 3rd: Tata Motors (13%)
- FAME-II Subsidy: ₹11,500 crore (2024-27)
- Charging Stations: 50,000+ (September 2025)

## PHARMACEUTICAL INDUSTRY
- Pharma Market Size: $50 billion (2024)
- Generic Drug Market Share: 70%
- Export Value: $27.9 billion (FY 2024-25)
- Top Export Destination: USA (31%)
- 2nd: UK (4%)
- 3rd: South Africa (4%)
- API (Active Pharmaceutical Ingredients) Production: $18 billion
- Bulk Drug Parks: 3 approved
- Pharma Parks: 4 operational
- WHO-GMP Compliant Plants: 2,000+
- USFDA Approved Plants: 750+
- Patent Applications: 8,500 per year
- Vaccine Production Capacity: 3.5 billion doses annually
- COVID-19 Vaccine Exports: 285 million doses (under COVAX)
- Biosimilars Market: $7 billion
- Ayurveda Market: $18 billion (AYUSH sector)
- Traditional Medicine Exports: $1.5 billion
- Pharma R&D Expenditure: 8-9% of revenue
- Clinical Trials: 3,200 ongoing (2024)
- Drug Master Files (DMFs) Filed: 1,200+ annually
- Employment: 3 million direct jobs

## TEXTILE INDUSTRY
- Textile Industry Size: $165 billion (2024)
- Textile Exports: $44.4 billion (FY 2024-25)
- Cotton Textile Exports: $16 billion
- Readymade Garments: $18 billion
- Man-Made Textile: $6 billion
- Handicrafts: $3.5 billion
- Top Export Destination: USA (27%)
- 2nd: UAE (12%)
- 3rd: Bangladesh (6%)
- Cotton Production: 34 million bales (170 kg each)
- Spinning Mills: 1,900
- Power Looms: 23 lakh
- Handlooms: 31 lakh
- Employment: 4.5 crore (direct + indirect)
- Women Workers: 60% of workforce
- Technical Textiles Market: $23 billion
- National Technical Textiles Mission: ₹1,480 crore
- PLI Scheme Outlay: ₹10,683 crore
- Mega Textile Parks: 7 approved
- FDI in Textiles: 100% automatic route
- Textile GDP Contribution: 2.3%

## CHEMICAL INDUSTRY
- Chemical Industry Size: $220 billion (2024)
- Specialty Chemicals: $35 billion
- Agrochemicals: $8.5 billion
- Petrochemicals: $65 billion
- Dyes & Pigments: $3.2 billion
- Chemical Exports: $28 billion
- Chemical Imports: $48 billion
- Pharmaceutical Chemicals: $18 billion
- Plastics & Petrochemicals: $45 billion
- Fertilizer Production: 500 lakh tonnes
- Urea Production: 250 lakh tonnes
- DAP Production: 120 lakh tonnes
- Fertilizer Subsidy: ₹1.88 lakh crore (FY 2025-26)
- Petroleum Refining Capacity: 255 MMT per annum
- Crude Oil Production: 29 MMT (FY 2024-25)
- Natural Gas Production: 35 BCM
- Petroleum Products Consumption: 220 MMT
- Chemical Parks: 50+
- PCPIR (Petroleum, Chemicals & Petrochemicals Investment Regions): 4
- Employment: 2 million direct jobs
- GDP Contribution: 3.4%

## STEEL INDUSTRY
- Crude Steel Production: 142 MMT (FY 2024-25)
- Finished Steel Consumption: 130 MMT
- Steel Exports: 18 MMT
- Steel Imports: 6 MMT
- Per Capita Steel Consumption: 87 kg (global average: 229 kg)
- Steel Industry Size: $140 billion
- Iron Ore Production: 280 MMT
- Iron Ore Exports: 35 MMT
- Integrated Steel Plants: 10 major
- Secondary Steel Producers: 550+
- DRI (Direct Reduced Iron) Production: 45 MMT
- Pig Iron Production: 8 MMT
- Sponge Iron Production: 38 MMT
- Steel Capacity: 154 MMT per annum
- Target Capacity by 2030: 300 MMT
- PLI Scheme for Specialty Steel: ₹6,322 crore
- Top Producer: SAIL (State-owned)
- 2nd: Tata Steel
- 3rd: JSW Steel
- Employment: 2.5 million (direct + indirect)
- GDP Contribution: 2.1%

## CEMENT INDUSTRY
- Cement Production: 390 MMT (FY 2024-25)
- Cement Consumption: 380 MMT
- Per Capita Cement Consumption: 263 kg
- Cement Exports: 15 MMT
- Cement Capacity: 560 MMT per annum
- Number of Cement Plants: 210
- Limestone Reserves: 28,000 MMT
- Top Producer: UltraTech Cement (120 MMT capacity)
- 2nd: Shree Cement (50 MMT)
- 3rd: Ambuja Cements (75 MMT)
- Employment: 1 million (direct + indirect)
- Cement Industry Size: $28 billion
- Green Cement Production: 15% of total
- Fly Ash Utilization: 75% of generated fly ash
- Coal Consumption: 30 MMT per annum
- Power Consumption: 35 billion units
- Exports Destination: Bangladesh (40%), Nepal, Sri Lanka
- GDP Contribution: 1.3%
- Target by 2030: 550 MMT production
- Waste Heat Recovery Systems: 85 units operational

## COAL & MINING
- Coal Production: 997 MMT (FY 2024-25)
- Coal India Limited Production: 710 MMT
- Singareni Collieries Production: 68 MMT
- Private Sector Coal Production: 155 MMT
- Coal Imports: 215 MMT
- Coking Coal Imports: 55 MMT
- Non-Coking Coal Imports: 160 MMT
- Coal Reserves: 361 billion tonnes
- Iron Ore Production: 280 MMT
- Bauxite Production: 25 MMT
- Copper Ore Production: 195,000 tonnes
- Zinc Ore Production: 885,000 tonnes
- Lead Ore Production: 138,000 tonnes
- Gold Production: 3,000 kg
- Manganese Ore Production: 2.8 MMT
- Chromite Production: 4.2 MMT
- Limestone Production: 390 MMT
- Mineral Production Value: ₹2.5 lakh crore
- Mining Leases: 3,500+
- Mining Sector Employment: 15 lakh
- Mines Operating: 1,550 (major minerals)
- National Mineral Index: Base 100 (2014-15)
- Mining GDP Contribution: 2.5%

## OIL & GAS
- Crude Oil Production: 29 MMT (FY 2024-25)
- Natural Gas Production: 35 BCM
- Crude Oil Imports: 228 MMT
- Import Dependency: 88%
- Petroleum Products Consumption: 220 MMT
- Refining Capacity: 255 MMT per annum
- LPG Consumption: 28 MMT
- Diesel Consumption: 85 MMT
- Petrol Consumption: 35 MMT
- Aviation Turbine Fuel (ATF): 8 MMT
- Natural Gas Reserves: 1,227 BCM (proven)
- Crude Oil Reserves: 594 MMT (proven)
- Shale Gas Reserves: 96 TCF (estimated)
- City Gas Distribution Networks: 450 cities covered
- PNG (Piped Natural Gas) Connections: 1.2 crore
- CNG Stations: 6,500+
- Oil & Gas Pipelines: 35,000 km
- Gas Pipelines: 22,000 km
- LNG Import Terminals: 6 operational
- Strategic Petroleum Reserves: 5.33 MMT capacity
- Oil & Gas Sector Investment: ₹8.5 lakh crore (FY 2025-26)
- Top Producer: ONGC (70% of domestic crude)
- 2nd: Oil India Limited
- 3rd: Reliance Industries (private)
- Petroleum Subsidy: ₹10,000 crore (LPG subsidy)
- Employment: 6 lakh (direct + indirect)
- Ethanol Blending: 12% achieved (target 20% by 2025-26)
- Biodiesel Production: 500 million liters
- GDP Contribution: 7.2%

## ELECTRONICS & IT HARDWARE
- Electronics Industry Size: $118 billion (2024)
- Electronics Production: $101 billion
- Electronics Exports: $29 billion
- Electronics Imports: $86 billion
- Mobile Phone Production: 33 crore units
- Mobile Phone Exports: $12 billion
- Semiconductor Market: $27 billion
- LED Production: $2.5 billion
- Consumer Electronics: $12 billion
- Industrial Electronics: $45 billion
- Computer Hardware Production: $8 billion
- IT Hardware Imports: $12 billion
- PLI Scheme (Mobile Manufacturing): ₹41,000 crore
- PLI Scheme (IT Hardware): ₹17,000 crore
- PLI Scheme (Semiconductor): ₹76,000 crore
- Semiconductor Fabs Approved: 3 projects
- Display Fabs Approved: 2 projects
- Electronics Manufacturing Clusters: 20
- Special Economic Zones (Electronics): 250+
- Employment: 5 million
- Electronics Exports Target by 2026: $120 billion
- Manufacturing Units: 1,500+
- R&D Centers: 450+
- GDP Contribution: 3.7%

## IT & SOFTWARE SERVICES
- IT-BPM Industry Size: $254 billion (FY 2024-25)
- IT Services: $142 billion
- BPM (Business Process Management): $46 billion
- Software Products: $38 billion
- ER&D (Engineering R&D): $28 billion
- IT Exports: $194 billion (76% of total revenue)
- Domestic IT Market: $60 billion
- IT Exports to USA: 52% of total exports
- IT Exports to Europe: 31%
- IT Exports to Rest of World: 17%
- Top IT Company: TCS (Revenue $29 billion)
- 2nd: Infosys ($18.6 billion)
- 3rd: HCL Technologies ($13.3 billion)
- 4th: Wipro ($11.2 billion)
- 5th: Tech Mahindra ($6.5 billion)
- IT Companies: 18,500+
- IT Professionals: 5.4 million
- Women in IT: 36%
- IT Hubs: Bangalore, Hyderabad, Pune, Chennai, NCR
- Software Technology Parks: 60+
- STPI Units: 9,500+
- IT Parks/SEZs: 120+
- Global Capability Centers (GCCs): 1,700+
- Startup Ecosystem: 7,000+ tech startups
- IT Spending (Domestic): $110 billion
- Cloud Services Market: $12 billion
- Cybersecurity Market: $3.5 billion
- IoT Market: $9.5 billion
- AI/ML Market: $7.8 billion
- GDP Contribution: 7.4%
- Employment Growth: 4.5% YoY

## E-COMMERCE
- E-commerce Market Size: $120 billion (2024)
- E-commerce Growth Rate: 18% YoY
- Online Retail: $75 billion
- Digital Services: $45 billion
- Online Shoppers: 35 crore users
- E-commerce Penetration: 8% of total retail
- Top Platform: Flipkart (33% market share)
- 2nd: Amazon India (31%)
- 3rd: Meesho (15%)
- 4th: JioMart (8%)
- Festive Season Sales: ₹1 lakh crore (Oct-Dec 2024)
- Fashion E-commerce: $28 billion
- Electronics E-commerce: $22 billion
- Grocery E-commerce: $8 billion
- Beauty & Personal Care: $6 billion
- Home & Furniture: $5 billion
- Food Delivery Market: $8 billion (Swiggy, Zomato)
- Quick Commerce (Q-commerce): $2.5 billion
- Social Commerce: $4 billion
- D2C Brands: 1,200+
- Logistics Partners: 250+
- E-commerce Exports: $5 billion
- Average Order Value: ₹1,850
- Return Rate: 15-20%
- Cash on Delivery: 35% of orders
- Digital Payments: 65% of orders
- Rural E-commerce: 35% of orders
- Employment: 8 million (direct + indirect)
- Warehousing Space: 45 million sq ft
- Target by 2030: $350 billion

## FINTECH
- Fintech Market Size: $150 billion (2024)
- Digital Payments: $110 billion
- Digital Lending: $18 billion
- Insurtech: $10 billion
- Wealthtech: $8 billion
- Neobanking: $4 billion
- Total Fintech Startups: 2,100+
- Fintech Unicorns: 21
- UPI Transactions: 15 billion per month
- UPI Transaction Value: ₹20 lakh crore/month
- Digital Wallet Users: 45 crore
- Digital Lending App Downloads: 50 crore+
- Peer-to-Peer Lending: ₹15,000 crore
- Buy Now Pay Later (BNPL): ₹25,000 crore
- Micro-Insurance Policies: 12 crore
- Digital Gold Market: ₹8,000 crore
- Robo-Advisory AUM: ₹5,000 crore
- Account Aggregator Framework: 1.5 crore accounts linked
- NPCI Transactions: 100 billion annually
- Top Fintech: Paytm (30 crore users)
- 2nd: PhonePe (48 crore users)
- 3rd: Google Pay (15 crore users)
- Fintech Funding: $6 billion (2024)
- Employment: 2.5 lakh
- Financial Inclusion via Fintech: 80% adults with digital access
- Target by 2030: $500 billion market

## FOODTECH & AGRITECH
- Foodtech Market Size: $13 billion (2024)
- Food Delivery: $8 billion
- Cloud Kitchens: $2 billion
- Grocery Delivery: $3 billion
- Top Food Delivery: Zomato (55% market share)
- 2nd: Swiggy (45%)
- Restaurant Partners: 4 lakh+
- Delivery Partners: 5 lakh
- Average Delivery Time: 28 minutes
- Food Delivery Users: 10 crore
- Order Frequency: 4 orders per month per user
- Cloud Kitchen Operations: 1,500+
- Quick Commerce Delivery: 10-15 minutes
- Agritech Market Size: $2.3 billion (2024)
- Agritech Startups: 1,500+
- Farm Management Software Users: 25 lakh farmers
- Precision Agriculture: $800 million
- Supply Chain & Logistics: $650 million
- Digital Marketplaces: $450 million
- Fintech for Agriculture: $400 million
- Farmers Onboarded Digitally: 5 crore
- e-NAM (National Agriculture Market): 1.77 crore farmers registered
- e-NAM Mandis: 1,389
- e-NAM Trade Value: ₹3.2 lakh crore
- Drone Usage in Agriculture: 1.5 lakh hectares covered
- Soil Testing Apps: 50 lakh farmers
- Weather Advisory Apps: 3.5 crore farmers
- Kisan Credit Cards: 7.4 crore active
- PM-KISAN Beneficiaries: 11 crore farmers
- DBT in Agriculture: ₹2.8 lakh crore transferred
- Agriculture Exports via Digital Platforms: $8 billion

## EDTECH
- Edtech Market Size: $7.5 billion (2024)
- Edtech Users: 9.5 crore
- Edtech Startups: 4,500+
- K-12 Online Learning: $3.2 billion
- Higher Education Online: $1.8 billion
- Test Preparation: $1.2 billion
- Professional Upskilling: $900 million
- Language Learning: $400 million
- Top Edtech: Byju's (15 crore users)
- 2nd: Unacademy (6 crore users)
- 3rd: PhysicsWallah (5 crore users)
- SWAYAM Platform: 3,000+ courses
- DIKSHA Platform: 6 crore users (teachers & students)
- National Digital Library: 8 crore resources
- Virtual Labs: 220 labs across 120 universities
- NPTEL Courses: 2,500+ courses
- MOOCs Enrollment: 8 crore learners
- PM eVIDYA: 34 DTH TV channels for classes
- Digital Learning Content: 80,000+ hours
- Teacher Training Online: 1.2 crore teachers
- Rural Edtech Penetration: 35%
- Urban Edtech Penetration: 68%
- Average Learning Time: 2.5 hours per week
- Paid Subscriptions: 1.2 crore users
- Free Users: 8.3 crore
- Edtech Funding: $2.5 billion (2024)
- Employment: 1.2 lakh
- Target by 2030: $30 billion

## HEALTHTECH & TELEMEDICINE
- Healthtech Market Size: $6.5 billion (2024)
- Telemedicine: $2.8 billion
- Online Pharmacy: $2.2 billion
- Health Insurance Tech: $900 million
- Diagnostics Tech: $600 million
- Total Healthtech Startups: 3,200+
- Online Doctor Consultations: 15 crore annually
- Registered Doctors on Platforms: 3.5 lakh
- Top Healthtech: 1mg (3 crore users)
- 2nd: PharmEasy (2.5 crore users)
- 3rd: Practo (4 crore users)
- e-Sanjeevani Platform: 28 crore consultations
- Telemedicine Consultations: 35 crore (FY 2024-25)
- Ayushman Bharat Digital Mission: 50 crore health IDs created
- Health Records Digitized: 8 crore
- Online Medicine Orders: 25 crore per year
- Diagnostic Tests Booked Online: 8 crore
- Mental Health App Users: 1.2 crore
- Fitness App Users: 6 crore
- Health Insurance Policies Sold Online: 2.5 crore
- AI in Diagnostics: 250+ hospitals using
- Remote Patient Monitoring: 50 lakh patients
- Wearable Health Devices: 2.5 crore users
- Healthtech Funding: $1.8 billion (2024)
- Employment: 80,000
- Rural Telemedicine Penetration: 25%
- Target by 2030: $50 billion

## LOGISTICS & SUPPLY CHAIN
- Logistics Industry Size: $250 billion (2024)
- Freight & Logistics: $180 billion
- Warehousing: $35 billion
- Express Delivery: $20 billion
- Cold Chain: $15 billion
- Logistics as % of GDP: 8.3% (target: 7% by 2030)
- Commercial Vehicles: 1.2 crore
- Goods Vehicles: 1 crore
- Freight Railways: 1,580 MMT
- Port Cargo: 1,400 MMT (FY 2024-25)
- Airport Cargo: 3.8 MMT
- Major Ports: 12
- Total Ports: 200+
- Inland Waterways: 111 declared
- National Waterway Length: 20,000 km
- Container Traffic: 16.6 million TEUs
- Top Port: Kandla (140 MMT)
- 2nd: Paradip (135 MMT)
- 3rd: Mumbai (75 MMT)
- Logistics Parks: 35 operational
- Multi-Modal Logistics Parks: 16 planned
- Warehouse Space: 300 million sq ft
- Grade A Warehousing: 180 million sq ft
- Cold Storage Capacity: 37 million MT
- Temperature-Controlled Warehouses: 1,500+
- E-commerce Logistics: $15 billion
- 3PL Market: $45 billion
- Last Mile Delivery: $8 billion
- Logistics Startups: 800+
- Logistics Employment: 4 crore
- Average Logistics Cost: 8.3% of product value
- Digital Freight Platforms: 150+
- GPS-Enabled Trucks: 40 lakh
- Electronic Way Bill (e-Way Bill): 8 crore generated monthly
- RFID Tags in Logistics: 5 crore
- Drone Deliveries (Pilot): 50,000 deliveries
## MEDIA & ENTERTAINMENT
- M&E Industry Size: ₹2.3 lakh crore (2024)
- Television: ₹87,000 crore
- Print Media: ₹28,000 crore
- Films: ₹24,000 crore
- Digital/OTT: ₹60,000 crore
- Animation & VFX: ₹12,000 crore
- Gaming: ₹20,000 crore
- Radio: ₹3,500 crore
- Music: ₹2,800 crore
- Out-of-Home Advertising: ₹4,200 crore
- TV Households: 21 crore
- Cable & Satellite TV: 14 crore households
- DTH Subscribers: 7 crore
- DD Free Dish: 4.5 crore households
- TV Channels: 900+
- FM Radio Stations: 380+
- Newspapers: 1.18 lakh registered
- Daily Newspapers: 11,000+
- Newspaper Circulation: 40 crore copies daily
- Cinema Screens: 9,500
- Multiplexes: 3,200
- Single Screens: 6,300
- Film Production (Hindi): 350 films per year
- Film Production (All Languages): 2,000+ films
- Box Office Collection: ₹12,500 crore (2024)
- OTT Platforms: 50+
- OTT Subscribers: 9.5 crore paid
- OTT Content Spend: ₹18,000 crore (2024)
- Top OTT: JioCinema (20 crore MAU)
- 2nd: Disney+ Hotstar (6 crore paid subscribers)
- 3rd: Amazon Prime Video (2.5 crore)
- 4th: Netflix (1 crore paid subscribers)
- 5th: SonyLIV (2.8 crore)
- YouTube Users: 46 crore (India)
- Social Media Users: 75 crore
- Gaming Market: Mobile Gaming 95%
- Online Gamers: 42 crore
- E-sports Market: ₹2,500 crore
- E-sports Players: 1.5 lakh professional
- Animation Studios: 450+
- VFX Studios: 250+
- Music Streaming Users: 40 crore
- Podcast Listeners: 10 crore
- Digital Advertising: ₹45,000 crore
- Social Media Advertising: ₹22,000 crore
- Search Advertising: ₹15,000 crore
- Display Advertising: ₹8,000 crore
- Employment: 40 lakh
- Content Creation Jobs: 15 lakh
- Influencer Marketing: ₹2,800 crore
- Content Creators/Influencers: 8 lakh
- Average Screen Time: 4.9 hours per day
- Target by 2030: ₹5 lakh crore

## RETAIL INDUSTRY
- Retail Market Size: $900 billion (2024)
- Organized Retail: $135 billion (15%)
- Unorganized Retail: $765 billion (85%)
- Online Retail: $75 billion (8.3%)
- Offline Retail: $825 billion
- Modern Trade: $50 billion
- Traditional Trade: $715 billion
- Food & Grocery: $570 billion (63%)
- Apparel & Fashion: $95 billion (10.5%)
- Consumer Electronics: $75 billion (8.3%)
- Furniture & Home Decor: $35 billion (3.9%)
- Jewelry: $55 billion (6.1%)
- Beauty & Personal Care: $28 billion (3.1%)
- Footwear: $18 billion (2%)
- Books & Music: $3 billion (0.3%)
- Total Retail Stores: 1.5 crore
- Kirana Stores: 1.2 crore
- Organized Retail Stores: 1 lakh
- Shopping Malls: 650+
- Mall Space: 75 million sq ft
- Hypermarkets: 250+
- Supermarkets: 5,000+
- Convenience Stores: 8,500+
- Top Retailer: Reliance Retail (₹2.6 lakh crore revenue)
- 2nd: D-Mart/Avenue Supermarts (₹52,000 crore)
- 3rd: Future Group (₹32,000 crore)
- 4th: Aditya Birla Fashion Retail (₹12,500 crore)
- 5th: Trent (Tata) (₹12,000 crore)
- Retail Employment: 5 crore
- FDI in Retail (Single Brand): 100%
- FDI in Multi-Brand Retail: Not Allowed
- Per Capita Retail Space: 2 sq ft (global average: 16 sq ft)
- Retail Real Estate: $80 billion
- Target by 2030: $1.8 trillion

## HOSPITALITY & TRAVEL
- Hospitality Market Size: ₹2.5 lakh crore (2024)
- Hotel Industry: ₹1.8 lakh crore
- Travel Agencies: ₹45,000 crore
- Car Rentals: ₹12,000 crore
- Budget Hotels: ₹15,000 crore
- Total Hotels: 2 lakh properties
- Star Hotels: 12,000+
- Budget Hotels: 1.5 lakh
- Heritage Hotels: 500+
- Hotel Rooms: 25 lakh (classified + unclassified)
- Five-Star Hotels: 350+
- Four-Star Hotels: 550+
- Three-Star Hotels: 950+
- Hotel Occupancy Rate: 68% (2024)
- Average Room Rate: ₹5,500 per night (4-5 star)
- Top Hotel Chain: Taj Hotels (200+ properties)
- 2nd: Oberoi Hotels (35 properties)
- 3rd: ITC Hotels (120+ properties)
- 4th: Lemon Tree Hotels (100+ properties)
- 5th: OYO Rooms (1.5 lakh properties globally)
- Online Travel Booking: 65% of total bookings
- MakeMyTrip Users: 7 crore
- Yatra Users: 3.5 crore
- Goibibo Users: 6 crore
- Airbnb Listings: 1.5 lakh
- Homestays: 50,000+
- Business Travel: ₹65,000 crore
- Leisure Travel: ₹1.2 lakh crore
- MICE (Meetings, Incentives, Conferences, Exhibitions): ₹35,000 crore
- Convention Centers: 120+
- Restaurants (organized): 7 lakh
- Quick Service Restaurants: 35,000+
- Fine Dining Restaurants: 15,000+
- Cafes: 25,000+
- Cloud Kitchens: 1,500+
- Employment: 4.5 crore
- Target by 2030: ₹6 lakh crore

## SPORTS INDUSTRY
- Sports Industry Size: ₹1.2 lakh crore (2024)
- Sports Broadcasting: ₹55,000 crore
- Sponsorships: ₹28,000 crore
- Sports Infrastructure: ₹18,000 crore
- Merchandise: ₹10,000 crore
- Sports Events: ₹9,000 crore
- Cricket Economy: ₹80,000 crore (67%)
- IPL Valuation: $10.9 billion (₹90,000 crore)
- IPL Media Rights: ₹48,390 crore (2023-27)
- IPL Brand Value: $16.4 billion
- IPL Average Viewership: 50 crore per match
- Average IPL Player Salary: ₹5.5 crore
- Football Economy: ₹12,000 crore (10%)
- ISL (Indian Super League) Valuation: ₹3,500 crore
- Badminton Economy: ₹3,500 crore
- Kabaddi Economy: ₹2,800 crore (Pro Kabaddi League)
- Hockey Economy: ₹1,200 crore
- Tennis Economy: ₹1,500 crore
- Wrestling Economy: ₹800 crore
- Sports Stadiums: 350+ (major venues)
- Cricket Stadiums: 52 international venues
- National Sports Academies: 8
- Khelo India Centers: 1,000+
- Sports Authority of India Budget: ₹3,400 crore (FY 2025-26)
- Olympic Medal Target 2028: 15-20 medals
- Asian Games 2023: 107 medals (4th position)
- Commonwealth Games 2022: 61 medals (4th)
- Professional Athletes: 50,000+
- Registered Sports Persons: 1.5 crore
- Sports Equipment Market: ₹8,500 crore
- Fitness Industry: ₹32,000 crore
- Gym Memberships: 1.2 crore
- Yoga Practitioners: 30 crore
- Sports Betting (Illegal): ~₹1.5 lakh crore (estimated)
- Fantasy Sports Users: 18 crore
- Fantasy Sports Market: ₹12,000 crore
- Top Fantasy Platform: Dream11 (20 crore users)
- Sports Sponsorship Growth: 15% YoY
- Employment: 12 lakh

## RENEWABLE ENERGY
- Total Renewable Capacity: 200 GW (45% of total power)
- Solar Capacity: 100 GW
- Wind Capacity: 45 GW
- Hydro Capacity (Small): 5 GW
- Biomass/Waste-to-Energy: 11 GW
- Large Hydro: 47 GW (separately counted)
- Nuclear: 7.5 GW
- Renewable Energy Target 2030: 500 GW
- Solar Target 2030: 280 GW
- Wind Target 2030: 140 GW
- Green Hydrogen Target 2030: 5 MMT
- Solar Panel Manufacturing: 15 GW per annum
- Solar Cell Manufacturing: 8 GW per annum
- Wind Turbine Manufacturing: 10 GW per annum
- Rooftop Solar: 11 GW installed
- Solar Parks: 50+ (aggregate 40 GW)
- Offshore Wind Target: 30 GW by 2030
- Offshore Wind Identified Potential: 127 GW
- Battery Storage Capacity: 10 GWh
- Battery Storage Target 2030: 50 GWh
- Pumped Storage Projects: 4.8 GW operational
- Pumped Storage Under Development: 10 GW
- Green Hydrogen Production: 50,000 tonnes (2024)
- National Green Hydrogen Mission: ₹19,744 crore
- PLI Scheme (Solar): ₹24,000 crore
- Renewable Energy Investment: $15 billion (FY 2024-25)
- Top Solar Developer: NTPC (5 GW)
- 2nd: Adani Green Energy (11 GW)
- 3rd: ReNew Power (13 GW)
- 4th: Tata Power (5 GW)
- Carbon Credits Traded: 2.5 million tonnes
- Renewable Energy Employment: 10 lakh
- Solar Irrigation Pumps: 3.5 lakh installed
- LED Bulbs Distributed: 36 crore (UJALA scheme)
- Energy Saved through LED: 48 billion units/year
- CO2 Reduction: 39 MMT per year (via LED)
- Electricity Access: 100% villages electrified
- Renewable Purchase Obligation (RPO): 43.33% by 2030
- Green Bonds Issued: $12 billion (cumulative)
- International Solar Alliance Members: 116 countries

## ELECTRIC VEHICLES (EV)
- EV Market Size: $8 billion (2024)
- Total EV Sales: 15 lakh units (FY 2024-25)
- EV Penetration: 6% of total vehicle sales
- E-Two Wheelers: 8 lakh units (5.5% penetration)
- E-Three Wheelers: 5 lakh units (47% penetration)
- E-Four Wheelers (Passenger): 1.5 lakh units (2% penetration)
- E-Buses: 7,000 units
- E-Cars Sold: 95,000 units (2024)
- E-2W Market Leaders: Ola Electric (35%), Ather (22%)
- E-4W Market Leaders: Tata Motors (70%), MG Motor (12%)
- Charging Stations: 50,000+ (public + semi-public)
- Fast Charging Stations: 8,500
- Battery Swapping Stations: 2,500+
- EV Manufacturing Units: 150+
- Battery Manufacturing: 50 GWh capacity (2025)
- Battery Manufacturing Target 2030: 500 GWh
- Lithium-ion Cell Production: 15 GWh (2024)
- FAME-II Budget: ₹11,500 crore (2024-2027)
- FAME-II Subsidy per Vehicle: ₹10,000-₹1.5 lakh
- EV Incentive (State-level): Various up to 15% of cost
- Import Duty on EV: 60-100%
- GST on EV: 5% (vs 28% on ICE)
- EV Battery Cost: $110 per kWh (2024)
- Target Battery Cost 2030: $60 per kWh
- Average EV Range: 150-400 km
- EV Two-Wheeler Range: 80-150 km
- EV Four-Wheeler Range: 250-600 km
- PLI Scheme (EV): ₹18,100 crore
- PLI Scheme (Battery): ₹18,100 crore
- Lithium Reserves (Discovered): 5.9 MMT (Jammu & Kashmir)
- Lithium Imports: 450 tonnes (2024)
- Lithium Import Bill: $180 million
- Cobalt Imports: 1,200 tonnes
- Battery Recycling Capacity: 5,000 tonnes per annum
- EV Employment: 5 lakh (projected 50 lakh by 2030)
- EV Exports: $500 million (2024)
- Total Investment in EV: ₹1.2 lakh crore (announced)
- Target EV Penetration 2030: 30% of new vehicle sales
- Target EV Sales 2030: 1 crore vehicles per year

## SPACE TECHNOLOGY
- Space Industry Size: $8 billion (2024)
- ISRO Budget: ₹13,700 crore (FY 2025-26)
- Total Satellites Launched: 430+ (including foreign)
- Operational Satellites: 54 (2024)
- Communication Satellites: 21
- Earth Observation Satellites: 20
- Navigation Satellites (NavIC): 7
- Scientific Satellites: 6
- PSLV Launches: 58 (100% success rate recent)
- GSLV Launches: 18
- GSLV Mk III Launches: 7
- Chandrayaan-3: Successful Moon landing (August 2023)
- Aditya-L1: Solar mission launched (September 2023)
- Gaganyaan Mission: Planned 2025 (first human spaceflight)
- Mars Orbiter Mission: Operational since 2014
- NavIC Coverage: India + 1,500 km radius
- NavIC Accuracy: 10 meters
- Remote Sensing Data Users: 10,000+ registered
- Space Applications: Agriculture, Disaster Management, Navigation
- Commercial Launch Revenue: $150 million (2024)
- Foreign Satellites Launched: 380+
- Satellite Launch Cost: $60-70 million (PSLV)
- GSLV Mk III Cost: $110 million per launch
- Satellite Manufacturing Cost: $20-200 million (varies by type)
- Space Startups: 190+
- IN-SPACe Registered Startups: 150+
- Private Space Companies: Skyroot, Agnikul, Pixxel, Dhruva Space
- Skyroot: First private rocket launch (Nov 2022)
- Small Satellite Market: $500 million
- Satellite Data Services: $1.2 billion
- Ground Station Services: $300 million
- Launch Services (Private): $400 million
- Space Manufacturing: $150 million
- Space Technology Centers: 14 (ISRO facilities)
- Satellite Integration & Test Facility: 3
- Mission Control Centers: 2 (Bangalore, Lucknow)
- Launch Pads: 2 (Sriharikota)
- Tracking Stations: 18 globally
- Space Employment: 50,000+
- Space Patents Filed: 250+ (2024)
- Space R&D Investment: ₹2,500 crore
- Foreign Space Cooperation: 60+ countries
- International Space Station: Indian experiments ongoing
- Space Debris Tracking: 200+ objects monitored
- Satellite Broadband: Planned (Jio, Airtel, Starlink)
- Target by 2030: $13 billion market
- Reusable Launch Vehicle: Under development
- Semi-Cryogenic Engine: Testing phase
- Human Rating Certification: In progress for Gaganyaan
- Space Sector FDI: 74% (49% automatic, rest approved)
- NewSpace India Limited Revenue: ₹600 crore (FY 2024)
- Antrix Corporation Revenue: ₹1,200 crore
- Space Parks: 3 planned
- Manufacturing Hubs: Bangalore, Thiruvananthapuram, Hyderabad

## DEFENSE & AEROSPACE
- Defense Budget: ₹6.21 lakh crore (FY 2025-26)
- Capital Expenditure: ₹1.72 lakh crore (28%)
- Revenue Expenditure: ₹4.49 lakh crore (72%)
- Defense as % of GDP: 1.9%
- Defense Allocation (Global Rank): 4th largest
- Army Budget: ₹2.8 lakh crore
- Navy Budget: ₹55,000 crore
- Air Force Budget: ₹2.1 lakh crore
- Defense Research: ₹23,000 crore
- DRDO Budget: ₹23,855 crore (FY 2025-26)
- Defense Production: ₹1.27 lakh crore (FY 2023-24)
- Defense Exports: ₹21,083 crore (FY 2023-24)
- Defense Export Target 2029: ₹50,000 crore
- Defense Imports: $13 billion (2024)
- Indigenous Content: 68% (target 70% by 2027)
- Make in India Defense Projects: 100+
- Defense Manufacturing Units: 350+ (public + private)
- Ordnance Factory Boards: 7 DPSUs
- Defense PSUs: Hindustan Aeronautics (HAL), BEL, BDL, BEML, etc.
- Private Defense Companies: 450+
- Defense Corridors: 2 (UP, Tamil Nadu)
- Defense Industrial Parks: 6 planned
- iDEX Startups: 300+
- Defense Startups Funding: ₹500 crore
- FDI in Defense: 74% (49% automatic route)
- Aircraft Manufacturing: HAL (capacity 24 aircraft/year)
- LCA Tejas: 180 on order
- LCA Tejas Cost: ₹309 crore per unit
- LCA Tejas Mk2: Under development
- AMCA (5th Gen Fighter): Development phase
- Rafale Fighters: 36 inducted
- Su-30MKI: 272 operational
- MiG-29: 69 operational
- Jaguar: 139 operational
- HAL Dhruv Helicopters: 325+ produced
- Apache Helicopters: 22 (28 on order)
- Chinook Helicopters: 15 operational
- Naval Ships Under Construction: 64
- Aircraft Carrier: INS Vikrant (commissioned 2022)
- Submarines Operational: 16
- Scorpene Submarines: 6 (Kalvari-class)
- Nuclear Submarines: 2 (INS Arihant, INS Arighat)
- Destroyers: 11
- Frigates: 14
- Corvettes: 23
- Brahmos Missiles: Operational (supersonic cruise)
- Agni-V ICBM: Operational (5,000+ km range)
- Prithvi Missiles: Operational (tactical)
- Akash Missile System: Operational (air defense)
- Dhanush Artillery: 114 inducted
- K-9 Vajra Howitzer: 100 inducted
- Arjun Tank: 124 operational
- T-90 Tanks: 1,000+
- T-72 Tanks: 2,400+
- INS Vikramaditya: Aircraft carrier operational
- Defense R&D Labs: 52 (DRDO)
- Defense Testing Ranges: 5 major
- Defense Personnel: 14.5 lakh (active)
- Army: 12.37 lakh
- Navy: 67,000
- Air Force: 1.40 lakh
- Paramilitary Forces: 10 lakh+
- Defense Reserves: 11.55 lakh
- Defense Pension: ₹1.41 lakh crore
- War Widows Pension: ₹4,200 crore
- Ex-Servicemen Welfare: ₹1.5 lakh crore

## CYBERSECURITY
- Cybersecurity Market Size: $3.5 billion (2024)
- Cybersecurity Growth Rate: 15% YoY
- Managed Security Services: $1.2 billion
- Security Software: $1 billion
- Security Hardware: $800 million
- Security Services: $500 million
- Cyber Incidents Reported: 13.9 lakh (2024)
- Financial Sector Incidents: 35%
- IT Sector Incidents: 18%
- Government Sector Incidents: 12%
- Ransomware Attacks: 15,000+ (2024)
- Phishing Attacks: 4.5 lakh reported
- Data Breaches: 850 major incidents
- Average Cost of Data Breach: $2.18 million
- Identity Theft Cases: 95,000+
- Cyber Fraud Losses: ₹1,750 crore (2024)
- UPI Fraud: ₹850 crore
- Credit/Debit Card Fraud: ₹400 crore
- Internet Banking Fraud: ₹500 crore
- Indian Computer Emergency Response Team (CERT-In): Central agency
- National Cyber Security Coordinator: Coordination body
- Cyber Crime Police Stations: 1,500+
- National Cyber Crime Reporting Portal: 25 lakh complaints
- Cybersecurity Professionals: 1 lakh
- Cybersecurity Skill Gap: 3 lakh positions vacant
- Cybersecurity Training Programs: 150+
- Cybersecurity Startups: 250+
- Bug Bounty Programs: 50+ companies
- Average Bug Bounty Reward: ₹50,000-₹5 lakh
- Penetration Testing Market: ₹800 crore
- Ethical Hackers: 25,000+
- SOC (Security Operations Center): 200+ operational
- Cybersecurity Budget (Government): ₹5,000 crore
- Data Protection Bill: Under legislative process
- CERT-In Empaneled Auditors: 150+
- ISO 27001 Certified Organizations: 5,000+
- Cyber Insurance Market: ₹250 crore
- Cyber Insurance Growth: 40% YoY
- Two-Factor Authentication Adoption: 45% of users
- Biometric Authentication Users: 85 crore (Aadhaar)
- VPN Users: 6 crore
- Antivirus Software Market: ₹1,200 crore
- Firewall Market: ₹1,500 crore
- Endpoint Security: ₹900 crore
- Cloud Security: ₹1,100 crore
- IoT Security: ₹400 crore
- Mobile Security: ₹350 crore
- OT/ICS Security: ₹300 crore
- Target by 2030: $20 billion

## ARTIFICIAL INTELLIGENCE & MACHINE LEARNING
- AI Market Size: $7.8 billion (2024)
- AI Growth Rate: 25% YoY
- AI Startups: 5,000+
- AI Unicorns: 8
- AI in BFSI: $2.5 billion
- AI in Healthcare: $1.2 billion
- AI in Retail: $1 billion
- AI in Manufacturing: $900 million
- AI in Agriculture: $600 million
- AI in Education: $500 million
- AI in Automotive: $450 million
- AI in Telecom: $350 million
- AI Investment: $4.5 billion (2024)
- Government AI Budget: ₹7,500 crore
- National AI Portal: 450+ resources
- Center of Excellence for AI: 4 operational
- AI Research Papers: 12,000+ published annually
- AI Patents Filed: 3,500+ (2024)
- AI Professionals: 4.5 lakh
- AI Skill Programs: 250+
- AI Companies: 1,200+
- Conversational AI Market: ₹800 crore
- Chatbot Adoption: 45% of enterprises
- Computer Vision Market: ₹1,200 crore
- Natural Language Processing: ₹950 crore
- Predictive Analytics: ₹1,500 crore
- AI in Customer Service: 60% of large companies
- AI in Fraud Detection: ₹450 crore
- AI in Credit Scoring: 80% of fintech
- Facial Recognition Systems: 1,200+ deployed
- AI in Radiology: 250+ hospitals
- AI Drug Discovery Startups: 25+
- AI Chips Import: $800 million
- AI Server Market: ₹2,500 crore
- GPU Servers: 15,000+ deployed
- AI Cloud Services: ₹3,500 crore
- MLOps Platform Market: ₹400 crore
- Data Labeling Market: ₹600 crore
- AI Ethics Framework: Under development
- AI Regulation: Draft guidelines released
- Responsible AI Adoption: 35% of AI users
- AI Transparency Index: Developing
- Deepfake Detection Tools: 15 deployed
- AI in Governance: 100+ projects
- DigiYatra (Face Recognition): 24 airports
- AI in Agriculture (Kisan AI): 50 lakh farmers
- AI Chatbots (Government): 150+ departments
- Target by 2030: $50 billion

## BLOCKCHAIN & WEB3
- Blockchain Market Size: $1.5 billion (2024)
- Blockchain Startups: 1,000+
- Blockchain Developers: 75,000+
- Cryptocurrency Users: 2.5 crore (despite regulatory uncertainty)
- Cryptocurrency Transaction Volume: $18 billion (2024)
- NFT Market: $120 million
- DeFi Users: 8 lakh
- Blockchain in BFSI: $600 million
- Blockchain in Supply Chain: $350 million
- Blockchain in Healthcare: $180 million
- Blockchain in Government: $220 million
- Blockchain Patents Filed: 850+ (2024)
- Blockchain Consortiums: 15+
- Banks Using Blockchain: 35+
- Trade Finance on Blockchain: ₹2,500 crore
- Land Registry on Blockchain: 8 states (pilot)
- Education Certificates on Blockchain: 150+ institutions
- Blockchain Identity Management: 5 lakh users
- Supply Chain Tracking: 200+ companies
- Food Traceability: 50+ FMCG companies
- Pharmaceutical Track & Trace: 80+ companies
- Diamond Tracking: 25+ companies
- Remittance via Blockchain: $2 billion
- Cross-Border Payments: $8 billion
- Smart Contracts Deployed: 50,000+
- Enterprise Blockchain Platforms: 25+
- Hyperledger Projects: 45+
- Private Blockchain Networks: 120+
- Central Bank Digital Currency (CBDC): Pilot phase
- Digital Rupee Users: 50 lakh (pilot)
- Digital Rupee Transactions: 5 crore (pilot cumulative)
- Digital Rupee Merchants: 5 lakh
- Blockchain Training Programs: 100+
- Blockchain Research Centers: 25+ universities
- Blockchain Investment: $800 million (2024)
- Web3 Startups: 600+
- Metaverse Startups: 150+
- Metaverse Market: $800 million
- Virtual Real Estate: $50 million
- Gaming Metaverse Users: 25 lakh
- Decentralized Apps (dApps): 500+
- DAO (Decentralized Autonomous Org): 80+
- Blockchain Jobs: 50,000+
- Blockchain Skill Demand: 180% increase YoY
- Target by 2030: $10 billion

## QUANTUM COMPUTING
- Quantum Computing Market: $250 million (2024)
- National Quantum Mission Budget: ₹6,003 crore (2023-2031)
- Quantum Research Centers: 8
- Quantum Startups: 25+
- Quantum Researchers: 2,500+
- Quantum Patents Filed: 150+
- Quantum Computing Labs: 15+ (IITs, IISc, TIFR)
- Quantum Simulators: 12 operational
- Qubit Development: 6-10 qubit systems (research phase)
- Quantum Communication: Delhi-Prayagraj link (100 km pilot)
- Quantum Key Distribution: 3 deployments
- Quantum Cryptography Research: 8 projects
- Quantum Sensors Development: 12 projects
- Quantum Materials Research: 20+ labs
- Quantum Computing Collaborations: IBM, AWS, Microsoft
- Quantum Cloud Access: 500+ researchers
- Quantum Algorithms Developed: 80+
- Quantum Machine Learning Projects: 35+
- Quantum Chemistry Applications: 15 projects
- Quantum Optimization Use Cases: 25+
- Quantum Training Programs: 20+
- Quantum PhD Students: 350+
- Quantum Postdocs: 120+
- Quantum Computing Investment: ₹1,200 crore (private + public)
- Target Quantum Computer: 50+ qubit by 2026
- Target Quantum Computer: 1000+ qubit by 2030
- Quantum Satellite Communication: Under development
- Quantum Random Number Generators: 5 deployed
- Quantum Internet Backbone: Planned (2030)
- Quantum Safe Cryptography: 12 institutions developing
- Quantum Employment: 3,000+ (target 50,000 by 2030)
- International Quantum Partnerships: 15 countries
- Quantum Computing as a Service: 3 providers
- Target by 2030: $2 billion market

## BIOTECHNOLOGY
- Biotech Industry Size: $80 billion (2024)
- Bio-pharma: $50 billion (62.5%)
- Bio-agriculture: $12 billion (15%)
- Bio-services: $10 billion (12.5%)
- Bio-industrial: $5 billion (6.25%)
- Bio-informatics: $3 billion (3.75%)
- Biotech Companies: 5,000+
- Biotech Startups: 3,500+
- Biotech Unicorns: 6
- Vaccine Production: 3 billion doses per year
- COVID-19 Vaccine Production: 220 crore doses (cumulative)
- Covaxin Doses: 33 crore
- Covishield Doses: 175 crore
- Generic Drug Production: 60,000 brands
- Biosimilars Market: $4 billion
- Insulin Production: 40 million vials per year
- Monoclonal Antibodies: $1.2 billion market
- Stem Cell Research Centers: 45+
- Gene Therapy Trials: 25+ ongoing
- CRISPR Research Projects: 80+
- Genomics Market: $1.8 billion
- DNA Sequencing: 50,000+ samples per year
- Bio-repositories: 35+
- Seed Banks: 12 major
- Biofertilizer Production: 1.2 lakh MT
- Biopesticides Market: ₹1,500 crore
- Bio-ethanol Production: 500 crore liters
- Industrial Enzymes: ₹2,500 crore
- Bioplastics Production: 80,000 MT
- Bioinformatics Companies: 150+
- Clinical Research Organizations: 400+
- Clinical Trials: 4,500+ ongoing
- Contract Research & Manufacturing: $8 billion
- Biotech R&D Investment: ₹25,000 crore
- National Biopharma Mission: ₹1,500 crore
- Biotechnology Parks: 18
- Biotech Incubators: 75+
- BioNEST Centers: 50+
- DBT-Supported Institutions: 200+
- Biotech PhDs: 8,000+ annually
- Biotech Employment: 3.5 lakh
- Biotech Exports: $28 billion
- Target by 2030: $150 billion
- Gene Banks: 10 (crops, livestock, microbes)
- Tissue Culture Labs: 500+
- Bio-safety Level 3 Labs: 25+
- Bio-safety Level 4 Labs: 2

## NANOTECHNOLOGY
- Nanotech Market Size: $4.5 billion (2024)
- Nanomaterials: $2 billion
- Nano-medicine: $1.2 billion
- Nano-electronics: $800 million
- Nano-coatings: $500 million
- Nanotech Startups: 180+
- Nanotech Companies: 350+
- Nano Research Centers: 60+
- Nanoscience & Technology Initiative: ₹1,800 crore
- Nanotech Patents Filed: 2,500+ (cumulative)
- Nanotech Researchers: 15,000+
- Nanotech PhD Students: 2,000+
- Carbon Nanotube Production: 50 MT per year
- Graphene Research Projects: 120+
- Quantum Dots Market: ₹250 crore
- Nano-silver Applications: ₹400 crore
- Nano-fertilizers: 5,000 MT production
- Nano-pesticides: Field trials in 15 states
- Nano-sensors Market: ₹800 crore
- Drug Delivery Systems: 25+ under development
- Nano-cancer Therapy: 8 clinical trials
- Nano-coatings (Industrial): ₹1,200 crore
- Self-cleaning Coatings: 50+ applications
- Anti-microbial Coatings: Healthcare, textiles
- Nano-composites: ₹1,500 crore
- Nano-textiles: ₹600 crore
- Water Purification (Nano): 200+ installations
- Nano-filtration Membranes: ₹350 crore
- Electronics (Nano): Chip manufacturing aids
- Nano-photonics: 30+ research projects
- Nano-characterization Facilities: 40+
- TEM/SEM Labs: 150+
- Atomic Force Microscopes: 80+ operational
- Nanotech Collaborations: 25+ countries
- Nanotech Publications: 8,000+ papers annually
- Nanotech Training Programs: 50+
- Nanotech Investment: ₹3,500 crore
- Nano Safety Guidelines: Being developed
- Target by 2030: $15 billion

## ROBOTICS & AUTOMATION
- Robotics Market Size: $2.8 billion (2024)
- Industrial Robotics: $1.5 billion
- Service Robotics: $800 million
- Collaborative Robots (Cobots): $350 million
- Autonomous Mobile Robots: $150 million
- Industrial Robot Installations: 4,500 units per year
- Robot Density: 7 robots per 10,000 employees (manufacturing)
- Global Average Robot Density: 141 per 10,000
- Automotive Sector Robots: 2,100 units (47%)
- Electronics Sector Robots: 900 units (20%)
- Metal & Machinery Robots: 450 units (10%)
- Food & Beverage Robots: 350 units (8%)
- Pharmaceutical Robots: 300 units (7%)
- Robotics Companies: 250+
- Robotics Startups: 180+
- Collaborative Robot Sales: 800 units per year
- Warehouse Robotics: 1,200+ deployed
- Agricultural Robots: 150+ (pilot/commercial)
- Medical Robots: 80+ (surgical, rehab)
- Surgical Robot Installations: 25+
- Robotic Process Automation (RPA): $1.2 billion
- RPA Bots Deployed: 1.5 lakh
- RPA Adoption: 55% of large enterprises
- AI-Powered Robots: 450+ deployed
- Delivery Robots (Pilot): 200+ in testing
- Drones (Commercial): 15,000+ registered
- Drone Deliveries: 2 lakh (pilot phase)
- Inspection Drones: 5,000+ (infrastructure, agriculture)
- Agriculture Drones: 8,000+ (spraying, monitoring)
- Drone Manufacturing Units: 120+
- PLI Scheme (Drones): ₹120 crore
- Robotics Labs (Educational): 2,500+
- Robotics Clubs (Schools): 5,000+
- Robotics Competitions: 150+ annually
- Robotics Engineers: 25,000+
- Automation Market: $12 billion
- Factory Automation: $7 billion
- Process Automation: $3 billion
- Building Automation: $2 billion
- PLC Market: ₹4,500 crore
- SCADA Systems: ₹2,800 crore
- HMI Market: ₹1,500 crore
- Industrial IoT: $4.5 billion
- Automation Employment: 8 lakh
- Robotics Training Centers: 80+
- Robotics R&D Investment: ₹1,500 crore
- Target by 2030: $12 billion robotics market

## INTERNET OF THINGS (IoT)
- IoT Market Size: $9.5 billion (2024)
- IoT Growth Rate: 28% YoY
- Connected IoT Devices: 3.5 billion
- Consumer IoT: $4.2 billion
- Industrial IoT (IIoT): $3.8 billion
- Smart Cities IoT: $1.2 billion
- Agriculture IoT: $300 million
- IoT Companies: 800+
- IoT Startups: 600+
- Smart Home Devices: 5 crore units installed
- Smart Speakers: 2 crore units
- Smart Lighting: 1.5 crore units
- Smart Security Systems: 80 lakh units
- Smart Appliances: 70 lakh units
- Wearable Devices: 12 crore users
- Fitness Trackers: 5 crore
- Smartwatches: 7 crore
- Smart Agriculture Sensors: 8 lakh deployed
- Precision Farming IoT: 15 lakh hectares
- Livestock Monitoring: 5 lakh animals
- Soil Moisture Sensors: 12 lakh units
- Weather Stations (IoT): 5,000+
- Smart Meters (Electricity): 3 crore installed
- Smart Water Meters: 50 lakh
- Smart Gas Meters: 10 lakh
- Connected Vehicles: 1.5 crore
- Fleet Management Systems: 50 lakh vehicles
- Telematics Market: ₹4,500 crore
- Smart City Projects: 100 cities
- Smart Street Lights: 25 lakh installed
- Smart Parking Systems: 150+ deployments
- Waste Management IoT: 80 cities
- Smart Traffic Management: 50+ cities
- Environmental Monitoring: 200+ deployments
- Industrial Asset Tracking: 10 lakh assets
- Predictive Maintenance: 8,000+ factories
- Supply Chain IoT: 5,000+ companies
- Cold Chain Monitoring: 2,500+ facilities
- Energy Management Systems: 15,000+ buildings
- Building Automation: 25,000+ commercial buildings
- Healthcare IoT: $600 million
- Remote Patient Monitoring: 12 lakh patients
- Connected Medical Devices: 8 lakh units
- Hospital Asset Tracking: 800+ hospitals
- IoT Gateways Deployed: 15 lakh
- IoT SIM Connections: 45 crore
- 5G IoT Connections: 2 crore
- NB-IoT Deployments: 50+ cities
- LoRaWAN Networks: 30+ deployments
- IoT Platform Market: ₹2,500 crore
- IoT Security Market: ₹1,200 crore
- Edge Computing for IoT: ₹1,800 crore
- IoT Data Analytics: ₹2,200 crore
- IoT Employment: 2.5 lakh
- IoT Training Programs: 200+
- Target by 2030: $35 billion

## AUGMENTED & VIRTUAL REALITY
- AR/VR Market Size: $1.8 billion (2024)
- AR Market: $1.1 billion
- VR Market: $700 million
- AR/VR Startups: 250+
- AR/VR Companies: 400+
- VR Headsets Sold: 4 lakh units (2024)
- AR Smart Glasses: 50,000 units
- Mixed Reality Devices: 15,000 units
- AR/VR in Gaming: $600 million
- AR/VR in Education: $350 million
- AR/VR in Healthcare: $250 million
- AR/VR in Real Estate: $180 million
- AR/VR in Retail: $150 million
- AR/VR in Manufacturing: $120 million
- AR/VR in Training: $100 million
- AR/VR in Tourism: $50 million
- VR Gaming Arcades: 500+
- VR Experience Centers: 300+
- AR Try-On Apps: 150+
- Virtual Showrooms: 1,200+
- 360° Virtual Tours: 5,000+ properties
- VR Training Simulations: 200+ enterprises
- Medical VR Simulations: 80+ institutions
- Surgical Training VR: 35+ medical colleges
- VR Therapy Sessions: 15,000+ (mental health)
- AR Navigation Apps: 8 crore users
- AR Filters (Social Media): 50 crore users
- AR Marketing Campaigns: 2,500+
- Industrial AR Maintenance: 350+ factories
- AR Remote Assistance: 500+ deployments
- 3D Modeling Studios: 800+
- Motion Capture Studios: 50+
- VR Content Creators: 5,000+
- AR/VR Developers: 15,000+
- AR/VR Investment: ₹1,800 crore
- AR/VR Labs (Educational): 150+
- Target by 2030: $10 billion

## 3D PRINTING & ADDITIVE MANUFACTURING
- 3D Printing Market: $1.2 billion (2024)
- Industrial 3D Printing: $700 million
- Desktop 3D Printing: $300 million
- 3D Printing Services: $200 million
- 3D Printers Installed: 15,000+ units
- Industrial 3D Printers: 2,500 units
- Desktop 3D Printers: 12,500 units
- 3D Printing Companies: 200+
- 3D Printing Startups: 150+
- 3D Printing Service Bureaus: 450+
- Aerospace Applications: $250 million
- Automotive 3D Printing: $200 million
- Healthcare 3D Printing: $180 million
- Dental 3D Printing: $120 million
- Consumer Goods: $100 million
- Architecture & Construction: $90 million
- Education 3D Printing: $80 million
- Jewelry 3D Printing: $60 million
- 3D Printed Prosthetics: 15,000+ units
- 3D Printed Orthotics: 25,000+ units
- 3D Printed Dental Models: 1.2 lakh units
- 3D Printed Hearing Aids: 8,000 units
- Rapid Prototyping: 80,000+ projects annually
- Metal 3D Printing: $180 million
- Polymer 3D Printing: $650 million
- Ceramic 3D Printing: $35 million
- Bio-printing Research: 25+ projects
- Tissue Engineering: 8 institutions
- 3D Printed Construction: 5 demo houses
- 3D Printing Materials Market: $450 million
- Filament Production: 500 MT per year
- Resin Production: 200 MT per year
- Metal Powder Production: 50 MT per year
- 3D Scanning Market: $280 million
- 3D Scanners Deployed: 3,500+ units
- Reverse Engineering Applications: 5,000+ projects
- Quality Control Scanning: 2,000+ factories
- 3D Design Software Market: $350 million
- CAD Users (3D Printing): 80,000+
- 3D Printing Labs (Educational): 1,200+
- 3D Printing Training Centers: 180+
- 3D Printing Engineers: 12,000+
- Spare Parts On-Demand: 500+ companies
- Mass Customization: 300+ brands
- 3D Printing Patents Filed: 450+ (2024)
- 3D Printing Investment: ₹1,500 crore
- Target by 2030: $5 billion

## SEMICONDUCTORS & ELECTRONICS MANUFACTURING
- Semiconductor Market (Consumption): $32 billion (2024)
- Electronics Manufacturing: $115 billion
- Domestic Production: $101 billion
- Electronics Imports: $75 billion
- Electronics Exports: $29 billion
- Trade Deficit: $46 billion
- Mobile Phone Production: 33 crore units
- Mobile Phone Exports: $15 billion
- Mobile Phone Value: ₹4.1 lakh crore (production)
- TV Production: 2.2 crore units
- LED Production: 3.5 crore units
- Laptop/Tablet Assembly: 50 lakh units
- Wearables Production: 1.2 crore units
- Semiconductor Design Market: $5 billion
- Chip Design Companies: 100+
- Fabless Semiconductor Companies: 2,000+ engineers
- VLSI Design Centers: 200+
- Semiconductor Fabrication Plants: 0 (under development)
- Approved Fab Projects: 3 (Micron, Tata, CG Power)
- Micron Plant Investment: $2.75 billion (Gujarat)
- Tata Semiconductor Plant: $11 billion (Gujarat)
- CG Power Plant: $5.8 billion (Gujarat)
- OSAT (Assembly, Test) Facilities: 2 planned
- Total Semiconductor Investment: ₹1.5 lakh crore
- PLI Scheme (Electronics): ₹73,000 crore
- PLI Scheme (IT Hardware): ₹17,000 crore
- PLI Scheme (Telecom): ₹12,195 crore
- PLI Beneficiaries: 45+ companies
- Apple Suppliers in India: 14 companies
- Samsung Manufacturing: 3 plants
- Foxconn Facilities: 5 units
- Electronics Manufacturing Clusters: 25+
- EMC (Electronic Manufacturing Clusters): 20
- ESDMs (Electronic System Design & Manufacturing): 15,000+ units
- PCB Manufacturing: $4.5 billion
- PCB Production: 350 million sq meters
- Components Manufacturing: $12 billion
- Passive Components: $3.5 billion
- Active Components: $2 billion
- Electro-mechanical: $6.5 billion
- Display Panel Manufacturing: Under development
- Battery Cell Manufacturing: 50 GWh (planned by 2030)
- Charger Production: 5 crore units
- Power Adapter Production: 8 crore units
- Semiconductor Design Professionals: 20,000+
- Electronics Engineers: 5 lakh+
- Electronics Employment: 25 lakh
- R&D Centers: 1,200+
- Patents (Electronics): 8,500+ annually
- Electronics Training Institutes: 500+
- Target Production 2030: $300 billion
- Target Exports 2030: $120 billion

## CHEMICALS & PETROCHEMICALS
- Chemical Industry Size: $220 billion (2024)
- Petrochemicals: $90 billion (41%)
- Specialty Chemicals: $45 billion (20.5%)
- Agrochemicals: $8 billion (3.6%)
- Dyes & Pigments: $7 billion (3.2%)
- Paints & Coatings: $10 billion (4.5%)
- Fertilizers: $25 billion (11.4%)
- Polymers: $35 billion (15.9%)
- Chemical Production: 280 million MT
- Petrochemical Production: 35 million MT
- Polymer Production: 25 million MT
- Polyethylene (PE): 8 million MT
- Polypropylene (PP): 7 million MT
- PVC: 4 million MT
- PET: 3 million MT
- Ethylene Production: 8.5 million MT
- Propylene Production: 6 million MT
- Benzene Production: 2.5 million MT
- Methanol Production: 3 million MT
- Caustic Soda Production: 4.5 million MT
- Soda Ash Production: 4 million MT
- Sulfuric Acid Production: 8 million MT
- Fertilizer Production: 55 million MT (nutrients)
- Urea Production: 26 million MT
- DAP Production: 5 million MT
- Pesticides Production: 2.8 lakh MT (technical grade)
- Dyes Production: 2.3 lakh MT
- Pigments Production: 3.5 lakh MT
- Paint Production: 8 billion liters
- Chemical Companies: 5,000+
- Large Chemical Companies: 250+
- SME Chemical Units: 4,750+
- Top Chemical Company: Reliance Industries (₹6 lakh crore revenue)
- 2nd: Indian Oil Corporation (₹7.9 lakh crore)
- 3rd: BPCL (₹3.8 lakh crore)
- 4th: HPCL (₹3.9 lakh crore)
- Refineries: 23 (254 MMT capacity)
- Petrochemical Complexes: 35+
- Chemical Parks: 15+
- Petroleum, Chemicals & Petrochemicals Investment Regions (PCPIRs): 4
- Chemical Exports: $45 billion
- Chemical Imports: $55 billion
- Specialty Chemicals Exports: $18 billion
- Agrochemicals Exports: $4.5 billion
- Dyes & Pigments Exports: $3.2 billion
- Plastic Exports: $8 billion
- R&D Investment: ₹12,000 crore
- Chemical Patents: 3,500+ annually
- Chemical Engineers: 3 lakh+
- Chemical Employment: 20 lakh (direct)
- Chemical Safety Regulations: MSIHC Rules
- Chemical Clusters: 50+
- Target by 2030: $450 billion

## PHARMACEUTICALS & HEALTHCARE
- Pharmaceutical Market Size: $50 billion (2024)
- Domestic Market: $32 billion
- Export Market: $27 billion
- Total Pharma Revenue: $50 billion (some overlap in manufacturing)
- Generic Drugs: 70% of market
- Branded Generics: 25%
- Patented Drugs: 5%
- Formulations: $42 billion
- Bulk Drugs/APIs: $8 billion
- Pharmaceutical Companies: 3,000+
- Licensed Manufacturing Units: 10,500+
- Pharma Plants (WHO-GMP): 2,000+
- US-FDA Approved Plants: 750+
- USFDA Inspections Passed: 90% compliance
- Top Pharma Company: Sun Pharma (₹42,000 crore revenue)
- 2nd: Cipla (₹23,500 crore)
- 3rd: Dr. Reddy's (₹25,000 crore)
- 4th: Lupin (₹19,000 crore)
- 5th: Aurobindo Pharma (₹27,000 crore)
- Generic Drug Exports: $22 billion
- Formulation Exports: $20 billion
- Bulk Drug Exports: $7 billion
- Top Export Destination: USA (31%)
- 2nd: UK (4%)
- 3rd: South Africa (4%)
- Vaccine Production: 3 billion doses per year
- Global Vaccine Supply: 60% from India
- API Production: 3 million MT
- API Import Dependency: 65-70% (China)
- PLI Scheme (Pharma): ₹15,000 crore
- Bulk Drug Parks: 3 (Gujarat, Himachal, Andhra)
- Medical Devices Market: $11 billion
- Medical Device Manufacturing: $6 billion
- Medical Device Imports: $8 billion
- Diagnostics Market: $12 billion
- In-vitro Diagnostics: $4.5 billion
- Imaging Equipment: $2.5 billion
- Diagnostic Labs: 1.5 lakh
- Path Labs: 5,000+ centers
- Dr. Lal PathLabs: 3,500+ collection centers
- Thyrocare: 2,000+ centers
- Hospital Beds: 19 lakh (1.3 per 1000 population)
- Government Hospital Beds: 7.13 lakh
- Private Hospital Beds: 11.9 lakh
- Total Hospitals: 70,000+
- Government Hospitals: 25,778
- Private Hospitals: 43,000+
- Super-specialty Hospitals: 750+
- Multi-specialty Hospitals: 3,500+
- Medical Colleges: 706
- MBBS Seats: 1.08 lakh per year
- PG Medical Seats: 72,000+
- Doctors: 13.8 lakh (registered)
- Doctor-Population Ratio: 1:834
- Nurses: 35 lakh (registered)
- Nurse-Population Ratio: 2.06 per 1000
- Pharmacists: 12 lakh (registered)
- AYUSH Practitioners: 8 lakh
- Ayurveda Market: $18 billion
- Ayurvedic Companies: 8,000+
- Patanjali Revenue: ₹30,000 crore
- Dabur Revenue: ₹12,500 crore (healthcare segment)
- Medical Tourism: $9 billion (2024)
- Medical Tourists: 7 lakh+ annually
- Health Insurance: 55 crore beneficiaries
- Ayushman Bharat: 12 crore families (50 crore beneficiaries)
- Health & Wellness Centers: 1.65 lakh
- Jan Aushadhi Kendras: 10,500+
- Generic Medicine Savings: ₹20,000 crore
- Healthcare Employment: 60 lakh
- Target Pharma by 2030: $120 billion
- Target Medical Devices 2030: $50 billion

## TEXTILES & APPAREL
- Textile Industry Size: $165 billion (2024)
- Domestic Market: $105 billion
- Textile Exports: $36 billion
- Cotton Textiles: $80 billion (48.5%)
- Man-made Textiles: $50 billion (30.3%)
- Silk Textiles: $5 billion (3%)
- Wool Textiles: $3 billion (1.8%)
- Jute & Other Fibers: $2 billion (1.2%)
- Technical Textiles: $25 billion (15.2%)
- Spinning Mills: 1,900+
- Weaving Units: 4.5 lakh (handloom + powerloom)
- Handlooms: 31 lakh
- Powerlooms: 2.4 lakh
- Textile Processing Units: 6,500+
- Garment Manufacturing Units: 45,000+
- Textile Machinery: 3,500 manufacturers
- Cotton Production: 344 lakh bales (170 kg each)
- Cotton Consumption: 310 lakh bales
- Cotton Exports: 25 lakh bales
- Man-made Fiber Production: 16 lakh MT
- Polyester Production: 13.5 lakh MT
- Viscose Production: 2.5 lakh MT
- Yarn Production: 58 lakh MT
- Fabric Production: 120 billion sq meters
- Garment Production: 15 billion pieces
- Top Textile Company: Welspun (₹10,000 crore revenue)
- 2nd: Arvind Limited (₹8,500 crore)
- 3rd: Vardhman Textiles (₹11,500 crore)
- 4th: Trident Group (₹7,500 crore)
- Apparel Exports: $16 billion
- Home Textiles Exports: $6.5 billion
- Cotton Yarn Exports: $3.5 billion
- Fabric Exports: $5 billion
- Made-ups Exports: $5 billion
- Top Export Market: USA (27%)
- 2nd: EU (18%)
- 3rd: UAE (9%)
- 4th: Bangladesh (6%)
- Technical Textiles Production: 18 lakh MT
- Medical Textiles: ₹10,000 crore
- Geotextiles: ₹3,500 crore
- Protective Textiles: ₹2,800 crore
- PLI Scheme (Textiles): ₹10,683 crore
- Textile Parks: 68 operational
- Mega Integrated Textile Parks: 18
- Apparel Parks: 12
- Silk Production: 38,000 MT
- Mulberry Silk: 32,000 MT (84%)
- Tasar Silk: 3,500 MT
- Eri Silk: 2,200 MT
- Muga Silk: 200 MT
- Silk Exports: $220 million
- Wool Production: 40 million kg
- Jute Production: 95 lakh bales (180 kg each)
- Jute Mills: 70+
- Carpet Industry: ₹12,000 crore
- Handicraft Textiles: ₹35,000 crore
- Textile Employment: 4.5 crore
- Handloom Employment: 35 lakh
- Powerloom Employment: 45 lakh
- Target by 2030: $350 billion

## GEMS & JEWELRY
- Gems & Jewelry Market: $75 billion (2024)
- Domestic Consumption: $55 billion
- Gems & Jewelry Exports: $25 billion
- Gold Jewelry: $45 billion (60%)
- Diamond Jewelry: $18 billion (24%)
- Gemstone Jewelry: $7 billion (9.3%)
- Silver Jewelry: $5 billion (6.7%)
- Gold Consumption: 800 tonnes per year
- Gold Imports: 1,000 tonnes
- Gold Reserves: 800+ tonnes (RBI)
- Diamond Imports (Rough): $16 billion
- Diamond Exports (Cut & Polished): $20 billion
- Diamond Processing: 90% of world's diamonds
- Diamond Units: 6,000+
- Diamond Workers: 10 lakh
- Surat Diamond Hub: 6,000+ units (90% of cutting)
- Mumbai Jewelry Hub: 2,500+ manufacturers
- Jaipur Gemstone Hub: 1,500+ units
- Top Jewelry Brand: Titan (₹40,000 crore revenue)
- 2nd: Kalyan Jewellers (₹18,000 crore)
- 3rd: Malabar Gold (₹45,000 crore)
- 4th: Tanishq (Titan subsidiary)
- 5th: PC Jewellers (₹3,500 crore)
- Hallmarking Centers: 1,450+
- BIS Hallmarked Jewelry: 85% compliance
- Gold Monetization: 50 tonnes (cumulative)
- Sovereign Gold Bonds: ₹65,000 crore issued
- Digital Gold Users: 80 lakh
- Lab-Grown Diamonds: $1.5 billion market
- Lab-Grown Diamond Units: 1,200+
- Gemstone Cutting Centers: 450+
- Colored Gemstones: $800 million
- Pearls Market: $300 million
- Artificial Jewelry: $8 billion
- Fashion Jewelry Exports: $1.8 billion
- Jewelry Design Institutes: 100+
- Jewelry Artisans: 50 lakh
- GIA Certified Gemologists: 15,000+
- CAD/CAM Jewelry Design: 2,000+ units
- 3D Printing (Jewelry): 500+ units
- E-commerce Jewelry: $4.5 billion
- BlueStone Online: ₹600 crore revenue
- CaratLane (Tanishq): ₹2,500 crore
- Target by 2030: $100 billion

## TOURISM & HOSPITALITY
- Tourism Industry Size: $230 billion (2024)
- Tourism GDP Contribution: 6.9%
- Domestic Tourism: $210 billion
- International Tourism: $20 billion
- Domestic Tourist Visits: 240 crore (2024)
- Foreign Tourist Arrivals: 1.08 crore (2024)
- Medical Tourism: $9 billion
- Foreign Exchange Earnings: ₹2.1 lakh crore
- Top Source Market: Bangladesh (22%)
- 2nd: USA (16%)
- 3rd: UK (8%)
- 4th: Canada (4%)
- 5th: Australia (3%)
- Hotels: 1.5 lakh properties
- Hotel Rooms: 20 lakh
- 5-Star Hotels: 1,200+
- 4-Star Hotels: 2,500+
- 3-Star Hotels: 5,000+
- Budget Hotels: 50,000+
- OYO Rooms: 1.3 lakh properties
- Airbnb Listings: 1.5 lakh
- Tourism Employment: 4 crore
- Direct Employment: 2.6 crore
- Indirect Employment: 1.4 crore
- Travel Agents: 75,000+
- Tour Operators: 15,000+
- Online Travel Market: $18 billion
- MakeMyTrip Revenue: ₹4,500 crore
- Yatra Revenue: ₹1,200 crore
- Goibibo Revenue: ₹2,800 crore
- EaseMyTrip Revenue: ₹900 crore
- UNESCO World Heritage Sites: 42
- Cultural Sites: 34
- Natural Sites: 8
- Wildlife Sanctuaries: 565
- National Parks: 106
- Tiger Reserves: 54
- Beaches: 7,500 km coastline
- Hill Stations: 100+
- Adventure Tourism: $2.5 billion
- Eco-Tourism: $1.8 billion
- Spiritual Tourism: $40 billion
- Pilgrims Annually: 120 crore
- Kumbh Mela 2019: 24 crore visitors
- Tirumala Temple: 10 crore visitors/year
- Vaishno Devi: 1 crore visitors/year
- Golden Temple: 1.5 lakh visitors/day
- Taj Mahal: 70 lakh visitors/year
- MICE Tourism: $3 billion
- Convention Centers: 450+
- Cruise Tourism: 5 lakh passengers
- Cruise Terminals: 12
- Heritage Hotels: 350+
- Homestays: 45,000+
- Caravan Tourism Parks: 50+
- Target by 2030: $450 billion
- Target Foreign Tourists 2030: 3 crore

## MEDIA & ENTERTAINMENT
- Media & Entertainment Market: $28 billion (2024)
- Digital Media: $12 billion (42.9%)
- Television: $9 billion (32.1%)
- Films: $3.5 billion (12.5%)
- Print Media: $2.5 billion (8.9%)
- Radio: $300 million (1.1%)
- Music: $250 million (0.9%)
- Out-of-Home: $450 million (1.6%)
- TV Households: 21 crore
- Cable/DTH Subscribers: 17 crore
- Digital Cable Homes: 10 crore
- DTH Subscribers: 7 crore
- DD Free Dish: 4.5 crore
- TV Channels: 900+
- News Channels: 400+
- Entertainment Channels: 350+
- Movies Channels: 80+
- Sports Channels: 70+
- TV Penetration: 67% of households
- OTT Subscribers: 12 crore paid
- OTT Platforms: 40+
- Netflix Subscribers: 1 crore
- Amazon Prime Video: 2.5 crore
- Disney+ Hotstar: 4.6 crore
- Zee5: 1.2 crore
- SonyLIV: 1 crore
- OTT Content Investment: ₹6,500 crore
- OTT Original Shows: 500+ (2024)
- Film Production: 2,500 films annually
- Hindi Films: 350
- Telugu Films: 450
- Tamil Films: 350
- Kannada Films: 250
- Malayalam Films: 220
- Bengali Films: 180
- Marathi Films: 150
- Other Languages: 550
- Multiplexes: 9,500 screens
- Single Screens: 7,500
- Total Cinema Screens: 17,000
- PVR INOX Screens: 1,700+
- Cinema Admissions: 100 crore tickets
- Box Office Revenue: ₹12,000 crore
- Highest Grossing Film 2024: Various regional blockbusters
- Bollywood Market Share: 35%
- South Cinema Market Share: 55%
- International Content: 10%
- Film Exports: $300 million
- Animation & VFX: $1.5 billion
- Gaming Market: $3.5 billion
- Mobile Gaming: $2.8 billion
- Console Gaming: $400 million
- PC Gaming: $300 million
- E-sports: $150 million
- E-sports Players: 1.5 lakh
- Gaming Cafes: 5,000+
- Music Streaming: 50 crore users
- Spotify: 4 crore users
- JioSaavn: 10 crore users
- Gaana: 8 crore users
- YouTube Music: 15 crore users
- Print Newspapers: 1,100+ dailies
- Newspaper Circulation: 35 crore copies
- Digital News Readers: 50 crore
- Radio Stations: 380+
- FM Radio Listeners: 6.5 crore
- Podcast Listeners: 10 crore
- Influencer Marketing: ₹2,200 crore
- YouTubers (1 lakh+ subscribers): 65,000+
- Instagram Influencers: 10 lakh+
- Social Media Advertising: $8 billion
- Digital Advertising: $10 billion
- TV Advertising: $4.5 billion
- Print Advertising: $1.5 billion
- Ad Film Production Houses: 2,500+
- Post-Production Studios: 3,000+
- Recording Studios: 1,500+
- Media Employment: 25 lakh
- Target by 2030: $75 billion

## SPORTS & FITNESS
- Sports Industry Size: $27 billion (2024)
- Sports Infrastructure: $8 billion
- Sports Goods Manufacturing: $4 billion
- Sports Services: $6 billion
- Fitness & Wellness: $9 billion
- Sports Sponsorship: $2.5 billion
- Sports Media Rights: $4 billion
- IPL Valuation: $16.4 billion
- IPL Media Rights (5 years): $6.2 billion
- IPL Franchise Values: $500 million-$1.1 billion average
- Mumbai Indians Value: $1.3 billion
- Chennai Super Kings Value: $1.15 billion
- Cricket Market: $15 billion
- BCCI Revenue: ₹7,000 crore (2024)
- International Cricket Venues: 52
- Domestic Cricket Teams: 38 (Ranji Trophy)
- Registered Cricketers: 8 lakh
- Cricket Academies: 5,000+
- National Sports Federations: 64
- Olympic Sports Federations: 36
- Sports Authority of India (SAI): 25 centers
- Khelo India Centers: 1,000+
- Khelo India Budget: ₹900 crore
- Target Olympic Podium Scheme: ₹309 crore
- Tokyo Olympics 2021: 7 medals
- Paris Olympics 2024: 6 medals
- Commonwealth Games 2022: 61 medals
- Asian Games 2022: 107 medals
- Badminton Players (registered): 10 lakh
- Badminton Academies: 3,000+
- Kabaddi League (PKL): ₹500 crore valuation
- Football Clubs (ISL): 12 teams
- ISL Valuation: $200 million
- Football Players (AIFF registered): 40 lakh
- Football Academies: 2,000+
- Hockey Players: 3 lakh registered
- Field Hockey Budget: ₹150 crore
- Wrestling Akhadas: 15,000+
- Boxing Academies: 1,500+
- Athletics Federations: 36 state units
- Marathon Events: 200+ annually
- Marathon Participants: 25 lakh
- Yoga Practitioners: 30 crore
- Yoga Studios: 50,000+
- Gym & Fitness Centers: 25,000+
- Gym Members: 3.5 crore
- Cult.fit Centers: 350+
- Gold's Gym: 180+ centers
- Fitness First: 80+ centers
- Talwalkars: 300+ centers
- Fitness Equipment Market: ₹6,500 crore
- Sports Goods Exports: $2.2 billion
- Jalandhar Sports Goods: 60% of production
- Meerut Sports Goods: 25% of production
- Football/Cricket Bat Manufacturing: 5,000+ units
- Sports Footwear: $3 billion market
- Sports Apparel: $5 billion
- Sportswear Brands: Nike, Adidas, Puma, Decathlon
- Decathlon Stores: 120+
- Sports Nutritional Supplements: ₹4,500 crore
- Zumba/Aerobics Instructors: 1.5 lakh
- Personal Trainers: 2 lakh
- Sports Medicine Clinics: 500+
- Sports Physiotherapists: 8,000+
- Sports Psychology: Emerging field
- E-sports Market: $150 million
- E-sports Players: 1.5 lakh
- Gaming Tournaments: 500+ annually
- Sports Betting (Illegal): Estimated $150 billion
- Fantasy Sports: $3.5 billion
- Dream11 Users: 20 crore
- MPL Users: 9 crore
- Target by 2030: $100 billion

## SHIPPING & PORTS
- Shipping Industry Size: $14 billion (2024)
- Port Cargo Handling: 1,600 million MT (2024)
- Container Traffic: 180 million TEUs
- Coastal Shipping: 95 million MT
- Major Ports: 12
- Non-Major Ports: 200+
- Total Ports: 212
- Operational Ports: 139
- Cargo Handling Capacity: 2,600 million MT
- Major Ports Capacity: 1,570 million MT
- Non-Major Ports Capacity: 1,030 million MT
- Top Port: Mundra (Gujarat) - 144 million MT
- 2nd: Paradip (Odisha) - 145 million MT
- 3rd: Kandla (Gujarat) - 115 million MT
- 4th: JNPT Mumbai - 81 million MT (containers)
- 5th: Visakhapatnam - 74 million MT
- Container Ports: 15 major
- JNPT Container Traffic: 5.8 million TEUs
- Mundra Container Traffic: 5.5 million TEUs
- Chennai Container Traffic: 2.1 million TEUs
- Kolkata Container Traffic: 1.2 million TEUs
- Liquid Cargo Terminals: 45+
- Dry Bulk Terminals: 80+
- Cruise Terminals: 12
- Fishing Harbors: 185
- Shipyards: 28 major
- Ship Building Capacity: 2 million DWT
- Ship Repair Facilities: 125+
- Dry Docks: 45
- Indian Merchant Fleet: 1,576 vessels
- Total Shipping Tonnage: 13.4 million GT
- Coastal Vessels: 850
- Overseas Vessels: 726
- Tankers: 450 vessels
- Bulk Carriers: 380 vessels
- Container Ships: 85 vessels
- General Cargo Ships: 320 vessels
- Passenger Ships: 180 vessels
- Offshore Vessels: 161 vessels
- Top Shipping Company: Shipping Corporation of India (SCI) - 59 vessels
- 2nd: Great Eastern Shipping - 46 vessels
- 3rd: Essar Shipping - 18 vessels
- Private Shipping Companies: 850+
- Seafarers: 2.5 lakh
- Port Employment: 3.5 lakh
- Dredging Fleet: 45 vessels
- Lighthouse & Navigational Aids: 196 lighthouses
- Coastal Radar Stations: 84
- Vessel Traffic Management Systems: 12 ports
- Port Connectivity (Rail): 85% of major ports
- Port Connectivity (Road): 100%
- Dedicated Freight Corridors: Connecting major ports
- Sagarmala Programme: ₹6 lakh crore (port-led development)
- Sagarmala Projects: 802 projects
- Inland Waterways: 111 declared
- National Waterways: 111
- Cargo on Inland Waterways: 108 million MT
- Inland Vessels: 3,000+
- Ro-Ro Ferry Services: 12 routes
- Passenger Ferry Services: 150+ routes
- Coastal Economic Zones: Under development
- Transshipment Cargo: 25% (target to reduce)
- Port Turnaround Time: 2.5 days (average)
- Dwell Time (Containers): 3.2 days
- Port Automation: 8 ports (partial/full)
- Green Ports: 15 certified
- LNG Terminals: 6 operational
- LNG Import Capacity: 42.5 MMTPA
- Crude Oil Terminals: 12
- POL Product Terminals: 35+
- Coal Import Terminals: 25+
- Iron Ore Export Terminals: 18
- Container Freight Stations: 180+
- Warehousing at Ports: 25 million sq ft
- Cold Storage at Ports: 1.5 million MT
- Port Logistics Parks: 12 under development
- Coastal Berths: 1,500+
- Deep Water Berths: 350+
- Maritime Training Institutes: 150+
- Marine Engineering Colleges: 45+
- Merchant Navy Officers: 1.5 lakh
- Ratings: 1 lakh
- Port Tariff Authority: Regulating 12 major ports
- Cabotage Relaxation: Selective routes
- Flag of Convenience: Limited adoption
- Ship Recycling Yards: 125 (Alang, Gujarat - world's largest)
- Ship Breaking Capacity: 6 million LDT
- Alang Ship Breaking: 50% of global capacity
- Maritime Clusters: 5 (Gujarat, Maharashtra, Tamil Nadu, Andhra, Odisha)
- Coastal Shipping Incentives: Subsidy schemes
- Sagarmala Skill Development: 1 lakh trained
- Port Privatization: 15 major terminals
- PPP Port Projects: 80+ operational
- Port Concessions: 30-year average
- Target Cargo 2030: 2,500 million MT
- Target by 2030: $25 billion industry

## RAILWAYS
- Railway Network: 68,000 km
- Broad Gauge: 61,000 km (89.7%)
- Meter Gauge: 3,500 km (5.1%)
- Narrow Gauge: 3,500 km (5.1%)
- Electrified Routes: 57,000 km (84%)
- Double/Multiple Lines: 32,000 km
- Railway Stations: 7,349
- Major Stations: 720
- A1 Category Stations: 75
- Railway Zones: 18
- Railway Divisions: 71
- Production Units: 6 (coaches, locomotives, wheels)
- Railway Employees: 12.5 lakh
- Train Services Daily: 13,500 trains
- Passenger Trains: 12,500
- Freight Trains: 9,000
- Mail/Express Trains: 4,500
- Passenger Trains (Local): 3,500
- Suburban Services: 3,000 trains/day
- Vande Bharat Trains: 102 (operational + ordered)
- Shatabdi Trains: 20
- Rajdhani Trains: 52
- Duronto Trains: 55
- Gatimaan Express: 160 km/h (fastest)
- Vande Bharat Speed: 180 km/h (max operational)
- High-Speed Rail (Bullet Train): Under construction
- Mumbai-Ahmedabad HSR: 508 km (320 km/h)
- HSR Investment: ₹1.08 lakh crore
- HSR Completion Target: 2028
- Railway Budget: ₹2.55 lakh crore (2024-25)
- Capital Expenditure: ₹2.52 lakh crore
- Revenue: ₹2.4 lakh crore
- Passenger Revenue: ₹72,000 crore
- Freight Revenue: ₹1.62 lakh crore
- Other Revenue: ₹6,000 crore
- Passenger Journeys: 850 crore annually
- Daily Passengers: 2.3 crore
- Suburban Passengers: 1.5 crore daily
- Reserved Passengers: 60 lakh daily
- Unreserved Passengers: 1.7 crore daily
- Freight Traffic: 1,500 million tonnes
- Coal Transportation: 700 million tonnes (47%)
- Iron Ore: 150 million tonnes
- Cement: 140 million tonnes
- Food Grains: 80 million tonnes
- Fertilizers: 60 million tonnes
- POL Products: 70 million tonnes
- Containers: 85 million tonnes
- Steel: 55 million tonnes
- Average Freight Lead: 620 km
- Freight Loading: 4.1 million tonnes/day
- Locomotives: 13,500
- Electric Locomotives: 10,500
- Diesel Locomotives: 3,000
- Passenger Coaches: 84,000
- AC Coaches: 28,000
- Non-AC Coaches: 56,000
- Freight Wagons: 3 lakh
- EMU/MEMU Coaches: 15,000
- Vande Bharat Trainsets: 102 (16-coach)
- Railway Workshops: 43
- Diesel Sheds: 75
- Electric Sheds: 250
- Carriage Repair Workshops: 35
- Locomotive Workshops: 8
- Dedicated Freight Corridors: 2 operational
- Eastern DFC: 1,856 km (Ludhiana-Dankuni)
- Western DFC: 1,504 km (Dadri-JNPT)
- DFC Investment: ₹81,459 crore
- Average Freight Speed: 25 km/h (target: 50 km/h on DFC)
- Railway Bridges: 1.45 lakh
- Railway Tunnels: 700+ (total 550 km)
- Longest Tunnel: Pir Panjal (11.2 km, J&K)
- Chenab Bridge: 1.3 km (world's highest railway bridge - 359m)
- Railway Electrification: 6,000 km per year
- Target 100% Electrification: 2024 (achieved)
- Solar Power Capacity: 1,500 MW (target)
- Solar Panels on Stations: 1,000+ stations
- Green Energy: 3,000 MW target by 2030
- Railway Catering: 7,000+ outlets
- IRCTC Revenue: ₹4,500 crore
- Online Ticket Booking: 95% of reserved tickets
- UTS App Tickets: 1.5 crore/day
- Railway WiFi Stations: 6,000+
- Railtel Fiber Network: 61,000 km
- Railway Telecom: 50,000 km
- Train Protection Systems: Kavach (TCAS)
- Kavach Deployment: 2,000 km (target: 10,000 km)
- Level Crossings: 18,000
- Unmanned Level Crossings: 0 (eliminated)
- Railway Accidents: 55 (2023-24)
- Accident Rate: Lowest in history
- Railway Safety Fund: ₹1 lakh crore
- Station Redevelopment: 508 stations
- World-Class Stations: 50 planned
- Vande Bharat Stations: 200 planned
- Railway Universities: 1 (Vadodara)
- Railway Training Institutes: 350+
- Railway Medical Facilities: 125 hospitals
- Railway Schools: 900+
- Railway Quarters: 8 lakh units
- Railway Land: 4.77 lakh hectares
- Dedicated Freight Corridors (Future): 4 more planned
- Metro Rail (Indian Railways): 700+ km operational
- Regional Rapid Transit: 3 corridors planned
- Namo Bharat (RRTS): 82 km (Delhi-Meerut)
- Mumbai-Ahmedabad HSR Stations: 12
- Hydrogen Trains: 35 routes identified (pilot)
- Hydrogen Locomotive: Under development
- Freight Corridors Target 2030: 6 corridors
- Gati Shakti Cargo Terminals: 100+ planned
- Private Freight Terminals: 150+
- Container Trains: 5,000+ rakes
- Automobile Freight Rakes: Special wagons
- Railway PSUs: 10 (IRCTC, IRFC, RailTel, etc.)
- IRCTC Market Cap: ₹60,000 crore
- IRFC Lending: ₹4 lakh crore
- Railway Pension Fund: ₹85,000 crore/year
- Railway Recruitment: 3 lakh (2022-2025)
- Target Freight 2030: 2,200 million tonnes
- Target Revenue 2030: ₹5 lakh crore

## CONSTRUCTION & INFRASTRUCTURE
- Construction Industry Size: $280 billion (2024)
- Infrastructure Investment: ₹11.1 lakh crore (2024-25)
- GDP Contribution: 8.2%
- Real Estate: $180 billion
- Infrastructure: $100 billion
- Road Network: 66.7 lakh km
- National Highways: 1.46 lakh km
- State Highways: 1.86 lakh km
- District Roads: 6.42 lakh km
- Rural Roads: 56.96 lakh km
- Expressways: 5,930 km
- Road Construction: 28 km/day (2023-24)
- National Highways Construction: 13,327 km (2023-24)
- Bharatmala Project: 34,800 km (₹5.35 lakh crore)
- Bharatmala Phase-I: 24,800 km
- Golden Quadrilateral: 5,846 km (completed)
- North-South Corridor: 4,076 km
- East-West Corridor: 3,640 km
- Port Connectivity Roads: 7,500 km
- Border Roads: 3,500 km/year (BRO)
- Longest Highway: NH-44 (4,112 km)
- Longest Expressway: Delhi-Mumbai (1,350 km) - under construction
- Completed Expressways: Yamuna, Agra-Lucknow, Purvanchal, etc.
- Road Bridges: 1.5 lakh+
- Flyovers: 5,000+
- Road Tunnels: 450+
- Atal Tunnel: 9.02 km (world's longest highway tunnel >10,000 ft)
- Road Surfacing: 70% paved
- Concrete Roads: 15,000 km
- Toll Plazas: 850+
- FASTag Adoption: 98%
- Highway ROB/RUB: 2,500+
- Road Safety Measures: ₹14,000 crore allocated
- Road Accidents: 4.6 lakh (2022)
- Road Deaths: 1.68 lakh (2022)
- PM Gram Sadak Yojana: 7.68 lakh km constructed
- PMGSY Budget: ₹19,000 crore (2024-25)
- Rural Connectivity: 97% habitations connected
- Road Construction Companies: 5,000+
- Top Construction Company: Larsen & Toubro (₹2.2 lakh crore revenue)
- 2nd: Adani Group (₹2.9 lakh crore - diversified)
- 3rd: Reliance Infrastructure (₹18,000 crore)
- 4th: GMR Group (₹28,000 crore)
- 5th: Shapoorji Pallonji (₹15,000 crore)
- 6th: Tata Projects (₹12,000 crore)
- 7th: NCC Limited (₹15,500 crore)
- 8th: IRB Infrastructure (₹8,500 crore)
- 9th: Ashoka Buildcon (₹6,500 crore)
- 10th: Sadbhav Engineering (₹4,500 crore)
- Construction Equipment Market: $4.5 billion
- Cement Consumption (Construction): 280 million tonnes
- Steel Consumption (Construction): 80 million tonnes
- Ready-Mix Concrete: 150 million cubic meters
- Construction Employment: 7 crore
- Skilled Workers: 1.5 crore
- Unskilled Workers: 5.5 crore
- Civil Engineers: 8 lakh
- Architects: 1.2 lakh
- Real Estate Developers: 50,000+
- Housing Units: 38 crore
- Urban Housing: 12 crore
- Rural Housing: 26 crore
- Housing Shortage: 1 crore units
- Urban Housing Shortage: 96 lakh
- Affordable Housing: 60% of demand
- PM Awas Yojana (Urban): 1.2 crore houses sanctioned
- PM Awas Yojana (Rural): 3 crore houses completed
- PMAY Budget: ₹54,500 crore (2024-25)
- PMAY Investment: ₹10 lakh crore (cumulative)
- Smart Cities Mission: 100 cities
- Smart Cities Investment: ₹2.4 lakh crore
- Smart Cities Projects: 8,000+
- AMRUT (Urban Infrastructure): 500 cities
- AMRUT Allocation: ₹77,640 crore
- Metro Rail Network: 945 km operational (2024)
- Metro Cities: 21
- Under Construction Metro: 1,000+ km
- Metro Investment: ₹5.5 lakh crore
- Delhi Metro: 393 km (largest)
- Mumbai Metro: 60 km operational (350 km planned)
- Bangalore Metro: 73 km
- Hyderabad Metro: 72 km
- Chennai Metro: 54 km
- Kolkata Metro: 69 km
- Lucknow Metro: 40 km
- Kochi Metro: 43 km
- Jaipur Metro: 39 km
- Nagpur Metro: 38 km
- Pune Metro: 33 km
- Ahmedabad Metro: 40 km
- Kanpur Metro: 32 km
- RRTS (Regional Rapid Transit): 82 km operational
- RRTS Under Construction: 500+ km
- Monorail: 20 km (Mumbai)
- Light Rail: 15 km operational
- Dedicated Bus Corridors: 450 km
- BRTS Systems: 12 cities
- Airports: 157 operational
- International Airports: 35
- Domestic Airports: 122
- Airport Authority of India Airports: 137
- Private Airports: 20
- Greenfield Airports: 21 under development
- Airport Modernization: ₹98,000 crore
- UDAN Airports: 74
- UDAN Routes: 450+
- Heliports: 25 operational
- Water Aerodromes: 18 identified
- Largest Airport: Indira Gandhi International (Delhi) - 70 million pax capacity
- Mumbai Airport: 48 million capacity
- Bangalore Airport: 33 million capacity
- Navi Mumbai Airport: Under construction (90 million capacity)
- Jewar Airport (Noida): Under construction (70 million capacity)
- Dam Projects: 5,334 large dams
- Under Construction Dams: 1,100+
- Multipurpose Projects: 450+
- Irrigation Dams: 4,200+
- Hydropower Dams: 600+
- Water Supply Dams: 3,500+
- Tallest Dam: Tehri (260.5 m)
- Longest Dam: Hirakud (25.8 km)
- Sardar Sarovar Dam: 1,210 m length (Narmada)
- Polavaram Project: ₹55,000 crore (under construction)
- Irrigation Potential: 140 million hectares
- Irrigation Potential Created: 126 million hectares
- Canal Network: 7 lakh km
- Interlinking of Rivers: 30 projects identified
- Ken-Betwa Link: Under construction (₹44,605 crore)
- Kaleshwaram Project: World's largest lift irrigation (Telangana)
- Power Plants: 1,500+
- Thermal Power Plants: 250+
- Hydropower Plants: 600+
- Solar Parks: 450+
- Wind Farms: 350+
- Nuclear Power Plants: 7 sites (22 reactors)
- Power Transmission Lines: 4.5 lakh km
- 765 kV Lines: 25,000 km
- 400 kV Lines: 1.75 lakh km
- 220 kV Lines: 2.5 lakh km
- Substations: 10,000+
- Power Grid Investment: ₹3.5 lakh crore
- Gas Pipelines: 21,000 km
- Under Construction Gas Pipelines: 15,000 km
- Oil Pipelines: 15,000 km
- LPG Pipelines: 3,500 km
- City Gas Distribution: 280 cities
- PNG Connections: 1.2 crore
- Fiber Optic Network: 35 lakh km
- Telecom Towers: 8.5 lakh
- 5G Towers: 4.5 lakh
- Data Centers: 150+
- Data Center Capacity: 950 MW
- SEZ (Special Economic Zones): 420
- Industrial Parks: 650+
- Logistics Parks: 85 planned (under PM Gati Shakti)
- Warehousing Space: 350 million sq ft
- Cold Storage Capacity: 37.5 million MT
- Container Freight Stations: 180+
- Multi-Modal Logistics Parks: 35 planned
- Convention Centers: 450+
- Sports Stadiums: 2,500+ (major)
- Cricket Stadiums: 52 international
- Indoor Stadiums: 1,200+
- Swimming Pools (Olympic): 120+
- Sewage Treatment Plants: 1,200+
- Sewage Treatment Capacity: 31,000 MLD
- Water Treatment Plants: 2,500+
- Solid Waste Management: 65% treatment
- Waste to Energy Plants: 150+
- Construction Waste Recycling: 180 units
- Green Buildings: 12,000+ (IGBC/GRIHA certified)
- LEED Certified Buildings: 5,500+
- Affordable Housing PPP: 250+ projects
- Infrastructure Investment Trusts (InvITs): 25
- Real Estate Investment Trusts (REITs): 3
- National Infrastructure Pipeline: ₹111 lakh crore (2020-2025)
- NIP Projects: 9,000+
- Public-Private Partnerships: 1,500+ projects
- PPP Investment: ₹8.5 lakh crore (cumulative)
- HAM (Hybrid Annuity Model) Projects: 450+ (roads)
- BOT (Build-Operate-Transfer): 350+ projects
- Construction Permits: Digitalized in 450+ cities
- Building Approvals: 15 lakh annually
- Real Estate Registration: 85 lakh transactions/year
- RERA Registered Projects: 95,000+
- RERA Complaints: 1.5 lakh (cumulative)
- Construction Safety Regulations: BIS Standards
- Green Building Target 2030: 25,000+ certified
- Infrastructure Employment: 7.5 crore
- Target Infrastructure Investment 2030: ₹200 lakh crore
- Target by 2030: $500 billion industry

## MINING & MINERALS
- Mining Industry Size: $40 billion (2024)
- Mineral Production Value: ₹3.2 lakh crore
- Coal Production: 997 million tonnes (2023-24)
- Coal India Production: 773 million tonnes
- Singareni Collieries: 68 million tonnes
- Private Coal Mining: 156 million tonnes
- Coal Reserves: 361 billion tonnes
- Proved Coal Reserves: 155 billion tonnes
- Lignite Production: 41 million tonnes
- Lignite Reserves: 46 billion tonnes
- Iron Ore Production: 280 million tonnes
- Iron Ore Reserves: 35 billion tonnes
- Hematite Reserves: 25 billion tonnes
- Magnetite Reserves: 10 billion tonnes
- Iron Ore Exports: 45 million tonnes
- Bauxite Production: 27 million tonnes
- Bauxite Reserves: 3.3 billion tonnes
- Aluminium Production: 4.1 million tonnes
- Alumina Production: 7.5 million tonnes
- Copper Ore Production: 15 lakh tonnes
- Copper Concentrate: 3.5 lakh tonnes
- Refined Copper: 8.5 lakh tonnes
- Copper Reserves: 2 billion tonnes (resources)
- Zinc Production: 8.8 lakh tonnes
- Lead Production: 1.5 lakh tonnes
- Zinc-Lead Reserves: 350 million tonnes
- Gold Production: 1.6 tonnes
- Gold Reserves: 550 tonnes (resources)
- Silver Production: 180 tonnes
- Diamond Production: Negligible (12,000 carats)
- Manganese Ore: 3.5 million tonnes
- Manganese Reserves: 450 million tonnes
- Chromite Production: 5 million tonnes
- Chromite Reserves: 300 million tonnes
- Limestone Production: 425 million tonnes
- Limestone Reserves: 285 billion tonnes
- Dolomite Production: 28 million tonnes
- Gypsum Production: 4.5 million tonnes
- Rock Phosphate Production: 1.5 million tonnes
- Phosphate Reserves: 350 million tonnes
- Graphite Production: 35,000 tonnes
- Graphite Reserves: 180 million tonnes
- Silica Sand Production: 12 million tonnes
- China Clay Production: 2.8 million tonnes
- Ball Clay Production: 1.8 million tonnes
- Feldspar Production: 2.5 million tonnes
- Mica Production: 2,800 tonnes
- Barytes Production: 1.8 million tonnes
- Fluorite Production: 25,000 tonnes
- Rare Earth Elements: 6.9 million tonnes (reserves)
- Rare Earth Production: Minimal (3,000 tonnes)
- Thorium Reserves: 11.93 million tonnes (world's largest)
- Uranium Reserves: 3.46 lakh tonnes
- Uranium Production: 700 tonnes
- Beach Sand Minerals: 5.5 lakh tonnes
- Ilmenite Production: 4.2 lakh tonnes
- Rutile Production: 35,000 tonnes
- Zircon Production: 28,000 tonnes
- Garnet Production: 1.2 lakh tonnes
- Natural Gas (associated with mining): 32 BCM
- Crude Oil: 29 million tonnes
- Coal Bed Methane: 0.6 BCM
- Shale Gas Reserves: Under exploration
- Dimension Stones: 18 million cubic meters
- Granite Production: 12 million cubic meters
- Marble Production: 4.5 million cubic meters
- Sandstone Production: 1.5 million cubic meters
- Mining Leases: 12,000+
- Operational Mines: 1,500+ (major)
- Coal Mines: 450+
- Metallic Mineral Mines: 450+
- Non-Metallic Mineral Mines: 600+
- Minor Mineral Quarries: 1.5 lakh+
- Captive Mines: 250+
- Merchant Mines: 1,250+
- Mining Companies: 3,500+
- Coal India Limited: 330+ mines
- NMDC (Iron Ore): 4 major mines
- Vedanta Limited: Multiple minerals
- Hindustan Zinc: Zinc, Lead, Silver
- Hindalco (Aditya Birla): Bauxite, Aluminium
- NALCO: Bauxite, Aluminium
- Hutti Gold Mines: Gold (Karnataka)
- Tata Steel: Captive iron ore mines
- JSW Steel: Captive iron ore mines
- Odisha Mining Corp: Iron Ore, Chromite
- Mining States: Odisha, Chhattisgarh, Jharkhand, MP, Karnataka
- Odisha Mineral Revenue: ₹45,000 crore
- Chhattisgarh Mineral Revenue: ₹25,000 crore
- Jharkhand Mineral Revenue: ₹18,000 crore
- Madhya Pradesh Mineral Revenue: ₹12,000 crore
- Mining Royalties: ₹1.2 lakh crore (2023-24)
- District Mineral Foundation: ₹65,000 crore (cumulative)
- National Mineral Exploration Trust: ₹8,000 crore corpus
- Mineral Exploration: ₹2,500 crore (annual)
- Geological Survey of India: 18,000+ reports
- IBM (Indian Bureau of Mines): Regulatory authority
- MECL (Mineral Exploration Corp): 450+ projects
- Mining Auctions: 350+ mines (2015-2024)
- E-Auction Platform: Transparent bidding
- Mining Lease Period: 50 years (renewable)
- Forest Clearance for Mining: 15,000+ hectares/year
- Environmental Clearance: 250+ mines/year
- Mine Reclamation Fund: ₹12,000 crore
- Mining Affected Areas: 2.5 crore people
- Mining Rehabilitation: ₹8,000 crore spent
- Illegal Mining Cases: 2,500+ annually
- Mining Safety: DGMS (Directorate General)
- Mining Accidents: 150+ annually
- Mine Rescue Stations: 15
- Mining Equipment Market: $3.5 billion
- Excavators: 15,000+ units
- Dumpers: 12,000+ units
- Drilling Rigs: 800+
- Mining Trucks: 8,000+
- Mineral Processing Plants: 450+
- Ore Beneficiation Units: 180+
- Pellet Plants: 45 (iron ore)
- Smelters: 85+
- Refineries (Non-Ferrous): 25+
- Mineral Exports: $8 billion
- Iron Ore Exports: $3.5 billion
- Aluminium Exports: $2 billion
- Copper Exports: $800 million
- Mica Exports: $150 million
- Bauxite Exports: Minimal (value-added focus)
- Mineral Imports: $25 billion
- Coal Imports: 240 million tonnes ($20 billion)
- Copper Imports: 4.5 lakh tonnes
- Gold Imports: 800 tonnes
- Coking Coal Imports: 55 million tonnes
- Critical Minerals Mission: Launched 2024
- Lithium Exploration: J&K (5.9 million tonnes inferred)
- Cobalt Reserves: Under exploration
- Nickel Reserves: 190 million tonnes (Odisha)
- Strategic Mineral Reserves: Under development
- Mineral Security Partnership: International collaboration
- Khanij Bidesh India Ltd: Overseas mineral acquisition
- Mining R&D: ₹1,500 crore
- Green Mining: 50+ eco-friendly mines
- Zero Discharge Mines: 25+
- Solar-Powered Mining: 120+ mines
- Mining Automation: 35+ mines (partial)
- Digital Mining: Mine Management Systems
- Mining Employment: 12 lakh (direct)
- Indirect Mining Employment: 50 lakh
- Women in Mining: 45,000+
- Mining Skill Development: 50,000 trained/year
- Mining Training Institutes: 45+
- Mining Engineers: 25,000+
- Geologists: 15,000+
- Target Mineral Production 2030: ₹6 lakh crore
- Target Coal Production 2030: 1.5 billion tonnes
- Target by 2030: $75 billion industry

## STEEL & METALS
- Steel Industry Size: $65 billion (2024)
- Crude Steel Production: 140 million tonnes (2023-24)
- Finished Steel Production: 125 million tonnes
- Steel Consumption: 130 million tonnes
- Per Capita Consumption: 90 kg/year
- World Ranking: 2nd largest producer
- Steel Capacity: 180 million tonnes
- Capacity Utilization: 78%
- Steel Exports: 8.5 million tonnes
- Steel Imports: 6 million tonnes
- Flat Steel: 70 million tonnes
- Long Steel: 55 million tonnes
- Special Steel: 12 million tonnes
- Stainless Steel: 4.5 million tonnes
- Alloy Steel: 7.5 million tonnes
- Steel Companies: 450+
- Integrated Steel Plants: 15
- Mini Steel Plants: 1,200+
- Induction Furnace Units: 850+
- Electric Arc Furnace Units: 180+
- Top Steel Company: Tata Steel - 21 million tonnes capacity
- 2nd: JSW Steel - 28 million tonnes capacity
- 3rd: SAIL (Steel Authority of India) - 21.4 million tonnes
- 4th: JSPL (Jindal Steel & Power) - 15 million tonnes
- 5th: AM/NS India (ArcelorMittal Nippon Steel) - 9 million tonnes
- 6th: Rashtriya Ispat Nigam (RINL/Vizag Steel) - 7.3 million tonnes
- 7th: Bhushan Steel - 5.6 million tonnes
- 8th: Essar Steel - 10 million tonnes
- 9th: Uttam Galva - 1.8 million tonnes
- 10th: Electrosteel - 2.5 million tonnes
- Tata Steel Revenue: ₹2.5 lakh crore
- JSW Steel Revenue: ₹1.8 lakh crore
- SAIL Revenue: ₹1.05 lakh crore
- JSPL Revenue: ₹62,000 crore
- Steel Clusters: Odisha, Jharkhand, Chhattisgarh, West Bengal
- Odisha Steel Production: 35 million tonnes
- Jharkhand Steel Production: 28 million tonnes
- Chhattisgarh Steel Production: 18 million tonnes
- West Bengal Steel Production: 12 million tonnes
- Blast Furnaces: 45 operational
- BOF (Basic Oxygen Furnace): 35 units
- Direct Reduced Iron: 45 million tonnes
- Sponge Iron: 38 million tonnes
- Pig Iron: 12 million tonnes
- Iron Ore Consumption: 180 million tonnes
- Coking Coal Consumption: 58 million tonnes
- Limestone Consumption: 45 million tonnes
- Steel Scrap Recycling: 25 million tonnes
- Scrap Collection Centers: 5,000+
- Steel Recycling Rate: 45%
- Hot Rolled Coils: 40 million tonnes
- Cold Rolled Coils: 25 million tonnes
- Galvanized Steel: 18 million tonnes
- Color Coated Steel: 4.5 million tonnes
- TMT Bars: 35 million tonnes
- Steel Pipes: 12 million tonnes
- Steel Tubes: 4.5 million tonnes
- Steel Wire: 3.5 million tonnes
- Steel Wire Rods: 22 million tonnes
- Steel Plates: 8 million tonnes
- Steel Sheets: 15 million tonnes
- Structural Steel: 12 million tonnes
- Rails: 1.8 million tonnes
- Steel Castings: 2.5 million tonnes
- Steel Forgings: 1.2 million tonnes
- Tool Steel: 350,000 tonnes
- High-Speed Steel: 180,000 tonnes
- Silicon Steel: 450,000 tonnes
- Bearing Steel: 280,000 tonnes
- Automotive Steel: 18 million tonnes
- Construction Steel: 55 million tonnes
- Infrastructure Steel: 28 million tonnes
- Machinery Steel: 8 million tonnes
- White Goods Steel: 3.5 million tonnes
- Steel Service Centers: 8,500+
- Steel Traders: 50,000+
- Steel Stockyards: 12,000+
- Steel Warehouses: 3,500+
- National Steel Policy Target: 300 million tonnes by 2030
- Steel Investment: ₹10 lakh crore (2015-2030)
- Greenfield Projects: 25 planned
- Brownfield Expansions: 40 projects
- Steel PLI Scheme: ₹6,322 crore
- Steel Employment: 25 lakh (direct)
- Indirect Employment: 50 lakh
- Steel R&D: ₹2,500 crore
- Steel Testing Labs: 180+
- Steel Standards: 1,500+ BIS standards
- Steel Exports Markets: Nepal, Bangladesh, Sri Lanka, Middle East
- Steel Import Sources: China, Japan, South Korea
- Steel Dumping Cases: Multiple anti-dumping duties
- Safeguard Duties: On various products
- Steel Prices: ₹55,000-75,000 per tonne (varies by grade)
- Steel Price Volatility: ±15% annually
- Steel Logistics Cost: 8-12% of production cost

## ALUMINIUM
- Aluminium Production: 4.1 million tonnes
- Aluminium Capacity: 4.6 million tonnes
- Aluminium Consumption: 4.3 million tonnes
- Per Capita Consumption: 3 kg/year
- World Ranking: 2nd largest producer (after China)
- Primary Aluminium: 3.8 million tonnes
- Secondary Aluminium: 3 lakh tonnes
- Aluminium Exports: 2.5 million tonnes
- Aluminium Imports: 2.8 million tonnes
- Top Aluminium Producer: NALCO - 2.3 million tonnes capacity
- 2nd: Hindalco (Aditya Birla) - 1.5 million tonnes
- 3rd: Vedanta Aluminium - 2.3 million tonnes
- 4th: Balco (Vedanta) - 570,000 tonnes
- Aluminium Smelters: 12
- Alumina Refineries: 8
- Aluminium Extrusion Units: 850+
- Aluminium Rolling Mills: 450+
- Aluminium Foil Units: 180+
- Bauxite Mining: 27 million tonnes
- Alumina Production: 7.5 million tonnes
- Aluminium Scrap Recycling: 5 lakh tonnes
- Extrusion Capacity: 1.2 million tonnes
- Flat Rolled Products: 1.5 million tonnes
- Conductor Grade Aluminium: 350,000 tonnes
- Aluminium Alloys: 450,000 tonnes
- Aluminium Castings: 280,000 tonnes
- Aluminium Wire: 250,000 tonnes
- Aluminium Sheets: 650,000 tonnes
- Aluminium Foil: 280,000 tonnes
- Automotive Aluminium: 450,000 tonnes
- Construction Aluminium: 850,000 tonnes
- Electrical Aluminium: 1.2 million tonnes
- Packaging Aluminium: 380,000 tonnes
- Aluminium Prices: ₹200-240 per kg
- Power Cost (Aluminium): 35-40% of production cost
- Aluminium Employment: 2.5 lakh

## COPPER
- Copper Production: 8.5 lakh tonnes (refined)
- Copper Ore Production: 15 lakh tonnes
- Copper Concentrate: 3.5 lakh tonnes
- Copper Consumption: 12 lakh tonnes
- Copper Imports: 5 lakh tonnes
- Copper Exports: 1.5 lakh tonnes
- Top Copper Producer: Hindalco - 5 lakh tonnes capacity
- 2nd: Sterlite Copper (Vedanta) - 4 lakh tonnes
- Copper Smelters: 4
- Copper Refineries: 5
- Copper Wire Rod: 8 lakh tonnes
- Copper Wire & Cable: 6 lakh tonnes
- Copper Tubes: 80,000 tonnes
- Copper Sheets: 45,000 tonnes
- Brass Production: 2.5 lakh tonnes
- Bronze Production: 80,000 tonnes
- Copper Scrap Recycling: 3 lakh tonnes
- Electrical Copper: 6.5 lakh tonnes
- Automotive Copper: 1.8 lakh tonnes
- Construction Copper: 2.5 lakh tonnes
- Copper Prices: ₹750-850 per kg
- Copper Employment: 80,000

## ZINC & LEAD
- Zinc Production: 8.8 lakh tonnes
- Lead Production: 1.5 lakh tonnes
- Zinc Capacity: 10 lakh tonnes
- Zinc Consumption: 6 lakh tonnes
- Lead Consumption: 3.2 lakh tonnes
- Top Producer: Hindustan Zinc (Vedanta) - 9.5 lakh tonnes zinc capacity
- Zinc Smelters: 4
- Lead Smelters: 3
- Zinc Exports: 3.5 lakh tonnes
- Lead-Acid Batteries: 2.8 lakh tonnes lead consumption
- Galvanizing Industry: 5.5 lakh tonnes zinc
- Zinc Oxide: 80,000 tonnes
- Lead Recycling: 2 lakh tonnes
- Zinc Prices: ₹250-290 per kg
- Lead Prices: ₹180-210 per kg

## NICKEL & OTHER METALS
- Nickel Reserves: 190 million tonnes
- Nickel Production: Minimal (imports dominate)
- Nickel Imports: 1.2 lakh tonnes
- Stainless Steel Nickel Use: 85%
- Titanium Sponge: 6,000 tonnes capacity
- Titanium Production: 3,500 tonnes
- Magnesium Production: 8,000 tonnes
- Manganese Ore: 3.5 million tonnes
- Ferro-Manganese: 8 lakh tonnes
- Ferro-Chrome: 12 lakh tonnes
- Ferro-Silicon: 5.5 lakh tonnes
- Ferro Alloys Total: 35 lakh tonnes
- Ferro Alloy Units: 85+
- Silico-Manganese: 9 lakh tonnes
- Tungsten Production: 800 tonnes
- Molybdenum Production: 200 tonnes
- Tin Production: Minimal (imports)
- Metal Casting Industry: $8 billion
- Foundries: 4,500+
- Die-Casting Units: 1,200+
- Investment Casting: 450+ units
- Sand Casting: 2,500+ units
- Metal Forging Units: 1,800+
- Precious Metals Refining: 25 units
- Non-Ferrous Foundries: 1,500+
- Metal Finishing Units: 3,500+
- Electroplating Units: 2,800+
- Metal Powder Production: 85,000 tonnes
- Metal Matrix Composites: Emerging sector
- Metal Additive Manufacturing: 150+ units
- Steel & Metals Employment: 35 lakh (direct)
- Total Metals Indirect Employment: 1.2 crore
- Metals R&D Centers: 45+
- Metal Testing Labs: 450+
- Target Steel 2030: 300 million tonnes
- Target Aluminium 2030: 10 million tonnes
- Target by 2030: $150 billion (Steel & Metals combined)

## CEMENT
- Cement Industry Size: $28 billion (2024)
- Cement Production: 420 million tonnes (2023-24)
- Cement Capacity: 600 million tonnes
- Capacity Utilization: 70%
- World Ranking: 2nd largest producer
- Cement Consumption: 410 million tonnes
- Per Capita Consumption: 290 kg/year
- Cement Companies: 550+
- Integrated Cement Plants: 210
- Grinding Units: 350+
- Cement Kilns: 650+
- Top Cement Company: UltraTech Cement - 140 million tonnes capacity
- 2nd: Shree Cement - 54 million tonnes
- 3rd: Ambuja Cement (Adani) - 89 million tonnes
- 4th: ACC (Adani) - 36 million tonnes
- 5th: Dalmia Cement - 36 million tonnes
- 6th: JK Cement - 23 million tonnes
- 7th: Birla Corporation - 16 million tonnes
- 8th: Ramco Cement - 21 million tonnes
- 9th: India Cements - 15 million tonnes
- 10th: Prism Cement - 12 million tonnes
- UltraTech Revenue: ₹68,000 crore
- Shree Cement Revenue: ₹21,000 crore
- Ambuja Revenue: ₹32,000 crore
- ACC Revenue: ₹19,000 crore
- Dalmia Bharat Revenue: ₹14,500 crore
- Market Share: UltraTech (24%), Shree (9%), Ambuja (15%), ACC (6%)
- OPC (Ordinary Portland Cement): 45%
- PPC (Portland Pozzolana Cement): 45%
- PSC (Portland Slag Cement): 8%
- White Cement: 2%
- Other Specialty Cement: 1%
- Grey Cement: 98%
- Clinker Production: 350 million tonnes
- Clinker Factor: 0.83
- Limestone Consumption: 420 million tonnes
- Gypsum Consumption: 12 million tonnes
- Flyash Utilization: 85 million tonnes
- Slag Utilization: 32 million tonnes
- Coal Consumption (Cement): 45 million tonnes
- Pet Coke Consumption: 8 million tonnes
- Alternative Fuels: 8% of thermal energy
- Biomass Use: 3 million tonnes
- Cement Kilns (Rotary): 550+
- Vertical Shaft Kilns: 100+
- Cement Mills: 850+
- Packing Plants: 1,200+
- Bulk Cement: 35%
- Bagged Cement: 65%
- Cement Bags: 8 billion bags/year
- Cement Bag Size: 50 kg standard
- Cement Distribution: 15,000+ dealers
- Cement Retailers: 5 lakh+
- Ready-Mix Concrete: 150 million cubic meters
- RMC Plants: 2,500+
- Concrete Blocks: 8 billion units
- Cement Prices: ₹350-450 per bag (50 kg)
- Regional Price Variation: ±20%
- Cement Freight Cost: 15-25% of price
- Cement Export: 8 million tonnes
- Cement Import: Negligible (0.5 million tonnes)
- Export Markets: Bangladesh, Sri Lanka, Nepal, Middle East
- Cement Plants by Region: Rajasthan (highest capacity 120 MT)
- Andhra Pradesh: 60 million tonnes capacity
- Tamil Nadu: 50 million tonnes
- Madhya Pradesh: 48 million tonnes
- Gujarat: 45 million tonnes
- Chhattisgarh: 38 million tonnes
- Karnataka: 35 million tonnes
- Odisha: 28 million tonnes
- Maharashtra: 55 million tonnes
- Uttar Pradesh: 32 million tonnes
- White Cement Production: 7 lakh tonnes
- White Cement Capacity: 10 lakh tonnes
- JK Cement (White): 4 lakh tonnes capacity
- Birla White: 3.5 lakh tonnes
- Specialty Cement: 4 million tonnes
- Oil Well Cement: 8 lakh tonnes
- Rapid Hardening Cement: 5 lakh tonnes
- Sulphate Resistant Cement: 3 lakh tonnes
- Low Heat Cement: 2 lakh tonnes
- High Alumina Cement: 80,000 tonnes
- Waterproof Cement: 6 lakh tonnes
- Colored Cement: 50,000 tonnes
- Cement Grinding Aids: 25,000 tonnes
- Cement Additives Market: ₹800 crore
- Cement Testing Labs: 350+
- BIS Standards: IS 269, IS 1489, IS 12269
- Blended Cement: 55% of production
- Clinkerization Ratio: 0.83
- Energy Consumption: 3.2 GJ/tonne clinker
- Thermal Energy: 750 kcal/kg clinker
- Electrical Energy: 85 kWh/tonne cement
- CO2 Emissions: 520 kg per tonne cement
- Waste Heat Recovery: 150+ plants
- Solar Power (Cement): 800 MW installed
- Wind Power (Cement): 450 MW installed
- Green Power Share: 25% of total energy
- Water Consumption: 80-100 liters per tonne
- Zero Liquid Discharge Plants: 80+
- Cement Plant Automation: 120+ plants
- Digital Cement Plants: 45+
- Cement Quality Control: Online analyzers
- Cement Blending Systems: 650+
- Cement Silos: 2,500+
- Cement Storage Capacity: 45 million tonnes
- Cement Logistics: 50,000+ trucks
- Rail Rake Movement: 15,000+ rakes/year
- Cement by Rail: 35%
- Cement by Road: 65%
- Cement Packaging Machines: 1,800+
- Palletized Cement: 15%
- Jumbo Bags: 8%
- Bulk Cement Terminals: 350+
- Cement Depots: 3,500+
- Cement Transit Mixers: 12,000+
- Concrete Pumps: 8,500+
- Cement Employment: 5 lakh (direct)
- Indirect Employment: 15 lakh
- Cement Skilled Workers: 2 lakh
- Cement Engineers: 25,000+
- Cement R&D: ₹500 crore annually
- Green Cement R&D: ₹200 crore
- Low Carbon Cement: Under development
- Geopolymer Cement: Pilot projects
- Carbon Capture: 3 pilot projects
- Cement Sustainability: NCB initiatives
- Cement Industry Association: CMA (Cement Manufacturers Association)
- NCB (National Council for Cement): Technical body
- CII Cement Forum: Industry collaboration
- Cement Standards: 15+ BIS standards
- Cement Testing: 5 million samples/year
- Cement Disputes: NCDRC oversight
- Cement Mergers: 25+ in last decade
- FDI in Cement: 100% allowed (automatic)
- Private Equity Investment: ₹25,000 crore (2015-2024)
- Cement Bonds: ₹15,000 crore issued
- Cement Exports Growth: 8% CAGR
- Housing Cement Demand: 55%
- Infrastructure Cement Demand: 35%
- Industrial Cement Demand: 10%
- Rural Cement Demand: 40%
- Urban Cement Demand: 60%
- Cement Seasonality: Peak (Oct-March), Low (June-Sept)
- Monsoon Impact: -25% demand
- Cement Credit Period: 30-60 days
- Cement Branding: 85% branded
- Cement Advertising: ₹1,500 crore annually
- Target Production 2030: 550 million tonnes
- Target Capacity 2030: 750 million tonnes
- Target by 2030: $40 billion industry

## MICRO, SMALL & MEDIUM ENTERPRISES (MSME) - DETAILED

### OVERALL MSME STATISTICS
- Total MSMEs: 6.34 crore enterprises (2023-24)
- Micro Enterprises: 6.30 crore (99.4%)
- Small Enterprises: 3.3 lakh (0.52%)
- Medium Enterprises: 5,000 (0.01%)
- MSME GDP Contribution: 30%
- Manufacturing GDP: 6.4% (MSMEs)
- Services GDP: 28.9% (MSMEs)
- MSME Exports: $150 billion (48% of total exports)
- MSME Employment: 11.1 crore
- Rural MSMEs: 3.2 crore (51%)
- Urban MSMEs: 3.14 crore (49%)
- Women-Owned MSMEs: 1.58 crore (25%)
- SC/ST MSMEs: 90 lakh (14%)
- Registered MSMEs (Udyam): 4.2 crore
- Manufacturing MSMEs: 1.9 crore (30%)
- Services MSMEs: 3.65 crore (58%)
- Trade MSMEs: 79 lakh (12%)

### MSME CLASSIFICATION (Post 2020)
**MICRO:**
- Investment: Up to ₹1 crore
- Turnover: Up to ₹5 crore
- Count: 6.30 crore

**SMALL:**
- Investment: ₹1-10 crore
- Turnover: ₹5-50 crore
- Count: 3.3 lakh

**MEDIUM:**
- Investment: ₹10-50 crore
- Turnover: ₹50-250 crore
- Count: 5,000

### STATE-WISE MSME DISTRIBUTION
- Uttar Pradesh: 89.5 lakh MSMEs (14.2%)
- West Bengal: 88.7 lakh (14%)
- Tamil Nadu: 49.9 lakh (7.9%)
- Maharashtra: 47.8 lakh (7.5%)
- Karnataka: 38.5 lakh (6.1%)
- Bihar: 37.2 lakh (5.9%)
- Andhra Pradesh: 36.8 lakh (5.8%)
- Gujarat: 35.6 lakh (5.6%)
- Madhya Pradesh: 33.8 lakh (5.3%)
- Rajasthan: 32.4 lakh (5.1%)
- Odisha: 28.5 lakh (4.5%)
- Kerala: 26.2 lakh (4.1%)
- Punjab: 21.8 lakh (3.4%)
- Haryana: 18.5 lakh (2.9%)
- Telangana: 17.2 lakh (2.7%)
- Jharkhand: 15.8 lakh (2.5%)
- Assam: 14.5 lakh (2.3%)
- Chhattisgarh: 12.6 lakh (2%)
- Delhi: 11.2 lakh (1.8%)
- Uttarakhand: 8.5 lakh (1.3%)

### MSME SECTORS (TOP 50)
1. **Textiles & Garments**: 1.2 crore units
2. **Food Processing**: 75 lakh units
3. **Retail Trade**: 65 lakh units
4. **Wholesale Trade**: 14 lakh units
5. **Construction**: 45 lakh units
6. **Transport Services**: 38 lakh units
7. **Agriculture Services**: 35 lakh units
8. **Repair & Maintenance**: 32 lakh units
9. **Wood Products**: 28 lakh units
10. **Metal Products**: 25 lakh units
11. **Chemicals**: 18 lakh units
12. **Plastic Products**: 16 lakh units
13. **Furniture**: 15 lakh units
14. **Leather Products**: 12 lakh units
15. **Paper Products**: 10 lakh units
16. **Rubber Products**: 8 lakh units
17. **Electronics**: 8.5 lakh units
18. **Electrical Equipment**: 7.5 lakh units
19. **Machinery**: 7 lakh units
20. **Auto Components**: 6.5 lakh units
21. **Printing & Publishing**: 6 lakh units
22. **Pharmaceuticals**: 5.5 lakh units
23. **Gems & Jewellery**: 5 lakh units
24. **Beverages**: 4.5 lakh units
25. **Non-Metallic Minerals**: 4 lakh units
26. **IT Services**: 3.8 lakh units
27. **Professional Services**: 3.5 lakh units
28. **Education Services**: 3.2 lakh units
29. **Healthcare Services**: 3 lakh units
30. **Hotels & Restaurants**: 2.8 lakh units
31. **Beauty & Wellness**: 2.5 lakh units
32. **Packaging**: 2.2 lakh units
33. **Sports Goods**: 2 lakh units
34. **Toys**: 1.8 lakh units
35. **Footwear**: 1.5 lakh units
36. **Handicrafts**: 1.2 lakh units
37. **Coir Products**: 80,000 units
38. **Jute Products**: 70,000 units
39. **Ceramics**: 65,000 units
40. **Glass Products**: 60,000 units
41. **Musical Instruments**: 50,000 units
42. **Scientific Instruments**: 45,000 units
43. **Optical Instruments**: 40,000 units
44. **Watches & Clocks**: 35,000 units
45. **Medical Devices**: 32,000 units
46. **Stationery**: 28,000 units
47. **Paints & Varnishes**: 25,000 units
48. **Adhesives**: 22,000 units
49. **Industrial Gases**: 18,000 units
50. **Biotechnology**: 15,000 units

### MSME CLUSTERS
- Total Clusters: 6,000+
- Registered Clusters: 3,800
- Mega Clusters: 150
- Major Clusters (500+): 850
- Geographic Clusters: 2,500+
- Product-Based Clusters: 3,500+

**TOP MSME CLUSTERS:**
1. **Tirupur**: Knitwear (5,000+ units, ₹25,000 crore)
2. **Surat**: Textiles & Diamonds (50,000+ units, ₹80,000 crore)
3. **Ludhiana**: Hosiery & Auto Parts (20,000+ units, ₹35,000 crore)
4. **Coimbatore**: Engineering (35,000+ units, ₹45,000 crore)
5. **Moradabad**: Brass & Handicrafts (8,000+ units, ₹8,000 crore)
6. **Agra**: Footwear & Leather (12,000+ units, ₹10,000 crore)
7. **Jaipur**: Gems & Jewellery (15,000+ units, ₹75,000 crore)
8. **Faridabad**: Engineering (18,000+ units, ₹28,000 crore)
9. **Rajkot**: Engineering (22,000+ units, ₹32,000 crore)
10. **Kanpur**: Leather (8,500+ units, ₹7,500 crore)
11. **Varanasi**: Textiles (12,000+ units, ₹9,000 crore)
12. **Jalandhar**: Sports Goods (2,500+ units, ₹5,000 crore)
13. **Firozabad**: Glass & Bangles (10,000+ units, ₹3,500 crore)
14. **Panipat**: Textiles (8,000+ units, ₹12,000 crore)
15. **Aligarh**: Locks (5,000+ units, ₹2,500 crore)
16. **Meerut**: Sports Goods (3,500+ units, ₹4,000 crore)
17. **Barabanki**: Furniture (4,000+ units, ₹1,800 crore)
18. **Saharanpur**: Wood Carving (6,000+ units, ₹2,000 crore)
19. **Bhiwandi**: Textiles (25,000+ units, ₹18,000 crore)
20. **Sivakasi**: Fireworks & Printing (3,000+ units, ₹3,500 crore)
21. **Karur**: Home Textiles (4,500+ units, ₹8,000 crore)
22. **Erode**: Textiles (8,000+ units, ₹15,000 crore)
23. **Ambur**: Leather (2,000+ units, ₹5,000 crore)
24. **Kollam**: Coir (5,000+ units, ₹1,200 crore)
25. **Thrissur**: Jewellery (3,500+ units, ₹25,000 crore)
26. **Bangalore**: Electronics (45,000+ units, ₹55,000 crore)
27. **Pune**: Auto Components (15,000+ units, ₹38,000 crore)
28. **Nashik**: Engineering (12,000+ units, ₹18,000 crore)
29. **Kolhapur**: Foundry (3,000+ units, ₹6,000 crore)
30. **Ichalkaranji**: Textiles (6,000+ units, ₹8,000 crore)

### MSME FINANCIAL SUPPORT
- Total MSME Credit: ₹25 lakh crore (2024)
- Priority Sector Lending: ₹18 lakh crore (to MSMEs)
- MUDRA Loans: ₹23 lakh crore (cumulative since 2015)
- MUDRA Accounts: 43 crore (cumulative)
- Shishu (up to ₹50,000): 35 crore accounts
- Kishore (₹50,000-5 lakh): 7.5 crore accounts
- Tarun (₹5-10 lakh): 50 lakh accounts
- Average MUDRA Loan: ₹53,000
- MUDRA Default Rate: 3.2%
- Stand-Up India: 1.45 lakh loans (₹32,000 crore)
- CGTMSE (Credit Guarantee): ₹3.5 lakh crore (cumulative guarantees)
- CGTMSE Approval Rate: 85%
- Emergency Credit Line (ECLGS): ₹5 lakh crore (COVID support)
- ECLGS Beneficiaries: 1.3 crore MSMEs
- MSME Equity Funding: ₹15,000 crore (2023-24)
- Venture Capital for MSMEs: ₹8,000 crore
- Angel Investment in MSMEs: ₹3,500 crore
- MSME IPOs: 180 (2020-2024)
- MSME Bonds: ₹12,000 crore issued
- MSME Interest Rates: 8-12% (bank loans)
- MSME NPA Ratio: 9.5%
- MSME Loan Recovery: 87%
- TReDS Platforms: 3 (Invoice discounting)
- TReDS Volume: ₹1.2 lakh crore
- Factoring for MSMEs: ₹45,000 crore
- MSME Leasing: ₹18,000 crore
- MSME Insurance Penetration: 12%

### GOVERNMENT SCHEMES FOR MSMEs
1. **Udyam Registration**: 4.2 crore registered
2. **PMEGP**: 8.5 lakh units (₹28,000 crore)
3. **SFURTI**: 500 clusters upgraded
4. **Technology Upgradation**: 15,000 units assisted
5. **ZED Certification**: 85,000 MSMEs certified
6. **Quality Certification**: 1.2 lakh MSMEs
7. **ISO Certification Support**: 45,000 MSMEs
8. **Marketing Support**: 25,000 MSMEs
9. **Trade Fairs**: 450 annually
10. **Export Promotion**: ₹5,000 crore
11. **Cluster Development**: ₹8,000 crore
12. **Infrastructure Development**: ₹12,000 crore
13. **Skill Development**: 50 lakh trained
14. **Entrepreneurship Development**: 12 lakh trained
15. **Incubation Support**: 450 incubators
16. **Innovation Support**: ₹2,500
15. **Incubation Support**: 450 incubators
16. **Innovation Support**: ₹2,500 crore
17. **Design Clinics**: 150 centers
18. **Tool Rooms**: 18 facilities
19. **Technology Centers**: 35
20. **Testing Labs**: 850+ (MSME access)
21. **Common Facility Centers**: 1,200+
22. **R&D Support**: ₹1,800 crore
23. **Patent Filing Support**: 8,500 MSMEs
24. **IPR Support**: 12,000 MSMEs
25. **Legal Support**: ₹500 crore
26. **Delayed Payment Portal**: 5.8 lakh cases
27. **MSME Samadhaan**: Online grievance redressal
28. **Champions Portal**: 2.2 lakh registrations
29. **Procurement Portal (GeM)**: 8.5 lakh MSME sellers
30. **Public Procurement**: 25% MSME mandate
31. **PSU Procurement from MSMEs**: ₹2.8 lakh crore
32. **E-Commerce Support**: 15 lakh MSMEs online
33. **Digital Marketing**: 8 lakh MSMEs trained
34. **Bharatcraft**: Handicraft MSMEs platform
35. **ODOP (One District One Product)**: 761 districts covered
36. **ODOP Products**: 1,200+ unique products
37. **ODOP Turnover**: ₹45,000 crore
38. **Khadi Program**: 8 lakh artisans
39. **Khadi Sales**: ₹4,200 crore annually
40. **Village Industries**: 12 lakh units
41. **Coir Board Support**: 5 lakh workers
42. **Handloom Support**: 35 lakh weavers
43. **Handicrafts Support**: 68 lakh artisans
44. **ASPIRE (Agro-Rural Industries): 80 incubators
45. **Livelihood Incubators**: 250+

### MSME MINISTRY BUDGET & EXPENDITURE
- Ministry of MSME Budget (2024-25): ₹22,138 crore
- PMEGP Allocation: ₹2,400 crore
- Credit Support: ₹8,500 crore
- Skill Development: ₹1,800 crore
- Technology Upgradation: ₹2,200 crore
- Marketing Support: ₹1,500 crore
- Cluster Development: ₹2,800 crore
- Khadi & Village Industries: ₹2,938 crore
- Coir Development: ₹350 crore

### MSME ORGANIZATIONS & INSTITUTIONS
- MSME-DI (Development Institutes): 31
- District Industries Centers (DICs): 650+
- NSIC (National Small Industries Corp): 38 branches
- NSIC Turnover: ₹8,500 crore
- KVIC (Khadi & Village Industries): 35 offices
- Coir Board: 16 regional offices
- DC MSME (Development Commissioner): Central authority
- State MSME Directorates: 28
- MSME Technology Development Centers: 35
- Testing Centers: 18
- Tool Rooms: 18
- Entrepreneurship Development Institutes: 250+
- MSME Business Development: 450+ organizations
- Industry Associations: 3,500+ (MSME focused)

### MSME EXPORTS (SECTOR-WISE)
- Engineering Goods: $45 billion
- Textiles & Garments: $32 billion
- Gems & Jewellery: $25 billion
- Leather Products: $6 billion
- Handicrafts: $4.5 billion
- Chemicals: $8 billion
- Plastics: $5 billion
- Food Products: $10 billion
- Electronics: $6 billion
- Automotive Components: $4 billion
- Pharmaceuticals: $3.5 billion
- Sports Goods: $800 million
- Marine Products: $7 billion
- Cashew: $800 million
- Spices: $4 billion

### MSME DIGITAL TRANSFORMATION
- Digitally Enabled MSMEs: 2.5 crore
- MSMEs on E-Commerce: 15 lakh
- MSMEs with Websites: 85 lakh
- MSMEs on Social Media: 1.8 crore
- Digital Payment Adoption: 4.5 crore MSMEs
- UPI Transactions (MSMEs): ₹45 lakh crore annually
- Cloud Adoption: 25 lakh MSMEs
- ERP Systems: 12 lakh MSMEs
- Cybersecurity Awareness: 35 lakh MSMEs
- Digital Marketing Budget: ₹8,000 crore
- IT Investment: ₹35,000 crore annually
- Software Adoption: 40%
- Automation: 8 lakh MSMEs
- IoT Adoption: 2.5 lakh MSMEs
- AI/ML Usage: 80,000 MSMEs
- 3D Printing: 15,000 MSMEs
- Drones: 8,000 MSMEs

### MSME SUSTAINABILITY & GREEN INITIATIVES
- Green MSMEs: 45,000
- Solar Power (MSMEs): 1,200 MW
- Renewable Energy: 1,800 MW
- Energy Efficient Units: 1.5 lakh
- Water Conservation: 80,000 units
- Waste Management: 1.2 lakh units
- Zero Liquid Discharge: 8,500 MSMEs
- Circular Economy: 25,000 MSMEs
- Sustainable Materials: 65,000 MSMEs
- Carbon Footprint Tracking: 15,000 MSMEs
- Green Certification: 32,000 MSMEs
- Eco-friendly Products: 1.8 lakh MSMEs
- Organic Products: 45,000 MSMEs
- Recycling Units: 85,000
- Waste to Wealth: 35,000 MSMEs

### MSME STARTUP ECOSYSTEM
- MSME Startups: 1.2 lakh (recognized)
- Tech Startups: 45,000
- Fintech MSMEs: 8,500
- Edtech MSMEs: 6,200
- Healthtech MSMEs: 4,800
- Agritech MSMEs: 5,500
- Cleantech MSMEs: 3,200
- Social Enterprises: 15,000
- Women-led Startups: 28,000
- Youth Entrepreneurs (18-35): 65 lakh
- Student Entrepreneurs: 12,000
- Incubated Startups: 35,000
- Accelerated Startups: 18,000
- Angel-backed MSMEs: 8,500
- VC-backed MSMEs: 4,200

### MSME CHALLENGES & ISSUES
- Credit Gap: ₹25 lakh crore
- Delayed Payments: ₹10 lakh crore outstanding
- Average Payment Delay: 90+ days
- Technology Gap: 60% units lack modern tech
- Skill Gap: 45% workers need upskilling
- Raw Material Price Volatility: Major concern
- Competition from Imports: 35% affected
- Land Acquisition: 40% units struggle
- Power Supply Issues: 25% face problems
- Logistics Cost: 12-18% of revenue
- GST Compliance Burden: 55% find complex
- Lack of Market Access: 45%
- Low R&D Investment: <1% of revenue
- Limited Export Capability: 85% domestic only
- Informal Sector: 4 crore unregistered

### MSME ASSOCIATIONS & BODIES
- FISME (Federation of Indian MSMEs): 12 lakh members
- LAGHU UDYOG BHARATI: 8 lakh members
- Indian Industries Association: 6 lakh members
- WASME (World Association): International
- State MSME Associations: 28
- Cluster Associations: 2,500+
- Product Associations: 1,800+
- Export Associations: 450+
- Women Entrepreneur Associations: 250+
- Youth Entrepreneur Forums: 350+

### MSME EMPLOYMENT DETAILS
- Total Employment: 11.1 crore
- Manufacturing: 3.6 crore
- Services: 5.8 crore
- Trade: 1.7 crore
- Male Workers: 7.8 crore (70%)
- Female Workers: 3.3 crore (30%)
- Skilled Workers: 4.5 crore
- Semi-skilled: 3.8 crore
- Unskilled: 2.8 crore
- Average Wage: ₹15,000-25,000/month
- Minimum Wage Compliance: 75%
- Social Security Coverage: 35%
- EPF Coverage: 2.5 crore
- ESI Coverage: 1.8 crore
- Apprentices: 12 lakh
- Contract Workers: 2.5 crore
- Permanent Workers: 6.5 crore
- Seasonal Workers: 2.1 crore

### MSME PRODUCTIVITY & PERFORMANCE
- Average Revenue: ₹15 lakh per unit
- Average Profit Margin: 8-12%
- Capacity Utilization: 65%
- Growth Rate: 12% CAGR
- Survival Rate (5 years): 55%
- Closure Rate: 8% annually
- Sick MSMEs: 3.5 lakh
- Revival Success: 35%
- Productivity per Worker: ₹8.5 lakh/year
- Asset Turnover: 2.5x
- Working Capital Cycle: 90 days
- Debt-Equity Ratio: 1.8:1
- Return on Investment: 15%
- Export Intensity: 8%
- Import Dependence: 25%

### MSME INFRASTRUCTURE
- Industrial Estates: 3,800+
- Growth Centers: 350
- Industrial Parks: 650
- Technology Parks: 180
- Export Promotion Parks: 85
- Food Parks: 42 operational
- Textile Parks: 38
- Leather Parks: 12
- Pharma Parks: 8
- Electronics Parks: 25
- IT Parks: 150+
- Biotech Parks: 20
- Plastic Parks: 15
- Ceramic Parks: 8
- Footwear Parks: 6
- Toy Clusters: 12
- Sports Goods Parks: 4
- Furniture Hubs: 45
- Agro-Processing Centers: 250+
- Cold Chain Infrastructure: 850 centers

### MSME TRAINING & SKILL DEVELOPMENT
- ITIs (Industrial Training Institutes): 14,900+
- ITI Seats: 25 lakh
- Polytechnics: 3,200+
- Skill Development Centers: 5,500+
- Entrepreneurship Training: 12 lakh annually
- Management Training: 5 lakh annually
- Technical Training: 18 lakh annually
- Quality Training: 3 lakh annually
- Export Training: 80,000 annually
- Digital Skills: 15 lakh annually
- Financial Literacy: 25 lakh annually
- Tool Room Training: 50,000 annually
- Design Training: 35,000 annually
- Safety Training: 8 lakh annually
- Online Training Programs: 2,500+

### MSME INNOVATION & R&D
- R&D Spending: ₹8,000 crore (0.5% of turnover)
- Patent Applications: 12,000 annually
- Patents Granted: 4,500 annually
- Trademarks: 85,000 annually
- Design Registrations: 15,000 annually
- Innovation Centers: 250+
- Prototyping Labs: 180+
- Testing Facilities: 850+
- Collaborative R&D: 5,500 projects
- University Partnerships: 1,200+
- CSIR Collaborations: 450 MSMEs
- New Product Development: 25,000 annually
- Process Innovation: 18,000 MSMEs
- Technology Licensing: 3,500 agreements
- Technology Transfer: 2,200 cases

### MSME QUALITY & STANDARDS
- ISO 9001 Certified: 45,000 MSMEs
- ISO 14001 (Environment): 12,000 MSMEs
- ISO 45001 (Safety): 8,500 MSMEs
- BIS Certifications: 65,000 MSMEs
- HACCP (Food): 8,000 MSMEs
- GMP Certified: 12,000 MSMEs
- CE Marking: 15,000 MSMEs
- FDA Approvals: 3,500 MSMEs
- Export Certifications: 25,000 MSMEs
- Quality Testing: 8 lakh tests annually
- Product Recalls: 2,500 annually
- Quality Awards: 850 annually
- Kaizen Implementation: 18,000 MSMEs
- Six Sigma: 5,500 MSMEs
- Lean Manufacturing: 12,000 MSMEs

### MSME COVID-19 IMPACT & RECOVERY
- Units Affected: 5.5 crore (87%)
- Revenue Loss: ₹12 lakh crore (2020-21)
- Job Losses: 1.5 crore (temporary)
- Permanent Closures: 12 lakh units
- ECLGS Support: ₹5 lakh crore
- Recovery Rate: 85% (by 2023)
- Digital Adoption Increase: 45%
- E-Commerce Growth: 80%
- Online Sales: ₹2.5 lakh crore
- Work from Home: 25 lakh MSMEs enabled
- Business Model Pivots: 8 lakh MSMEs
- Diversification: 12 lakh MSMEs
- Resilience Building: ₹5,000 crore investment

### MSME TARGETS & VISION 2030
- Target MSMEs: 10 crore units
- Target Employment: 15 crore
- Target GDP Contribution: 40%
- Target Exports: $300 billion
- Target Credit: ₹50 lakh crore
- Target Digital MSMEs: 6 crore
- Target Green MSMEs: 50 lakh
- Target Global Champions: 10,000 MSMEs
- Target Innovation: ₹25,000 crore R&D
- Target Skilled Workers: 8 crore
- Target Women MSMEs: 3.5 crore
- Target Rural MSMEs: 5 crore
- Target by 2030: $1 trillion MSME economy

## TEXTILES & APPAREL

### OVERALL INDUSTRY
- Textile Industry Size: $165 billion (2023-24)
- Domestic Market: $110 billion
- Export Market: $55 billion
- GDP Contribution: 2.3%
- Manufacturing GDP: 7%
- Industrial Production: 5%
- World Ranking: 6th largest exporter
- Employment: 4.5 crore
- Women Employment: 60% (2.7 crore)
- Second Largest Employer (after agriculture)
- FDI (2000-2024): $4.2 billion

### PRODUCTION STATISTICS
- Cotton Production: 335 lakh bales (170 kg each)
- Cotton Yarn: 4,800 million kg
- Blended Yarn: 1,200 million kg
- Synthetic Yarn: 2,500 million kg
- Filament Yarn: 1,800 million kg
- Total Yarn: 10,300 million kg
- Fabric Production: 95,000 million sq meters
- Cotton Fabric: 45,000 million sq meters
- Synthetic Fabric: 35,000 million sq meters
- Blended Fabric: 15,000 million sq meters
- Apparel Production: $65 billion
- Home Textiles: $18 billion
- Technical Textiles: $21 billion
- Made-ups: $12 billion
"""
    return content

# ==================== MAIN EXECUTION ====================

def main():
    """Main execution function"""
    
    start_time = datetime.now()
    
    print("\n" + "="*70)
    print("🎯 RBI GRADE B - CURRENT AFFAIRS QUESTION GENERATOR")
    print("="*70)
    print(f"📅 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Load content
    content, content_mode = load_current_affairs_content(CURRENT_AFFAIRS_FILE)
    
    if not content:
        print("\n❌ ERROR: No content available!")
        return
    
    # Step 2: Upload to Gemini (if file mode)
    uploaded_content, content_type = upload_to_gemini(content, content_mode)
    
    if not uploaded_content:
        print("\n❌ ERROR: Content preparation failed!")
        return
    
    # Step 3: Generate questions
    questions = generate_all_current_affairs_questions(
        uploaded_content,
        content_type,
        TOTAL_QUESTIONS,
        DIFFICULTY_WEIGHTS
    )
    
    if not questions:
        print("\n❌ ERROR: No questions generated!")
        return
    
    # Step 4: Validate questions
    validate_questions(questions)
    
    # Step 5: Save questions
    output_file = save_current_affairs_questions(questions)
    
    # Step 6: Print statistics
    print_final_statistics(questions, start_time)
    
    print(f"\n✅ SUCCESS! Generated {len(questions)} questions")
    print(f"📁 Output: {output_file}")
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
