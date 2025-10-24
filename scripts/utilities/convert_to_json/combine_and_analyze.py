import json
import os
from collections import Counter
from typing import Dict, List
import pandas as pd

class RBIDataProcessor:
    def __init__(self):
        self.all_questions = []
        self.statistics = {}
        
    def load_all_json_files(self, base_dir="rbi_txt"):
        """Load all JSON files from different years"""
        years = ['2017', '2018', '2019', '2022', '2023']
        
        for year in years:
            json_path = f"{base_dir}/{year}/RBI_PYP_PHASE_01_{year}_Complete.json"
            
            if os.path.exists(json_path):
                print(f"📂 Loading {year} data...")
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    questions = data.get('questions', [])
                    
                    # Add year tag to each question
                    for q in questions:
                        q['year'] = int(year)
                    
                    self.all_questions.extend(questions)
                    print(f"   ✅ Loaded {len(questions)} questions from {year}")
            else:
                print(f"   ❌ File not found: {json_path}")
        
        print(f"📊 Total questions loaded: {len(self.all_questions)}")
        
    def analyze_dataset(self):
        """Analyze the complete dataset"""
        print("🔍 DATASET ANALYSIS")
        print("="*50)
        
        # Basic counts
        self.statistics = {
            'total_questions': len(self.all_questions),
            'by_year': Counter([q['year'] for q in self.all_questions]),
            'by_subject': Counter([q['subject'] for q in self.all_questions]),
            'by_difficulty': Counter([q.get('difficulty', 'Unknown') for q in self.all_questions]),
            'with_answers': sum(1 for q in self.all_questions if q.get('correct_answer')),
            'with_explanations': sum(1 for q in self.all_questions if q.get('explanation')),
            'missing_options': []
        }
        
        # Find questions with issues
        for q in self.all_questions:
            if not q.get('options') or len(q['options']) < 4:
                self.statistics['missing_options'].append({
                    'year': q['year'],
                    'number': q['question_number'],
                    'subject': q['subject']
                })
        
        # Print statistics
        print(f"📚 Total Questions: {self.statistics['total_questions']}")
        
        print(f"📅 By Year:")
        for year, count in sorted(self.statistics['by_year'].items()):
            print(f"   {year}: {count} questions")
        
        print(f"📖 By Subject:")
        for subject, count in self.statistics['by_subject'].items():
            print(f"   {subject}: {count} questions")
        
        print(f"💪 By Difficulty:")
        for diff, count in self.statistics['by_difficulty'].items():
            print(f"   {diff}: {count} questions")
        
        print(f"✅ Data Quality:")
        print(f"   With Answers: {self.statistics['with_answers']}/{self.statistics['total_questions']}")
        print(f"   With Explanations: {self.statistics['with_explanations']}/{self.statistics['total_questions']}")
        print(f"   Missing/Incomplete Options: {len(self.statistics['missing_options'])} questions")
        
    def create_master_dataset(self):
        """Create a unified master dataset"""
        
        # Clean and standardize all questions
        cleaned_questions = []
        
        for q in self.all_questions:
            # Skip questions with critical issues
            if not q.get('text') or not q.get('options'):
                continue
            
            cleaned_q = {
                'id': f"{q['year']}_Q{q['question_number']}",
                'question_number': q['question_number'],
                'year': q['year'],
                'subject': q['subject'],
                'questions': q['text'].strip(),
                'options': q['options'],
                'correct_answer': q.get('correct_answer', None),
                'explanation': q.get('explanation', ''),
                'difficulty': q.get('difficulty', 'Medium'),
                'topics': [],  # To be filled by AI later
                'skills_tested': [],  # To be filled by AI later
                'has_visual': False,  # Mark if question needs diagrams
                'quality_score': 1.0  # Can be updated based on student performance
            }
            
            # Check for visual requirements
            visual_keywords = ['graph', 'chart', 'diagram', 'figure', 'table', 'image']
            if any(keyword in q['text'].lower() for keyword in visual_keywords):
                cleaned_q['has_visual'] = True
            
            cleaned_questions.append(cleaned_q)
        
        return cleaned_questions
    
    def save_master_dataset(self, output_path="RBI_Master_Dataset.json"):
        """Save the combined dataset"""
        
        master_data = {
            'metadata': {
                'total_questions': len(self.all_questions),
                'years_covered': [2017, 2018, 2019, 2022, 2023],
                'subjects': {
                    'General_Awareness': {'total': 0, 'range_per_year': '1-80'},
                    'English': {'total': 0, 'range_per_year': '81-110'},
                    'Quantitative_Aptitude': {'total': 0, 'range_per_year': '111-140'},
                    'Reasoning': {'total': 0, 'range_per_year': '141-200'}
                },
                'statistics': self.statistics,
                'data_quality': {
                    'complete_questions': 0,
                    'questions_needing_review': [],
                    'visual_questions': 0
                }
            },
            'questions': []
        }
        
        # Create cleaned dataset
        cleaned_questions = self.create_master_dataset()
        master_data['questions'] = cleaned_questions
        
        # Update metadata
        for q in cleaned_questions:
            subject = q['subject']
            master_data['metadata']['subjects'][subject]['total'] += 1
            
            if q['has_visual']:
                master_data['metadata']['data_quality']['visual_questions'] += 1
            
            if not q['correct_answer'] or not q['explanation']:
                master_data['metadata']['data_quality']['questions_needing_review'].append(q['id'])
        
        master_data['metadata']['data_quality']['complete_questions'] = len(cleaned_questions)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Master dataset saved to: {output_path}")
        print(f"   Total cleaned questions: {len(cleaned_questions)}")
        
        return master_data
    
    def create_training_splits(self, master_data, train_ratio=0.8):
        """Split data for AI training and testing"""
        
        import random
        random.seed(42)  # For reproducibility
        
        questions = master_data['questions']
        
        # Separate by subject to maintain balance
        by_subject = {}
        for q in questions:
            subject = q['subject']
            if subject not in by_subject:
                by_subject[subject] = []
            by_subject[subject].append(q)
        
        train_set = []
        test_set = []
        
        for subject, subject_questions in by_subject.items():
            random.shuffle(subject_questions)
            split_point = int(len(subject_questions) * train_ratio)
            
            train_set.extend(subject_questions[:split_point])
            test_set.extend(subject_questions[split_point:])
            
            print(f"{subject}: {split_point} train, {len(subject_questions)-split_point} test")
        
        # Save splits
        with open('RBI_Train_Set.json', 'w') as f:
            json.dump(train_set, f, indent=2)
        
        with open('RBI_Test_Set.json', 'w') as f:
            json.dump(test_set, f, indent=2)
        
        print(f"📊 Data Splits Created:")
        print(f"   Training Set: {len(train_set)} questions")
        print(f"   Test Set: {len(test_set)} questions")
        
        return train_set, test_set

def main():
    processor = RBIDataProcessor()
    
    # Load all data
    processor.load_all_json_files()
    
    # Analyze
    processor.analyze_dataset()
    
    # Create and save master dataset
    master_data = processor.save_master_dataset()
    
    # Create training splits
    print("🎯 Creating Training/Test Splits...")
    processor.create_training_splits(master_data)
    
    print("✅ Data preparation complete!")
    print("🚀 Ready for AI integration!")

if __name__ == "__main__":
    main()