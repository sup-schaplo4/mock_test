# convert_to_json_fixed.py
import re
import json
import os
from typing import Dict, List

class RBIQuestionParser:
    def __init__(self):
        # Define question number ranges for each subject
        self.subject_ranges = {
            "General_Awareness": (1, 80),
            "English": (171, 200),
            "Quantitative_Aptitude": (81, 110),
            "Reasoning": (111, 170)
        }
    
    def get_subject_by_question_number(self, q_num: int) -> str:
        """Determine subject based on question number"""
        for subject, (start, end) in self.subject_ranges.items():
            if start <= q_num <= end:
                return subject
        return "Unknown"
    
    def parse_questions_file(self, filepath: str) -> List[Dict]:
        """Parse questions from text file"""
        print("📖 Parsing questions file...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into lines
        lines = content.split('\n')
        print(f"📊 Total lines: {len(lines)}")
        
        questions = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for question pattern: Q.1) or Q.1 )
            q_match = re.match(r'^Q\.(\d+)\s*\)', line)
            
            if q_match:
                q_num = int(q_match.group(1))
                
                # Determine subject based on question number
                subject = self.get_subject_by_question_number(q_num)
                
                # Extract question text
                question_text = ""
                i += 1
                
                # Read lines until we hit option (a)
                while i < len(lines):
                    current_line = lines[i].strip()
                    
                    # Stop if we hit an option or another question
                    if current_line.startswith('(a)') or current_line.startswith('Q.'):
                        break
                    
                    # Add non-empty lines to question text
                    if current_line:
                        question_text += current_line + " "
                    
                    i += 1
                
                # Now parse options (a) through (e)
                options = {}
                option_letters = ['a', 'b', 'c', 'd', 'e']
                
                for letter in option_letters:
                    if i < len(lines):
                        current_line = lines[i].strip()
                        
                        # Check if line starts with (a), (b), etc.
                        if current_line.startswith(f'({letter})'):
                            # Extract option text after (a)
                            option_text = current_line[3:].strip()
                            
                            # Continue reading if option spans multiple lines
                            i += 1
                            while i < len(lines):
                                next_line = lines[i].strip()
                                
                                # Stop if we hit next option or question
                                if (next_line.startswith('(') and next_line[1:2] in option_letters) or \
                                   next_line.startswith('Q.'):
                                    break
                                
                                # Add to option text if not empty
                                if next_line:
                                    option_text += " " + next_line
                                    i += 1
                                else:
                                    i += 1
                                    break
                            
                            options[letter.upper()] = option_text
                        else:
                            # No more options found
                            break
                
                # Store the question
                questions.append({
                    "number": q_num,
                    "text": question_text.strip(),
                    "options": options,
                    "subject": subject
                })
                
                # Progress indicator
                if q_num % 20 == 0:
                    print(f"   ✅ Parsed up to Q.{q_num}")
            else:
                i += 1
        
        print(f"📊 Total questions parsed: {len(questions)}")
        
        # Show breakdown by subject
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
        
        lines = content.split('\n')
        print(f"📊 Total lines: {len(lines)}")
        
        answers = {}
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for answer pattern: Q.1) Ans: (a)
            ans_match = re.match(r'^Q\.(\d+)\s*\)\s*Ans:\s*\(([a-eA-E])\)', line)
            
            if ans_match:
                q_num = int(ans_match.group(1))
                answer_letter = ans_match.group(2).upper()
                
                # Get explanation (if exists)
                explanation = ""
                i += 1
                
                while i < len(lines):
                    current_line = lines[i].strip()
                    
                    # Stop at next question
                    if current_line.startswith('Q.') and ')' in current_line:
                        break
                    
                    # Skip "EXP:" prefix if present
                    if current_line.startswith('EXP:'):
                        current_line = current_line[4:].strip()
                    
                    # Add to explanation
                    if current_line:
                        explanation += current_line + " "
                    
                    i += 1
                
                answers[q_num] = {
                    "answer": answer_letter,
                    "explanation": explanation.strip()
                }
                
                # Progress indicator
                if q_num % 20 == 0:
                    print(f"   ✅ Parsed answers up to Q.{q_num}")
            else:
                i += 1
        
        print(f"📊 Total answers parsed: {len(answers)}")
        
        return answers
    
    def determine_difficulty(self, question_text: str, options: Dict) -> str:
        """Determine difficulty based on question characteristics"""
        
        # Default to Easy
        if not options:
            return "Easy"
        
        # Combine all option texts
        all_options_text = " ".join(options.values()).lower()
        
        # Check for complexity indicators
        hard_indicators = [
            "and",
            "only",
            "both",
            #"neither",
            #"either",
            #"1)", "2)", "3)",  # Sub-options
            #"i.", "ii.", "iii.",  # Roman numerals
            #"(a)", "(b)",  # Nested options
        ]
        
        for indicator in hard_indicators:
            if indicator in all_options_text:
                return "Hard"
        
        # Long questions are usually harder
        if len(question_text) > 400:
            return "Hard"
        
        # Check if multiple statements in options
        if all_options_text.count(',') > 5:
            return "Hard"
        
        return "Easy"
    
    def merge_questions_and_answers(self, questions_file: str, answers_file: str) -> List[Dict]:
        """Merge questions and answers into final format"""
        
        print("="*60)
        print("🚀 RBI QUESTION PARSER - SIMPLE VERSION")
        print("="*60)
        
        # Parse both files
        questions = self.parse_questions_file(questions_file)
        answers = self.parse_answers_file(answers_file)
        
        print("🔄 Merging questions with answers...")
        
        all_questions = []
        matched_count = 0
        
        for q in questions:
            q_num = q['number']
            
            # Get answer if exists
            answer_data = answers.get(q_num, {})
            
            if answer_data:
                matched_count += 1
            
            # Determine difficulty
            difficulty = self.determine_difficulty(q['text'], q['options'])
            
            # Create final question object
            final_question = {
                "id": q_num,  # Using question number as ID
                "question_number": q_num,
                "text": q['text'],
                "options": q['options'],
                "correct_answer": answer_data.get('answer', None),
                "explanation": answer_data.get('explanation', ''),
                "subject": q['subject'],
                "difficulty": difficulty,
                "year": 2017,
                "exam": "RBI Grade B Phase 1"
            }
            
            all_questions.append(final_question)
        
        print(f"✅ Matched {matched_count}/{len(questions)} questions with answers")
        
        return all_questions

def main():
    """Main function to run the parser"""
    
    parser = RBIQuestionParser()
    
    # File paths
    base_dir = "rbi_txt/2017"
    questions_file = os.path.join(base_dir, "RBI_PYP_PHASE_01_2017_Questions.txt")
    answers_file = os.path.join(base_dir, "RBI_PYP_PHASE_01_2017_Solutions.txt")
    
    print("📂 Working directory:", os.getcwd())
    print("📄 Questions file:", questions_file)
    print("📄 Answers file:", answers_file)
    print()
    
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
        
        # Calculate statistics
        stats = {
            "total": len(all_questions),
            "by_subject": {},
            "by_difficulty": {"Easy": 0, "Hard": 0},
            "with_answers": 0,
            "with_explanations": 0
        }
        
        for q in all_questions:
            # Count by subject
            subject = q['subject']
            stats['by_subject'][subject] = stats['by_subject'].get(subject, 0) + 1
            
            # Count by difficulty
            stats['by_difficulty'][q['difficulty']] += 1
            
            # Count with answers and explanations
            if q['correct_answer']:
                stats['with_answers'] += 1
            if q['explanation']:
                stats['with_explanations'] += 1
        
        # Create output JSON
        output = {
            "metadata": {
                "source": "RBI Grade B 2017 Phase 1",
                "total_questions": stats['total'],
                "question_ranges": {
                    "General_Awareness": "1-80",
                    "English": "81-110",
                    "Quantitative_Aptitude": "111-140",
                    "Reasoning": "141-200"
                },
                "statistics": stats
            },
            "questions": all_questions
        }
        
        # Save to JSON file
        output_file = os.path.join(base_dir, "RBI_PYP_PHASE_01_2017_Complete.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print("" + "="*60)
        print("✅ SUCCESS! Conversion complete!")
        print("="*60)
        print(f"📁 Output saved to: {output_file}")
        
        # Print summary statistics
        print("📊 SUMMARY STATISTICS:")
        print(f"   Total Questions: {stats['total']}")
        print(f"   With Answers: {stats['with_answers']}")
        print(f"   With Explanations: {stats['with_explanations']}")
        
        print("📚 Questions by Subject:")
        for subject, count in stats['by_subject'].items():
            expected = {
                "General_Awareness": 80,
                "English": 30,
                "Quantitative_Aptitude": 30,
                "Reasoning": 60
            }
            exp_count = expected.get(subject, 0)
            status = "✅" if count == exp_count else "⚠️"
            print(f"   {status} {subject}: {count} (expected: {exp_count})")
        
        print("📈 Questions by Difficulty:")
        for diff, count in stats['by_difficulty'].items():
            percentage = (count / stats['total']) * 100
            print(f"   {diff}: {count} ({percentage:.1f}%)")
        
        # Show a sample question
        if all_questions:
            print("📝 Sample Question:")
            sample = all_questions[0]
            print(f"   Number: Q.{sample['question_number']}")
            print(f"   Subject: {sample['subject']}")
            print(f"   Text: {sample['text'][:100]}...")
            print(f"   Options: {len(sample['options'])} options")
            print(f"   Answer: {sample['correct_answer']}")
            print(f"   Has Explanation: {'Yes' if sample['explanation'] else 'No'}")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
