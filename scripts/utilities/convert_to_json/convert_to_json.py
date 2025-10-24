# convert_to_json_fixed.py
import re
import json
import os
from typing import Dict, List, Tuple

class RBIQuestionParser:
    def __init__(self):
        # Define question number ranges for each subject
        self.subject_ranges = {
            "General_Awareness": (1, 80),
            "English": (81, 110),
            "Quantitative_Aptitude": (111, 140),
            "Reasoning": (141, 200)
        }
    
    def get_subject_by_question_number(self, q_num: int) -> str:
        """Determine subject based on question number"""
        for subject, (start, end) in self.subject_ranges.items():
            if start <= q_num <= end:
                return subject
        return "Unknown"
    
    def find_all_question_positions(self, lines: List[str]) -> List[Tuple[int, int]]:
        """Find all question start positions and their numbers"""
        question_positions = []
        
        for i, line in enumerate(lines):
            # Match Q.1) or Q.1 ) pattern
            match = re.match(r'^Q\.(\d+)\s*\)', line.strip())
            if match:
                q_num = int(match.group(1))
                question_positions.append((i, q_num))
                
        return question_positions
    
    def parse_single_question(self, lines: List[str], start_idx: int, end_idx: int, q_num: int) -> Dict:
        """Parse a single question from start_idx to end_idx"""
        
        # Get subject
        subject = self.get_subject_by_question_number(q_num)
        
        # Extract question text
        question_text = ""
        i = start_idx + 1  # Skip the Q.X) line
        
        # Read until we find (a) or reach the end
        while i < end_idx:
            line = lines[i].strip()
            
            # Stop when we hit the first option
            if line.startswith('(a)'):
                break
                
            # Add to question text
            if line and not line.startswith('('):
                question_text += line + " "
            
            i += 1
        
        # Parse options
        options = {}
        option_letters = ['a', 'b', 'c', 'd', 'e']
        current_option = None
        current_option_text = ""
        
        while i < end_idx:
            line = lines[i].strip()
            
            # Check if this is a new option
            is_new_option = False
            for letter in option_letters:
                if line.startswith(f'({letter})'):
                    # Save previous option if exists
                    if current_option:
                        options[current_option.upper()] = current_option_text.strip()
                    
                    # Start new option
                    current_option = letter
                    current_option_text = line[3:].strip()  # Remove (a) part
                    is_new_option = True
                    break
            
            if not is_new_option and current_option:
                # Continue building current option text
                if line and not line.startswith('Q.'):
                    current_option_text += " " + line
            
            i += 1
        
        # Save last option
        if current_option:
            options[current_option.upper()] = current_option_text.strip()
        
        return {
            "number": q_num,
            "text": question_text.strip(),
            "options": options,
            "subject": subject
        }
    
    def parse_questions_file(self, filepath: str) -> List[Dict]:
        """Parse questions from text file"""
        print("📖 Parsing questions file...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('  ')
        print(f"📊 Total lines: {len(lines)}")
        
        # First, find all question positions
        print("🔍 Finding all question positions...")
        question_positions = self.find_all_question_positions(lines)
        print(f"📊 Found {len(question_positions)} questions")
        
        # Show distribution
        if question_positions:
            print(f"   First question: Q.{question_positions[0][1]} at line {question_positions[0][0]}")
            print(f"   Last question: Q.{question_positions[-1][1]} at line {question_positions[-1][0]}")
        
        # Parse each question
        questions = []
        
        for idx, (line_num, q_num) in enumerate(question_positions):
            # Determine where this question ends
            if idx + 1 < len(question_positions):
                # Next question starts here
                end_line = question_positions[idx + 1][0]
            else:
                # Last question - goes to end of file
                end_line = len(lines)
            
            # Parse this question
            question = self.parse_single_question(lines, line_num, end_line, q_num)
            questions.append(question)
            
            # Progress indicator
            if q_num % 20 == 0:
                print(f"   ✅ Parsed up to Q.{q_num}")
        
        # Summary by subject
        print(f"📊 Questions parsed by subject:")
        subject_counts = {}
        for q in questions:
            subject = q['subject']
            subject_counts[subject] = subject_counts.get(subject, 0) + 1
        
        for subject, count in subject_counts.items():
            print(f"   {subject}: {count} questions")
        
        return questions
    
    def parse_answers_file(self, filepath: str) -> Dict[int, Dict]:
        """Parse answers from text file"""
        print("📖 Parsing answers file...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('  ')
        print(f"📊 Total lines: {len(lines)}")
        
        # Find all answer positions first
        answer_positions = []
        for i, line in enumerate(lines):
            # Match various answer patterns
            match = re.match(r'^Q\.(\d+)\s*\)?\s*(?:Ans:)?\s*$([a-eA-E])$', line.strip())
            if match:
                q_num = int(match.group(1))
                answer = match.group(2).upper()
                answer_positions.append((i, q_num, answer))
        
        print(f"📊 Found {len(answer_positions)} answers")
        
        # Parse each answer with its explanation
        answers = {}
        
        for idx, (line_num, q_num, answer_letter) in enumerate(answer_positions):
            # Determine where this answer's explanation ends
            if idx + 1 < len(answer_positions):
                end_line = answer_positions[idx + 1][0]
            else:
                end_line = len(lines)
            
            # Extract explanation
            explanation = ""
            for i in range(line_num + 1, end_line):
                line = lines[i].strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Remove EXP: prefix if present
                if line.startswith('EXP:'):
                    line = line[4:].strip()
                
                explanation += line + " "
            
            answers[q_num] = {
                "answer": answer_letter,
                "explanation": explanation.strip()
            }
            
            # Progress indicator
            if q_num % 20 == 0:
                print(f"   ✅ Parsed answers up to Q.{q_num}")
        
        return answers
    
    def determine_difficulty(self, question_text: str, options: Dict) -> str:
        """Determine difficulty based on question characteristics"""
        
        if not options:
            return "Easy"
        
        # Combine all option texts
        all_options_text = " ".join(options.values()).lower()
        
        # Hard indicators
        hard_indicators = [
            "only 1",
            "only 2",
            "only 3",
            "1 and 2",
            "2 and 3",
            "1 and 3",
            "all of the above",
            "none of the above",
            "both",
            "neither",
            "i.", "ii.", "iii.",
            "statement 1", "statement 2"
        ]
        
        for indicator in hard_indicators:
            if indicator in all_options_text.lower():
                return "Hard"
        
        # Long questions are harder
        if len(question_text) > 400:
            return "Hard"
        
        return "Easy"
    
    def merge_questions_and_answers(self, questions_file: str, answers_file: str) -> List[Dict]:
        """Merge questions and answers into final format"""
        
        print("="*60)
        print("🚀 RBI QUESTION PARSER - FIXED VERSION")
        print("="*60)
        
        # Parse both files
        questions = self.parse_questions_file(questions_file)
        answers = self.parse_answers_file(answers_file)
        
        print("🔄 Merging questions with answers...")
        
        all_questions = []
        matched_count = 0
        missing_answers = []
        
        for q in questions:
            q_num = q['number']
            
            # Get answer if exists
            answer_data = answers.get(q_num, {})
            
            if answer_data:
                matched_count += 1
            else:
                missing_answers.append(q_num)
            
            # Determine difficulty
            difficulty = self.determine_difficulty(q['text'], q['options'])
            
            # Create final question object
            final_question = {
                "id": q_num,
                "question_number": q_num,
                "text": q['text'],
                "options": q['options'],
                "correct_answer": answer_data.get('answer', None),
                "explanation": answer_data.get('explanation', ''),
                "subject": q['subject'],
                "difficulty": difficulty,
                "year": 2023,
                "exam": "RBI Grade B Phase 1"
            }
            
            all_questions.append(final_question)
        
        print(f"✅ Matched {matched_count}/{len(questions)} questions with answers")
        
        if missing_answers and len(missing_answers) <= 10:
            print(f"⚠️  Missing answers for questions: {missing_answers}")
        
        return all_questions

def validate_output(questions: List[Dict]) -> None:
    """Validate the parsed output"""
    print("Validating output...")
    
    # Check for sequential question numbers
    expected_nums = set(range(1, 201))  # 1 to 200
    found_nums = {q['question_number'] for q in questions}
    missing_nums = expected_nums - found_nums
    
    if missing_nums:
        print(f"⚠️  Missing question numbers: {sorted(missing_nums)[:10]}...")
    else:
        print("✅ All question numbers present (1-200)")
    
    # Check options
    questions_without_options = []
    questions_with_incomplete_options = []
    
    for q in questions:
        if not q['options']:
            questions_without_options.append(q['question_number'])
        elif len(q['options']) < 5:
            questions_with_incomplete_options.append(q['question_number'])
    
    if questions_without_options:
        print(f"⚠️  Questions without options: {questions_without_options[:5]}...")
    
    if questions_with_incomplete_options:
        print(f"⚠️  Questions with < 5 options: {questions_with_incomplete_options[:5]}...")

def main():
    """Main function"""
    
    parser = RBIQuestionParser()
    
    # File paths
    base_dir = "rbi_txt/2023"
    questions_file = os.path.join(base_dir, "RBI_PYP_PHASE_01_2023_Questions.txt")
    answers_file = os.path.join(base_dir, "RBI_PYP_PHASE_01_2023_Solutions.txt")
    
    print("📂 Working directory:", os.getcwd())
    print("📄 Questions file:", questions_file)
    print("📄 Answers file:", answers_file)
    
    # Check if files exist
    if not os.path.exists(questions_file):
        print("❌ Questions file not found!")
        return
    
    if not os.path.exists(answers_file):
        print("❌ Answers file not found!")
        return
    
    try:
        # Parse and merge
        all_questions = parser.merge_questions_and_answers(questions_file, answers_file)
        
        if not all_questions:
            print("❌ No questions were extracted!")
            return
        
        # Validate
        validate_output(all_questions)
        
        # Calculate statistics
        stats = {
            "total": len(all_questions),
            "by_subject": {},
            "by_difficulty": {"Easy": 0, "Hard": 0},
            "with_answers": 0,
            "with_explanations": 0
        }
        
        for q in all_questions:
            subject = q['subject']
            stats['by_subject'][subject] = stats['by_subject'].get(subject, 0) + 1
            stats['by_difficulty'][q['difficulty']] += 1
            
            if q['correct_answer']:
                stats['with_answers'] += 1
            if q['explanation']:
                stats['with_explanations'] += 1
        
        # Create output
        output = {
            "metadata": {
                "source": "RBI Grade B 2023 Phase 1",
                "total_questions": stats['total'],
                "statistics": stats
            },
            "questions": all_questions
        }
        
        # Save JSON
        output_file = os.path.join(base_dir, "RBI_PYP_PHASE_01_2023_Complete.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print("" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"📁 Saved to: {output_file}")
        print(f"📊 Total: {stats['total']} questions")
        print(f"✅ With answers: {stats['with_answers']}")
        print(f"📝 With explanations: {stats['with_explanations']}")
        
        # Show sample
        if all_questions:
            print("📝 Sample Question 1:")
            q1 = all_questions[0]
            print(f"   Number: Q.{q1['question_number']}")
            print(f"   Text: {q1['text'][:100]}...")
            print(f"   Options: {list(q1['options'].keys())}")
            print(f"   Answer: {q1['correct_answer']}")
            
            if len(all_questions) > 80:
                print("📝 Sample Question 81 (English):")
                q81 = next((q for q in all_questions if q['question_number'] == 81), None)
                if q81:
                    print(f"   Number: Q.{q81['question_number']}")
                    print(f"   Subject: {q81['subject']}")
                    print(f"   Text: {q81['text'][:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
