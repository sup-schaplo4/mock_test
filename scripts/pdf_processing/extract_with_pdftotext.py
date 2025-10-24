# extract_with_pdftotext.py
import subprocess
import re
import json
import os

def extract_with_pdftotext(pdf_path):
    """Use pdftotext with layout preservation"""
    
    print("🔧 Using pdftotext with layout preservation...")
    
    # Output text file
    txt_file = "temp_extracted.txt"
    
    try:
        # Use pdftotext with layout flag
        # -layout : maintains original physical layout
        result = subprocess.run([
            'pdftotext',
            '-layout',  # Preserve layout
            pdf_path,
            txt_file
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return []
        
        # Read the extracted text
        with open(txt_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"✅ Extracted {len(text)} characters")
        
        # Save for inspection
        with open('layout_preserved.txt', 'w') as f:
            f.write(text)
        print("💾 Saved layout-preserved text to layout_preserved.txt")
        
        # Process the text
        questions = process_layout_text(text)
        
        # Clean up
        os.remove(txt_file)
        
        return questions
        
    except FileNotFoundError:
        print("❌ pdftotext not found. Install with:")
        print("   Ubuntu/Debian: sudo apt-get install poppler-utils")
        print("   Mac: brew install poppler")
        print("   Windows: Download from https://blog.alivate.com.au/poppler-windows/")
        return []

def process_layout_text(text):
    """Process text that maintains layout"""
    
    # The layout-preserved text should have columns side by side
    # We need to process it carefully
    
    lines = text.split(' ')
    
    # Reconstruct by detecting column positions
    all_text = []
    
    for line in lines:
        if line.strip():
            # Check if line has content in both columns
            # Usually there's significant spacing between columns
            if '     ' in line:  # Multiple spaces indicate column separator
                parts = re.split(r'\s{5,}', line)
                all_text.extend(parts)
            else:
                all_text.append(line)
    
    # Join and extract questions
    combined = ' '.join(all_text)
    
    # Extract questions
    questions = []
    pattern = r'Q\.(\d+)\)(.*?)(?=Q\.\d+\)|$)'
    
    for match in re.finditer(pattern, combined, re.DOTALL):
        # ... same extraction logic ...
        pass
    
    return questions

# Install pdftotext:
# Ubuntu/Debian: sudo apt-get install poppler-utils
# Mac: brew install poppler

extract_with_pdftotext("rbi_pdf/RBI_PYP_PHASE_01_2023_General_Awareness_Questions.pdf")