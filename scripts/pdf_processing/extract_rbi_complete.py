# extract_rbi_complete.py
import pdfplumber
import re
import json
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RBIQuestionExtractor:
    def __init__(self):
        self.questions = []
        self.current_year = None
        self.exam_phase = None
        
    def extract_from_pdf(self, pdf_path: str, year: int = 2023, phase: str = "phase_1") -> List[Dict]:
        """Extract questions from RBI PDF format with sections"""
        
        self.current_year = year
        self.exam_phase = phase
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + ""
                    logger.info(f"Processed page {page_num + 1}")
                
                # Parse questions with section detection
                self.questions = self._parse_questions_with_sections(full_text)
                logger.info(f"Extracted {len(self.questions)} questions")
                
                return self.questions
                
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return []
    
    def _parse_questions_with_sections(self, text: str) -> List[Dict]:
        """Parse questions and detect their sections"""
        
        questions = []
        current_section = "general_awareness"  # Default section
        
        # Look for section headers
        section_patterns = {
            "general_awareness": r"(General Awareness|Current Affairs|GA Section)",
            "reasoning": r"(Reasoning|Logical Reasoning|Reasoning Ability)",
            "english": r"(English Language|English|Verbal Ability)",
            "quantitative": r"(Quantitative Aptitude|Numerical Ability|Quant|Mathematics)",
            "esi": r"(Economic.*Social|ESI|Economic Issues)",
            "finance_management": r"(Finance.*Management|F&M|Financial Management)"
        }
        
        # Split text into lines for section detection
        lines = text.split('')
        
        for i, line in enumerate(lines):
            # Check if this line indicates a new section
            for section, pattern in section_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    current_section = section
                    logger.info(f"Found section: {section}")
                    break
        
        # Extract questions
        question_pattern = r'Q\.(\d+)\)(.*?)(?=Q\.\d+\)|$)'
        matches = re.finditer(question_pattern, text, re.DOTALL)
        
        for match in matches:
            q_num = match.group(1)
            q_content = match.group(2).strip()
            
            # Extract question data
            question_data = self._extract_question_and_options(q_content, q_num)
            
            if question_data:
                # Add section information
                question_data["section"] = self._detect_section_from_content(
                    question_data["question"], 
                    current_section
                )
                question_data["exam_phase"] = self.exam_phase
                questions.append(question_data)
        
        return questions
    
    def _detect_section_from_content(self, question: str, default_section: str) -> str:
        """Detect section from question content"""
        
        section_keywords = {
            "reasoning": ["arrange", "series", "puzzle", "blood relation", "coding", "decoding", 
                         "syllogism", "direction", "ranking", "seating arrangement"],
            "english": ["grammar", "vocabulary", "comprehension", "fill in the blanks", 
                       "error spotting", "sentence", "paragraph"],
            "quantitative": ["calculate", "percentage", "ratio", "profit", "loss", "interest",
                           "probability", "average", "speed", "distance"],
            "general_awareness": ["RBI", "government", "scheme", "recently", "launched", 
                                "minister", "country", "currency", "appointed"],
            "esi": ["economic", "GDP", "inflation", "fiscal", "monetary policy", "budget",
                   "poverty", "unemployment", "social"],
            "finance_management": ["management", "leadership", "organization", "SEBI", 
                                 "stock market", "derivatives", "banking regulation"]
        }
        
        question_lower = question.lower()
        
        # Check keywords to determine section
        section_scores = {}
        for section, keywords in section_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in question_lower)
            if score > 0:
                section_scores[section] = score
        
        # Return section with highest score, or default
        if section_scores:
            return max(section_scores, key=section_scores.get)
        return default_section
    
    def _extract_question_and_options(self, content: str, q_num: str) -> Optional[Dict]:
        """Extract question text and options"""
        
        # Pattern for options: (a), (b), (c), (d), (e)
        option_pattern = r'$([a-e])$\s*([^(]+?)(?=$[a-e]$|$)'
        
        # Find where options start
        first_option = re.search(r'$a$', content)
        
        if not first_option:
            logger.warning(f"No options found for Q.{q_num}")
            return None
        
        # Question text is everything before first option
        question_text = content[:first_option.start()].strip()
        
        # Extract all options
        options_text = content[first_option.start():]
        options = {}
        
        option_matches = re.finditer(option_pattern, options_text, re.DOTALL)
        
        for opt_match in option_matches:
            option_letter = opt_match.group(1).upper()
            option_text = opt_match.group(2).strip()
            
            # Clean up option text
            option_text = re.sub(r'\s+', ' ', option_text)
            option_text = option_text.replace('', ' ').strip()
            
            options[option_letter] = option_text
        
        # Detect topic within section
        topic = self._detect_topic(question_text)
        
        # Detect difficulty
        difficulty = self._detect_difficulty(question_text)
        
        question_obj = {
            "question_number": int(q_num),
            "question": question_text,
            "options": options,
            "correct_answer": "",  # Will be added from answer key
            "solution": "",  # Will be added from solution PDF
            "year": self.current_year,
            "section": "",  # Will be set by caller
            "topic": topic,  # Specific topic within section
            "difficulty": difficulty,
            "pattern": self._detect_pattern(question_text),
            "source": "RBI Grade B Previous Year"
        }
        
        return question_obj
    
    def _detect_topic(self, question: str) -> str:
        """Detect specific topic within section"""
        
        topic_keywords = {
            # General Awareness topics
            "monetary_policy": ["repo", "reverse repo", "CRR", "SLR", "monetary", "inflation target"],
            "banking_awareness": ["bank", "NPA", "CASA", "priority sector", "Basel", "capital adequacy"],
            "current_affairs": ["recently", "launched", "announced", "appointed", "summit", "conference"],
            "government_schemes": ["scheme", "yojana", "mission", "programme", "initiative"],
            "international": ["World Bank", "IMF", "WTO", "UN", "G20", "BRICS"],
            
            # Reasoning topics
            "puzzles": ["sits", "floor", "building", "arrangement"],
            "syllogism": ["statements", "conclusions", "follows"],
            "coding_decoding": ["code", "coded", "decode"],
            "blood_relations": ["father", "mother", "brother", "sister", "family"],
            
            # English topics
            "reading_comprehension": ["passage", "author", "infer", "implies"],
            "grammar": ["error", "incorrect", "grammatically"],
            "vocabulary": ["synonym", "antonym", "meaning", "word"],
            
            # Quant topics
            "arithmetic": ["percentage", "profit", "loss", "ratio", "proportion"],
            "data_interpretation": ["table", "graph", "chart", "data"],
            "number_series": ["series", "pattern", "next number"]
        }
        
        question_lower = question.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword.lower() in question_lower for keyword in keywords):
                return topic
        
        return "general"
    
    def _detect_difficulty(self, question: str) -> str:
        """Detect difficulty level"""
        
        # Difficulty based on question complexity
        if any(word in question.lower() for word in ["calculate", "compute", "analyze", "evaluate"]):
            return "hard"
        elif len(question) > 150 or "which of the following" in question.lower():
            return "medium"
        else:
            return "easy"
    
    def _detect_pattern(self, question: str) -> str:
        """Detect question pattern"""
        
        patterns = {
            "direct_factual": ["what is", "which", "who", "when", "where"],
            "calculation": ["calculate", "compute", "find the value", "what will be"],
            "match_the_following": ["match", "following pairs", "correctly matched"],
            "statement_based": ["which of the following", "statements", "correct", "true"],
            "current_affairs": ["recently", "latest", "current", "launched"],
            "fill_blanks": ["fill", "blank", "_____"],
            "error_spotting": ["error", "mistake", "incorrect"]
        }
        
        question_lower = question.lower()
        
        for pattern, keywords in patterns.items():
            if any(keyword in question_lower for keyword in keywords):
                return pattern
        
        return "standard"
    
    def add_solutions_from_pdf(self, solution_pdf_path: str):
        """Extract and add detailed solutions from solution PDF"""
        
        logger.info(f"Extracting solutions from {solution_pdf_path}")
        
        with pdfplumber.open(solution_pdf_path) as pdf:
            solution_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    solution_text += page_text + ""
            
            # Pattern for solutions - adjust based on your PDF format
            # Looking for: Q.1) Answer: (c) followed by explanation
            solution_pattern = r'Q\.(\d+)\).*?(?:Answer|Ans)[:\s]*$([a-e])$(.*?)(?=Q\.\d+\)|$)'
            
            matches = re.finditer(solution_pattern, solution_text, re.DOTALL | re.IGNORECASE)
            
            solutions_found = 0
            for match in matches:
                q_num = int(match.group(1))
                answer = match.group(2).upper()
                explanation = match.group(3).strip()
                
                # Clean up explanation
                explanation = re.sub(r'\s+', ' ', explanation)
                explanation = explanation.replace('', ' ').strip()
                
                # Limit explanation length
                if len(explanation) > 500:
                    explanation = explanation[:497] + "..."
                
                # Find and update the question
                for question in self.questions:
                    if question["question_number"] == q_num:
                        question["correct_answer"] = answer
                        question["solution"] = explanation
                        solutions_found += 1
                        break
            
            logger.info(f"Added solutions to {solutions_found} questions")
    
    def add_answers_only(self, answer_key: Dict[int, str]):
        """Add just answers from a simple answer key"""
        
        for q_num, answer in answer_key.items():
            for question in self.questions:
                if question["question_number"] == q_num:
                    question["correct_answer"] = answer.upper()
                    break

def process_complete_extraction():
    """Complete extraction with sections and solutions"""
    
    extractor = RBIQuestionExtractor()
    
    all_data = {
        "metadata": {
            "total_questions": 0,
            "years": [],
            "sections": {},  # Changed from topics to sections
            "topics": {},     # Keep topics as sub-classification
            "phases": {}
        },
        "questions": []
    }
    
    # Your PDF files with their details
    pdf_sets = [
        {
            "question_pdf": "RBI_Grade_B_2023_Phase1.pdf",
            "solution_pdf": "RBI_Grade_B_2023_Solutions.pdf",
            "year": 2023,
            "phase": "phase_1"
        },
        {
            "question_pdf": "RBI_Grade_B_2023_Phase2_ESI.pdf",
            "solution_pdf": "RBI_Grade_B_2023_Phase2_Solutions.pdf",
            "year": 2023,
            "phase": "phase_2"
        },
        # Add all your PDFs here
    ]
    
    for pdf_set in pdf_sets:
        logger.info(f"{'='*50}")
        logger.info(f"Processing {pdf_set['question_pdf']}...")
        
        # Extract questions
        questions = extractor.extract_from_pdf(
            pdf_set['question_pdf'], 
            pdf_set['year'],
            pdf_set['phase']
        )
        
        # Add solutions if available
        if pdf_set.get('solution_pdf'):
            extractor.add_solutions_from_pdf(pdf_set['solution_pdf'])
        
        # Update metadata
        all_data["questions"].extend(questions)
        
        # Count sections and topics
        for q in questions:
            section = q.get('section', 'unknown')
            topic = q.get('topic', 'unknown')
            
            all_data["metadata"]["sections"][section] = \
                all_data["metadata"]["sections"].get(section, 0) + 1
            
            all_data["metadata"]["topics"][topic] = \
                all_data["metadata"]["topics"].get(topic, 0) + 1
        
        # Track phases
        phase = pdf_set['phase']
        all_data["metadata"]["phases"][phase] = \
            all_data["metadata"]["phases"].get(phase, 0) + len(questions)
    
    # Update final metadata
    all_data["metadata"]["total_questions"] = len(all_data["questions"])
    all_data["metadata"]["years"] = list(set([q["year"] for q in all_data["questions"]]))
    
    # Save to JSON
    with open('rbi_complete_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    # Print detailed summary
    print("" + "="*60)
    print("EXTRACTION COMPLETE!")
    print("="*60)
    print(f"Total Questions: {all_data['metadata']['total_questions']}")
    print(f"Years: {all_data['metadata']['years']}")
    
    print("Section Distribution:")
    for section, count in all_data["metadata"]["sections"].items():
        print(f"{section}: {count} questions")
    
    print("Phase Distribution:")
    for phase, count in all_data["metadata"]["phases"].items():
        print(f"{phase}: {count} questions")
    
    print("Top Topics:")
    sorted_topics = sorted(all_data["metadata"]["topics"].items(), 
                          key=lambda x: x[1], reverse=True)[:10]
    for topic, count in sorted_topics:
        print(f"{topic}: {count} questions")
    
    return all_data

# Extract solutions using AI if pattern matching fails
def extract_solutions_with_ai(solution_pdf_path: str):
    """Use AI to extract solutions from complex PDFs"""
    
    from groq import Groq
    client = Groq(api_key="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")
    
    solutions = {}
    
    with pdfplumber.open(solution_pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            
            if not page_text:
                continue
            
            prompt = f"""
            Extract question numbers, answers, and explanations from this solution text.
            
            Text:
            {page_text[:3000]}
            
            Return as JSON:
            {{
                "1": {{
                    "answer": "C",
                    "explanation": "The explanation text here"
                }},
                "2": {{
                    "answer": "A",
                    "explanation": "The explanation text here"
                }}
            }}
            
            Return ONLY valid JSON.
            """
            
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            try:
                page_solutions = json.loads(response.choices[0].message.content)
                solutions.update(page_solutions)
                print(f"Page {page_num + 1}: Extracted {len(page_solutions)} solutions")
            except:
                print(f"Page {page_num + 1}: Failed to parse solutions")
    
    return solutions

if __name__ == "__main__":
    # Run complete extraction
    print("Starting complete extraction with sections and solutions...")
    data = process_complete_extraction()
    
    # Print sample output
    if data["questions"]:
        print("" + "="*60)
        print("SAMPLE EXTRACTED QUESTION:")
        print("="*60)
        sample = data["questions"][0]
        print(json.dumps(sample, indent=2))
