import json
import random
from groq import Groq
from typing import Dict, List, Optional
from datetime import datetime

class RBIExamAI:
    def __init__(self, api_key: str):
        """Initialize the RBI Exam AI System"""
        
        self.client = Groq(api_key=api_key)
        self.model = "mixtral-8x7b-32768"  # or "llama2-70b-4096"

        # Load your question bank
        self.load_question_bank()
        
        # Subject-wise example questions for AI reference
        self.example_questions = self.organize_examples()
        
    def load_question_bank(self):
        """Load the master dataset and training set"""
        print("📚 Loading RBI Question Bank...")
        
        with open('RBI_Master_Dataset.json', 'r') as f:
            self.master_data = json.load(f)
        
        with open('RBI_Train_Set.json', 'r') as f:
            self.train_questions = json.load(f)
        
        print(f"✅ Loaded {len(self.train_questions)} training questions")
    
    def organize_examples(self) -> Dict:
        """Organize questions by subject and difficulty for AI examples"""
        examples = {
            'General_Awareness': {'Easy': [], 'Hard': []},
            'English': {'Easy': [], 'Hard': []},
            'Quantitative_Aptitude': {'Easy': [], 'Hard': []},
            'Reasoning': {'Easy': [], 'Hard': []}
        }
        
        for q in self.train_questions:
            subject = q['subject']
            difficulty = q['difficulty']
            if len(examples[subject][difficulty]) < 3:  # Keep 3 examples each
                examples[subject][difficulty].append(q)
        
        return examples
    
    def generate_new_question(self, subject: str, difficulty: str = "Medium", 
                             topic: Optional[str] = None) -> Dict:
        """Generate a new RBI-style question using AI"""
        
        print(f"🤖 Generating new {difficulty} {subject} question...")
        
        # Get example questions
        examples = self.example_questions[subject][difficulty][:2]
        
        # Create the prompt
        prompt = f"""You are an expert RBI Grade B Phase 1 exam question creator. 
        
                    Based on these authentic RBI exam questions, create a NEW similar question:
                    
                    Generate the question now.
                    EXAMPLES:
                    """
        for i, ex in enumerate(examples, 1):
            prompt += f"\nExample {i}:\n"
            prompt += f"Question: {ex['text']}\n"
            prompt += f"Options:\n"
            for opt, text in ex['options'].items():
                prompt += f"({opt}) {text}\n"
            prompt += f"Correct Answer: ({ex['correct_answer']})\n"
        
        prompt += f"""
                    Now create a NEW {difficulty} {subject} question following the EXACT same format and style.
                    {f'The topic should be related to: {topic}' if topic else ''}

                    Requirements:
                    1. Question must be completely different from examples but similar in style
                    2. Exactly 5 options labeled (A) through (E)
                    3. One clear correct answer
                    4. RBI exam relevant content, language should be formal and align with the standard of the RBI exam.
                    5. Provide the correct answer and a brief explanation, citing the concept it's based on

                    Return in this JSON format:
                    {{
                        "question": "question text",
                        "options": {{
                            "A": "option A text",
                            "B": "option B text",
                            "C": "option C text",
                            "D": "option D text",
                            "E": "option E text"
                        }},
                        "correct_answer": "letter",
                        "explanation": "brief explanation",
                        "topic": "specific topic"
                    }}
                    """
        
        try:

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an RBI exam expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )

            
            # Parse the response
            content = response.choices[0].message.content
            
            # Try to extract JSON even if there's extra text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                question_data = json.loads(json_match.group())
                
                # Add metadata
                question_data['subject'] = subject
                question_data['difficulty'] = difficulty
                question_data['generated_by_ai'] = True
                question_data['generation_date'] = datetime.now().isoformat()
                
                return question_data
            else:
                raise ValueError("No valid JSON in response")
                
        except Exception as e:
            print(f"❌ Error generating question: {e}")
            return None
    
    def create_mock_test(self, 
                        custom_distribution: Optional[Dict] = None,
                        include_ai_questions: bool = True,
                        ai_percentage: float = 0.2) -> Dict:
        """Create a complete mock test mixing real and AI questions"""
        
        print("\n📝 Creating RBI Mock Test...")
        
        # Default RBI exam distribution
        distribution = custom_distribution or {
            'General_Awareness': 80,
            'English': 30,
            'Quantitative_Aptitude': 30,
            'Reasoning': 60
        }
        
        mock_test = {
            'test_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'total_questions': sum(distribution.values()),
            'duration_minutes': 120,
            'questions': [],
            'answer_key': {},
            'statistics': {
                'real_questions': 0,
                'ai_generated': 0,
                'by_subject': {}
            }
        }
        
        question_number = 1
        
        for subject, count in distribution.items():
            print(f"   Adding {count} {subject} questions...")
            
            # Calculate how many AI questions to include
            ai_count = int(count * ai_percentage) if include_ai_questions else 0
            real_count = count - ai_count
            
            # Get real questions
            subject_questions = [q for q in self.train_questions if q['subject'] == subject]
            selected_real = random.sample(subject_questions, min(real_count, len(subject_questions)))
            
            # Add real questions
            for q in selected_real:
                mock_question = {
                    'question_number': question_number,
                    'subject': subject,
                    'text': q['text'],
                    'options': q['options'],
                    'difficulty': q.get('difficulty', 'Medium'),
                    'is_ai_generated': False
                }
                mock_test['questions'].append(mock_question)
                mock_test['answer_key'][question_number] = {
                    'correct_answer': q['correct_answer'],
                    'explanation': q.get('explanation', '')
                }
                question_number += 1
                mock_test['statistics']['real_questions'] += 1
            
            # Generate AI questions
            for _ in range(ai_count):
                difficulty = random.choice(['Easy', 'Hard'])
                ai_question = self.generate_new_question(subject, difficulty)
                
                if ai_question:
                    mock_question = {
                        'question_number': question_number,
                        'subject': subject,
                        'text': ai_question['question'],
                        'options': ai_question['options'],
                        'difficulty': difficulty,
                        'is_ai_generated': True
                    }
                    mock_test['questions'].append(mock_question)
                    mock_test['answer_key'][question_number] = {
                        'correct_answer': ai_question['correct_answer'],
                        'explanation': ai_question['explanation']
                    }
                    question_number += 1
                    mock_test['statistics']['ai_generated'] += 1
            
            mock_test['statistics']['by_subject'][subject] = count
        
        print(f"\n✅ Mock Test Created!")
        print(f"   Total Questions: {len(mock_test['questions'])}")
        print(f"   Real Questions: {mock_test['statistics']['real_questions']}")
        print(f"   AI Generated: {mock_test['statistics']['ai_generated']}")
        
        return mock_test
    
    def analyze_question_similarity(self, question_text: str, subject: str) -> List[Dict]:
        """Find similar questions from the bank using AI"""
        
        prompt = f"""Given this RBI exam question, find the most similar topics and concepts:
        
                    Question: {question_text}
                    Subject: {subject}

                    Analyze and return:
                    1. Main topic
                    2. Sub-topics covered
                    3. Difficulty level
                    4. Key concepts tested
                    """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an RBI exam expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )

        
        analysis = response.choices[0].message.content
        
        # Find similar questions from bank
        similar = []
        subject_questions = [q for q in self.train_questions if q['subject'] == subject]
        
        # Simple keyword matching (can be improved with embeddings)
        keywords = analysis.lower().split()
        for q in subject_questions[:5]:  # Top 5 similar
            if any(kw in q['text'].lower() for kw in keywords[:10]):
                similar.append(q)
        
        return similar
    
    def generate_explanation(self, question: Dict) -> str:
        """Generate detailed explanation for a question"""
        
        prompt = f"""Provide a detailed explanation for this RBI exam question:
        
                    Question: {question['text']}
                    Options:
                    {chr(10).join([f"({k}) {v}" for k, v in question['options'].items()])}
                    Correct Answer: ({question.get('correct_answer', 'Not provided')})

                    Provide:
                    1. Why the correct answer is right
                    2. Why other options are wrong
                    3. Key concept being tested
                    4. Tips for similar questions
                    """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an RBI exam expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )

        
        return response.choices[0].message.content
    
    def save_mock_test(self, mock_test: Dict, filename: Optional[str] = None):
        """Save mock test to JSON file"""
        
        if not filename:
            filename = f"MockTest_{mock_test['test_id']}.json"
        
        with open(filename, 'w') as f:
            json.dump(mock_test, f, indent=2)
        
        print(f"💾 Mock test saved to: {filename}")
        
        return filename

def main():
    """Demo the AI system"""
    
    # Replace with your actual API key
    API_KEY = "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"
    
    print("🚀 RBI EXAM AI SYSTEM")
    print("="*50)
    
    # Initialize AI system
    ai_system = RBIExamAI(API_KEY)
    
    # Demo 1: Generate a single question
    print("\n📝 DEMO 1: Generate New Question")
    new_question = ai_system.generate_new_question(
        subject="General_Awareness",
        difficulty="Hard",
        topic="Banking Regulation"
    )
    if new_question:
        print(f"Generated Question: {new_question['question'][:100]}...")
        print(f"Options: {list(new_question['options'].keys())}")
    
    # Demo 2: Create a mini mock test
    print("\n📝 DEMO 2: Create Mini Mock Test")
    mini_distribution = {
        'General_Awareness': 10,
        'English': 5,
        'Quantitative_Aptitude': 5,
        'Reasoning': 10
    }
    
    mock_test = ai_system.create_mock_test(
        custom_distribution=mini_distribution,
        include_ai_questions=True,
        ai_percentage=0.3  # 30% AI questions
    )
    
    # Save the mock test
    ai_system.save_mock_test(mock_test)
    
    print("\n✅ AI System Ready!")
    print("\n💡 You can now:")
    print("   1. Generate unlimited new questions")
    print("   2. Create custom mock tests")
    print("   3. Get AI explanations")
    print("   4. Analyze question patterns")

if __name__ == "__main__":
    main()
