# parse_pdftotext_output.py
import subprocess
import re
import json
import os
from typing import List, Dict, Optional
from datetime import datetime

class PDFTextParser:
    def __init__(self):
        self.questions = []
        
    def extract_from_pdf(self, pdf_path: str) -> List[Dict]:
        """Extract questions using pdftotext with layout preservation"""
        
        print(f"{'='*70}")
        print(f"📖 Processing: {os.path.basename(pdf_path)}")
        print(f"{'='*70}")
        
        # Step 1: Extract text using pdftotext
        text = self.run_pdftotext(pdf_path)
        
        if not text:
            print("❌ Failed to extract text")
            return []
        
        # Step 2: Clean the text
        cleaned_text = self.clean_extracted_text(text)
        
        # Step 3: Extract questions
        questions = self.extract_questions(cleaned_text)
        
        print(f"✅ Successfully extracted {len(questions)} questions")
        
        return questions
    
    def run_pdftotext(self, pdf_path: str) -> str:
        """Run pdftotext command with layout preservation"""
        
        temp_file = "temp_extracted.txt"
        
        try:
            print("🔧 Running pdftotext with layout preservation...")
            
            # Run pdftotext
            result = subprocess.run([
                'pdftotext',
                '-layout',  # Preserve layout
                pdf_path,
                temp_file
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ pdftotext error: {result.stderr}")
                return ""
            
            # Read the extracted text
            with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            print(f"✓ Extracted {len(text)} characters")
            
            # Clean up temp file
            os.remove(temp_file)
            
            return text
            
        except FileNotFoundError:
            print("❌ pdftotext not found. Install with:")
            print("   Ubuntu/Debian: sudo apt-get install poppler-utils")
            print("   Mac: brew install poppler")
            return ""
        except Exception as e:
            print(f"❌ Error: {e}")
            return ""
    
    def clean_extracted_text(self, text: str) -> str:
        """Clean the extracted text and handle two-column layout"""
        
        lines = text.split(' ')
        cleaned_lines = []
        
        for line in lines:
            # Skip header/footer lines
            if any(skip in line.upper() for skip in [
                'ANUJJINDAL.IN',
                'GENERAL AWARENESS |',
                'RBI GRADE B',
                'PREVIOUS YEAR'
            ]):
                continue
            
            # Skip standalone page numbers
            if re.match(r'^\s*\d+\s*$', line) and len(line.strip()) <= 3:
                continue
            
            # Skip empty lines
            if not line.strip():
                continue
            
            cleaned_lines.append(line)
        
        return ''.join(cleaned_lines)
    
    def extract_questions(self, text: str) -> List[Dict]:
        """Extract all questions from the cleaned text"""
        
        questions = []
        
        # Pattern to match Q.number) format
        # This captures question number and everything until next Q. or end
        pattern = r'Q\.(\d+)\)(.*?)(?=Q\.\d+\)|$)'
        
        matches = list(re.finditer(pattern, text, re.DOTALL))
        
        print(f"🔍 Found {len(matches)} question patterns")
        
        for i, match in enumerate(matches):
            q_num = match.group(1)
            content = match.group(2).strip()
            
            # Parse the question content
            question_data = self.parse_question_content(content, q_num)
            
            if question_data:
                questions.append(question_data)
                
                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"  ✓ Processed {i + 1} questions...")
        
        return questions
    
    def parse_question_content(self, content: str, q_num: str) -> Optional[Dict]:
        """Parse question text and options"""
        
        # Find where options start
        option_match = re.search(r'$[a-e]$', content, re.IGNORECASE)
        
        if not option_match:
            return None
        
        # Question text is everything before first option
        question_text = content[:option_match.start()].strip()
        
        # Clean question text
        question_text = re.sub(r'\s+', ' ', question_text)
        question_text = question_text.strip()
        
        # Extract all options
        options = {}
        
        # Pattern to capture options
        option_pattern = r'$([a-e])$\s*([^(]+?)(?=$[a-e]$|$)'
        
        for opt_match in re.finditer(option_pattern, content[option_match.start():], re.IGNORECASE | re.DOTALL):
            letter = opt_match.group(1).upper()
            opt_text = opt_match.group(2).strip()
            
            # Clean option text
            opt_text = re.sub(r'\s+', ' ', opt_text)
            
            # Remove trailing spaces and limit length
            opt_text = opt_text.strip()
            if len(opt_text) > 200:
                opt_text = opt_text[:197] + "..."
            
            options[letter] = opt_text
        
        # Validate we have enough options (at least 3)
        if len(options) < 3:
            return None
        
        return {
            "question_id": f"Q{q_num}",
            "question_number": int(q_num),
            "question_text": question_text,
            "options": options,
            "correct_answer": "",  # To be filled later
            "solution": "",  # To be filled later
            "metadata": {
                "extraction_method": "pdftotext",
                "extraction_date": datetime.now().isoformat()
            }
        }

def batch_process_pdfs(pdf_folder: str):
    """Process all PDFs in a folder"""
    
    parser = PDFTextParser()
    all_results = {}
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    
    print(f"📚 Found {len(pdf_files)} PDF files to process")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        
        # Extract questions
        questions = parser.extract_from_pdf(pdf_path)
        
        # Store results
        all_results[pdf_file] = {
            "filename": pdf_file,
            "total_questions": len(questions),
            "questions": questions
        }
        
        # Save individual file results
        output_file = pdf_file.replace('.pdf', '_extracted.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results[pdf_file], f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {output_file}")
    
    # Save combined results
    with open('all_questions_combined.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ All done! Processed {len(pdf_files)} files")
    
    # Print summary
    total_questions = sum(r['total_questions'] for r in all_results.values())
    print(f"📊 Total questions extracted: {total_questions}")

def main():
    """Main function"""
    
    # Single file processing
    pdf_path = "rbi_pdf/RBI_PYP_PHASE_01_2023_General_Awareness_Questions.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    parser = PDFTextParser()
    questions = parser.extract_from_pdf(pdf_path)
    
    # Save results
    output = {
        "metadata": {
            "source_file": pdf_path,
            "total_questions": len(questions),
            "extraction_method": "pdftotext with layout preservation"
        },
        "questions": questions
    }
    
    output_file = "rbi_2023_ga_parsed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to {output_file}")
    
    # Show sample results
    if questions:
        print(f"📝 Sample Results:")
        for q in questions[:3]:
            print(f"Q.{q['question_number']}:")
            print(f"Text: {q['question_text'][:100]}...")
            print(f"Options: {list(q['options'].keys())}")
            if q['options']:
                first_key = list(q['options'].keys())[0]
                print(f"  {first_key}: {q['options'][first_key][:50]}...")
    
    # Process all PDFs in folder (uncomment to run)
    # batch_process_pdfs("rbi_pdf")

if __name__ == "__main__":
    main()
