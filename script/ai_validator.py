#!/usr/bin/env python3
"""
RBI Quiz JSON Validator & Fixer
Validates quiz JSON files and fixes issues using GPT-4o
Author: Quiz Automation System
Date: 2025
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Tuple
import openai
from pathlib import Path
import shutil

# ================================
# 📁 FILE CONFIGURATION
# ================================

# Input files (modify these paths)
INPUT_FILES = [
    "generated_tests/quizmaker_ready/quiz_maker_import_rbi_phase1_mock_01.json",
    "generated_tests/quizmaker_ready/quiz_maker_import_rbi_phase1_mock_02.json",
    "generated_tests/quizmaker_ready/quiz_maker_import_rbi_phase1_mock_03.json",
    "generated_tests/quizmaker_ready/quiz_maker_import_rbi_phase1_mock_04.json",
    "generated_tests/quizmaker_ready/quiz_maker_import_rbi_phase1_mock_05.json",
    "generated_tests/quizmaker_ready/quiz_maker_import_rbi_phase1_mock_06.json",
    "generated_tests/quizmaker_ready/quiz_maker_import_rbi_phase1_mock_07.json"
]

# Output directory for fixed files
OUTPUT_DIR = "generated_tests/quizmaker_ready/fixed_quizzes"

# Backup directory (original files saved here)
BACKUP_DIR = "generated_tests/quizmaker_ready/backup/original_quizzes"

# Report directory (HTML reports saved here)
REPORT_DIR = "generated_tests/quizmaker_ready/reports"

# ================================
# 🔑 API CONFIGURATION
# ================================

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("❌ Please set OPENAI_API_KEY environment variable")

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ================================
# 📊 QUIZ STRUCTURE RULES
# ================================

# Valid categories with expected question counts
CATEGORY_RULES = {
    "General Awareness": 80,
    "Arithmetic": 15,
    "Reasoning": 60,
    "English Language": 30,
    "Data Interpretation": 15
}

TOTAL_QUESTIONS = 200  # Sum of all categories

# Weight configuration
CORRECT_WEIGHT = 1
INCORRECT_WEIGHT = -0.25

# ================================
# UTILITY FUNCTIONS
# ================================

def setup_directories():
    """Create necessary directories if they don't exist"""
    for directory in [OUTPUT_DIR, BACKUP_DIR, REPORT_DIR]:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print("✅ Directories initialized")

def backup_file(filepath: str) -> str:
    """Create backup of original file"""
    filename = Path(filepath).name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{Path(filename).stem}_backup_{timestamp}.json"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    shutil.copy2(filepath, backup_path)
    return backup_path

# ================================
# STAGE 1: LOCAL VALIDATION
# ================================

class QuizValidator:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = Path(filepath).name
        self.errors = []
        self.warnings = []
        self.data = None
        self.stats = {}
        
    def validate(self) -> Tuple[bool, List[str], List[str], Dict]:
        """Run all validation checks"""
        print(f"\n{'='*80}")
        print(f"🔍 VALIDATING: {self.filename}")
        print(f"{'='*80}\n")
        
        # Load JSON
        if not self._load_json():
            return False, self.errors, self.warnings, {}
            
        # Run all checks
        self._check_structure()
        self._check_question_count()
        self._check_category_distribution()
        self._check_duplicate_ids()
        self._check_questions()
        self._check_answers()
        self._check_weights()
        self._check_categories()
        self._gather_statistics()
        
        # Summary
        has_errors = len(self.errors) > 0
        print(f"\n{'='*80}")
        print(f"📊 VALIDATION SUMMARY: {self.filename}")
        print(f"{'='*80}")
        print(f"❌ Critical Errors: {len(self.errors)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"📝 Total Questions: {len(self.data)}")
        print(f"✅ Status: {'FAILED' if has_errors else 'PASSED'}")
        
        return not has_errors, self.errors, self.warnings, self.stats
    
    def _load_json(self) -> bool:
        """Load and parse JSON file"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ JSON syntax valid")
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON Syntax Error at line {e.lineno}: {e.msg}")
            print(f"❌ JSON syntax invalid: {e}")
            return False
        except Exception as e:
            self.errors.append(f"File Error: {str(e)}")
            print(f"❌ Cannot read file: {e}")
            return False
    
    def _check_structure(self):
        """Validate basic structure"""
        if not isinstance(self.data, list):
            self.errors.append("❌ Root element must be an array")
            return
            
        required_fields = ["id", "question", "type", "category", "answers", "explanation", "published", "weight"]
        
        for idx, q in enumerate(self.data):
            q_num = idx + 1
            q_id = q.get("id", "unknown")
            
            # Check required fields
            for field in required_fields:
                if field not in q:
                    self.errors.append(f"❌ Q{q_num} (ID:{q_id}): Missing required field '{field}'")
            
            # Check data types
            if "id" in q and not isinstance(q["id"], str):
                self.errors.append(f"❌ Q{q_num}: 'id' must be string, got {type(q['id']).__name__}")
            
            if "question" in q and not isinstance(q["question"], str):
                self.errors.append(f"❌ Q{q_num} (ID:{q_id}): 'question' must be string")
            
            if "answers" in q and not isinstance(q["answers"], list):
                self.errors.append(f"❌ Q{q_num} (ID:{q_id}): 'answers' must be array")
            
            if "type" in q and q["type"] != "radio":
                self.warnings.append(f"⚠️ Q{q_num} (ID:{q_id}): Unexpected type '{q['type']}', expected 'radio'")
            
            if "published" in q and q["published"] not in ["0", "1", 0, 1]:
                self.warnings.append(f"⚠️ Q{q_num} (ID:{q_id}): 'published' should be '0' or '1', got '{q['published']}'")
    
    def _check_question_count(self):
        """Check if total question count is correct"""
        actual_count = len(self.data)
        if actual_count != TOTAL_QUESTIONS:
            self.errors.append(f"❌ Expected {TOTAL_QUESTIONS} questions, found {actual_count}")
        else:
            print(f"✅ Question count correct: {TOTAL_QUESTIONS}")
    
    def _check_category_distribution(self):
        """Check if category distribution matches expected counts"""
        category_counts = {}
        
        for q in self.data:
            category = q.get("category", "Unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print(f"\n📊 Category Distribution:")
        print(f"{'-'*60}")
        
        for category, expected_count in CATEGORY_RULES.items():
            actual_count = category_counts.get(category, 0)
            status = "✅" if actual_count == expected_count else "❌"
            
            print(f"{status} {category:25} Expected: {expected_count:3} | Actual: {actual_count:3}")
            
            if actual_count != expected_count:
                difference = actual_count - expected_count
                sign = "+" if difference > 0 else ""
                self.errors.append(
                    f"❌ Category '{category}': Expected {expected_count} questions, "
                    f"found {actual_count} ({sign}{difference})"
                )
        
        # Check for unknown categories
        for category, count in category_counts.items():
            if category not in CATEGORY_RULES:
                self.errors.append(f"❌ Unknown category '{category}' found ({count} questions)")
                print(f"❌ {'Unknown Category':25} Found: {count} questions - '{category}'")
        
        print(f"{'-'*60}\n")
    
    def _check_duplicate_ids(self):
        """Check for duplicate question IDs"""
        ids = [q.get("id") for q in self.data if "id" in q]
        seen = {}
        duplicates = []
        
        for idx, id_val in enumerate(ids):
            if id_val in seen:
                duplicates.append(f"ID '{id_val}' (positions {seen[id_val]+1} and {idx+1})")
            else:
                seen[id_val] = idx
        
        if duplicates:
            self.errors.append(f"❌ Duplicate IDs found: {'; '.join(duplicates)}")
        else:
            print(f"✅ No duplicate IDs found")
    
    def _check_questions(self):
        """Validate question content"""
        for idx, q in enumerate(self.data):
            q_num = idx + 1
            q_id = q.get("id", "unknown")
            
            # Empty question
            question_text = q.get("question", "").strip()
            if not question_text:
                self.errors.append(f"❌ Q{q_num} (ID:{q_id}): Question text is empty")
            
            # Question too short
            elif len(question_text) < 10:
                self.warnings.append(f"⚠️ Q{q_num} (ID:{q_id}): Question seems too short ({len(question_text)} chars)")
            
            # Missing explanation
            explanation = q.get("explanation", "").strip()
            if not explanation:
                self.warnings.append(f"⚠️ Q{q_num} (ID:{q_id}): Missing or empty explanation")
            
            # Check for common formatting issues
            if "  " in question_text:
                self.warnings.append(f"⚠️ Q{q_num} (ID:{q_id}): Multiple consecutive spaces in question")
            
            if question_text != question_text.strip():
                self.warnings.append(f"⚠️ Q{q_num} (ID:{q_id}): Question has leading/trailing whitespace")
            
            # Check for placeholder text
            placeholders = ["lorem ipsum", "test question", "sample", "TODO", "xxx"]
            if any(placeholder in question_text.lower() for placeholder in placeholders):
                self.errors.append(f"❌ Q{q_num} (ID:{q_id}): Contains placeholder text")
            
            # Check question_image field based on category
            category = q.get("category", "")
            question_image = q.get("question_image")
            
            if category == "Data Interpretation":
                # DI questions must have a question_image with a hyperlink
                if not question_image or question_image.strip() == "":
                    self.errors.append(f"❌ Q{q_num} (ID:{q_id}): Data Interpretation question missing 'question_image' field")
                elif not self._is_valid_hyperlink(question_image):
                    self.errors.append(f"❌ Q{q_num} (ID:{q_id}): Data Interpretation 'question_image' is not a valid hyperlink: '{question_image}'")
            else:
                # Non-DI questions should have question_image=null
                if question_image is not None and question_image != "":
                    self.warnings.append(f"⚠️ Q{q_num} (ID:{q_id}): Non-DI question has 'question_image' field (should be null): '{question_image}'")
    
    def _is_valid_hyperlink(self, url: str) -> bool:
        """Check if the given string is a valid hyperlink"""
        if not url or not isinstance(url, str):
            return False
        
        url = url.strip()
        
        # Check for common URL patterns
        url_patterns = [
            r'^https?://',  # http:// or https://
            r'^www\.',      # www.
            r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # domain.com pattern
            r'^/[a-zA-Z0-9/_.-]+',  # relative path starting with /
            r'^[a-zA-Z0-9/_.-]+\.(png|jpg|jpeg|gif|svg|pdf)$'  # file extensions
        ]
        
        import re
        return any(re.match(pattern, url) for pattern in url_patterns)
    
    def _check_answers(self):
        """Validate answer options"""
        for idx, q in enumerate(self.data):
            q_num = idx + 1
            q_id = q.get("id", "unknown")
            answers = q.get("answers", [])
            
            # Must have at least 2 options
            if len(answers) < 2:
                self.errors.append(f"❌ Q{q_num} (ID:{q_id}): Must have at least 2 answer options, found {len(answers)}")
                continue
            
            # Typically should have 4-5 options
            if len(answers) < 4:
                self.warnings.append(f"⚠️ Q{q_num} (ID:{q_id}): Only {len(answers)} options (typically 4-5 expected)")
            
            # Count correct answers
            correct_count = sum(1 for a in answers if str(a.get("correct")) == "1")
            
            if correct_count == 0:
                self.errors.append(f"❌ Q{q_num} (ID:{q_id}): No correct answer marked")
            elif correct_count > 1:
                self.errors.append(f"❌ Q{q_num} (ID:{q_id}): Multiple correct answers marked ({correct_count})")
            
            # Check each answer
            for a_idx, answer in enumerate(answers):
                a_label = chr(65 + a_idx)  # A, B, C, D, E...
                
                # Required fields in answer
                if "answer" not in answer:
                    self.errors.append(f"❌ Q{q_num} (ID:{q_id}) Option {a_label}: Missing 'answer' field")
                
                if "correct" not in answer:
                    self.errors.append(f"❌ Q{q_num} (ID:{q_id}) Option {a_label}: Missing 'correct' field")
                
                if "weight" not in answer:
                    self.errors.append(f"❌ Q{q_num} (ID:{q_id}) Option {a_label}: Missing 'weight' field")
                
                # Empty answer text
                answer_text = answer.get("answer", "").strip()
                if not answer_text:
                    self.errors.append(f"❌ Q{q_num} (ID:{q_id}) Option {a_label}: Answer text is empty")
                
                # Validate correct field
                correct_val = str(answer.get("correct"))
                if correct_val not in ["0", "1"]:
                    self.errors.append(f"❌ Q{q_num} (ID:{q_id}) Option {a_label}: 'correct' must be '0' or '1', got '{correct_val}'")
                
                # Check for duplicate answers
                other_answers = [a.get("answer", "").strip() for i, a in enumerate(answers) if i != a_idx]
                if answer_text in other_answers:
                    self.warnings.append(f"⚠️ Q{q_num} (ID:{q_id}) Option {a_label}: Duplicate answer text found")
    
    def _check_weights(self):
        """Validate weight values"""
        for idx, q in enumerate(self.data):
            q_num = idx + 1
            q_id = q.get("id", "unknown")
            
            # Question weight
            q_weight = q.get("weight")
            if q_weight != CORRECT_WEIGHT:
                self.errors.append(f"❌ Q{q_num} (ID:{q_id}): Question weight is {q_weight}, expected {CORRECT_WEIGHT}")
            
            # Answer weights
            answers = q.get("answers", [])
            for a_idx, answer in enumerate(answers):
                a_label = chr(65 + a_idx)
                weight = answer.get("weight")
                is_correct = str(answer.get("correct")) == "1"
                
                if is_correct and weight != CORRECT_WEIGHT:
                    self.errors.append(
                        f"❌ Q{q_num} (ID:{q_id}) Option {a_label}: "
                        f"Correct answer weight is {weight}, expected {CORRECT_WEIGHT}"
                    )
                
                if not is_correct and weight != INCORRECT_WEIGHT:
                    self.errors.append(
                                                f"❌ Q{q_num} (ID:{q_id}) Option {a_label}: "
                        f"Incorrect answer weight is {weight}, expected {INCORRECT_WEIGHT}"
                    )
    
    def _check_categories(self):
        """Validate categories"""
        valid_categories = list(CATEGORY_RULES.keys())
        
        for idx, q in enumerate(self.data):
            q_num = idx + 1
            q_id = q.get("id", "unknown")
            category = q.get("category", "")
            
            if not category:
                self.errors.append(f"❌ Q{q_num} (ID:{q_id}): Category is empty")
            elif category not in valid_categories:
                self.errors.append(
                    f"❌ Q{q_num} (ID:{q_id}): Invalid category '{category}'. "
                    f"Valid categories: {', '.join(valid_categories)}"
                )
    
    def _gather_statistics(self):
        """Gather quiz statistics"""
        self.stats = {
            "total_questions": len(self.data),
            "categories": {},
            "published_count": 0,
            "unpublished_count": 0,
            "avg_question_length": 0,
            "avg_options_per_question": 0,
            "questions_with_images": 0,
            "answers_with_images": 0
        }
        
        total_q_length = 0
        total_options = 0
        
        for q in self.data:
            # Category stats
            category = q.get("category", "Unknown")
            self.stats["categories"][category] = self.stats["categories"].get(category, 0) + 1
            
            # Published stats
            if str(q.get("published")) == "1":
                self.stats["published_count"] += 1
            else:
                self.stats["unpublished_count"] += 1
            
            # Length stats
            total_q_length += len(q.get("question", ""))
            total_options += len(q.get("answers", []))
            
            # Image stats (only for Data Interpretation questions)
            if q.get("category") == "Data Interpretation" and q.get("question_image"):
                self.stats["questions_with_images"] += 1
            
            for answer in q.get("answers", []):
                if answer.get("image"):
                    self.stats["answers_with_images"] += 1
        
        if self.data:
            self.stats["avg_question_length"] = total_q_length / len(self.data)
            self.stats["avg_options_per_question"] = total_options / len(self.data)

# ================================
# STAGE 2: AI-POWERED DEEP CHECK
# ================================

class AIQuizChecker:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = Path(filepath).name
        self.data = None
        self.ai_report = []
        
    def deep_check(self) -> Dict:
        """Run AI-powered content analysis"""
        print(f"\n{'='*80}")
        print(f"🤖 AI DEEP CHECK: {self.filename}")
        print(f"{'='*80}\n")
        
        # Load data
        with open(self.filepath, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # Process in batches (to avoid token limits)
        batch_size = 25  # Smaller batches for detailed analysis
        total_questions = len(self.data)
        total_batches = (total_questions + batch_size - 1) // batch_size
        
        print(f"Processing {total_questions} questions in {total_batches} batches...")
        print(f"{'-'*80}")
        
        for i in range(0, total_questions, batch_size):
            batch = self.data[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"📦 Batch {batch_num}/{total_batches} (Questions {i+1}-{min(i+batch_size, total_questions)})...", end=" ")
            
            issues = self._check_batch_with_ai(batch, i)
            self.ai_report.extend(issues)
            
            print(f"✅ {len(issues)} issues found")
        
        print(f"{'-'*80}")
        print(f"✅ AI Analysis Complete: {len(self.ai_report)} total issues found\n")
        
        return {
            "filename": self.filename,
            "total_questions": total_questions,
            "issues_found": len(self.ai_report),
            "issues": self.ai_report
        }
    
    def _check_batch_with_ai(self, batch: List[Dict], start_idx: int) -> List[Dict]:
        """Analyze a batch of questions with GPT-4o"""
        
        # Prepare questions for AI
        questions_for_ai = []
        for idx, q in enumerate(batch):
            questions_for_ai.append({
                "position": start_idx + idx + 1,
                "id": q.get("id"),
                "category": q.get("category"),
                "question": q.get("question"),
                "answers": [a.get("answer") for a in q.get("answers", [])],
                "correct_answer": next(
                    (a.get("answer") for a in q.get("answers", []) if str(a.get("correct")) == "1"),
                    None
                ),
                "explanation": q.get("explanation")
            })
        
        prompt = f"""You are an expert quiz validator for RBI (Reserve Bank of India) Grade B exam preparation.

Analyze these questions for the following issues:

1. **Factual Accuracy**: Check if information is correct and current (as of 2025)
2. **Outdated Content**: Flag references to old dates, superseded laws, or obsolete facts
3. **Grammar & Spelling**: Identify language errors
4. **Logic Issues**: Verify the correct answer actually answers the question
5. **Clarity**: Ensure questions and answers are clear and unambiguous
6. **Answer Quality**: Check if explanation is helpful and accurate
7. **Duplicate/Similar Questions**: Identify if questions are too similar to each other

Current date context: October 2025

Questions to analyze:
{json.dumps(questions_for_ai, indent=2)}

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question_position": 1,
    "question_id": "1",
    "severity": "error",
    "type": "outdated",
    "issue": "References September 2025, but we're now in October 2025",
    "suggestion": "Update to 'September 2024' or verify the actual date"
  }}
]

Severity levels:
- "error": Critical issues that make question wrong/unusable
- "warning": Issues that should be reviewed but question is still usable

Type categories:
- "factual": Incorrect facts or data
- "grammar": Language/spelling errors  
- "logic": Answer doesn't match question or explanation wrong
- "outdated": Old dates, superseded information
- "clarity": Ambiguous or confusing wording
- "duplicate": Similar to another question in this batch

If no issues found, return: []

Return ONLY the JSON array, no other text.
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a quiz validation expert. You MUST return only valid JSON array, nothing else."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Lower temperature for more consistent output
                max_tokens=4000
            )
            
            result = response.choices[0].message.content.strip()
            
            # Clean up response if needed
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()
            
            issues = json.loads(result)
            
            # Validate structure
            if not isinstance(issues, list):
                print(f"⚠️ AI returned non-array response")
                return []
            
            return issues
            
        except json.JSONDecodeError as e:
            print(f"⚠️ AI returned invalid JSON: {e}")
            return []
        except Exception as e:
            print(f"⚠️ AI API Error: {e}")
            return []

# ================================
# STAGE 3: AUTO-FIX
# ================================

class QuizFixer:
    def __init__(self, filepath: str, errors: List[str], warnings: List[str]):
        self.filepath = filepath
        self.filename = Path(filepath).name
        self.errors = errors
        self.warnings = warnings
        self.data = None
        self.fixed_count = 0
        self.fixes_applied = []
        
    def auto_fix(self) -> Tuple[bool, str]:
        """Automatically fix common issues"""
        print(f"\n{'='*80}")
        print(f"🔧 AUTO-FIXING: {self.filename}")
        print(f"{'='*80}\n")
        
        # Load data
        with open(self.filepath, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # Apply fixes
        self._fix_weights()
        self._fix_whitespace()
        self._fix_published_field()
        self._normalize_correct_field()
        self._fix_empty_images()
        self._fix_question_ids()
        
        # Save if changes made
        if self.fixed_count > 0:
            output_path = self._save_fixed_file()
            print(f"\n✅ Fixed {self.fixed_count} issues automatically")
            print(f"📄 Saved to: {output_path}")
            return True, output_path
        else:
            print(f"\n✅ No auto-fixable issues found")
            return False, ""
    
    def _fix_weights(self):
        """Fix incorrect weight values"""
        for idx, q in enumerate(self.data):
            q_num = idx + 1
            
            # Fix question weight
            if q.get("weight") != CORRECT_WEIGHT:
                q["weight"] = CORRECT_WEIGHT
                self.fixed_count += 1
                self.fixes_applied.append(f"Q{q_num}: Fixed question weight to {CORRECT_WEIGHT}")
            
            # Fix answer weights
            for a_idx, answer in enumerate(q.get("answers", [])):
                a_label = chr(65 + a_idx)
                is_correct = str(answer.get("correct")) == "1"
                
                expected_weight = CORRECT_WEIGHT if is_correct else INCORRECT_WEIGHT
                
                if answer.get("weight") != expected_weight:
                    answer["weight"] = expected_weight
                    self.fixed_count += 1
                    self.fixes_applied.append(
                        f"Q{q_num} Option {a_label}: Fixed weight to {expected_weight}"
                    )
    
    def _fix_whitespace(self):
        """Fix whitespace issues"""
        for idx, q in enumerate(self.data):
            q_num = idx + 1
            
            # Fix question text
            if "question" in q:
                original = q["question"]
                # Remove leading/trailing whitespace
                fixed = original.strip()
                # Replace multiple spaces with single space
                fixed = re.sub(r'\s+', ' ', fixed)
                
                if fixed != original:
                    q["question"] = fixed
                    self.fixed_count += 1
                    self.fixes_applied.append(f"Q{q_num}: Fixed whitespace in question")
            
            # Fix explanation
            if "explanation" in q:
                original = q["explanation"]
                fixed = original.strip()
                fixed = re.sub(r'\s+', ' ', fixed)
                
                if fixed != original:
                    q["explanation"] = fixed
                    self.fixed_count += 1
                    self.fixes_applied.append(f"Q{q_num}: Fixed whitespace in explanation")
            
            # Fix answers
            for a_idx, answer in enumerate(q.get("answers", [])):
                a_label = chr(65 + a_idx)
                
                if "answer" in answer:
                    original = answer["answer"]
                    fixed = original.strip()
                    fixed = re.sub(r'\s+', ' ', fixed)
                    
                    if fixed != original:
                        answer["answer"] = fixed
                        self.fixed_count += 1
                        self.fixes_applied.append(f"Q{q_num} Option {a_label}: Fixed whitespace")
    
    def _fix_published_field(self):
        """Normalize published field to string "1" or "0" """
        for idx, q in enumerate(self.data):
            q_num = idx + 1
            
            if "published" in q:
                published = q["published"]
                
                # Convert to string
                if published == 1 or published == "1" or published == True:
                    if q["published"] != "1":
                        q["published"] = "1"
                        self.fixed_count += 1
                        self.fixes_applied.append(f"Q{q_num}: Normalized 'published' to '1'")
                else:
                    if q["published"] != "0":
                        q["published"] = "0"
                        self.fixed_count += 1
                        self.fixes_applied.append(f"Q{q_num}: Normalized 'published' to '0'")
    
    def _normalize_correct_field(self):
        """Normalize correct field in answers to string "1" or "0" """
        for idx, q in enumerate(self.data):
            q_num = idx + 1
            
            for a_idx, answer in enumerate(q.get("answers", [])):
                a_label = chr(65 + a_idx)
                
                if "correct" in answer:
                    correct = answer["correct"]
                    
                    # Convert to string
                    if correct == 1 or correct == "1" or correct == True:
                        if answer["correct"] != "1":
                            answer["correct"] = "1"
                            self.fixed_count += 1
                            self.fixes_applied.append(
                                f"Q{q_num} Option {a_label}: Normalized 'correct' to '1'"
                            )
                    else:
                        if answer["correct"] != "0":
                            answer["correct"] = "0"
                            self.fixed_count += 1
                            self.fixes_applied.append(
                                f"Q{q_num} Option {a_label}: Normalized 'correct' to '0'"
                            )
    
    def _fix_empty_images(self):
        """Ensure image fields are properly set based on question category.
        - Data Interpretation questions: question_image should have hyperlink (not empty)
        - Other questions: question_image should be null"""
        for idx, q in enumerate(self.data):
            q_num = idx + 1
            
            # Fix question_image based on category
            category = q.get("category", "")
            if category == "Data Interpretation":
                # DI questions: ensure question_image is not empty (should have hyperlink)
                if "question_image" in q and not q["question_image"]:
                    if q["question_image"] != "":
                        q["question_image"] = ""
                        self.fixed_count += 1
                        self.fixes_applied.append(f"Q{q_num}: Set empty 'question_image' to empty string")
            else:
                # Non-DI questions: set question_image to null
                if "question_image" in q and q["question_image"] is not None and q["question_image"] != "":
                    q["question_image"] = None
                    self.fixed_count += 1
                    self.fixes_applied.append(f"Q{q_num}: Set 'question_image' to null for non-DI question")
            
            # Fix answer images
            for a_idx, answer in enumerate(q.get("answers", [])):
                a_label = chr(65 + a_idx)
                
                if "image" in answer and not answer["image"]:
                    if answer["image"] != "":
                        answer["image"] = ""
                        self.fixed_count += 1
                        self.fixes_applied.append(
                            f"Q{q_num} Option {a_label}: Set empty 'image' to empty string"
                        )
    
    def _fix_question_ids(self):
        """Ensure question IDs are sequential and properly formatted"""
        for idx, q in enumerate(self.data):
            expected_id = str(idx + 1)
            actual_id = str(q.get("id", ""))
            
            if actual_id != expected_id:
                q["id"] = expected_id
                self.fixed_count += 1
                self.fixes_applied.append(
                    f"Q{idx+1}: Fixed ID from '{actual_id}' to '{expected_id}'"
                )
    
    def _save_fixed_file(self) -> str:
        """Save the fixed JSON file"""
        filename = Path(self.filepath).name
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=3, ensure_ascii=False)
        
        return output_path

# ================================
# STAGE 4: REPORT GENERATION
# ================================

class ReportGenerator:
    def __init__(self):
        self.all_results = []
    
    def add_file_result(self, filename: str, validation_result: Dict, ai_result: Dict = None):
        """Add results for a file"""
        self.all_results.append({
            "filename": filename,
            "validation": validation_result,
            "ai_check": ai_result
        })
    
    def generate_html_report(self) -> str:
        """Generate comprehensive HTML report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"quiz_validation_report_{timestamp}.html"
        report_path = os.path.join(REPORT_DIR, report_filename)
        
        html_content = self._build_html()
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path
    
    def _build_html(self) -> str:
        """Build HTML report content"""
        
        # Calculate summary stats
        total_files = len(self.all_results)
        total_errors = sum(len(r["validation"]["errors"]) for r in self.all_results)
        total_warnings = sum(len(r["validation"]["warnings"]) for r in self.all_results)
        total_ai_issues = sum(
            r["ai_check"]["issues_found"] if r["ai_check"] else 0 
            for r in self.all_results
        )
        files_passed = sum(1 for r in self.all_results if len(r["validation"]["errors"]) == 0)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quiz Validation Report - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 36px;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 18px;
            opacity: 0.9;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .stat-number {{
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card.success .stat-number {{ color: #28a745; }}
        .stat-card.error .stat-number {{ color: #dc3545; }}
        .stat-card.warning .stat-number {{ color: #ffc107; }}
        .stat-card.info .stat-number {{ color: #17a2b8; }}
        .stat-card.primary .stat-number {{ color: #667eea; }}
        
        .content {{
            padding: 40px;
        }}
        
        .file-section {{
            margin-bottom: 40px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .file-header {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 2px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .file-header h2 {{
            font-size: 24px;
            color: #333;
        }}
        
        .status-badge {{
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            text-transform: uppercase;
        }}
        
        .status-badge.passed {{
            background: #d4edda;
            color: #155724;
        }}
        
        .status-badge.failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .file-body {{
            padding: 20px;
        }}
        
        .issue-section {{
            margin-bottom: 30px;
        }}
        
        .issue-section h3 {{
            font-size: 18px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #dee2e6;
            color: #495057;
        }}
        
        .issue-list {{
            list-style: none;
        }}
        
        .issue-item {{
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            border-left: 4px solid;
            background: #f8f9fa;
        }}
        
        .issue-item.error {{
            border-left-color: #dc3545;
            background: #fff5f5;
        }}
        
        .issue-item.warning {{
            border-left-color: #ffc107;
            background: #fffbf0;
        }}
        
        .issue-item.ai-error {{
            border-left-color: #e83e8c;
            background: #fff0f6;
        }}
        
        .issue-item.ai-warning {{
            border-left-color: #17a2b8;
            background: #f0f9ff;
        }}
        
        .category-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .category-item {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #dee2e6;
        }}
        
        .category-name {{
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }}
        
        .category-count {{
            color: #6c757d;
            font-size: 14px;
        }}
        
        .ai-issue {{
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 6px;
            background: white;
            border: 1px solid #dee2e6;
        }}
        
        .ai-issue-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-weight: bold;
        }}
        
        .ai-issue-type {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            background: #e9ecef;
            color: #495057;
        }}
        
        .ai-issue-description {{
            margin-bottom: 10px;
            color: #495057;
        }}
        
        .ai-issue-suggestion {{
            padding: 10px;
            background: #e7f3ff;
            border-left: 3px solid #17a2b8;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .no-issues {{
            text-align: center;
            padding: 40px;
            color: #28a745;
            font-size: 18px;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .stat-card:hover {{
                transform: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Quiz Validation Report</h1>
            <p>Generated on {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}</p>
        </div>
        
        <div class="summary">
            <div class="stat-card primary">
                <div class="stat-number">{total_files}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card success">
                <div class="stat-number">{files_passed}</div>
                <div class="stat-label">Files Passed</div>
            </div>
            <div class="stat-card error">
                <div class="stat-number">{total_errors}</div>
                <div class="stat-label">Critical Errors</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-number">{total_warnings}</div>
                <div class="stat-label">Warnings</div>
            </div>
            <div class="stat-card info">
                <div class="stat-number">{total_ai_issues}</div>
                <div class="stat-label">AI Issues</div>
            </div>
        </div>
        
        <div class="content">
"""
        
        # Add each file's results
        for result in self.all_results:
            filename = result["filename"]
            validation = result["validation"]
            ai_check = result["ai_check"]
            
            passed = len(validation["errors"]) == 0
            status_class = "passed" if passed else "failed"
            status_text = "✅ PASSED" if passed else "❌ FAILED"
            
            html += f"""
            <div class="file-section">
                <div class="file-header">
                    <h2>📄 {filename}</h2>
                    <span class="status-badge {status_class}">{status_text}</span>
                </div>
                <div class="file-body">
"""
            
            # Statistics
            stats = validation.get("stats", {})
            if stats:
                html += f"""
                    <div class="issue-section">
                        <h3>📊 Statistics</h3>
                        <div class="category-stats">
                            <div class="category-item">
                                <div class="category-name">Total Questions</div>
                                <div class="category-count">{stats.get('total_questions', 0)}</div>
                            </div>
                            <div class="category-item">
                                <div class="category-name">Published</div>
                                <div class="category-count">{stats.get('published_count', 0)}</div>
                            </div>
                            <div class="category-item">
                                <div class="category-name">Avg Question Length</div>
                                <div class="category-count">{stats.get('avg_question_length', 0):.1f} chars</div>
                            </div>
                            <div class="category-item">
                                <div class="category-name">Avg Options</div>
                                <div class="category-count">{stats.get('avg_options_per_question', 0):.1f}</div>
                            </div>
                        </div>
                    </div>
"""
            
            # Category distribution
            if stats.get("categories"):
                html += """
                    <div class="issue-section">
                        <h3>📚 Category Distribution</h3>
                        <div class="category-stats">
"""
                for category, count in stats["categories"].items():
                    expected = CATEGORY_RULES.get(category, "?")
                    html += f"""
                            <div class="category-item">
                                <div class="category-name">{category}</div>
                                <div class="category-count">{count} / {expected} questions</div>
                            </div>
"""
                html += """
                        </div>
                    </div>
"""
            
            # Errors
            if validation["errors"]:
                html += """
                    <div class="issue-section">
                        <h3>❌ Critical Errors</h3>
                        <ul class="issue-list">
"""
                for error in validation["errors"]:
                    html += f"""
                            <li class="issue-item error">{error}</li>
"""
                html += """
                        </ul>
                    </div>
"""
            
            # Warnings
            if validation["warnings"]:
                html += """
                    <div class="issue-section">
                        <h3>⚠️ Warnings</h3>
                        <ul class="issue-list">
"""
                for warning in validation["warnings"]:
                    html += f"""
                            <li class="issue-item warning">{warning}</li>
"""
                html += """
                        </ul>
                    </div>
"""
            
            # AI Issues
            if ai_check and ai_check.get("issues"):
                html += """
                    <div class="issue-section">
                        <h3>🤖 AI-Detected Issues</h3>
"""
                for issue in ai_check["issues"]:
                    severity_class = f"ai-{issue.get('severity', 'warning')}"
                    issue_type = issue.get('type', 'general')
                    question_pos = issue.get('question_position', '?')
                    question_id = issue.get('question_id', '?')
                    issue_desc = issue.get('issue', 'No description')
                    suggestion = issue.get('suggestion', '')
                    
                    html += f"""
                        <div class="ai-issue">
                            <div class="ai-issue-header">
                                <span>Question #{question_pos} (ID: {question_id})</span>
                                <span class="ai-issue-type">{issue_type}</span>
                            </div>
                            <div class="ai-issue-description">
                                <strong>Issue:</strong> {issue_desc}
                            </div>
"""
                    if suggestion:
                        html += f"""
                            <div class="ai-issue-suggestion">
                                <strong>💡 Suggestion:</strong> {suggestion}
                            </div>
"""
                    html += """
                        </div>
"""
                html += """
                    </div>
"""
            
            # No issues message
            if not validation["errors"] and not validation["warnings"] and (not ai_check or not ai_check.get("issues")):
                html += """
                    <div class="no-issues">
                        ✅ No issues found! This file is perfect.
                    </div>
"""
            
            html += """
                </div>
            </div>
"""
        
        html += f"""
        </div>
        
        <div class="footer">
            <p>RBI Quiz Validation System v2.0 | Powered by GPT-4o</p>
            <p>Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>
"""
        return html

# ================================
# MAIN EXECUTION PIPELINE
# ================================

def validate_single_file(filepath: str, run_ai_check: bool = True, auto_fix: bool = True):
    """Validate a single file"""
    filename = Path(filepath).name
    
    print(f"\n{'#'*80}")
    print(f"# PROCESSING: {filename}")
    print(f"{'#'*80}")
    
    # Create backup
    backup_path = backup_file(filepath)
    print(f"💾 Backup created: {backup_path}")
    
    # Stage 1: Basic Validation
    validator = QuizValidator(filepath)
    passed, errors, warnings, stats = validator.validate()
    
    validation_result = {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "stats": stats
    }
    
    # Stage 2: AI Deep Check (optional)
    ai_result = None
    if run_ai_check and OPENAI_API_KEY != "your-openai-api-key-here":
        try:
            ai_checker = AIQuizChecker(filepath)
            ai_result = ai_checker.deep_check()
        except Exception as e:
            print(f"⚠️ AI check failed: {e}")
    elif run_ai_check:
        print("⚠️ Skipping AI check: OpenAI API key not configured")
    
    # Stage 3: Auto-fix (optional)
    fixed_path = filepath
    if auto_fix and (errors or warnings):
        fixer = QuizFixer(filepath, errors, warnings)
        was_fixed, fixed_path = fixer.auto_fix()
        
        if was_fixed:
            # Re-validate fixed file
            print(f"\n{'='*80}")
            print(f"🔄 RE-VALIDATING FIXED FILE")
            print(f"{'='*80}\n")
            
            validator2 = QuizValidator(fixed_path)
            passed, errors, warnings, stats = validator2.validate()
            
            validation_result = {
                "passed": passed,
                "errors": errors,
                "warnings": warnings,
                "stats": stats,
                "was_fixed": True,
                "fixes_applied": fixer.fixes_applied
            }
    
    return validation_result, ai_result

def main():
    """Main execution function"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                    RBI QUIZ VALIDATION SYSTEM v2.0                            ║
║                                                                               ║
║                    Comprehensive JSON Validator & Fixer                       ║
║                         Powered by GPT-4o AI                                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Setup
    print("\n🔧 Initializing system...")
    setup_directories()
    
    # Configuration summary
    print(f"\n📋 Configuration:")
    print(f"{'─'*80}")
    print(f"Input files: {len(INPUT_FILES)}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Backup directory: {BACKUP_DIR}")
    print(f"Report directory: {REPORT_DIR}")
    print(f"Total expected questions per file: {TOTAL_QUESTIONS}")
    print(f"AI Deep Check: {'Enabled' if OPENAI_API_KEY != 'your-openai-api-key-here' else 'Disabled (no API key)'}")
    print(f"{'─'*80}")
    
    print(f"\n📊 Expected Category Distribution:")
    print(f"{'─'*80}")
    for category, count in CATEGORY_RULES.items():
        print(f"  • {category:25} {count:3} questions")
    print(f"{'─'*80}")
    
    # Ask user for options
    print(f"\n⚙️  Options:")
    try:
        run_ai = input("Run AI deep check? (y/n) [y]: ").strip().lower() or 'y'
    except (EOFError, KeyboardInterrupt):
        run_ai = 'y'  # Default to yes in non-interactive environments
        print("y (default)")
    run_ai = run_ai == 'y'
    
    try:
        auto_fix = input("Auto-fix issues? (y/n) [y]: ").strip().lower() or 'y'
    except (EOFError, KeyboardInterrupt):
        auto_fix = 'y'  # Default to yes in non-interactive environments
        print("y (default)")
    auto_fix = auto_fix == 'y'
    
    # Process all files
    report_gen = ReportGenerator()
    
    for idx, filepath in enumerate(INPUT_FILES, 1):
        if not os.path.exists(filepath):
            print(f"\n⚠️ File not found: {filepath}")
            continue
        
        print(f"\n{'='*80}")
        print(f"Processing file {idx}/{len(INPUT_FILES)}")
        print(f"{'='*80}")
        
        try:
            validation_result, ai_result = validate_single_file(
                filepath, 
                run_ai_check=run_ai, 
                auto_fix=auto_fix
            )
            
            report_gen.add_file_result(
                Path(filepath).name,
                validation_result,
                ai_result
            )
            
        except Exception as e:
            print(f"❌ Error processing file: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate report
    print(f"\n{'='*80}")
    print(f"📝 GENERATING COMPREHENSIVE REPORT")
    print(f"{'='*80}\n")
    
    report_path = report_gen.generate_html_report()
    print(f"✅ Report generated: {report_path}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"✅ VALIDATION COMPLETE")
    print(f"{'='*80}")
    print(f"Files processed: {len(INPUT_FILES)}")
    print(f"Report: {report_path}")
    print(f"Fixed files: {OUTPUT_DIR}")
    print(f"Backups: {BACKUP_DIR}")
    print(f"{'='*80}\n")
    
    # Open report (optional)
    try:
        open_report = input("Open report in browser? (y/n) [y]: ").strip().lower() or 'y'
    except (EOFError, KeyboardInterrupt):
        open_report = 'n'  # Default to no in non-interactive environments
        print("n (default)")
    if open_report == 'y':
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(report_path)}")

# ================================
# ENTRY POINT
# ================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
