# convert_to_json_debug.py
import re
import json
import os
from typing import Dict, List, Tuple

class RBIQuestionParser:
    def __init__(self):
        self.sections = {
            "General Awareness": "General_Awareness",
            "English": "English", 
            "Quantitative Aptitude": "Quantitative_Aptitude",
            "Reasoning": "Reasoning"
        }
        
    def parse_questions_file(self, filepath: str) -> Dict:
        """Parse the questions text file with debugging"""
        print("🔍 DEBUG: Opening questions file...")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 File size: {len(content)} characters")
        
        # Show first 500 characters to see format
        print("📝 First 500 characters of file:")
        print("-" * 50)
        print(content[:500])
        print("-" * 50)
        
        questions_by_section = {}
        current_section = None
        
        # Split by lines for easier processing
        lines = content.split(' ')
        print(f"📊 Total lines in file: {len(lines)}")
        
        # Look for section headers
        section_count = 0
        for i, line in enumerate(lines[:50]):  # Check first 50 lines
            if '--' in line or '—' in line:  # Check both dash types
                print(f"Line {i}: Potential section header: '{line.strip()}'")
                section_count += 1
        
        print(f"🔍 Found {section_count} potential section headers")
        
        # Try to find questions
        question_count = 0
        for i, line in enumerate(lines[:100]):  # Check first 100 lines
            if re.search(r'Q\.\s*\d+\s*\)', line):
                print(f"Line {i}: Found question: '{line.strip()[:50]}...'")
                question_count += 1
                if question_count >= 3:  # Just show first 3
                    break
        
        print(f"🔍 Found {question_count} questions in first 100 lines")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Try multiple section header formats
            # Check for -- or — (em dash)
            if ('--' in line or '—' in line) and len(line) > 4:
                # Clean up the section name
                section_name = line.replace('--', '').replace('—', '').strip()
                print(f"🎯 Found section marker at line {i}: '{section_name}'")
                
                # Try to match section name
                for known_section, code in self.sections.items():
                    if known_section.lower() in section_name.lower():
                        current_section = code
                        questions_by_section[current_section] = []
                        print(f"   ✅ Matched to section: {current_section}")
                        break
                
                if not current_section and section_name:
                    print(f"   ⚠️ Could not match section: '{section_name}'")
                    print(f"   Known sections: {list(self.sections.keys())}")
                
                i += 1
                continue
            
            # Try multiple question formats
            # More flexible regex for Q.1) or Q. 1) or Q.1 )
            q_match = re.match(r'Q\.\s*(\d+)\s*\)', line)
            if q_match and current_section:
                q_num = int(q_match.group(1))
                print(f"📝 Found Question {q_num} in {current_section}")
                
                # Get question text
                question_text = ""
                i += 1
                
                # Read until we hit options
                while i < len(lines) and not re.match(r'^\s*$[a-eA-E]$', lines[i]):
                    if lines[i].strip() and not lines[i].strip().startswith('Q.'):
                        question_text += lines[i].strip() + " "
                    i += 1
                
                print(f"   Question text length: {len(question_text)}")
                
                # Read options
                options = {}
                while i < len(lines) and re.match(r'^\s*$([a-eA-E])$', lines[i]):
                    opt_match = re.match(r'^\s*$([a-eA-E])$\s*(.*)', lines[i])
                    if opt_match:
                        letter = opt_match.group(1).upper()
                        opt_text = opt_match.group(2).strip()
                        options[letter] = opt_text
                    i += 1
                
                print(f"   Found {len(options)} options")
                
                if current_section not in questions_by_section:
                    questions_by_section[current_section] = []
                
                questions_by_section[current_section].append({
                    "number": q_num,
                    "text": question_text.strip(),
                    "options": options,
                    "section": current_section
                })
            else:
                i += 1
        
        print(f"📊 Final parsing summary:")
        for section, questions in questions_by_section.items():
            print(f"  {section}: {len(questions)} questions")
        
        return questions_by_section
    
    def parse_answers_file(self, filepath: str) -> Dict:
        """Parse the answers text file with debugging"""
        print("🔍 DEBUG: Opening answers file...")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 File size: {len(content)} characters")
        
        # Show first 500 characters
        print("📝 First 500 characters of file:")
        print("-" * 50)
        print(content[:500])
        print("-" * 50)
        
        answers_by_section = {}
        current_section = None
        
        lines = content.split(' ')
        print(f"📊 Total lines in file: {len(lines)}")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for section header (both -- and —)
            if ('--' in line or '—' in line) and len(line) > 4:
                section_name = line.replace('--', '').replace('—', '').strip()
                print(f"🎯 Found section: '{section_name}'")
                
                for known_section, code in self.sections.items():
                    if known_section.lower() in section_name.lower():
                        current_section = code
                        answers_by_section[current_section] = {}
                        print(f"   ✅ Matched to: {current_section}")
                        break
                
                i += 1
                continue
            
            # More flexible answer matching
            # Try multiple formats: Q.1) Ans: (a) or Q.1 ) Ans: (a) etc.
            ans_match = re.match(r'Q\.\s*(\d+)\s*\)\s*Ans\s*:\s*$([a-eA-E])$', line, re.IGNORECASE)
            if ans_match and current_section:
                q_num = int(ans_match.group(1))
                answer = ans_match.group(2).upper()
                
                print(f"   Found Answer Q.{q_num}: {answer}")
                
                # Get explanation
                explanation = ""
                i += 1
                
                while i < len(lines):
                    next_line = lines[i].strip()
                    
                    if (next_line.startswith('Q.') and ')' in next_line) or \
                       ('--' in next_line or '—' in next_line):
                        break
                    
                    if next_line.startswith('EXP:'):
                        next_line = next_line[4:].strip()
                    
                    if next_line:
                        explanation += next_line + " "
                    
                    i += 1
                
                if current_section not in answers_by_section:
                    answers_by_section[current_section] = {}
                    
                answers_by_section[current_section][q_num] = {
                    "answer": answer,
                    "explanation": explanation.strip()
                }
            else:
                i += 1
        
        print(f"📊 Answers parsing summary:")
        for section, answers in answers_by_section.items():
            print(f"  {section}: {len(answers)} answers")
        
        return answers_by_section
    
    def determine_difficulty(self, question_text: str, options: Dict) -> str:
        """Determine difficulty based on question characteristics"""
        
        if not options:  # Safety check
            return "Easy"
        
        # Check all options text combined
        all_options_text = " ".join(options.values()).lower()
        
        # Hard if options contain these patterns
        hard_indicators = [
            " and ",
            " only",
            ",",  # Multiple items in options
            "1)", "2)", "3)",  # Numbered sub-options
            "i)", "ii)", "iii)",  # Roman numeral sub-options
        ]
        
        for indicator in hard_indicators:
            if indicator in all_options_text:
                return "Hard"
        
        # Also check question text length and complexity
        if len(question_text) > 400:  # Long questions are usually harder
            return "Hard"
        
        return "Easy"
    
    def merge_questions_and_answers(self, questions_file: str, answers_file: str) -> List[Dict]:
        """Merge questions and answers into final format"""
        
        print("" + "="*60)
        print("📖 PARSING QUESTIONS FILE")
        print("="*60)
        questions_by_section = self.parse_questions_file(questions_file)
        
        print("" + "="*60)
        print("📖 PARSING ANSWERS FILE")
        print("="*60)
        answers_by_section = self.parse_answers_file(answers_file)
        
        all_questions = []
        question_id = 1
        
        print("" + "="*60)
        print("🔄 MERGING QUESTIONS AND ANSWERS")
        print("="*60)
        
        for section, questions in questions_by_section.items():
            print(f"📝 Processing {section}: {len(questions)} questions")
            
            section_answers = answers_by_section.get(section, {})
            print(f"   Found {len(section_answers)} answers for this section")
            
            for q in questions:
                q_num = q['number']
                
                # Get answer and explanation
                answer_data = section_answers.get(q_num, {})
                
                # Determine difficulty
                difficulty = self.determine_difficulty(q['text'], q['options'])
                
                # Create final question object
                final_question = {
                    "id": question_id,
                    "question_number": q_num,
                    "text": q['text'],
                    "options": q['options'],
                    "correct_answer": answer_data.get('answer', None),
                    "explanation": answer_data.get('explanation', ''),
                    "subject": section,
                    "difficulty": difficulty,
                    "year": 2023,
                    "exam": "RBI Grade B Phase 1"
                }
                
                all_questions.append(final_question)
                question_id += 1
        
        return all_questions

def main():
    """Main conversion function with better error handling"""
    
    parser = RBIQuestionParser()
    
    # Define base directory and file paths
    base_dir = "rbi_txt/2023"
    questions_file = os.path.join(base_dir, "RBI_PYP_PHASE_01_2023_Questions.txt")
    answers_file = os.path.join(base_dir, "RBI_PYP_PHASE_01_2023_Solutions.txt")
    
    print("🚀 RBI Question Parser - DEBUG VERSION")
    print("=" * 60)
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"📄 Questions file: {questions_file}")
    print(f"📄 Answers file: {answers_file}")
    print("=" * 60)
    
    # Check if files exist
    if not os.path.exists(questions_file):
        print(f"❌ Questions file not found: {questions_file}")
        return
    
    if not os.path.exists(answers_file):
        print(f"❌ Answers file not found: {answers_file}")
        return
    
    try:
        # Parse and merge
        all_questions = parser.merge_questions_and_answers(questions_file, answers_file)
        
        if not all_questions:
            print("❌ No questions were extracted!")
            print("Possible issues:")
            print("1. Section headers format might be different")
            print("2. Question format might be different")
            print("3. File encoding issues")
            print("Please check the debug output above for clues.")
            return
        
        # Statistics
        stats = {
            "total": len(all_questions),
            "by_subject": {},
            "by_difficulty": {"Easy": 0, "Hard": 0},
            "with_answers": 0,
            "with_explanations": 0
        }
        
        for q in all_questions:
            # Subject stats
            subject = q['subject']
            stats['by_subject'][subject] = stats['by_subject'].get(subject, 0) + 1
            
            # Difficulty stats
            stats['by_difficulty'][q['difficulty']] += 1
            
            # Answer stats
            if q['correct_answer']:
                stats['with_answers'] += 1
            if q['explanation']:
                stats['with_explanations'] += 1
        
        # Create final JSON
        output = {
            "metadata": {
                "source": "RBI Grade B 2023 Phase 1",
                "total_questions": len(all_questions),
                "statistics": stats
            },
            "questions": all_questions
        }
        
        # Save to JSON
        output_file = os.path.join(base_dir, "RBI_PYP_PHASE_01_2023_Complete.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully saved {len(all_questions)} questions to:")
        print(f"   {output_file}")
        
        # Print summary
        print("📊 Summary:")
        print(f"Total Questions: {stats['total']}")
        print(f"With Answers: {stats['with_answers']}")
        print(f"With Explanations: {stats['with_explanations']}")
        
        if stats['total'] > 0:
            print("📚 By Subject:")
            for subject, count in stats['by_subject'].items():
                print(f"  • {subject}: {count}")
            
            print("📈 By Difficulty:")
            for diff, count in stats['by_difficulty'].items():
                percentage = (count / stats['total']) * 100
                print(f"  • {diff}: {count} ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
