# extract_with_ocr_advanced.py
import os
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
import re
import json
from PIL import Image
import easyocr
from typing import List, Dict, Tuple

class AdvancedPDFExtractor:
    def __init__(self, use_gpu=False):
        """Initialize with OCR engines"""
        # EasyOCR for better accuracy
        self.reader = easyocr.Reader(['en'], gpu=use_gpu)
        self.questions = []
        
    def detect_columns(self, image):
        """Detect if page has columns and split them"""
        # Convert to grayscale
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        height, width = gray.shape
        
        # Detect vertical lines for column separation
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=height*0.5, maxLineGap=10)
        
        # Find middle of page
        mid_x = width // 2
        column_separator = None
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                # Check if line is vertical and near middle
                if abs(x1 - x2) < 10 and abs(x1 - mid_x) < width * 0.1:
                    column_separator = x1
                    break
        
        # If no clear separator, check for whitespace in middle
        if column_separator is None:
            middle_strip = gray[:, mid_x-50:mid_x+50]
            if np.mean(middle_strip) > 240:  # Mostly white
                column_separator = mid_x
        
        if column_separator:
            # Split into two columns
            left_col = image.crop((0, 0, column_separator - 10, image.height))
            right_col = image.crop((column_separator + 10, 0, image.width, image.height))
            return [left_col, right_col], True
        
        return [image], False
    
    def preprocess_image(self, image):
        """Enhance image for better OCR"""
        # Convert PIL to OpenCV
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        
        # Convert to grayscale
        gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        # Dilation and erosion to remove noise
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed = cv2.medianBlur(processed, 3)
        
        # Convert back to PIL
        return Image.fromarray(processed)
    
    def extract_text_with_easyocr(self, image):
        """Extract text using EasyOCR (more accurate for complex layouts)"""
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Run OCR
        results = self.reader.readtext(img_array, detail=1, paragraph=True)
        
        # Sort by vertical position
        results.sort(key=lambda x: x[0][0][1])
        
        # Combine text
        text = ""
        for detection in results:
            text += detection[1] + " "
        
        return text
    
    def extract_text_with_tesseract(self, image):
        """Fallback to Tesseract"""
        # Configure Tesseract
        custom_config = r'--oem 3 --psm 6 -l eng'
        
        # Extract text
        text = pytesseract.image_to_string(image, config=custom_config)
        
        return text
    
    def parse_questions(self, text):
        """Parse questions from text with improved pattern matching"""
        # Clean text
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(\d+)\s+(\d+)', r'\1\2', text)  # Fix split numbers
        
        # Multiple patterns for questions
        patterns = [
            r'Q\.?\s*(\d+)\s*\)(.*?)(?=Q\.?\s*\d+\s*\)|$)',  # Q.1) or Q1)
            r'Question\s+(\d+)[:\.]?(.*?)(?=Question\s+\d+|$)',  # Question 1: or Question 1.
            r'(\d+)\.\s+(?=\w)(.*?)(?=\d+\.\s+\w|$)',  # 1. Question text
        ]
        
        questions = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                for match in matches:
                    q_num = match[0]
                    q_content = match[1].strip()
                    
                    # Extract options
                    options = {}
                    
                    # Multiple option patterns
                    option_patterns = [
                        r'$([a-e])$\s*([^()]+?)(?=$[a-e]$|$)',  # (a) option
                        r'([a-e])\)\s*([^()]+?)(?=[a-e]\)|$)',  # a) option
                        r'([a-e])\.\s*([^.]+?)(?=[a-e]\.|$)',  # a. option
                    ]
                    
                    for opt_pattern in option_patterns:
                        opt_matches = re.findall(opt_pattern, q_content, re.IGNORECASE)
                        if opt_matches:
                            for opt in opt_matches:
                                options[opt[0].upper()] = opt[1].strip()
                            
                            # Remove options from question text
                            first_opt_match = re.search(opt_pattern, q_content, re.IGNORECASE)
                            if first_opt_match:
                                q_text = q_content[:first_opt_match.start()].strip()
                            break
                    else:
                        q_text = q_content
                    
                    if q_text:  # Only add if there's actual question text
                        questions.append({
                            "number": int(q_num),
                            "text": q_text,
                            "options": options
                        })
                
                break  # Use first matching pattern
        
        return questions
    
    def extract_from_pdf(self, pdf_path):
        """Main extraction function"""
        print(f"📄 Processing: {os.path.basename(pdf_path)}")
        
        # Convert PDF to images
        print("📖 Converting PDF to images...")
        try:
            # Use lower DPI for faster processing
            images = convert_from_path(pdf_path, dpi=200, fmt='PNG')
        except Exception as e:
            print(f"❌ Error converting PDF: {e}")
            return []
        
        all_text = ""
        
        for i, image in enumerate(images):
            print(f"📝 Processing page {i+1}/{len(images)}...")
            
            # Detect columns
            columns, has_columns = self.detect_columns(image)
            
            if has_columns:
                print(f"  📊 Detected 2-column layout")
            
            # Process each column
            for j, col_image in enumerate(columns):
                # Preprocess
                processed = self.preprocess_image(col_image)
                
                # Try EasyOCR first (more accurate)
                try:
                    text = self.extract_text_with_easyocr(processed)
                except:
                    # Fallback to Tesseract
                    text = self.extract_text_with_tesseract(processed)
                
                all_text += text + ""
                
                if has_columns:
                    print(f"    ✅ Column {j+1} extracted")
        
        # Parse questions
        questions = self.parse_questions(all_text)
        
        print(f"✅ Extracted {len(questions)} questions")
        
        return questions

class SimplifiedOCRExtractor:
    """Simpler version using just Tesseract"""
    
    def __init__(self):
        self.questions = []
    
    def extract_from_pdf(self, pdf_path):
        """Extract using Tesseract only"""
        print(f"📄 Processing: {os.path.basename(pdf_path)}")
        
        # Convert PDF to images
        print("📖 Converting PDF to images...")
        images = convert_from_path(pdf_path, dpi=300)
        
        all_text = ""
        
        for i, image in enumerate(images):
            print(f"📝 Processing page {i+1}/{len(images)}...")
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Enhance contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2)
            
            # OCR with specific config for 2-column layout
            custom_config = r'--oem 3 --psm 3 -l eng'  # PSM 3 for automatic page segmentation
            
            text = pytesseract.image_to_string(image, config=custom_config)
            all_text += text + ""
        
        # Parse questions
        questions = self.parse_questions(all_text)
        
        print(f"✅ Extracted {len(questions)} questions")
        
        return questions
    
    def parse_questions(self, text):
        """Simple but robust parsing"""
        questions = []
        
        # Split into lines and reconstruct
        lines = text.split(' ')
        
        current_q = None
        q_text = ""
        options = {}
        
        for line in lines:
            line = line.strip()
            
            # Check for question start - very flexible patterns
            q_patterns = [
                r'^Q\.?\s*(\d+)\s*\)',
                r'^(\d+)\s*\)',
                r'^Question\s+(\d+)',
            ]
            
            matched = False
            for pattern in q_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous question
                    if current_q and q_text:
                        questions.append({
                            "number": current_q,
                            "text": q_text.strip(),
                            "options": options
                        })
                    
                    # Start new question
                    current_q = int(match.group(1))
                    q_text = line[match.end():].strip()
                    options = {}
                    matched = True
                    break
            
            if not matched and current_q:
                # Check for options
                opt_match = re.match(r'^[$$$]?([a-e])[$$$\.]\s*(.*)', line, re.IGNORECASE)
                if opt_match:
                    letter = opt_match.group(1).upper()
                    options[letter] = opt_match.group(2).strip()
                elif line:
                    q_text += " " + line
        
        # Save last question
        if current_q and q_text:
            questions.append({
                "number": current_q,
                "text": q_text.strip(),
                "options": options
            })
        
        return questions

def main():
    """Main function"""
    
    # Choose extractor
    print("🎯 OCR-based PDF Question Extractor")
    print("=" * 50)
    
    # Check dependencies
    try:
        import easyocr
        print("✅ EasyOCR available - using advanced extractor")
        extractor = AdvancedPDFExtractor(use_gpu=False)
    except ImportError:
        print("📦 EasyOCR not found - using simplified extractor")
        extractor = SimplifiedOCRExtractor()
    
    # Process all PDFs
    pdf_folder = "rbi_pdf"
    
    if not os.path.exists(pdf_folder):
        print(f"❌ Folder {pdf_folder} not found")
        return
    
    pdfs = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    
    if not pdfs:
        print(f"❌ No PDFs found in {pdf_folder}")
        return
    
    print(f"📚 Found {len(pdfs)} PDFs to process")
    
    all_results = {}
    
    for pdf in pdfs:
        pdf_path = os.path.join(pdf_folder, pdf)
        
        try:
            questions = extractor.extract_from_pdf(pdf_path)
            
            all_results[pdf] = {
                "filename": pdf,
                "total": len(questions),
                "questions": questions
            }
            
        except Exception as e:
            print(f"❌ Error processing {pdf}: {e}")
            all_results[pdf] = {
                "filename": pdf,
                "total": 0,
                "questions": [],
                "error": str(e)
            }
    
    # Save results
    output_file = "extracted_questions_ocr.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Complete! Results saved to {output_file}")
    
    # Summary
    print("📊 Extraction Summary:")
    print("-" * 40)
    
    total_questions = 0
    for pdf, data in all_results.items():
        count = data['total']
        total_questions += count
        status = "✅" if count > 0 else "❌"
        print(f"{status} {pdf}: {count} questions")
    
    print("-" * 40)
    print(f"📈 Total: {total_questions} questions from {len(pdfs)} PDFs")

if __name__ == "__main__":
    main()
